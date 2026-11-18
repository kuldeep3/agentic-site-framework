<?php
/**
 * 301s from the old site's URLs (docs/02-information-architecture.md §4).
 *
 * Three kinds of rule, checked in this order:
 *   1. exact paths (hm_redirect_map), then 410 Gone for exact paths (hm_gone_paths),
 *   2. path prefixes, for the old site's archives and custom post types, where hundreds of
 *      thin URLs share one new home (hm_redirect_prefixes; the longest prefix wins),
 *   3. 410 Gone for prefixes with no new home (hm_gone_prefixes).
 * A target may carry a fragment (/awards/x/#past-winners): browsers keep it, so the anchor must
 * exist on the new page. Redirects only fire for paths WordPress can't serve itself (404), so a
 * rule never shadows a real page.
 *
 * ON PRODUCTION: import these into the SEO plugin's redirections (so marketing can
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

/**
 * Every path under a prefix goes to one place, e.g.
 *   '/press-release/'    => '/news/',
 *   '/past_winners/'     => '/awards/#past-winners',
 */
function hm_redirect_prefixes(): array {
	return array();
}

/** Paths that are gone for good (410). */
function hm_gone_paths(): array {
	return array();
}

/** Prefixes that are gone for good (410), e.g. empty archives: '/tag/', '/author/'. */
function hm_gone_prefixes(): array {
	return array();
}

/** Where an old path goes: a target path, 'gone', or '' (no rule). */
function hm_redirect_target( string $path ): string {
	$map = hm_redirect_map();
	if ( isset( $map[ $path ] ) ) {
		return $map[ $path ];
	}
	if ( in_array( $path, hm_gone_paths(), true ) ) {
		return 'gone';
	}
	// A dynamic rule, when old single pages map one-to-one onto anchors of a new list, e.g.:
	// if ( preg_match( '#^/publication/([a-z0-9-]+)/$#', $path, $m ) ) {
	// 	return '/publications/#' . $m[1]; // Each row on /publications/ carries the old slug as its id.
	// }
	$prefixes = hm_redirect_prefixes();
	uksort( $prefixes, static fn( $a, $b ) => strlen( $b ) <=> strlen( $a ) );
	foreach ( $prefixes as $prefix => $target ) {
		if ( str_starts_with( $path, $prefix ) ) {
			return $target;
		}
	}
	foreach ( hm_gone_prefixes() as $prefix ) {
		if ( str_starts_with( $path, $prefix ) ) {
			return 'gone';
		}
	}
	return '';
}

add_action(
	'template_redirect',
	function () {
		if ( defined( 'HM_PHP_REDIRECTS' ) && ! HM_PHP_REDIRECTS ) {
			return;
		}
		$path   = '/' . trim( (string) wp_parse_url( $_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH ), '/' ) . '/'; // phpcs:ignore
		$target = hm_redirect_target( $path );
		if ( 'gone' === $target ) {
			status_header( 410 );
			nocache_headers();
			return;
		}
		// Only redirect what WordPress can't serve itself (never shadow a real page).
		if ( '' !== $target && is_404() ) {
			wp_safe_redirect( home_url( $target ), 301, 'ASF Base' );
			exit;
		}
	},
	0
);

// Never let WordPress guess a destination for a 404 (it picks wrong pages). Explicit map only.
add_filter( 'do_redirect_guess_404_permalink', '__return_false' );
