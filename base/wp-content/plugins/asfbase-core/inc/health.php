<?php
/**
 * Private site health for launch checks and the weekly report:
 *   GET /wp-json/asfbase/v1/health
 *
 * Admins only (an Application Password, like the metrics endpoint). It reports what an outside
 * scan can't see: pending updates, risky settings, admin accounts, sample content left behind,
 * and whether lead emails are failing. It returns counts and yes/no answers only, never names,
 * emails or logins, because the result is saved in the project's reports.
 *
 * Used by `docs/framework/qa/launch.py` (security and launch checks) and `bin/asf report`.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

// Remember the last time WordPress failed to send an email (the lead notification, usually).
add_action(
	'wp_mail_failed',
	static function ( WP_Error $error ) {
		$prev = (array) get_option( 'hm_mail_failed', array() );
		update_option(
			'hm_mail_failed',
			array(
				'at'    => gmdate( 'c' ),
				'error' => substr( (string) preg_replace( '/[^\s@<>]+@[^\s@<>]+/', '[email]', $error->get_error_message() ), 0, 160 ),
				'count' => (int) ( $prev['count'] ?? 0 ) + 1,
			),
			false
		);
	}
);

add_action(
	'rest_api_init',
	static function () {
		register_rest_route(
			'asfbase/v1',
			'/health',
			array(
				'methods'             => 'GET',
				'permission_callback' => static fn() => current_user_can( 'manage_options' ),
				'callback'            => 'hm_health',
			)
		);
	}
);

/** Pending updates from WordPress's own update check (no outbound request is made here). */
function hm_health_updates(): array {
	if ( ! function_exists( 'get_plugins' ) ) {
		require_once ABSPATH . 'wp-admin/includes/plugin.php';
	}
	$core    = get_site_transient( 'update_core' );
	$plugins = get_site_transient( 'update_plugins' );
	$themes  = get_site_transient( 'update_themes' );
	$all     = get_plugins();
	$out     = array(
		'checked'     => isset( $plugins->last_checked ) ? gmdate( 'c', (int) $plugins->last_checked ) : null,
		'wordpress'   => null,
		'plugins'     => array(),
		'themes'      => array(),
	);
	foreach ( (array) ( $core->updates ?? array() ) as $offer ) {
		if ( 'upgrade' === ( $offer->response ?? '' ) ) {
			$out['wordpress'] = $offer->current ?? $offer->version ?? 'available';
			break;
		}
	}
	foreach ( (array) ( $plugins->response ?? array() ) as $file => $info ) {
		$out['plugins'][] = array(
			'name' => $all[ $file ]['Name'] ?? $file,
			'from' => $all[ $file ]['Version'] ?? '',
			'to'   => $info->new_version ?? '',
		);
	}
	foreach ( (array) ( $themes->response ?? array() ) as $slug => $info ) {
		$theme            = wp_get_theme( $slug );
		$out['themes'][] = array(
			'name' => $theme->exists() ? $theme->get( 'Name' ) : $slug,
			'from' => $theme->exists() ? $theme->get( 'Version' ) : '',
			'to'   => $info['new_version'] ?? '',
		);
	}
	return $out;
}

function hm_health() {
	if ( ! function_exists( 'get_plugins' ) ) {
		require_once ABSPATH . 'wp-admin/includes/plugin.php';
	}
	$active   = (array) get_option( 'active_plugins', array() );
	$inactive = array_diff( array_keys( get_plugins() ), $active );
	$smtp     = array_values(
		array_filter(
			$active,
			static fn( $file ) => (bool) preg_match( '/smtp|mailgun|sendgrid|postmark|wp-ses|mailjet|brevo|sendinblue/i', $file )
		)
	);
	$sample = array();
	foreach ( array( 'post' => 'hello-world', 'page' => 'sample-page' ) as $type => $slug ) {
		$found = get_page_by_path( $slug, OBJECT, $type );
		if ( $found && 'publish' === $found->post_status ) {
			$sample[] = "{$type}: {$slug}";
		}
	}
	$admins = get_users( array( 'role' => 'administrator', 'fields' => array( 'user_login' ) ) );
	$lead   = (string) hm_entity( 'lead_email' );

	return rest_ensure_response(
		array(
			'site'        => home_url( '/' ),
			'generated'   => gmdate( 'c' ),
			'environment' => wp_get_environment_type(),
			'versions'    => array(
				'wordpress' => get_bloginfo( 'version' ),
				'php'       => PHP_VERSION,
			),
			'updates'     => hm_health_updates(),
			'plugins'     => array(
				'active'   => count( $active ),
				'inactive' => count( $inactive ),
			),
			'settings'    => array(
				'search_engines_allowed' => '1' === (string) get_option( 'blog_public' ),
				'https'                  => str_starts_with( home_url(), 'https://' ) && str_starts_with( site_url(), 'https://' ),
				'file_editor_off'        => defined( 'DISALLOW_FILE_EDIT' ) && DISALLOW_FILE_EDIT,
				'errors_shown'           => defined( 'WP_DEBUG' ) && WP_DEBUG && ( ! defined( 'WP_DEBUG_DISPLAY' ) || WP_DEBUG_DISPLAY ),
				'anyone_can_register'    => (bool) get_option( 'users_can_register' ),
				'comments_open'          => 'open' === get_option( 'default_comment_status' ),
				'xmlrpc'                 => hm_flag( 'ASF_ALLOW_XMLRPC', false ),
				'security_headers'       => hm_flag( 'ASF_SECURITY_HEADERS', true ),
			),
			'users'       => array(
				'administrators' => count( $admins ),
				'login_admin'    => (bool) array_filter( $admins, static fn( $u ) => in_array( strtolower( $u->user_login ), array( 'admin', 'administrator' ), true ) ),
			),
			'content'     => array( 'sample_content' => $sample ),
			'email'       => array(
				'lead_email'  => is_email( $lead ) ? 'set' : 'missing',
				'smtp_plugin' => $smtp ? dirname( $smtp[0] ) : null,
				'last_failed' => get_option( 'hm_mail_failed' ) ?: null,
			),
		)
	);
}
