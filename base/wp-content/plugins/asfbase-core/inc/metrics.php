<?php
/**
 * Private metrics for the weekly report:
 *   GET /wp-json/asfbase/v1/metrics?from=2026-11-09&to=2026-11-15
 *
 * Admins only. Scripts sign in with an Application Password (Users → Profile → Application
 * Passwords), never the real password. Leads are first-party data: no analytics account is needed to know how many
 * enquiries came in this week, what they asked for, and which pages and sources sent them.
 * The response compares the range with the same number of days before it.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

add_action(
	'rest_api_init',
	function () {
		register_rest_route(
			'asfbase/v1',
			'/metrics',
			array(
				'methods'             => 'GET',
				'permission_callback' => static fn() => current_user_can( 'manage_options' ),
				'callback'            => 'hm_metrics',
				'args'                => array(
					'from' => array( 'type' => 'string', 'pattern' => '^\d{4}-\d{2}-\d{2}$' ),
					'to'   => array( 'type' => 'string', 'pattern' => '^\d{4}-\d{2}-\d{2}$' ),
				),
			)
		);
	}
);

/** Count leads created between two dates (inclusive), grouped the ways a weekly report needs. */
function hm_metrics_leads( string $from, string $to ): array {
	$ids = get_posts(
		array(
			'post_type'      => 'hm_lead',
			'post_status'    => array( 'private', 'publish' ),
			'posts_per_page' => -1,
			'fields'         => 'ids',
			'date_query'     => array( array( 'after' => "{$from} 00:00:00", 'before' => "{$to} 23:59:59", 'inclusive' => true ) ),
		)
	);
	$out  = array( 'total' => 0, 'brief' => 0, 'newsletter' => 0, 'by_need' => array(), 'by_budget' => array(), 'by_page' => array(), 'by_source' => array() );
	$home = wp_parse_url( home_url(), PHP_URL_HOST );
	$add  = static function ( array &$bucket, string $key ) {
		$bucket[ $key ] = ( $bucket[ $key ] ?? 0 ) + 1;
	};
	foreach ( $ids as $id ) {
		$type = 'newsletter' === get_post_meta( $id, 'hm_type', true ) ? 'newsletter' : 'brief';
		++$out['total'];
		++$out[ $type ];
		$page = (string) get_post_meta( $id, 'hm_page', true );
		$add( $out['by_page'], '' !== $page ? $page : '(unknown)' );
		$utm    = (array) get_post_meta( $id, 'hm_utm', true );
		$source = (string) ( $utm['utm_source'] ?? '' );
		if ( '' === $source ) {
			$ref_host = wp_parse_url( (string) get_post_meta( $id, 'hm_referrer', true ), PHP_URL_HOST );
			$source   = ( $ref_host && $ref_host !== $home ) ? $ref_host : 'direct';
		}
		$add( $out['by_source'], $source );
		if ( 'brief' === $type ) {
			foreach ( (array) get_post_meta( $id, 'hm_needs', true ) as $need ) {
				$add( $out['by_need'], (string) $need );
			}
			$budget = (string) get_post_meta( $id, 'hm_budget', true );
			if ( '' !== $budget ) {
				$add( $out['by_budget'], $budget );
			}
		}
	}
	foreach ( array( 'by_need', 'by_budget', 'by_page', 'by_source' ) as $k ) {
		arsort( $out[ $k ] );
	}
	return $out;
}

function hm_metrics( WP_REST_Request $req ) {
	$tz   = wp_timezone();
	$to   = $req->get_param( 'to' ) ?: ( new DateTimeImmutable( 'yesterday', $tz ) )->format( 'Y-m-d' );
	$from = $req->get_param( 'from' ) ?: ( new DateTimeImmutable( $to, $tz ) )->modify( '-6 days' )->format( 'Y-m-d' );
	$days = (int) ( new DateTimeImmutable( $from, $tz ) )->diff( new DateTimeImmutable( $to, $tz ) )->days + 1;
	$p_to   = ( new DateTimeImmutable( $from, $tz ) )->modify( '-1 day' );
	$p_from = $p_to->modify( '-' . ( $days - 1 ) . ' days' );

	return rest_ensure_response(
		array(
			'site'      => home_url( '/' ),
			'from'      => $from,
			'to'        => $to,
			'generated' => gmdate( 'c' ),
			'leads'     => hm_metrics_leads( $from, $to ),
			'previous'  => array(
				'from'  => $p_from->format( 'Y-m-d' ),
				'to'    => $p_to->format( 'Y-m-d' ),
				'leads' => hm_metrics_leads( $p_from->format( 'Y-m-d' ), $p_to->format( 'Y-m-d' ) ),
			),
			'content'   => array(
				'pages'        => (int) wp_count_posts( 'page' )->publish,
				'case_studies' => (int) wp_count_posts( 'case_study' )->publish,
				'posts'        => (int) wp_count_posts( 'post' )->publish,
			),
		)
	);
}
