<?php
/**
 * Theme supports, assets and front-end hygiene.
 *
 * @package asfbase
 */

defined( 'ABSPATH' ) || exit;

add_action(
	'after_setup_theme',
	function () {
		add_theme_support( 'editor-styles' );
		add_theme_support( 'responsive-embeds' );
		add_theme_support( 'post-thumbnails' );
		remove_theme_support( 'core-block-patterns' ); // Keep the inserter to our own patterns.
		add_editor_style( 'assets/css/main.css' );
		if ( file_exists( ASFBASE_DIR . '/assets/css/brand.css' ) ) {
			add_editor_style( 'assets/css/brand.css' );
		}

		add_image_size( 'asfbase-card', 1200, 900, true );
		add_image_size( 'asfbase-wide', 2000, 1125, true );
	}
);

add_action(
	'wp_enqueue_scripts',
	function () {
		$css = ASFBASE_DIR . '/assets/css/main.css';
		$js  = ASFBASE_DIR . '/assets/js/site.js';

		wp_enqueue_style( 'asfbase', ASFBASE_URI . '/assets/css/main.css', array( 'global-styles' ), (string) filemtime( $css ) );
		// Brand layer: the client's palette, type and shape, loaded after the shared components (see docs/04-design-system.md).
		// During the design review (stage 3), ?asf_direction=b swaps in assets/css/directions/b.css instead.
		$direction = asfbase_preview_direction();
		$brand_rel = $direction ? "assets/css/directions/{$direction}.css" : 'assets/css/brand.css';
		$brand     = ASFBASE_DIR . '/' . $brand_rel;
		if ( file_exists( $brand ) ) {
			wp_enqueue_style( 'asfbase-brand', ASFBASE_URI . '/' . $brand_rel, array( 'asfbase' ), (string) filemtime( $brand ) );
		}
		wp_enqueue_script(
			'asfbase',
			ASFBASE_URI . '/assets/js/site.js',
			array(),
			(string) filemtime( $js ),
			array( 'strategy' => 'defer', 'in_footer' => true )
		);
		wp_localize_script(
			'asfbase',
			'ASFBASE',
			array(
				'leadEndpoint' => esc_url_raw( rest_url( 'asfbase/v1/leads' ) ),
				'thankYou'     => esc_url_raw( home_url( '/thank-you/' ) ),
			)
		);
	}
);

// Preload the display face (it paints the hero headline, the LCP) and colour the browser UI.
add_action(
	'wp_head',
	function () {
		// Both come from theme.json, so they follow each client's fonts and palette.
		foreach ( (array) wp_get_global_settings( array( 'typography', 'fontFamilies', 'theme' ) ) as $family ) {
			$src = $family['fontFace'][0]['src'][0] ?? '';
			if ( 'display' === ( $family['slug'] ?? '' ) && $src ) {
				printf( '<link rel="preload" href="%s" as="font" type="font/woff2" crossorigin>' . "\n", esc_url( ASFBASE_URI . '/' . ltrim( str_replace( 'file:./', '', $src ), '/' ) ) );
			}
		}
		foreach ( (array) wp_get_global_settings( array( 'color', 'palette', 'theme' ) ) as $color ) {
			if ( 'ink' === ( $color['slug'] ?? '' ) ) {
				printf( '<meta name="theme-color" content="%s">' . "\n", esc_attr( $color['color'] ) );
			}
		}
		// Client copy the CSS needs (logo-strip caption), from the facts file.
		printf( '<style>:root{--hm-logos-caption:%s}</style>' . "\n", wp_json_encode( (string) asfbase_fact( 'logos_caption', '' ) ) );
		// Flag JS early so the hero can animate without a flash; undone if site.js never runs.
		echo "<script>document.documentElement.classList.add('hm-js');setTimeout(function(){if(!window.__hmReady){document.documentElement.classList.remove('hm-js')}},3000)</script>\n";
	},
	1
);

// Front-end weight: no emoji polyfill, no oEmbed discovery, no jQuery migrate.
remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
remove_action( 'wp_print_styles', 'print_emoji_styles' );
remove_action( 'wp_head', 'wp_oembed_add_discovery_links' );
remove_action( 'wp_head', 'wlwmanifest_link' );
remove_action( 'wp_head', 'rsd_link' );
remove_action( 'wp_head', 'wp_generator' );

// Body classes the CSS can hook on (e.g. dark hero pages).
add_filter(
	'body_class',
	function ( array $classes ) {
		if ( is_singular() && get_post_meta( get_the_ID(), '_hm_dark_hero', true ) ) {
			$classes[] = 'has-dark-hero';
		}
		return $classes;
	}
);

// Block styles editors can pick in the sidebar.
add_action(
	'init',
	function () {
		register_block_style( 'core/button', array( 'name' => 'outline', 'label' => 'Outline' ) );
		register_block_style( 'core/button', array( 'name' => 'link', 'label' => 'Text + arrow' ) );
		register_block_style( 'core/heading', array( 'name' => 'eyebrow', 'label' => 'Eyebrow (mono label)' ) );
		register_block_style( 'core/paragraph', array( 'name' => 'lead', 'label' => 'Lead' ) );
		register_block_style( 'core/paragraph', array( 'name' => 'eyebrow', 'label' => 'Eyebrow (mono label)' ) );
		register_block_style( 'core/list', array( 'name' => 'checks', 'label' => 'Checks' ) );
		register_block_style( 'core/group', array( 'name' => 'dark', 'label' => 'Dark section' ) );
		register_block_style( 'core/group', array( 'name' => 'orange', 'label' => 'Orange section' ) );
		register_block_style( 'core/group', array( 'name' => 'bone', 'label' => 'Bone section' ) );
	}
);

// Pattern category for the inserter.
add_action(
	'init',
	function () {
		register_block_pattern_category( 'asfbase', array( 'label' => 'ASF Base sections' ) );
	}
);

/**
 * Design review (stage 3): the direction being previewed, or '' for the real brand layer.
 *
 * Each design direction is written as assets/css/directions/<name>.css (a, b, c), so the
 * client and designer compare them on the real pages (/?asf_direction=b) and on the review
 * page made from those pages, before one becomes brand.css. Never on production: there the
 * parameter is ignored. Preview pages are noindex and carry a small label saying which
 * direction is showing.
 */
function asfbase_preview_direction(): string {
	static $direction = null;
	if ( null === $direction ) {
		$direction = '';
		$asked     = isset( $_GET['asf_direction'] ) ? sanitize_key( wp_unslash( $_GET['asf_direction'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification
		if ( $asked && 'production' !== wp_get_environment_type() && file_exists( ASFBASE_DIR . "/assets/css/directions/{$asked}.css" ) ) {
			$direction = $asked;
		}
	}
	return $direction;
}

add_filter(
	'wp_robots',
	function ( array $robots ): array {
		if ( asfbase_preview_direction() ) {
			$robots['noindex']  = true;
			$robots['nofollow'] = true;
		}
		return $robots;
	}
);

add_action(
	'wp_footer',
	function () {
		$direction = asfbase_preview_direction();
		if ( $direction ) {
			printf(
				'<p class="asf-direction-label" style="position:fixed;left:12px;bottom:12px;z-index:9999;margin:0;padding:6px 10px;background:#111;color:#fff;font:600 13px/1.2 system-ui,sans-serif;border-radius:4px">Design review · direction %s</p>',
				esc_html( strtoupper( $direction ) )
			);
		}
	}
);
