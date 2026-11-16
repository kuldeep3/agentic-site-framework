<?php
/**
 * Plugin Name: ASF Base Core
 * Description: Site functionality for ASF Base: case studies, lead capture, SEO/AEO (schema, llms.txt, robots), redirects, dynamic blocks, analytics, metrics, hardening and site health. Theme-independent by design.
 * Version: 1.0.0
 * Requires at least: 6.6
 * Requires PHP: 8.1
 * Author: ASF Base
 * Text Domain: hm
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

define( 'HM_CORE_VERSION', '1.0.0' );
define( 'HM_CORE_DIR', __DIR__ );
define( 'HM_CORE_FILE', __FILE__ );

foreach ( array( 'entity', 'post-types', 'blocks', 'leads', 'seo', 'schema', 'llms', 'robots', 'redirects', 'analytics', 'metrics', 'hardening', 'health' ) as $hm_module ) {
	require HM_CORE_DIR . "/inc/{$hm_module}.php";
}

register_activation_hook(
	__FILE__,
	function () {
		hm_register_content_types();
		hm_llms_rewrite();
		flush_rewrite_rules();
	}
);
