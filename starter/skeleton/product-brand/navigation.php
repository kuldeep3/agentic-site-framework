<?php
/**
 * Site navigation — the single place to change header, mega-menu and footer links.
 *
 * Product-brand layout: the mega panel lists product lines; the header button and the
 * "next step" link send buyers to where they can buy. URLs are site-relative.
 * Fill it from docs/02-information-architecture.md §3.
 *
 * @package asfbase
 */

defined( 'ABSPATH' ) || exit;

/**
 * @return array{primary: array, services: array, cta: array, footer: array, legal: array}
 */
function asfbase_nav(): array {
	return array(
		'primary'   => array(
			array( 'label' => 'Products', 'url' => '/products/', 'mega' => 'services' ),
			array( 'label' => 'Builds', 'url' => '/work/' ),
			array( 'label' => 'Support', 'url' => '/support/' ),
			array( 'label' => 'About', 'url' => '/about/' ),
		),

		// Mega panel: product lines. Icons: brand, ads, growth, store, speed, code, chart, arrow.
		'services'  => array(
			array(
				'group' => 'Product lines',
				'items' => array(
					array( 'label' => 'Example line', 'url' => '/products/example-line/', 'desc' => 'One line on what it is and what it fits.', 'icon' => 'store' ),
				),
			),
		),

		'mega'      => array(
			'title'  => 'Every product line, <em>in one place</em>.',
			'footer' => 'Not sure what fits your vehicle? Ask us and we’ll point you to the right part.',
		),

		// The "next step" link under the mega panel and at the end of the mobile menu.
		'secondary' => array( 'label' => 'Become a dealer', 'url' => '/dealers/', 'mega' => 'Ask about fitment →' ),

		'cta'       => array( 'label' => 'Where to buy', 'url' => '/where-to-buy/' ),

		'footer'    => array(
			array(
				'title' => 'Products',
				'links' => array(
					array( 'label' => 'All products', 'url' => '/products/' ),
					array( 'label' => 'Example line', 'url' => '/products/example-line/' ),
				),
			),
			array(
				'title' => 'Buy',
				'links' => array(
					array( 'label' => 'Where to buy', 'url' => '/where-to-buy/' ),
					array( 'label' => 'Become a dealer', 'url' => '/dealers/' ),
				),
			),
			array(
				'title' => 'Company',
				'links' => array(
					array( 'label' => 'Builds', 'url' => '/work/' ),
					array( 'label' => 'Support', 'url' => '/support/' ),
					array( 'label' => 'About', 'url' => '/about/' ),
					array( 'label' => 'Contact', 'url' => '/contact/' ),
				),
			),
		),

		'legal'     => array(
			array( 'label' => 'Privacy', 'url' => '/privacy-policy/' ),
		),
	);
}
