<?php
/**
 * 301s from the old site's URLs (docs/02-information-architecture.md §5).
 *
 * ON PRODUCTION: import these into Rank Math → Redirections (so marketing can
 * manage them), then set HM_PHP_REDIRECTS to false in wp-config.php.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

function hm_redirect_map(): array {
	return array(
		// '/old-url/' => '/new-url/',  (from docs/02-information-architecture.md §4)
	);
}

/** Paths that are gone for good (410). */
function hm_gone_paths(): array {
	return array();
}

add_action(
	'template_redirect',
	function () {
		if ( defined( 'HM_PHP_REDIRECTS' ) && ! HM_PHP_REDIRECTS ) {
			return;
		}
		$path = '/' . trim( (string) wp_parse_url( $_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH ), '/' ) . '/'; // phpcs:ignore
		$map  = hm_redirect_map();
		if ( isset( $map[ $path ] ) ) {
			wp_safe_redirect( home_url( $map[ $path ] ), 301, 'ASF Base' );
			exit;
		}
		if ( in_array( $path, hm_gone_paths(), true ) ) {
			status_header( 410 );
			nocache_headers();
		}
	},
	0
);

// Never let WordPress guess a destination for a 404 (it picks wrong pages). Explicit map only.
add_filter( 'do_redirect_guess_404_permalink', '__return_false' );
