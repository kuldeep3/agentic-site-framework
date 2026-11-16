<?php
/**
 * Content types: case studies (+ service/industry taxonomies) and private leads.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

function hm_register_content_types(): void {
	// Taxonomies first: their /work/service/{term}/ rules must come before the
	// case study's /work/{slug}/… rules, or the filter URLs 404.
	register_taxonomy(
		'hm_service',
		'case_study',
		array(
			'labels'            => array( 'name' => 'Services', 'singular_name' => 'Service' ),
			'public'            => true,
			'hierarchical'      => true,
			'show_admin_column' => true,
			'show_in_rest'      => true,
			'rewrite'           => array( 'slug' => 'work/service', 'with_front' => false ),
		)
	);

	register_taxonomy(
		'hm_industry',
		'case_study',
		array(
			'labels'            => array( 'name' => 'Industries', 'singular_name' => 'Industry' ),
			'public'            => false,
			'show_ui'           => true,
			'hierarchical'      => true,
			'show_admin_column' => true,
			'show_in_rest'      => true,
		)
	);

	register_post_type(
		'case_study',
		array(
			'labels'        => array(
				'name'          => 'Case studies',
				'singular_name' => 'Case study',
				'add_new_item'  => 'Add case study',
				'edit_item'     => 'Edit case study',
				'menu_name'     => 'Work',
			),
			'public'        => true,
			'has_archive'   => 'work',
			'rewrite'       => array( 'slug' => 'work', 'with_front' => false ),
			'menu_icon'     => 'dashicons-portfolio',
			'menu_position' => 21,
			'show_in_rest'  => true,
			'supports'      => array( 'title', 'editor', 'excerpt', 'thumbnail', 'custom-fields', 'page-attributes', 'revisions' ),
			'template'      => array( array( 'core/paragraph', array( 'placeholder' => 'Start with the challenge…' ) ) ),
		)
	);

	// Card + header facts. Editable in the "Custom fields" panel.
	$meta = array(
		'hm_client'     => 'Client name shown on cards and the case header.',
		'hm_year'       => 'Year or range, e.g. "2015–present".',
		'hm_stat'       => 'Headline number on the card, e.g. "20k/hr".',
		'hm_stat_label' => 'What the number means, e.g. "peak traffic held".',
	);
	foreach ( $meta as $key => $description ) {
		register_post_meta( 'case_study', $key, array( 'type' => 'string', 'single' => true, 'show_in_rest' => true, 'description' => $description ) );
	}

	// SEO overrides on any public type (used only when no SEO plugin is active).
	foreach ( array( 'page', 'post', 'case_study' ) as $type ) {
		register_post_meta( $type, '_hm_seo_title', array( 'type' => 'string', 'single' => true, 'show_in_rest' => true, 'auth_callback' => fn() => current_user_can( 'edit_posts' ) ) );
		register_post_meta( $type, '_hm_meta_description', array( 'type' => 'string', 'single' => true, 'show_in_rest' => true, 'auth_callback' => fn() => current_user_can( 'edit_posts' ) ) );
		register_post_meta( $type, '_hm_noindex', array( 'type' => 'boolean', 'single' => true, 'show_in_rest' => true, 'auth_callback' => fn() => current_user_can( 'edit_posts' ) ) );
	}
	add_post_type_support( 'page', 'excerpt' );

	register_post_type(
		'hm_lead',
		array(
			'labels'          => array( 'name' => 'Leads', 'singular_name' => 'Lead', 'menu_name' => 'Leads' ),
			'public'          => false,
			'show_ui'         => true,
			'show_in_rest'    => false,
			'menu_icon'       => 'dashicons-email-alt',
			'menu_position'   => 22,
			'supports'        => array( 'title', 'custom-fields' ),
			'capability_type' => 'post',
			'capabilities'    => array( 'create_posts' => 'do_not_allow' ),
			'map_meta_cap'    => true,
		)
	);
}
add_action( 'init', 'hm_register_content_types' );

// Case studies are ordered by menu_order (drag order in "Work"), then newest.
add_action(
	'pre_get_posts',
	function ( WP_Query $q ) {
		if ( ! is_admin() && $q->is_main_query() && ( $q->is_post_type_archive( 'case_study' ) || $q->is_tax( 'hm_service' ) ) ) {
			$q->set( 'orderby', array( 'menu_order' => 'ASC', 'date' => 'DESC' ) );
			$q->set( 'posts_per_page', -1 );
		}
	}
);
