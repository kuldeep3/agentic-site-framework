<?php
/**
 * Site navigation — the single place to change header, mega-menu and footer links.
 *
 * Why a PHP array and not WP Menus: the header is a designed component (mega panel,
 * descriptions, groups), and it changes rarely. One readable file beats a menu UI
 * that can't express groups or descriptions. URLs are site-relative.
 * Fill it from docs/02-information-architecture.md §3.
 *
 * Mega items show an icon ('icon' => 'growth', …) or, with 'tile' => 'x', a plain square the
 * design layer colours through the class .is-x (e.g. one colour per product line or stage).
 *
 * @package asfbase
 */

defined( 'ABSPATH' ) || exit;

/**
 * @return array{primary: array, services: array, cta: array, footer: array, legal: array}
 */
function asfbase_nav(): array {
	return array(
		'primary'  => array(
			array( 'label' => 'Services', 'url' => '/services/', 'mega' => 'services' ),
			array( 'label' => 'Work', 'url' => '/work/' ),
			array( 'label' => 'Approach', 'url' => '/approach/' ),
			array( 'label' => 'About', 'url' => '/about/' ),
		),

		// Mega panel groups. Icons: brand, ads, growth, store, speed, code, chart, arrow.
		'services' => array(
			array(
				'group' => 'Services',
				'items' => array(
					array( 'label' => 'Example service', 'url' => '/services/example-service/', 'desc' => 'One line on what changes for the client.', 'icon' => 'growth' ),
				),
			),
		),

		// Copy around the Services mega panel.
		'mega'     => array(
			'title'  => 'One line on how the services <em>connect</em>.',
			'footer' => 'Not sure where to start? We’ll point you to the smallest step that moves your number.',
		),

		// Featured case study card shown inside the Services mega panel (optional).
		// 'feature' => array( 'eyebrow' => 'Case study', 'title' => '…', 'client' => '…', 'url' => '/work/…/' ),

		'cta'      => array( 'label' => 'Book a call', 'url' => '/contact/' ),

		'footer'   => array(
			array(
				'title' => 'Services',
				'links' => array(
					array( 'label' => 'Example service', 'url' => '/services/example-service/' ),
				),
			),
			array(
				'title' => 'Company',
				'links' => array(
					array( 'label' => 'Work', 'url' => '/work/' ),
					array( 'label' => 'Approach', 'url' => '/approach/' ),
					array( 'label' => 'About', 'url' => '/about/' ),
					array( 'label' => 'Ways to start', 'url' => '/start/' ),
				),
			),
		),

		'legal'    => array(
			array( 'label' => 'Privacy', 'url' => '/privacy-policy/' ),
		),
	);
}
