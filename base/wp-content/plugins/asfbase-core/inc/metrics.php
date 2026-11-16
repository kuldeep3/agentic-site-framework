<?php
/**
 * Private metrics for the weekly report and campaign results:
 *   GET /wp-json/asfbase/v1/metrics?from=2026-11-09&to=2026-11-15
 *   GET /wp-json/asfbase/v1/metrics?from=2026-12-01&to=2026-12-14&campaign=spring-audit   (one campaign)
 *
 * Admins only. Scripts sign in with an Application Password (Users → Profile → Application
 * Passwords), never the real password. Leads are first-party data: no analytics account is needed to know how many
 * enquiries came in this week, what they asked for, and which pages, sources and campaigns sent them.
 * The response compares the range with the same number of days before it.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

add_action(
	'rest_api_init',
	function () {
		register_rest_route(
			'asfbase/v1',
			'/metrics',
			array(
				'methods'             => 'GET',
				'permission_callback' => static fn() => current_user_can( 'manage_options' ),
				'callback'            => 'hm_metrics',
				'args'                => array(
					'from'     => array( 'type' => 'string', 'pattern' => '^\d{4}-\d{2}-\d{2}$' ),
					'to'       => array( 'type' => 'string', 'pattern' => '^\d{4}-\d{2}-\d{2}$' ),
					'campaign' => array( 'type' => 'string', 'pattern' => '^[a-z0-9-]{1,80}$' ),
				),
			)
		);
	}
);

/**
 * Count leads created between two dates (inclusive), grouped the ways a weekly report needs.
 * With $campaign: only leads whose utm_campaign matches, plus counts by creative (utm_content) and by day.
 */
function hm_metrics_leads( string $from, string $to, string $campaign = '' ): array {
	$ids = get_posts(
		array(
			'post_type'      => 'hm_lead',
			'post_status'    => array( 'private', 'publish' ),
			'posts_per_page' => -1,
			'fields'         => 'ids',
			'date_query'     => array( array( 'after' => "{$from} 00:00:00", 'before' => "{$to} 23:59:59", 'inclusive' => true ) ),
		)
	);
	$out = array(
		'total'       => 0,
		'brief'       => 0,
		'newsletter'  => 0,
		'by_need'     => array(),
		'by_budget'   => array(),
		'by_page'     => array(),
		'by_landing'  => array(),
		'by_source'   => array(),
		'by_medium'   => array(),
		'by_campaign' => array(),
	);
	if ( $campaign ) {
		$out += array( 'by_content' => array(), 'by_day' => array() );
	}
	$home = wp_parse_url( home_url(), PHP_URL_HOST );
	$add  = static function ( array &$bucket, string $key ) {
		$bucket[ $key ] = ( $bucket[ $key ] ?? 0 ) + 1;
	};
	foreach ( $ids as $id ) {
		$utm = (array) get_post_meta( $id, 'hm_utm', true );
		$cmp = sanitize_title( (string) ( $utm['utm_campaign'] ?? '' ) );
		if ( $campaign && $cmp !== $campaign ) {
			continue;
		}
		$type = 'newsletter' === get_post_meta( $id, 'hm_type', true ) ? 'newsletter' : 'brief';
		++$out['total'];
		++$out[ $type ];
		$page    = (string) get_post_meta( $id, 'hm_page', true );
		$landing = (string) get_post_meta( $id, 'hm_landing', true );
		$add( $out['by_page'], '' !== $page ? $page : '(unknown)' );
		$add( $out['by_landing'], '' !== $landing ? $landing : ( '' !== $page ? $page : '(unknown)' ) );
		$source = (string) ( $utm['utm_source'] ?? '' );
		if ( '' === $source ) {
			$ref_host = wp_parse_url( (string) get_post_meta( $id, 'hm_referrer', true ), PHP_URL_HOST );
			$source   = ( $ref_host && $ref_host !== $home ) ? $ref_host : 'direct';
		}
		$add( $out['by_source'], $source );
		$add( $out['by_medium'], (string) ( $utm['utm_medium'] ?? '' ) ?: '(none)' );
		if ( $cmp ) {
			$add( $out['by_campaign'], $cmp );
		}
		if ( $campaign ) {
			$add( $out['by_content'], (string) ( $utm['utm_content'] ?? '' ) ?: '(none)' );
			$add( $out['by_day'], (string) get_the_date( 'Y-m-d', $id ) );
		}
		if ( 'brief' === $type ) {
			foreach ( (array) get_post_meta( $id, 'hm_needs', true ) as $need ) {
				$add( $out['by_need'], (string) $need );
			}
			$budget = (string) get_post_meta( $id, 'hm_budget', true );
			if ( '' !== $budget ) {
				$add( $out['by_budget'], $budget );
			}
		}
	}
	foreach ( array( 'by_need', 'by_budget', 'by_page', 'by_landing', 'by_source', 'by_medium', 'by_campaign', 'by_content' ) as $k ) {
		if ( isset( $out[ $k ] ) ) {
			arsort( $out[ $k ] );
		}
	}
	if ( isset( $out['by_day'] ) ) {
		ksort( $out['by_day'] );
	}
	// An empty breakdown is still an object in JSON ({}, not []), so readers can always look keys up.
	foreach ( $out as $k => $v ) {
		if ( is_array( $v ) && ! $v ) {
			$out[ $k ] = new stdClass();
		}
	}
	return $out;
}

function hm_metrics( WP_REST_Request $req ) {
	$tz     = wp_timezone();
	$to     = $req->get_param( 'to' ) ?: ( new DateTimeImmutable( 'yesterday', $tz ) )->format( 'Y-m-d' );
	$from   = $req->get_param( 'from' ) ?: ( new DateTimeImmutable( $to, $tz ) )->modify( '-6 days' )->format( 'Y-m-d' );
	$days   = (int) ( new DateTimeImmutable( $from, $tz ) )->diff( new DateTimeImmutable( $to, $tz ) )->days + 1;
	$p_to   = ( new DateTimeImmutable( $from, $tz ) )->modify( '-1 day' );
	$p_from = $p_to->modify( '-' . ( $days - 1 ) . ' days' );
	$cmp    = (string) $req->get_param( 'campaign' );

	return rest_ensure_response(
		array(
			'site'      => home_url( '/' ),
			'from'      => $from,
			'to'        => $to,
			'campaign'  => '' !== $cmp ? $cmp : null,
			'generated' => gmdate( 'c' ),
			'leads'     => hm_metrics_leads( $from, $to, $cmp ),
			'previous'  => array(
				'from'  => $p_from->format( 'Y-m-d' ),
				'to'    => $p_to->format( 'Y-m-d' ),
				'leads' => hm_metrics_leads( $p_from->format( 'Y-m-d' ), $p_to->format( 'Y-m-d' ), $cmp ),
			),
			'content'   => array(
				'pages'        => (int) wp_count_posts( 'page' )->publish,
				'case_studies' => (int) wp_count_posts( 'case_study' )->publish,
				'posts'        => (int) wp_count_posts( 'post' )->publish,
			),
		)
	);
}
