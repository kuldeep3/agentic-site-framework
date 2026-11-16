<?php
/**
 * The organisation, described once.
 *
 * AI engines and Google trust entities whose facts are identical everywhere.
 * Footer, About, Organization schema and llms.txt all read from here — change a
 * fact in this file and it changes everywhere. Fill it from docs/truth.md
 * (Stage 3.1). Items marked CONFIRM go in docs/06-content-checklist.md.
 *
 * WHITE-LABEL RULE: never name the engineering partner here or anywhere public.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

/**
 * @param string|null $key A single fact, or null for all of them.
 * @return mixed
 */
function hm_entity( ?string $key = null ) {
	static $entity = null;

	if ( null === $entity ) {
		$entity = apply_filters(
			'hm_entity',
			array(
				'name'        => '__NAME__',
				'legal_name'  => '__NAME__', // CONFIRM: as written in the client's Terms of Service.
				'alternate'   => array( '__SHORT__' ),
				'tagline'     => '[CONFIRM: tagline from docs/01-strategy.md §3]',
				'description' => '[CONFIRM: who-we-are line: category + defining difference + one proof. 1–2 sentences an AI engine can quote.]',
				'url'         => home_url( '/' ),
				'phone'       => '', // CONFIRM
				'phone_e164'  => '', // CONFIRM: e.g. +15555550123
				'email'       => '', // CONFIRM: public inbox.
				'lead_email'  => get_option( 'admin_email' ), // Where new briefs are emailed. CONFIRM for production.
				'booking'     => '/contact/', // CONFIRM: booking link (e.g. Calendly).
				'founded'     => '', // CONFIRM: year founded.
				'area_served' => 'United States',
				'founders'    => array(
					// array( 'name' => 'Full Name', 'alt' => 'Nickname', 'role' => 'Founder' ),
				),
				'facebook'    => '',
				'instagram'   => '',
				'linkedin'    => '',
				'knows_about' => array(
					// Services and topics, as buyers name them. Feeds Organization schema.
				),
				// Plain-language facts for /llms.txt (one line each; keep them true and public).
				'facts'       => array(
					// 'Serves: …', 'In business: …', 'What makes it different: …',
				),
				// Site-wide copy that templates read (so no client text is hard-coded in the theme).
				'work_description' => '[CONFIRM: one line on the kinds of work in the case studies]',
				'logo'             => array( 'mark' => '__MARK__', 'word' => '__NAME__' ), // Header: square mark + word.
				'wordmark'         => array( '__NAME__' ),                                // Big footer wordmark, one span each.
				'logos_caption'    => '', // e.g. "Trusted by founder-led brands for more than a decade".
				'newsletter_label' => 'One useful idea a month',
				'location_note'    => '', // e.g. "A virtual-first team serving brands across the United States."
				'footer_note'      => '',
				// Company pages listed in /llms.txt (services and case studies are listed automatically).
				'llms_pages'       => array( 'about', 'approach', 'start', 'contact' ),
				// Brief form choices (keys are stored on the lead; labels are what visitors see).
				'brief_form'       => array(
					'needs'   => array(
						'example' => 'Example service',
						'unsure'  => 'Not sure yet, help me figure it out',
					),
					'budgets' => array( 'under-2k' => 'Under $2k / mo', '2k-5k' => '$2k–$5k / mo', '5k-10k' => '$5k–$10k / mo', '10k-plus' => '$10k+ / mo', 'project' => 'A one-off project' ),
				),
				'footer_cta'       => array(
					'title'  => '[CONFIRM: closing echo of the hero, with an <em>accent.</em>]',
					'text'   => 'A 30-minute strategy call. You’ll leave with a straight read on what to fix first, even if we’re not the right fit.',
					'anchor' => '[CONFIRM: price anchor: the lowest real starting price + how the rest is scoped]',
					'button' => 'Get a strategy call',
				),
			)
		);
	}

	return null === $key ? $entity : ( $entity[ $key ] ?? null );
}

/** sameAs profiles for schema (non-empty only). */
function hm_entity_profiles(): array {
	return array_values( array_filter( array( hm_entity( 'facebook' ), hm_entity( 'instagram' ), hm_entity( 'linkedin' ) ) ) );
}
