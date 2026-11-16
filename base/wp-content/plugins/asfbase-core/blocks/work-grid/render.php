<?php
/**
 * Work grid. On a service archive (/work/service/{slug}/) it follows that term.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

$hm_count   = (int) ( $attributes['count'] ?? 4 );
$hm_layout  = in_array( $attributes['layout'] ?? '', array( 'featured', 'grid' ), true ) ? $attributes['layout'] : 'featured';
$hm_service = sanitize_title( $attributes['service'] ?? '' );
$hm_active  = '';

if ( is_tax( 'hm_service' ) ) {
	$hm_service = get_queried_object()->slug;
	$hm_active  = $hm_service;
}

$hm_args = array(
	'post_type'      => 'case_study',
	'posts_per_page' => $hm_count > 0 ? $hm_count : -1,
	'orderby'        => array( 'menu_order' => 'ASC', 'date' => 'DESC' ),
	'no_found_rows'  => true,
);
if ( $hm_service ) {
	$hm_args['tax_query'] = array( array( 'taxonomy' => 'hm_service', 'field' => 'slug', 'terms' => $hm_service ) ); // phpcs:ignore WordPress.DB.SlowDBQuery
}
if ( ! empty( $attributes['excludeCurrent'] ) && is_singular( 'case_study' ) ) {
	$hm_args['post__not_in'] = array( get_the_ID() );
}
$hm_query = new WP_Query( $hm_args );

if ( ! $hm_query->have_posts() && empty( $attributes['showFilter'] ) ) {
	return;
}
?>
<div <?php echo get_block_wrapper_attributes( array( 'class' => 'hm-work-wrap' ) ); // phpcs:ignore ?>>
	<?php if ( ! empty( $attributes['showFilter'] ) ) : ?>
		<?php $hm_terms = get_terms( array( 'taxonomy' => 'hm_service', 'hide_empty' => true ) ); ?>
		<nav class="hm-work-filter" aria-label="Filter work by service">
			<a href="<?php echo esc_url( get_post_type_archive_link( 'case_study' ) ); ?>"<?php echo '' === $hm_active ? ' aria-current="page"' : ''; ?>>All work</a>
			<?php foreach ( is_array( $hm_terms ) ? $hm_terms : array() as $hm_term ) : ?>
				<a href="<?php echo esc_url( get_term_link( $hm_term ) ); ?>"<?php echo $hm_active === $hm_term->slug ? ' aria-current="page"' : ''; ?>><?php echo esc_html( wp_specialchars_decode( $hm_term->name ) ); ?></a>
			<?php endforeach; ?>
		</nav>
	<?php endif; ?>

	<div class="hm-work hm-work--<?php echo esc_attr( $hm_layout ); ?><?php echo 1 === $hm_query->post_count ? ' hm-work--single' : ''; ?>">
		<?php
		while ( $hm_query->have_posts() ) :
			$hm_query->the_post();
			$hm_card = hm_case_card( get_post() );
			?>
			<article class="hm-work__item">
				<a class="hm-work__link" href="<?php echo esc_url( $hm_card['url'] ); ?>">
					<div class="hm-work__media">
						<?php if ( $hm_card['image'] ) : ?>
							<?php echo $hm_card['image']; // phpcs:ignore WordPress.Security.EscapeOutput ?>
						<?php else : ?>
							<?php // No photo yet: a typographic cover built from the headline number. ?>
							<span class="hm-work__placeholder" aria-hidden="true">
								<span class="hm-work__ph-client"><?php echo esc_html( $hm_card['client'] ); ?></span>
								<strong><?php echo esc_html( $hm_card['stat'] ?: mb_substr( $hm_card['client'] ?: $hm_card['title'], 0, 2 ) ); ?></strong>
								<span class="hm-work__ph-label"><?php echo esc_html( $hm_card['stat_label'] ); ?></span>
							</span>
						<?php endif; ?>
						<?php if ( $hm_card['stat'] && $hm_card['image'] ) : ?>
							<span class="hm-work__stat"><strong><?php echo esc_html( $hm_card['stat'] ); ?></strong> <?php echo esc_html( $hm_card['stat_label'] ); ?></span>
						<?php endif; ?>
					</div>
					<div class="hm-work__meta"><span><?php echo esc_html( $hm_card['client'] ); ?></span><span><?php echo esc_html( $hm_card['services'] ); ?></span></div>
					<?php // Under a page's h1 (the /work/ archives) the card titles are h2; under a section's h2, h3. ?>
					<h<?php echo 2 === (int) ( $attributes['titleLevel'] ?? 3 ) ? 2 : 3; ?> class="hm-work__title"><?php echo esc_html( $hm_card['title'] ); ?></h<?php echo 2 === (int) ( $attributes['titleLevel'] ?? 3 ) ? 2 : 3; ?>>
				</a>
			</article>
		<?php endwhile; ?>
		<?php wp_reset_postdata(); ?>
	</div>
</div>
