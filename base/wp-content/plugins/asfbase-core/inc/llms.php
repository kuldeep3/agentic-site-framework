<?php
/**
 * /llms.txt — a plain-Markdown map of the site for AI assistants (llmstxt.org).
 *
 * Generated live from published content, so it never goes stale: entity
 * summary → services (with their meta descriptions) → case studies (with the
 * headline number) → company pages → contact. Cached for an hour; the cache
 * clears whenever a page or case study is saved.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

function hm_llms_rewrite(): void {
	add_rewrite_rule( '^llms\.txt$', 'index.php?hm_llms=1', 'top' );
}
add_action( 'init', 'hm_llms_rewrite' );
add_filter( 'query_vars', fn( $vars ) => array_merge( $vars, array( 'hm_llms' ) ) );

add_action(
	'template_redirect',
	function () {
		if ( ! get_query_var( 'hm_llms' ) ) {
			return;
		}
		$body = get_transient( 'hm_llms_txt' );
		if ( false === $body ) {
			$body = hm_llms_build();
			set_transient( 'hm_llms_txt', $body, HOUR_IN_SECONDS );
		}
		status_header( 200 );
		header( 'Content-Type: text/plain; charset=utf-8' );
		header( 'X-Robots-Tag: noindex' );
		echo $body; // phpcs:ignore WordPress.Security.EscapeOutput
		exit;
	},
	1 // Before redirect_canonical (priority 10), which would add a trailing slash.
);
add_action( 'save_post', fn() => delete_transient( 'hm_llms_txt' ) );

function hm_llms_build(): string {
	$e     = hm_entity();
	$line  = fn( WP_Post $p, string $extra = '' ) => sprintf( '- [%s](%s): %s%s', html_entity_decode( get_the_title( $p ), ENT_QUOTES, 'UTF-8' ), get_permalink( $p ), hm_meta_description( $p->ID ), $extra );
	$out   = array();
	$out[] = '# ' . $e['name'];
	$out[] = '';
	$out[] = '> ' . $e['description'];
	$out[] = '';
	$out[] = 'Key facts:';
	// Empty facts are left out: a blank "Founders:" line reads as a broken fact, not a missing one.
	if ( ! empty( $e['alternate'] ) ) {
		$out[] = '- Also known as: ' . implode( ', ', (array) $e['alternate'] );
	}
	if ( ! empty( $e['founders'] ) ) {
		$out[] = '- Founders: ' . implode( '; ', array_map( fn( $f ) => trim( $f['name'] . ( ! empty( $f['alt'] ) ? " ({$f['alt']})" : '' ) ) . ', ' . $f['role'], $e['founders'] ) );
	}
	foreach ( (array) ( $e['facts'] ?? array() ) as $fact ) {
		$out[] = '- ' . $fact;
	}
	// Only the contact routes that exist. The booking link may be a site path (/contact/) or a full URL;
	// its label is the entity's 'contact_label' (e.g. "donate", "where to buy").
	$booking = (string) ( $e['booking'] ?? '' );
	if ( '' !== $booking && str_starts_with( $booking, '/' ) ) {
		$booking = home_url( $booking );
	}
	$contact = array_filter( array( $e['phone'] ?? '', $e['email'] ?? '', $booking ? ( $e['contact_label'] ?? 'book a call' ) . ': ' . $booking : '' ) );
	if ( $contact ) {
		$out[] = '- Contact: ' . implode( ' · ', $contact );
	}
	$out[] = '';

	// Offer pages: the children of one hub page (entity 'llms_offers': heading => hub path).
	foreach ( (array) ( $e['llms_offers'] ?? array( 'Services' => 'services' ) ) as $heading => $hub_path ) {
		$hub = get_page_by_path( $hub_path );
		if ( ! $hub ) {
			continue;
		}
		$out[] = '## ' . $heading;
		$out[] = '';
		foreach ( get_pages( array( 'parent' => $hub->ID, 'sort_column' => 'menu_order' ) ) as $p ) {
			$out[] = $line( $p );
		}
		$out[] = '';
	}

	$cases = get_posts( array( 'post_type' => 'case_study', 'posts_per_page' => -1, 'orderby' => array( 'menu_order' => 'ASC', 'date' => 'DESC' ) ) );
	if ( $cases ) {
		$out[] = '## ' . ( $e['work_label'] ?? 'Case studies' );
		$out[] = '';
		foreach ( $cases as $p ) {
			$stat  = trim( get_post_meta( $p->ID, 'hm_stat', true ) . ' ' . get_post_meta( $p->ID, 'hm_stat_label', true ) );
			$out[] = $line( $p, $stat ? " (Result: {$stat}; client: " . get_post_meta( $p->ID, 'hm_client', true ) . ')' : '' );
		}
		$out[] = '';
	}

	// Heading for the about/contact pages: 'llms_pages_label' (e.g. "Organisation" for a non-profit).
	$out[] = '## ' . ( $e['llms_pages_label'] ?? 'Company' );
	$out[] = '';
	foreach ( (array) ( $e['llms_pages'] ?? array( 'about', 'contact' ) ) as $path ) {
		$p = get_page_by_path( $path );
		if ( $p && 'publish' === $p->post_status ) {
			$out[] = $line( $p );
		}
	}
	$out[] = '';

	$posts = get_posts( array( 'posts_per_page' => 10 ) );
	if ( $posts ) {
		$out[] = '## Insights';
		$out[] = '';
		foreach ( $posts as $p ) {
			$out[] = $line( $p );
		}
		$out[] = '';
	}

	$out[] = '## Optional';
	$out[] = '';
	$out[] = '- [Sitemap](' . home_url( '/wp-sitemap.xml' ) . ')';

	return implode( "\n", $out ) . "\n";
}
