<?php
/**
 * Next case study (Work order, wrapping to the first).
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

$hm_id  = (int) ( $block->context['postId'] ?? get_the_ID() );
$hm_ids = get_posts(
	array(
		'post_type'      => 'case_study',
		'posts_per_page' => -1,
		'fields'         => 'ids',
		'orderby'        => array( 'menu_order' => 'ASC', 'date' => 'DESC' ),
	)
);
if ( count( $hm_ids ) < 2 ) {
	return;
}
$hm_pos  = array_search( $hm_id, $hm_ids, true );
$hm_next = get_post( $hm_ids[ ( false === $hm_pos ? 0 : $hm_pos + 1 ) % count( $hm_ids ) ] );
$hm_card = hm_case_card( $hm_next );
?>
<section <?php echo get_block_wrapper_attributes( array( 'class' => 'hm-section hm-dark alignfull' ) ); // phpcs:ignore ?>>
	<a class="hm-next-case" href="<?php echo esc_url( $hm_card['url'] ); ?>">
		<span>
			<span class="hm-label">Next case · <?php echo esc_html( $hm_card['client'] ); ?></span>
			<span class="hm-next-case__title" style="display:block;margin-top:1.25rem"><?php echo esc_html( $hm_card['title'] ); ?></span>
		</span>
		<span class="hm-btn hm-btn--orange" aria-hidden="true">Read it <?php echo function_exists( 'asfbase_icon' ) ? asfbase_icon( 'arrow' ) : '→'; // phpcs:ignore ?></span>
	</a>
</section>
