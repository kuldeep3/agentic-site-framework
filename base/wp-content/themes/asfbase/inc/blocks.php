<?php
/**
 * Theme blocks: site header, footer and hero visual. Rendered in PHP (render.php beside each
 * block.json) so markup and accessibility stay fully under our control.
 *
 * In the editor they preview via ServerSideRender — no build step needed.
 *
 * @package asfbase
 */

defined( 'ABSPATH' ) || exit;

add_action(
	'init',
	function () {
		wp_register_script(
			'asfbase-editor-blocks',
			ASFBASE_URI . '/assets/js/editor-blocks.js',
			array( 'wp-blocks', 'wp-element', 'wp-server-side-render', 'wp-block-editor' ),
			ASFBASE_VERSION,
			true
		);

		register_block_type( ASFBASE_DIR . '/blocks/site-header' );
		register_block_type( ASFBASE_DIR . '/blocks/site-footer' );
		register_block_type( ASFBASE_DIR . '/blocks/hero-visual' );
	}
);
