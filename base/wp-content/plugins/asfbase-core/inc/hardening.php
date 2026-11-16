<?php
/**
 * Hardening every marketing site needs, on by default.
 *
 * Each piece can be turned off in wp-config.php when a client really needs it. Record the reason
 * in docs/decisions.md.
 *
 *   ASF_SECURITY_HEADERS  false  don't send the headers below (e.g. the host's edge already does)
 *   ASF_HSTS              false  no Strict-Transport-Security (it's only ever sent over HTTPS)
 *   ASF_CSP               '…'    a Content-Security-Policy to enforce (none by default: analytics,
 *                                tag managers and embeds each need their own sources)
 *   ASF_CSP_REPORT_ONLY   '…'    the same, report-only, to tune a policy before enforcing it
 *   ASF_ALLOW_XMLRPC      true   keep XML-RPC (Jetpack and the WordPress mobile app need it)
 *   ASF_AUTHOR_ARCHIVES   true   keep /author/… pages (they reveal login names)
 *   DISALLOW_FILE_EDIT    false  allow the theme and plugin file editor in wp-admin
 *
 * The site is checked from outside by `docs/framework/qa/launch.py --only security`.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

/** A wp-config switch: the constant's value when it's defined, the default otherwise. */
function hm_flag( string $name, bool $default ): bool {
	return defined( $name ) ? (bool) constant( $name ) : $default;
}

// ── XML-RPC: an old remote API that's mostly used to guess passwords. ─────────────────────
if ( ! hm_flag( 'ASF_ALLOW_XMLRPC', false ) ) {
	if ( defined( 'XMLRPC_REQUEST' ) && XMLRPC_REQUEST ) {
		status_header( 403 );
		header( 'Content-Type: text/plain; charset=utf-8' );
		echo 'XML-RPC is turned off on this site.';
		exit;
	}
	add_filter( 'xmlrpc_enabled', '__return_false' );
	add_filter( 'pings_open', '__return_false' );
	add_filter(
		'wp_headers',
		static function ( array $headers ) {
			unset( $headers['X-Pingback'] );
			return $headers;
		}
	);
	remove_action( 'wp_head', 'rsd_link' );
}

// ── The theme and plugin file editor: one stolen admin login away from running any code. ──
if ( ! defined( 'DISALLOW_FILE_EDIT' ) ) {
	define( 'DISALLOW_FILE_EDIT', true );
}

// ── Security headers on every front-end response. ──────────────────────────────────────────
add_action(
	'send_headers',
	static function () {
		if ( ! hm_flag( 'ASF_SECURITY_HEADERS', true ) || headers_sent() ) {
			return;
		}
		$headers = array(
			'X-Content-Type-Options' => 'nosniff',
			'X-Frame-Options'        => 'SAMEORIGIN',
			'Referrer-Policy'        => 'strict-origin-when-cross-origin',
			'Permissions-Policy'     => 'camera=(), microphone=(), geolocation=(), payment=(), usb=()',
		);
		if ( is_ssl() && hm_flag( 'ASF_HSTS', true ) && 'local' !== wp_get_environment_type() ) {
			$headers['Strict-Transport-Security'] = 'max-age=31536000';
		}
		if ( defined( 'ASF_CSP' ) && ASF_CSP ) {
			$headers['Content-Security-Policy'] = (string) ASF_CSP;
		}
		if ( defined( 'ASF_CSP_REPORT_ONLY' ) && ASF_CSP_REPORT_ONLY ) {
			$headers['Content-Security-Policy-Report-Only'] = (string) ASF_CSP_REPORT_ONLY;
		}
		foreach ( (array) apply_filters( 'hm_security_headers', $headers ) as $name => $value ) {
			header( "{$name}: {$value}" );
		}
		header_remove( 'X-Powered-By' );
	}
);

// ── Don't advertise the WordPress version. ──────────────────────────────────────────────────
remove_action( 'wp_head', 'wp_generator' );
add_filter( 'the_generator', '__return_empty_string' );

/** Core assets carry ?ver=<WordPress version>. Keep the cache-busting, lose the version. */
function hm_hide_core_version( $src ) {
	static $hash = null;
	if ( is_admin() || ! is_string( $src ) ) {
		return $src;
	}
	$version = get_bloginfo( 'version' );
	$hash  ??= substr( md5( $version . wp_salt( 'nonce' ) ), 0, 8 );
	return preg_replace( '/([?&]ver=)' . preg_quote( $version, '/' ) . '(?=&|$)/', '${1}' . $hash, $src );
}
add_filter( 'style_loader_src', 'hm_hide_core_version', 20 );
add_filter( 'script_loader_src', 'hm_hide_core_version', 20 );

// ── Login names: never reveal them to visitors. ────────────────────────────────────────────
if ( ! hm_flag( 'ASF_AUTHOR_ARCHIVES', false ) ) {
	// /?author=1 normally redirects to /author/<login>/. Visitors get a 404 instead.
	add_action(
		'template_redirect',
		static function () {
			if ( is_author() && ! is_user_logged_in() ) {
				global $wp_query;
				$wp_query->set_404();
				status_header( 404 );
				nocache_headers();
				remove_action( 'template_redirect', 'redirect_canonical' );
			}
		},
		1
	);
	add_filter( 'wp_sitemaps_add_provider', static fn( $provider, $name ) => 'users' === $name ? false : $provider, 10, 2 );
}

// The users API lists every author's login slug to anyone who asks.
add_filter(
	'rest_pre_dispatch',
	static function ( $result, $server, $request ) {
		if ( null === $result && str_starts_with( $request->get_route(), '/wp/v2/users' ) && ! is_user_logged_in() ) {
			return new WP_Error( 'rest_forbidden', 'Sorry, you are not allowed to do that.', array( 'status' => 401 ) );
		}
		return $result;
	},
	10,
	3
);

// oEmbed responses name the author and link to their archive.
add_filter(
	'oembed_response_data',
	static function ( array $data ) {
		unset( $data['author_name'], $data['author_url'] );
		return $data;
	}
);

// A failed login says which half was wrong. Say neither.
add_filter( 'login_errors', static fn() => 'Those details didn’t work. Check them and try again, or reset your password.' );
