<?php
/**
 * Hero visual: one real client photo and one small results card. Kept
 * deliberately calm. The headline does the talking; this proves it's real work.
 * With "alt" set, the photo is content (alt text, optional caption); without it, decorative (aria-hidden).
 *
 * @package asfbase
 */

defined( 'ABSPATH' ) || exit;

$asfbase_photo = asfbase_case_image( $attributes['photoCase'] ?? '', 'large' );
if ( ! empty( $attributes['image'] ) ) {
	// Width/height stop the layout jumping while it loads (CLS); srcset serves a smaller size on phones.
	$asfbase_photo = asfbase_media_img( (string) $attributes['image'], 'fetchpriority="high"' );
}
$asfbase_alt     = trim( (string) ( $attributes['alt'] ?? '' ) );
$asfbase_caption = trim( (string) ( $attributes['caption'] ?? '' ) );
if ( $asfbase_alt && $asfbase_photo ) {
	$asfbase_photo = preg_replace( '/ alt=""/', ' alt="' . esc_attr( $asfbase_alt ) . '"', $asfbase_photo, 1 );
}
$asfbase_case  = get_page_by_path( (string) ( $attributes['photoCase'] ?? '' ), OBJECT, 'case_study' );
$asfbase_stat  = $asfbase_case ? (string) get_post_meta( $asfbase_case->ID, 'hm_stat', true ) : '';
$asfbase_who   = $asfbase_case ? (string) get_post_meta( $asfbase_case->ID, 'hm_client', true ) : '';
?>
<div <?php echo get_block_wrapper_attributes( array( 'class' => 'hm-hv' ) ); // phpcs:ignore ?> data-parallax<?php echo $asfbase_alt ? '' : ' aria-hidden="true"'; ?>>
	<div class="hm-hv__photo" data-depth="0.02"><?php echo $asfbase_photo; // phpcs:ignore WordPress.Security.EscapeOutput ?></div>
	<?php if ( $asfbase_caption ) : ?>
		<p class="hm-hv__caption"><?php echo esc_html( $asfbase_caption ); ?></p>
	<?php endif; ?>
	<?php if ( $asfbase_stat ) : ?>
		<div class="hm-hv__card" data-depth="0.06">
			<span class="hm-hv__card-label"><?php echo esc_html( $attributes['photoChip'] ?? '' ); ?></span>
			<strong><?php echo esc_html( $asfbase_stat ); ?></strong>
			<span class="hm-hv__card-who"><?php echo esc_html( $asfbase_who ); ?></span>
		</div>
	<?php endif; ?>
</div>
