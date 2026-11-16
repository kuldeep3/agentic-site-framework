<?php
/**
 * Fallback SEO tags: title, description, Open Graph, robots.
 *
 * Production runs Rank Math. When Rank Math or Yoast is active, this file
 * steps aside entirely and the plugin owns titles and meta. Locally (no SEO
 * plugin) these fallbacks keep every page correct, and the values come from:
 *   _hm_seo_title        → <title> (else "Page title | ASF Base")
 *   _hm_meta_description → meta description (else the excerpt)
 *   _hm_noindex          → noindex,follow
 * The seed script writes the same values into Rank Math's fields too.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

function hm_seo_plugin_active(): bool {
	return defined( 'RANK_MATH_VERSION' ) || defined( 'WPSEO_VERSION' ) || defined( 'AIOSEO_VERSION' );
}

function hm_meta_description( ?int $post_id = null ): string {
	if ( is_404() ) {
		return '';
	}
	if ( null === $post_id && ( is_front_page() || is_home() ) ) {
		$post_id = (int) get_option( is_home() && ! is_front_page() ? 'page_for_posts' : 'page_on_front' );
	}
	if ( null === $post_id && is_post_type_archive( 'case_study' ) ) {
		$desc = sprintf( '%s from %s: %s.', hm_entity( 'work_label' ) ?? 'Case studies', hm_entity( 'name' ), hm_entity( 'work_description' ) );
	} elseif ( null === $post_id && is_tax( 'hm_service' ) ) {
		$desc = sprintf( '%s case studies from %s: the challenge, what we built, and the numbers that changed.', wp_specialchars_decode( single_term_title( '', false ) ), hm_entity( 'name' ) );
	} else {
		$post_id = $post_id ?? ( is_singular() ? get_the_ID() : 0 );
		if ( ! $post_id ) {
			$desc = (string) hm_entity( 'description' );
		} else {
			$desc = (string) get_post_meta( $post_id, '_hm_meta_description', true );
			if ( '' === $desc ) {
				$desc = has_excerpt( $post_id ) ? get_the_excerpt( $post_id ) : wp_trim_words( wp_strip_all_tags( strip_shortcodes( get_post_field( 'post_content', $post_id ) ) ), 28, '…' );
			}
		}
	}
	$desc = trim( preg_replace( '/\s+/', ' ', wp_strip_all_tags( $desc ) ) );
	return mb_strlen( $desc ) > 155 ? rtrim( mb_substr( $desc, 0, 154 ), " ,.;:–—" ) . '…' : $desc;
}

add_action(
	'init',
	function () {
		if ( hm_seo_plugin_active() ) {
			return;
		}

		add_filter(
			'pre_get_document_title',
			function ( $title ) {
				$id = is_front_page() ? (int) get_option( 'page_on_front' ) : ( is_home() ? (int) get_option( 'page_for_posts' ) : ( is_singular() ? get_the_ID() : 0 ) );
				$custom = $id ? (string) get_post_meta( $id, '_hm_seo_title', true ) : '';
				if ( $custom ) {
					return $custom;
				}
				if ( is_post_type_archive( 'case_study' ) ) {
					return sprintf( '%s | %s', hm_entity( 'work_title' ) ?? 'Our Work: Case Studies', hm_entity( 'name' ) );
				}
				return $title;
			}
		);
		add_filter( 'document_title_separator', fn() => '|' );

		add_action(
			'wp_head',
			function () {
				$desc  = hm_meta_description();
				$title = wp_get_document_title();
				$url   = is_singular() ? get_permalink() : home_url( add_query_arg( array() ) );
				$image = is_singular() && has_post_thumbnail() ? get_the_post_thumbnail_url( null, 'asfbase-wide' ) : '';
				if ( ! $image ) {
					$image = plugins_url( 'assets/og-default.png', HM_CORE_FILE );
				}
				$tags = array(
					'description'         => $desc,
					'og:type'             => is_singular( array( 'post', 'case_study' ) ) ? 'article' : 'website',
					'og:site_name'        => hm_entity( 'name' ),
					'og:title'            => $title,
					'og:description'      => $desc,
					'og:url'              => $url,
					'og:image'            => $image,
					'twitter:card'        => 'summary_large_image',
					'twitter:title'       => $title,
					'twitter:description' => $desc,
					'twitter:image'       => $image,
				);
				foreach ( $tags as $name => $content ) {
					if ( '' === (string) $content ) {
						continue;
					}
					$attr = str_starts_with( $name, 'og:' ) ? 'property' : 'name';
					printf( '<meta %s="%s" content="%s">' . "\n", esc_attr( $attr ), esc_attr( $name ), esc_attr( $content ) );
				}
				// WordPress core only prints a canonical on singular pages; archives need their own.
				$canonical = '';
				if ( is_post_type_archive( 'case_study' ) ) {
					$canonical = get_post_type_archive_link( 'case_study' );
				} elseif ( is_category() || is_tag() || is_tax() ) {
					$canonical = get_term_link( get_queried_object() );
				} elseif ( is_home() && ! is_front_page() && ! is_paged() ) {
					$canonical = get_permalink( (int) get_option( 'page_for_posts' ) );
				}
				if ( $canonical && ! is_wp_error( $canonical ) ) {
					printf( '<link rel="canonical" href="%s">' . "\n", esc_url( $canonical ) );
				}
			},
			2
		);
	}
);

// noindex: thank-you, intake questionnaires, search, and anything flagged.
add_filter(
	'wp_robots',
	function ( array $robots ) {
		if ( hm_seo_plugin_active() ) {
			return $robots;
		}
		$flagged = is_singular() && get_post_meta( get_the_ID(), '_hm_noindex', true );
		if ( $flagged || is_search() || is_page( array( 'thank-you', 'marketing-questionnaire', 'branding-questionnaire' ) ) ) {
			$robots['noindex'] = true;
			$robots['follow']  = true;
		} else {
			$robots['max-image-preview'] = 'large';
		}
		return $robots;
	}
);

// Leads must never appear in the core sitemap.
add_filter( 'wp_sitemaps_post_types', fn( $types ) => array_diff_key( $types, array( 'hm_lead' => true ) ) );
add_filter( 'wp_sitemaps_add_provider', fn( $provider, $name ) => 'users' === $name ? false : $provider, 10, 2 );
