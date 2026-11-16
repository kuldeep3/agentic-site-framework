<?php
/**
 * Hero visual: one real client photo and one small results card. Kept
 * deliberately calm. The headline does the talking; this proves it's real work.
 * Decorative (aria-hidden): the same result appears as text in the case study.
 *
 * @package asfbase
 */

defined( 'ABSPATH' ) || exit;

$asfbase_photo = asfbase_case_image( $attributes['photoCase'] ?? '', 'large' );
if ( ! empty( $attributes['image'] ) ) {
	// Width and height stop the layout jumping while the image loads (CLS).
	$asfbase_dims = '';
	$asfbase_up   = wp_get_upload_dir();
	$asfbase_rel  = str_replace( set_url_scheme( $asfbase_up['baseurl'], 'relative' ), '', (string) wp_parse_url( $attributes['image'], PHP_URL_PATH ) );
	$asfbase_size = str_starts_with( $asfbase_rel, '/' ) ? wp_getimagesize( $asfbase_up['basedir'] . $asfbase_rel ) : false;
	if ( $asfbase_size ) {
		$asfbase_dims = sprintf( ' width="%d" height="%d"', $asfbase_size[0], $asfbase_size[1] );
	}
	$asfbase_photo = '<img src="' . esc_url( $attributes['image'] ) . '" alt=""' . $asfbase_dims . ' fetchpriority="high">';
}
$asfbase_case  = get_page_by_path( (string) ( $attributes['photoCase'] ?? '' ), OBJECT, 'case_study' );
$asfbase_stat  = $asfbase_case ? (string) get_post_meta( $asfbase_case->ID, 'hm_stat', true ) : '';
$asfbase_who   = $asfbase_case ? (string) get_post_meta( $asfbase_case->ID, 'hm_client', true ) : '';
?>
<div <?php echo get_block_wrapper_attributes( array( 'class' => 'hm-hv' ) ); // phpcs:ignore ?> data-parallax aria-hidden="true">
	<div class="hm-hv__photo" data-depth="0.02"><?php echo $asfbase_photo; // phpcs:ignore WordPress.Security.EscapeOutput ?></div>
	<?php if ( $asfbase_stat ) : ?>
		<div class="hm-hv__card" data-depth="0.06">
			<span class="hm-hv__card-label"><?php echo esc_html( $attributes['photoChip'] ?? '' ); ?></span>
			<strong><?php echo esc_html( $asfbase_stat ); ?></strong>
			<span class="hm-hv__card-who"><?php echo esc_html( $asfbase_who ); ?></span>
		</div>
	<?php endif; ?>
</div>
