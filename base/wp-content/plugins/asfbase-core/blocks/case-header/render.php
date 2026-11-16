<?php
/**
 * Case study header: breadcrumb, title, summary, facts row.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

$hm_id = (int) ( $block->context['postId'] ?? get_the_ID() );
if ( ! $hm_id || 'case_study' !== get_post_type( $hm_id ) ) {
	return;
}

$hm_services   = get_the_terms( $hm_id, 'hm_service' );
$hm_industries = get_the_terms( $hm_id, 'hm_industry' );
$hm_list       = fn( $terms ) => $terms && ! is_wp_error( $terms ) ? wp_specialchars_decode( implode( ', ', wp_list_pluck( $terms, 'name' ) ) ) : '—';
$hm_client     = get_post_meta( $hm_id, 'hm_client', true );
$hm_year       = get_post_meta( $hm_id, 'hm_year', true );
?>
<section <?php echo get_block_wrapper_attributes( array( 'class' => 'hm-section hm-page-hero hm-case-hero alignfull' ) ); // phpcs:ignore ?>>
	<p class="hm-label"><a href="<?php echo esc_url( get_post_type_archive_link( 'case_study' ) ); ?>" style="color:inherit">Work</a>&nbsp;/&nbsp;<?php echo esc_html( $hm_client ); ?></p>
	<h1><?php echo esc_html( get_the_title( $hm_id ) ); ?></h1>
	<?php if ( has_excerpt( $hm_id ) ) : ?>
		<p class="hm-lead" style="margin-top:2rem"><?php echo esc_html( get_the_excerpt( $hm_id ) ); ?></p>
	<?php endif; ?>
	<ul class="hm-case-meta">
		<li><strong>Client</strong><?php echo esc_html( $hm_client ?: '—' ); ?></li>
		<li><strong>Services</strong><?php echo esc_html( $hm_list( $hm_services ) ); ?></li>
		<li><strong>Industry</strong><?php echo esc_html( $hm_list( $hm_industries ) ); ?></li>
		<li><strong>Timeline</strong><?php echo esc_html( $hm_year ?: '—' ); ?></li>
	</ul>
</section>
