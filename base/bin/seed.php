<?php
/**
 * Seed the site from /content. Idempotent: safe to run again (upserts by slug).
 *
 *   wp eval-file bin/seed.php <path-to-content>      (bin/setup.sh does this for you)
 *
 * content/
 *   media/*.jpg|png        → Media Library (matched by filename; re-imported when the file changes)
 *   pages/*.html           → Pages      (front matter + Gutenberg block markup)
 *   work/*.html            → Case studies
 *   posts/posts.json       → Insights posts (snapshot of the live blog)
 *
 * Front matter is an HTML comment at the very top of each .html file:
 *   <!--
 *   title: WooCommerce Performance
 *   slug: services/woocommerce-performance     ← full path; parents must exist (files load parents-first)
 *   seo_title: WooCommerce Performance Optimization | Agency Name
 *   description: Meta description (≤155 chars).
 *   excerpt: Card/summary text (case studies). Defaults to description.
 *   template: page-prose                       ← optional block template (page-landing: campaign page, no menu)
 *   cta: Get the audit                         ← landing pages: the header button's label (it jumps to #form)
 *   order: 3                                   ← menu_order
 *   noindex: true                              ← optional
 *
 * Re-runs update pages by slug. A page or case study this script made earlier whose file has been
 * renamed or deleted is moved to the Trash (pages made by hand in WordPress are left alone).
 *   dark_hero: true                            ← header starts light-on-dark
 *   # case studies only:
 *   client: Example Co | year: 2015–present | stat: 20k/hr | stat_label: hits held
 *   services: WooCommerce, Performance | industry: E-commerce | image: mfm.png
 *   -->
 *
 * Placeholders in content: {{media:file.jpg}} → site-relative URL (works on any host); {{media-thumbnail:…}} etc. pick a size, {{media-id:file.jpg}} → attachment ID,
 * {{booking}} → Calendly URL, {{phone}}, {{phone-e164}}, {{email}}.
 * Image blocks whose <img src> is a {{media…:file}} placeholder also get the attachment ID (the block's
 * "id" and sizeSlug, class wp-image-N on the <img>), so WordPress adds width/height, srcset and lazy-loading.
 *
 * NOTE: seed files are the source of truth for LOCAL builds. After launch, the
 * WordPress database is the source of truth. Don't re-seed production.
 *
 * @package hm
 */

// phpcs:disable WordPress.WP.GlobalVariablesOverride, WordPress.PHP.DevelopmentFunctions

if ( ! defined( 'WP_CLI' ) ) {
	exit;
}

require_once ABSPATH . 'wp-admin/includes/media.php';
require_once ABSPATH . 'wp-admin/includes/file.php';
require_once ABSPATH . 'wp-admin/includes/image.php';

$hm_dir = rtrim( $args[0] ?? dirname( __DIR__ ) . '/content', '/' );
if ( ! is_dir( $hm_dir ) ) {
	WP_CLI::error( "Content folder not found: {$hm_dir}" );
}

/** Parse "<!-- key: value -->" front matter. @return array{0:array,1:string} */
function hm_seed_parse( string $file ): array {
	$raw  = file_get_contents( $file );
	$meta = array();
	if ( preg_match( '/\A\s*<!--(.*?)-->\s*/s', $raw, $m ) ) {
		foreach ( preg_split( '/\R/', trim( $m[1] ) ) as $line ) {
			if ( preg_match( '/^\s*([a-z_]+)\s*:\s*(.*)$/', $line, $kv ) ) {
				$meta[ $kv[1] ] = trim( $kv[2] );
			}
		}
		$raw = substr( $raw, strlen( $m[0] ) );
	}
	return array( $meta, trim( $raw ) );
}

/**
 * Import every file in content/media. A file is imported again when its contents change (say it was
 * recompressed), so the uploads always match the folder. @return array<string, int> filename → attachment ID
 */
function hm_seed_media( string $dir ): array {
	$map = array();
	// Mirror the folder: seeded attachments whose file was removed from content/media are deleted.
	$seeded = get_posts( array( 'post_type' => 'attachment', 'posts_per_page' => -1, 'fields' => 'ids', 'meta_key' => '_hm_seed_file' ) ); // phpcs:ignore
	foreach ( $seeded as $attachment_id ) {
		if ( ! file_exists( $dir . '/' . get_post_meta( $attachment_id, '_hm_seed_file', true ) ) ) {
			wp_delete_attachment( $attachment_id, true );
		}
	}
	foreach ( glob( "{$dir}/*.{jpg,jpeg,png,webp,svg}", GLOB_BRACE ) as $path ) {
		$name     = basename( $path );
		$hash     = md5_file( $path );
		$existing = get_posts( array( 'post_type' => 'attachment', 'meta_key' => '_hm_seed_file', 'meta_value' => $name, 'fields' => 'ids', 'posts_per_page' => 1 ) ); // phpcs:ignore
		if ( $existing && get_post_meta( $existing[0], '_hm_seed_hash', true ) === $hash ) {
			$map[ $name ] = (int) $existing[0];
			continue;
		}
		if ( $existing ) {
			// Changed, or seeded before hashes were kept: import it again. The new attachment gets a new
			// ID; the pages below are re-seeded with it, and the file keeps its name (so its URL).
			wp_delete_attachment( $existing[0], true );
		}
		$tmp = wp_tempnam( $name );
		copy( $path, $tmp );
		$id = media_handle_sideload( array( 'name' => $name, 'tmp_name' => $tmp ), 0 );
		if ( is_wp_error( $id ) ) {
			WP_CLI::warning( "Media {$name}: " . $id->get_error_message() );
			continue;
		}
		update_post_meta( $id, '_hm_seed_file', $name );
		update_post_meta( $id, '_hm_seed_hash', $hash );
		$map[ $name ] = (int) $id;
		WP_CLI::log( "  media  {$name}" . ( $existing ? ' (changed)' : '' ) );
	}
	return $map;
}

/**
 * Image blocks written as <img src="{{media…:file}}"> get what the editor stores when an image is
 * picked from the Media Library: the block's "id" and sizeSlug, a size-* class on the <figure> and
 * class="wp-image-N" on the <img>. WordPress needs that class to add width/height (no layout shift),
 * srcset and lazy-loading when the page is shown.
 */
function hm_seed_image_ids( string $html, array $media ): string {
	return preg_replace_callback(
		'/<!-- wp:image(?: (\{[^\n]*?\}))? -->(.*?)<!-- \/wp:image -->/s',
		static function ( array $m ) use ( $media ): string {
			$inner = $m[2];
			if ( ! preg_match( '/<img\b[^>]*\ssrc="\{\{media(?:-(thumbnail|medium|medium_large|large|full))?:([^}]+)\}\}"[^>]*>/', $inner, $img ) ) {
				return $m[0]; // Not a placeholder image.
			}
			$id    = $media[ $img[2] ] ?? 0;
			$attrs = '' === $m[1] ? array() : json_decode( $m[1], true );
			if ( ! $id || ! is_array( $attrs ) ) {
				return $m[0]; // A file not in content/media (lint_content.py reports it), or attributes that hold a placeholder.
			}
			$size              = $img[1] ? $img[1] : 'large';
			$attrs             = array_merge( array( 'id' => $id ), $attrs, array( 'id' => $id, 'sizeSlug' => $size ) );
			// The <img>: class="… wp-image-N" (replacing a stale one).
			$tag = $img[0];
			if ( preg_match( '/\sclass="([^"]*)"/', $tag, $class ) ) {
				$names = trim( preg_replace( '/\s+/', ' ', preg_replace( '/\bwp-image-\d+\b/', '', $class[1] ) ) . " wp-image-{$id}" );
				$tag   = str_replace( $class[0], ' class="' . $names . '"', $tag );
			} else {
				$tag = preg_replace( '/\s*\/?>$/', ' class="wp-image-' . $id . '"$0', $tag, 1 );
			}
			$inner = str_replace( $img[0], $tag, $inner );
			// The <figure>: one size-* class, matching sizeSlug.
			$inner = preg_replace_callback(
				'/(<figure\b[^>]*\sclass=")([^"]*)"/',
				static fn( array $f ): string => $f[1] . trim( preg_replace( '/\s*\bsize-[\w-]+/', '', $f[2] ) . " size-{$size}" ) . '"',
				$inner,
				1
			);
			return '<!-- wp:image ' . serialize_block_attributes( $attrs ) . ' -->' . $inner . '<!-- /wp:image -->';
		},
		$html
	);
}

function hm_seed_placeholders( string $html, array $media ): string {
	$html = hm_seed_image_ids( $html, $media );
	$html = preg_replace_callback( '/\{\{media-id:([^}]+)\}\}/', fn( $m ) => (string) ( $media[ $m[1] ] ?? 0 ), $html );
	// {{media:file}} = large; {{media-thumbnail:file}}, {{media-medium:file}}, {{media-medium_large:file}}, {{media-full:file}} pick a size.
	$html = preg_replace_callback(
		'/\{\{media(?:-(thumbnail|medium|medium_large|large|full))?:([^}]+)\}\}/',
		fn( $m ) => isset( $media[ $m[2] ] ) ? wp_make_link_relative( (string) wp_get_attachment_image_url( $media[ $m[2] ], $m[1] ?: 'large' ) ) : '',
		$html
	);
	return strtr(
		$html,
		array(
			'{{booking}}'    => (string) hm_entity( 'booking' ),
			'{{phone}}'      => (string) hm_entity( 'phone' ),
			'{{phone-e164}}' => (string) hm_entity( 'phone_e164' ),
			'{{email}}'      => (string) hm_entity( 'email' ),
		)
	);
}

/** Create or update a post by type + path. */
function hm_seed_upsert( string $type, array $meta, string $content, array $media ): int {
	$path   = trim( $meta['slug'] ?? '', '/' );
	$parts  = explode( '/', $path );
	$slug   = array_pop( $parts );
	$parent = 0;
	if ( $parts ) {
		$parent_post = get_page_by_path( implode( '/', $parts ), OBJECT, $type );
		if ( ! $parent_post ) {
			WP_CLI::warning( "Parent missing for {$path}; seeding at top level." );
		}
		$parent = $parent_post ? $parent_post->ID : 0;
	}
	$existing = get_page_by_path( $path, OBJECT, $type );
	$postarr  = array(
		'ID'           => $existing ? $existing->ID : 0,
		'post_type'    => $type,
		'post_status'  => 'publish',
		'post_title'   => $meta['title'] ?? $slug,
		'post_name'    => $slug,
		'post_parent'  => $parent,
		'menu_order'   => (int) ( $meta['order'] ?? 0 ),
		'post_excerpt' => $meta['excerpt'] ?? ( $meta['description'] ?? '' ),
		'post_content' => hm_seed_placeholders( $content, $media ),
	);
	$id = wp_insert_post( wp_slash( $postarr ), true );
	if ( is_wp_error( $id ) ) {
		WP_CLI::warning( "{$path}: " . $id->get_error_message() );
		return 0;
	}

	update_post_meta( $id, '_hm_seed_path', $path ); // So a reseed can tell its own pages from hand-made ones.
	update_post_meta( $id, '_wp_page_template', $meta['template'] ?? '' );
	update_post_meta( $id, '_hm_seo_title', $meta['seo_title'] ?? '' );
	update_post_meta( $id, '_hm_meta_description', $meta['description'] ?? '' );
	update_post_meta( $id, '_hm_noindex', ! empty( $meta['noindex'] ) );
	update_post_meta( $id, '_hm_dark_hero', ! empty( $meta['dark_hero'] ) );
	update_post_meta( $id, '_hm_cta', $meta['cta'] ?? '' ); // Landing pages: the header button's label.
	// Same values for Rank Math, so a staging site with Rank Math is ready too.
	update_post_meta( $id, 'rank_math_title', $meta['seo_title'] ?? '' );
	update_post_meta( $id, 'rank_math_description', $meta['description'] ?? '' );

	if ( 'case_study' === $type ) {
		foreach ( array( 'client', 'year', 'stat', 'stat_label' ) as $k ) {
			update_post_meta( $id, "hm_{$k}", $meta[ $k ] ?? '' );
		}
		foreach ( array( 'services' => 'hm_service', 'industry' => 'hm_industry' ) as $k => $tax ) {
			$names = array_filter( array_map( 'trim', explode( ',', $meta[ $k ] ?? '' ) ) );
			$ids   = array();
			foreach ( $names as $name ) {
				$term  = term_exists( $name, $tax ) ?: wp_insert_term( $name, $tax );
				$ids[] = (int) ( is_array( $term ) ? $term['term_id'] : $term );
			}
			wp_set_object_terms( $id, $ids, $tax );
		}
	}
	if ( ! empty( $meta['image'] ) && isset( $media[ $meta['image'] ] ) ) {
		set_post_thumbnail( $id, $media[ $meta['image'] ] );
	}
	WP_CLI::log( sprintf( '  %-6s /%s/', 'case_study' === $type ? 'work' : $type, 'case_study' === $type ? "work/{$path}" : $path ) );
	return (int) $id;
}

// ---------------------------------------------------------------------------
WP_CLI::log( 'Media' );
$hm_media = hm_seed_media( "{$hm_dir}/media" );

WP_CLI::log( 'Pages' );
$hm_pages = array();
foreach ( glob( "{$hm_dir}/pages/*.html" ) as $file ) {
	[ $meta, $body ] = hm_seed_parse( $file );
	$hm_pages[]      = array( $meta, $body );
}
// Parents first: sort by path depth, then by file order.
usort( $hm_pages, fn( $a, $b ) => substr_count( $a[0]['slug'] ?? '', '/' ) <=> substr_count( $b[0]['slug'] ?? '', '/' ) );
$hm_seeded = array();
foreach ( $hm_pages as [ $meta, $body ] ) {
	$hm_seeded[] = hm_seed_upsert( 'page', $meta, $body, $hm_media );
}

WP_CLI::log( 'Case studies' );
foreach ( glob( "{$hm_dir}/work/*.html" ) as $file ) {
	[ $meta, $body ] = hm_seed_parse( $file );
	$hm_seeded[] = hm_seed_upsert( 'case_study', $meta, $body, $hm_media );
}

// Pages and case studies this script made earlier whose file is gone (renamed or deleted) go to the
// Trash, so a renamed skeleton page doesn't stay live. Pages made by hand in WordPress are never touched.
$hm_gone = get_posts(
	array(
		'post_type'      => array( 'page', 'case_study' ),
		'post_status'    => array( 'publish', 'draft', 'private' ),
		'posts_per_page' => -1,
		'meta_key'       => '_hm_seed_path', // phpcs:ignore
		'post__not_in'   => array_filter( $hm_seeded ),
	)
);
foreach ( $hm_gone as $hm_post ) {
	wp_trash_post( $hm_post->ID );
	WP_CLI::log( "  trashed {$hm_post->post_type} /" . get_post_meta( $hm_post->ID, '_hm_seed_path', true ) . '/ (its file is gone; restore it from the Trash if that was a mistake)' );
}

WP_CLI::log( 'Posts' );
$hm_author = get_user_by( 'login', 'team' );
if ( ! $hm_author ) {
	$hm_uid    = wp_insert_user( array( 'user_login' => 'team', 'user_pass' => wp_generate_password( 32 ), 'display_name' => 'The ' . ( (array) hm_entity( 'alternate' ) )[0] . ' Team', 'role' => 'author', 'user_email' => 'team@example.test' ) );
	$hm_author = get_user_by( 'id', $hm_uid );
}
$hm_json = "{$hm_dir}/posts/posts.json";
foreach ( file_exists( $hm_json ) ? json_decode( file_get_contents( $hm_json ), true ) : array() as $p ) {
	$existing = get_page_by_path( $p['slug'], OBJECT, 'post' );
	$id       = wp_insert_post(
		wp_slash(
			array(
				'ID'           => $existing ? $existing->ID : 0,
				'post_type'    => 'post',
				'post_status'  => 'publish',
				'post_title'   => $p['title'],
				'post_name'    => $p['slug'],
				'post_date'    => str_replace( 'T', ' ', $p['date'] ),
				'post_excerpt' => $p['excerpt'],
				'post_content' => $p['content'],
				'post_author'  => $hm_author->ID,
			)
		)
	);
	if ( $id && ! is_wp_error( $id ) && ! empty( $p['image'] ) && isset( $hm_media[ $p['image'] ] ) ) {
		set_post_thumbnail( $id, $hm_media[ $p['image'] ] );
	}
	WP_CLI::log( "  post   /{$p['slug']}/" );
}

WP_CLI::log( 'Settings' );
$hm_home     = get_page_by_path( 'home' );
$hm_insights = get_page_by_path( 'insights' );
if ( $hm_home ) {
	update_option( 'show_on_front', 'page' );
	update_option( 'page_on_front', $hm_home->ID );
}
if ( $hm_insights ) {
	update_option( 'page_for_posts', $hm_insights->ID );
}
update_option( 'blogname', (string) hm_entity( 'name' ) );
update_option( 'blogdescription', (string) hm_entity( 'tagline' ) );
update_option( 'posts_per_page', 12 );
foreach ( array( 'post' => 'hello-world', 'page' => 'sample-page' ) as $hm_type => $hm_slug ) { // WordPress install defaults.
	$hm_default = get_page_by_path( $hm_slug, OBJECT, $hm_type );
	if ( $hm_default ) {
		wp_delete_post( $hm_default->ID, true );
	}
}
delete_transient( 'hm_llms_txt' );
flush_rewrite_rules();

WP_CLI::success( 'Seeded ' . count( $hm_pages ) . ' pages, ' . count( glob( "{$hm_dir}/work/*.html" ) ) . ' case studies, ' . count( $hm_media ) . ' images.' );
