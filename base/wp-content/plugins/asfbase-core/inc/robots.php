<?php
/**
 * robots.txt: explicitly welcome search and AI crawlers.
 *
 * Being read and cited by AI assistants is usually a goal for an agency or brand,
 * not a risk; record the client's decision in docs/decisions.md. Only applies to
 * WordPress's virtual robots.txt. If a physical robots.txt exists on the server, it wins.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

add_filter(
	'robots_txt',
	function ( string $output, bool $public ) {
		if ( ! $public ) {
			return $output; // "Discourage search engines" is on (e.g. staging): leave WP's Disallow.
		}
		$ai = array( 'GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'PerplexityBot', 'Google-Extended', 'Applebot-Extended', 'Bingbot' );
		$lines   = array( '', '# AI assistants and answer engines are welcome.' );
		foreach ( $ai as $bot ) {
			$lines[] = "User-agent: {$bot}";
			$lines[] = 'Allow: /';
			$lines[] = 'Disallow: /wp-admin/';
			$lines[] = '';
		}
		$lines[] = '# Plain-language site map for LLMs';
		$lines[] = '# ' . home_url( '/llms.txt' );
		return rtrim( $output ) . "\n" . implode( "\n", $lines ) . "\n";
	},
	10,
	2
);
