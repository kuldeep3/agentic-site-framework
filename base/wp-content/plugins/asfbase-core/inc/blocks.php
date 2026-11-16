<?php
/**
 * Dynamic blocks (PHP-rendered; previewed in the editor via ServerSideRender):
 *
 *   hm/work-grid    case study cards — featured (asymmetric) or grid, optional service filter
 *   hm/brief-form   multi-step qualifying lead form (front-end logic in the theme's site.js)
 *   hm/case-header  case study header built from the post + its meta (single template)
 *   hm/case-next    "next case" link (single template)
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

add_action(
	'init',
	function () {
		wp_register_script(
			'hm-editor-blocks',
			plugins_url( 'assets/editor-blocks.js', HM_CORE_FILE ),
			array( 'wp-blocks', 'wp-element', 'wp-server-side-render', 'wp-block-editor' ),
			HM_CORE_VERSION,
			true
		);
		foreach ( array( 'work-grid', 'brief-form', 'case-header', 'case-next' ) as $block ) {
			register_block_type( HM_CORE_DIR . "/blocks/{$block}" );
		}
	}
);

/**
 * Card data for one case study, used by the grid and the "next" link.
 *
 * @return array{url:string,title:string,client:string,services:string,stat:string,stat_label:string,image:string}
 */
function hm_case_card( WP_Post $post ): array {
	$terms = get_the_terms( $post, 'hm_service' );
	return array(
		'url'        => get_permalink( $post ),
		'title'      => get_the_title( $post ),
		'client'     => (string) get_post_meta( $post->ID, 'hm_client', true ),
		'services'   => $terms && ! is_wp_error( $terms ) ? wp_specialchars_decode( implode( ' · ', wp_list_pluck( array_slice( $terms, 0, 2 ), 'name' ) ) ) : '',
		'stat'       => (string) get_post_meta( $post->ID, 'hm_stat', true ),
		'stat_label' => (string) get_post_meta( $post->ID, 'hm_stat_label', true ),
		'image'      => has_post_thumbnail( $post ) ? get_the_post_thumbnail( $post, 'asfbase-card', array( 'loading' => 'lazy', 'sizes' => '(max-width: 800px) 100vw, 50vw' ) ) : '',
	);
}
