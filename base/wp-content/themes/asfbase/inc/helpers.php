<?php
/**
 * Small template helpers shared by the header/footer blocks.
 *
 * @package asfbase
 */

defined( 'ABSPATH' ) || exit;

/**
 * Organisation facts (phone, email, booking link…). The single source of truth is
 * hm_entity() in the asfbase-core plugin; the fallback only keeps the theme
 * rendering if the plugin is switched off.
 */
function asfbase_entity( string $key ): string {
	if ( function_exists( 'hm_entity' ) ) {
		$value = hm_entity( $key );
		if ( is_string( $value ) ) {
			return $value;
		}
	}
	// Without the plugin, only the site name is known (set from the entity by bin/seed.php).
	$fallback = array( 'name' => get_bloginfo( 'name' ) );
	return $fallback[ $key ] ?? '';
}

/**
 * Structured client facts (arrays such as footer_cta) from hm_entity(), with a fallback
 * so the theme still renders without the plugin.
 */
function asfbase_fact( string $key, $fallback = '' ) {
	$value = function_exists( 'hm_entity' ) ? hm_entity( $key ) : null;
	return null === $value ? $fallback : $value;
}

/** Turn a site-relative path from navigation.php into a full URL. */
function asfbase_url( string $path ): string {
	return str_starts_with( $path, 'http' ) ? $path : home_url( $path );
}

/** Is this nav URL the current page (or a parent of it)? */
function asfbase_is_current( string $path ): bool {
	$request = '/' . trim( (string) wp_parse_url( add_query_arg( array() ), PHP_URL_PATH ), '/' ) . '/';
	$path    = '/' . trim( $path, '/' ) . '/';
	return '//' !== $path && str_starts_with( $request, $path );
}

/** Inline SVG icons. Decorative: always aria-hidden. */
function asfbase_icon( string $name ): string {
	$icons = array(
		'arrow'    => '<path d="M5 12h14M13 6l6 6-6 6"/>',
		'arrow-ne' => '<path d="M7 17 17 7M8 7h9v9"/>',
		'plus'     => '<path d="M12 5v14M5 12h14"/>',
		'menu'     => '<path d="M4 8h16M4 16h16"/>',
		'close'    => '<path d="M6 6l12 12M18 6 6 18"/>',
		'brand'    => '<path d="M12 3l2.6 5.6L20 9.3l-4 4.1.9 5.6L12 16.3 7.1 19l.9-5.6-4-4.1 5.4-.7z"/>',
		'ads'      => '<path d="M4 10v4a1 1 0 0 0 1 1h2l5 4V5L7 9H5a1 1 0 0 0-1 1zM16 8.5a5 5 0 0 1 0 7M18.5 6a8.5 8.5 0 0 1 0 12"/>',
		'growth'   => '<path d="M3 17l6-6 4 4 8-8M15 7h6v6"/>',
		'store'    => '<path d="M5 8h14l-1 12H6zM9 8V6a3 3 0 0 1 6 0v2"/>',
		'speed'    => '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
		'code'     => '<path d="M8 8l-4 4 4 4M16 8l4 4-4 4M14 5l-4 14"/>',
		'chart'    => '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
		'phone'    => '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
	);
	if ( ! isset( $icons[ $name ] ) ) {
		return '';
	}
	return '<svg class="hm-icon hm-icon--' . esc_attr( $name ) . '" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' . $icons[ $name ] . '</svg>';
}

/**
 * Featured image of a case study by slug (used by the hero collage and UI mocks,
 * so the visuals always show real client work from the Media Library).
 */
function asfbase_case_image( string $slug, string $size = 'large' ): string {
	$case = $slug ? get_page_by_path( $slug, OBJECT, 'case_study' ) : null;
	if ( ! $case || ! has_post_thumbnail( $case ) ) {
		return '';
	}
	return get_the_post_thumbnail( $case, $size, array( 'alt' => '', 'loading' => 'eager', 'decoding' => 'async' ) );
}

/**
 * An <img> for a Media Library URL given as a block attribute (e.g. "image":"{{media:file.jpg}}",
 * which the seed turns into a site-relative URL of the large size). When the URL is an attachment or
 * one of its sizes, WordPress adds width/height (no layout shift) and srcset, as it does for image
 * blocks. A file in uploads that isn't an attachment gets its width/height from the file; any other
 * URL is printed as it is.
 *
 * @param string $url   Image URL, absolute or site-relative.
 * @param string $attrs Extra attributes, already escaped (e.g. 'fetchpriority="high"').
 */
function asfbase_media_img( string $url, string $attrs = '' ): string {
	$tag  = '<img src="' . esc_url( $url ) . '" alt=""' . ( $attrs ? ' ' . $attrs : '' ) . '>';
	$up   = wp_get_upload_dir();
	$base = (string) set_url_scheme( $up['baseurl'], 'relative' ); // e.g. /wp-content/uploads
	$path = (string) wp_parse_url( $url, PHP_URL_PATH );
	if ( ! str_starts_with( $path, $base . '/' ) ) {
		return $tag;
	}
	$file = substr( $path, strlen( $base ) + 1 ); // e.g. 2026/11/photo-1024x768.jpg
	$orig = (string) preg_replace( '/-\d+x\d+(?=\.\w+$)/', '', $file ); // The size's original…
	foreach ( array_unique( array( $file, $orig, (string) preg_replace( '/(\.\w+)$/', '-scaled$1', $orig ) ) ) as $candidate ) { // …which WordPress may have scaled down.
		$id = attachment_url_to_postid( $up['baseurl'] . '/' . $candidate );
		if ( $id ) {
			$tag = wp_img_tag_add_width_and_height_attr( $tag, 'asfbase', $id );
			return wp_img_tag_add_srcset_and_sizes_attr( $tag, 'asfbase', $id );
		}
	}
	$size = wp_getimagesize( $up['basedir'] . '/' . $file );
	return $size ? str_replace( '<img ', sprintf( '<img width="%d" height="%d" ', $size[0], $size[1] ), $tag ) : $tag;
}
