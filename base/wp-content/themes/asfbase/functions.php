<?php
/**
 * ASF Base theme bootstrap.
 *
 * Presentation only: layout, styles, header/footer and front-end behaviour.
 * Content types, SEO, schema and lead capture live in the asfbase-core plugin
 * so the site keeps working if the theme is ever replaced.
 *
 * @package asfbase
 */

defined( 'ABSPATH' ) || exit;

define( 'ASFBASE_VERSION', '1.0.0' );
define( 'ASFBASE_DIR', get_template_directory() );
define( 'ASFBASE_URI', get_template_directory_uri() );

require ASFBASE_DIR . '/inc/navigation.php';
require ASFBASE_DIR . '/inc/setup.php';
require ASFBASE_DIR . '/inc/blocks.php';
require ASFBASE_DIR . '/inc/helpers.php';
