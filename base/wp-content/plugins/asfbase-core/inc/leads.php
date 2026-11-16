<?php
/**
 * Lead capture: POST /wp-json/asfbase/v1/leads
 *
 * Receives the brief form, the audit form and newsletter signups. Each lead is
 * saved as a private `hm_lead` post (Dashboard → Leads) and emailed to
 * hm_entity('lead_email'). Spam defence without CAPTCHAs: honeypot field,
 * minimum time on page, and a per-IP rate limit.
 *
 * To send leads to a CRM later (HubSpot, etc.), hook `hm_lead_created`.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

const HM_LEAD_FIELDS = array( 'name', 'email', 'company', 'website', 'phone', 'message', 'budget', 'timeline', 'variant' );

add_action(
	'rest_api_init',
	function () {
		register_rest_route(
			'asfbase/v1',
			'/leads',
			array(
				'methods'             => 'POST',
				'permission_callback' => '__return_true', // Public form; abuse is handled in hm_lead_guard().
				'callback'            => 'hm_lead_create',
			)
		);
	}
);

/** @return true|WP_Error */
function hm_lead_guard( WP_REST_Request $req ) {
	// Bots fill hidden fields and submit instantly.
	if ( '' !== (string) $req->get_param( 'company_url' ) ) {
		return new WP_Error( 'hm_spam', 'Thanks!', array( 'status' => 200 ) );
	}
	if ( 'brief' === $req->get_param( 'type' ) && (int) $req->get_param( 'elapsed' ) < 4 ) {
		return new WP_Error( 'hm_too_fast', 'That was quick. Please try again in a moment.', array( 'status' => 429 ) );
	}
	$ip_key = 'hm_lead_rl_' . md5( (string) ( $_SERVER['REMOTE_ADDR'] ?? '' ) ); // phpcs:ignore
	$count  = (int) get_transient( $ip_key );
	if ( $count >= 8 ) {
		return new WP_Error( 'hm_rate', 'Too many submissions. Please call us instead.', array( 'status' => 429 ) );
	}
	set_transient( $ip_key, $count + 1, HOUR_IN_SECONDS );
	return true;
}

function hm_lead_create( WP_REST_Request $req ) {
	$guard = hm_lead_guard( $req );
	if ( is_wp_error( $guard ) ) {
		return 'hm_spam' === $guard->get_error_code() ? rest_ensure_response( array( 'ok' => true ) ) : $guard;
	}

	$type  = in_array( $req->get_param( 'type' ), array( 'brief', 'newsletter' ), true ) ? $req->get_param( 'type' ) : 'brief';
	$email = sanitize_email( (string) $req->get_param( 'email' ) );
	if ( ! is_email( $email ) ) {
		return new WP_Error( 'hm_email', 'Please enter a valid email address.', array( 'status' => 400 ) );
	}

	$data = array( 'type' => $type, 'email' => $email );
	foreach ( HM_LEAD_FIELDS as $field ) {
		$value = $req->get_param( $field );
		if ( null !== $value && 'email' !== $field ) {
			$data[ $field ] = 'message' === $field ? sanitize_textarea_field( (string) $value ) : sanitize_text_field( (string) $value );
		}
	}
	if ( 'brief' === $type && empty( $data['name'] ) ) {
		return new WP_Error( 'hm_name', 'Please tell us your name.', array( 'status' => 400 ) );
	}
	$data['needs']    = array_map( 'sanitize_key', (array) $req->get_param( 'needs' ) );
	$data['page']     = esc_url_raw( (string) $req->get_param( 'page' ) );
	$data['referrer'] = esc_url_raw( (string) $req->get_param( 'referrer' ) );
	$data['utm']      = array_map( 'sanitize_text_field', array_slice( (array) $req->get_param( 'utm' ), 0, 8 ) );

	$title   = 'newsletter' === $type ? "Newsletter: {$email}" : trim( ( $data['name'] ?? '' ) . ( ! empty( $data['company'] ) ? " · {$data['company']}" : '' ) );
	$lead_id = wp_insert_post(
		array(
			'post_type'   => 'hm_lead',
			'post_status' => 'private',
			'post_title'  => $title ?: $email,
		),
		true
	);
	if ( is_wp_error( $lead_id ) ) {
		return new WP_Error( 'hm_save', 'We couldn’t save that. Please call us.', array( 'status' => 500 ) );
	}
	foreach ( $data as $key => $value ) {
		update_post_meta( $lead_id, "hm_{$key}", $value );
	}

	if ( 'brief' === $type ) {
		hm_lead_notify( $lead_id, $data );
	}
	do_action( 'hm_lead_created', $lead_id, $data );

	return rest_ensure_response( array( 'ok' => true ) );
}

function hm_lead_notify( int $lead_id, array $data ): void {
	$lines = array(
		'New brief from the website',
		'',
		'Name:     ' . ( $data['name'] ?? '' ),
		'Email:    ' . $data['email'],
		'Company:  ' . ( $data['company'] ?? '' ),
		'Website:  ' . ( $data['website'] ?? '' ),
		'Phone:    ' . ( $data['phone'] ?? '' ),
		'Needs:    ' . implode( ', ', $data['needs'] ),
		'Budget:   ' . ( $data['budget'] ?? '' ),
		'Timeline: ' . ( $data['timeline'] ?? '' ),
		'Page:     ' . $data['page'],
		'Source:   ' . ( $data['utm']['utm_source'] ?? ( $data['referrer'] ?: 'direct' ) ),
		'',
		$data['message'] ?? '',
		'',
		'Open in WordPress: ' . admin_url( "post.php?post={$lead_id}&action=edit" ),
	);
	wp_mail(
		(string) hm_entity( 'lead_email' ),
		'New brief: ' . ( $data['name'] ?? $data['email'] ) . ( ! empty( $data['budget'] ) ? " ({$data['budget']})" : '' ),
		implode( "\n", $lines ),
		array( 'Reply-To: ' . ( $data['name'] ?? '' ) . ' <' . $data['email'] . '>' )
	);
}

// Leads list: the columns a strategist scans first.
add_filter(
	'manage_hm_lead_posts_columns',
	fn( $cols ) => array(
		'cb'          => $cols['cb'],
		'title'       => 'Lead',
		'hm_type'     => 'Type',
		'hm_needs'    => 'Needs',
		'hm_budget'   => 'Budget',
		'hm_timeline' => 'Timeline',
		'hm_source'   => 'Source',
		'date'        => 'Received',
	)
);
add_action(
	'manage_hm_lead_posts_custom_column',
	function ( $col, $id ) {
		if ( 'hm_needs' === $col ) {
			echo esc_html( implode( ', ', (array) get_post_meta( $id, 'hm_needs', true ) ) );
		} elseif ( 'hm_source' === $col ) {
			$utm = (array) get_post_meta( $id, 'hm_utm', true );
			$ref = (string) get_post_meta( $id, 'hm_referrer', true );
			echo esc_html( $utm['utm_source'] ?? ( $ref ? wp_parse_url( $ref, PHP_URL_HOST ) : 'direct' ) );
		} elseif ( str_starts_with( $col, 'hm_' ) ) {
			echo esc_html( (string) get_post_meta( $id, $col, true ) );
		}
	},
	10,
	2
);
