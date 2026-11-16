<?php
/**
 * JSON-LD structured data, printed as one @graph.
 *
 * Always:  Service (service pages), FAQPage (any .hm-faq section)
 * Only without an SEO plugin: Organization, WebSite, WebPage, BreadcrumbList, Article, Person
 *
 * FAQs are read straight from content: a Group with class "hm-faq" containing
 * core/details blocks (summary = question, body = answer). Editors add FAQs in
 * the editor and the schema follows; there is nothing to keep in sync.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

add_action( 'wp_head', 'hm_schema_print', 20 );

function hm_schema_print(): void {
	$graph = array();
	$org   = home_url( '/#organization' );
	$full  = ! hm_seo_plugin_active();
	$post  = is_singular() ? get_post() : null;

	if ( $full ) {
		$graph[] = array_filter(
			array(
				'@type'        => 'Organization',
				'@id'          => $org,
				'name'         => hm_entity( 'name' ),
				'legalName'    => hm_entity( 'legal_name' ),
				'alternateName' => hm_entity( 'alternate' ),
				'url'          => home_url( '/' ),
				'description'  => hm_entity( 'description' ),
				'slogan'       => hm_entity( 'tagline' ),
				'logo'         => plugins_url( 'assets/logo.png', HM_CORE_FILE ),
				'foundingDate' => hm_entity( 'founded' ),
				'areaServed'   => array( '@type' => 'Country', 'name' => hm_entity( 'area_served' ) ),
				'knowsAbout'   => hm_entity( 'knows_about' ),
				'sameAs'       => hm_entity_profiles(),
				'founder'      => array_map(
					fn( $p ) => array_filter( array( '@type' => 'Person', 'name' => $p['name'], 'alternateName' => $p['alt'], 'jobTitle' => $p['role'] ) ),
					hm_entity( 'founders' )
				),
				'contactPoint' => array(
					'@type'             => 'ContactPoint',
					'contactType'       => 'sales',
					'telephone'         => hm_entity( 'phone_e164' ),
					'email'             => hm_entity( 'email' ),
					'areaServed'        => 'US',
					'availableLanguage' => 'English',
				),
			)
		);
		$graph[] = array(
			'@type'     => 'WebSite',
			'@id'       => home_url( '/#website' ),
			'url'       => home_url( '/' ),
			'name'      => hm_entity( 'name' ),
			'publisher' => array( '@id' => $org ),
		);

		if ( $post ) {
			$crumbs  = hm_schema_breadcrumbs( $post );
			$graph[] = array(
				'@type'         => 'WebPage',
				'@id'           => get_permalink( $post ) . '#webpage',
				'url'           => get_permalink( $post ),
				'name'          => wp_get_document_title(),
				'description'   => hm_meta_description( $post->ID ),
				'isPartOf'      => array( '@id' => home_url( '/#website' ) ),
				'about'         => array( '@id' => $org ),
				'datePublished' => get_the_date( 'c', $post ),
				'dateModified'  => get_the_modified_date( 'c', $post ),
				'breadcrumb'    => count( $crumbs ) > 1 ? array( '@id' => get_permalink( $post ) . '#breadcrumb' ) : null,
			);
			if ( count( $crumbs ) > 1 ) {
				$graph[] = array(
					'@type'           => 'BreadcrumbList',
					'@id'             => get_permalink( $post ) . '#breadcrumb',
					'itemListElement' => array_map(
						fn( $c, $i ) => array( '@type' => 'ListItem', 'position' => $i + 1, 'name' => $c[0], 'item' => $c[1] ),
						$crumbs,
						array_keys( $crumbs )
					),
				);
			}
			if ( in_array( $post->post_type, array( 'post', 'case_study' ), true ) ) {
				$graph[] = array_filter(
					array(
						'@type'            => 'Article',
						'@id'              => get_permalink( $post ) . '#article',
						'headline'         => get_the_title( $post ),
						'description'      => hm_meta_description( $post->ID ),
						'image'            => get_the_post_thumbnail_url( $post, 'full' ) ?: null,
						'datePublished'    => get_the_date( 'c', $post ),
						'dateModified'     => get_the_modified_date( 'c', $post ),
						'author'           => 'post' === $post->post_type ? array( '@type' => 'Person', 'name' => get_the_author_meta( 'display_name', $post->post_author ) ) : array( '@id' => $org ),
						'publisher'        => array( '@id' => $org ),
						'mainEntityOfPage' => array( '@id' => get_permalink( $post ) . '#webpage' ),
						'about'            => 'case_study' === $post->post_type ? array_filter( array( '@type' => 'Organization', 'name' => get_post_meta( $post->ID, 'hm_client', true ) ) ) : null,
					)
				);
			}
		}
	}

	// Service: child pages of /services/.
	if ( $post && 'page' === $post->post_type && $post->post_parent && 'services' === get_post_field( 'post_name', $post->post_parent ) ) {
		$graph[] = array(
			'@type'       => 'Service',
			'@id'         => get_permalink( $post ) . '#service',
			'name'        => get_the_title( $post ),
			'serviceType' => get_the_title( $post ),
			'description' => hm_meta_description( $post->ID ),
			'url'         => get_permalink( $post ),
			'areaServed'  => array( '@type' => 'Country', 'name' => 'United States' ),
			'provider'    => $full ? array( '@id' => $org ) : array( '@type' => 'Organization', 'name' => hm_entity( 'name' ), 'url' => home_url( '/' ) ),
		);
	}

	// FAQPage from content.
	if ( $post ) {
		$faqs = hm_schema_faqs( parse_blocks( $post->post_content ) );
		if ( $faqs ) {
			$graph[] = array(
				'@type'      => 'FAQPage',
				'@id'        => get_permalink( $post ) . '#faq',
				'mainEntity' => array_map(
					fn( $qa ) => array( '@type' => 'Question', 'name' => $qa[0], 'acceptedAnswer' => array( '@type' => 'Answer', 'text' => $qa[1] ) ),
					$faqs
				),
			);
		}
	}

	if ( ! $graph ) {
		return;
	}
	$json = wp_json_encode( array( '@context' => 'https://schema.org', '@graph' => array_values( array_map( 'array_filter', $graph ) ) ), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE );
	echo '<script type="application/ld+json">' . $json . '</script>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput
}

/** @return array<int, array{0:string,1:string}> [name, url] from Home down to the current page. */
function hm_schema_breadcrumbs( WP_Post $post ): array {
	$crumbs = array( array( 'Home', home_url( '/' ) ) );
	if ( 'case_study' === $post->post_type ) {
		$crumbs[] = array( 'Work', get_post_type_archive_link( 'case_study' ) );
	} elseif ( 'post' === $post->post_type && get_option( 'page_for_posts' ) ) {
		$crumbs[] = array( 'Insights', get_permalink( (int) get_option( 'page_for_posts' ) ) );
	}
	foreach ( array_reverse( get_post_ancestors( $post ) ) as $ancestor ) {
		$crumbs[] = array( get_the_title( $ancestor ), get_permalink( $ancestor ) );
	}
	if ( (int) get_option( 'page_on_front' ) !== $post->ID ) {
		$crumbs[] = array( get_the_title( $post ), get_permalink( $post ) );
	}
	return $crumbs;
}

/**
 * Walk the block tree; collect core/details inside any block whose className has "hm-faq".
 *
 * @return array<int, array{0:string,1:string}>
 */
function hm_schema_faqs( array $blocks, bool $inside = false ): array {
	$out = array();
	foreach ( $blocks as $block ) {
		$is_faq = $inside || str_contains( (string) ( $block['attrs']['className'] ?? '' ), 'hm-faq' );
		if ( $is_faq && 'core/details' === $block['blockName'] ) {
			$html = render_block( $block );
			if ( preg_match( '#<summary[^>]*>(.*?)</summary>(.*)</details>#s', $html, $m ) ) {
				$q = trim( wp_strip_all_tags( $m[1] ) );
				$a = trim( preg_replace( '/\s+/', ' ', wp_strip_all_tags( $m[2] ) ) );
				if ( $q && $a ) {
					$out[] = array( $q, $a );
				}
			}
			continue;
		}
		if ( ! empty( $block['innerBlocks'] ) ) {
			$out = array_merge( $out, hm_schema_faqs( $block['innerBlocks'], $is_faq ) );
		}
	}
	return $out;
}
