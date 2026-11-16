<?php
/**
 * Site header. Behaviour (sticky hide/show, mega panel, mobile menu) is in assets/js/site.js.
 *
 * @package asfbase
 */

defined( 'ABSPATH' ) || exit;

$asfbase_nav = asfbase_nav();
$asfbase_cta = $asfbase_nav['cta'];
// The menu item that opens the mega panel names its intro and "All …" link.
$asfbase_mega_item = current( array_filter( $asfbase_nav['primary'], static fn( $item ) => ! empty( $item['mega'] ) ) ) ?: array( 'label' => 'Services', 'url' => '/services/' );
// The "next step" link under the mega panel and at the end of the mobile menu (navigation.php → 'secondary').
$asfbase_next = wp_parse_args( (array) ( $asfbase_nav['secondary'] ?? array() ), array( 'label' => 'Ways to start', 'url' => '/start/', 'mega' => 'See ways to start →' ) );
$asfbase_logo = wp_parse_args( (array) asfbase_fact( 'logo', array() ), array( 'mark' => '', 'word' => asfbase_entity( 'name' ) ) );
?>
<header class="hm-header" data-header>
	<a class="hm-skip" href="#main">Skip to content</a>
	<div class="hm-header__bar">
		<a class="hm-logo" href="<?php echo esc_url( home_url( '/' ) ); ?>" aria-label="<?php echo esc_attr( asfbase_entity( 'name' ) ); ?>, home">
			<?php if ( $asfbase_logo['mark'] ) : ?>
				<span class="hm-logo__mark" aria-hidden="true"><?php echo esc_html( $asfbase_logo['mark'] ); ?></span>
			<?php endif; ?>
			<span class="hm-logo__word" aria-hidden="true"><?php echo esc_html( $asfbase_logo['word'] ); ?></span>
		</a>

		<nav class="hm-nav" aria-label="Primary">
			<ul class="hm-nav__list">
				<?php foreach ( $asfbase_nav['primary'] as $asfbase_item ) : ?>
					<?php $asfbase_current = asfbase_is_current( $asfbase_item['url'] ); ?>
					<li class="hm-nav__item<?php echo ! empty( $asfbase_item['mega'] ) ? ' has-mega' : ''; ?>">
						<?php if ( ! empty( $asfbase_item['mega'] ) ) : ?>
							<button class="hm-nav__link" type="button" aria-expanded="false" aria-controls="hm-mega-<?php echo esc_attr( $asfbase_item['mega'] ); ?>"<?php echo $asfbase_current ? ' data-current' : ''; ?>>
								<?php echo esc_html( $asfbase_item['label'] ); ?>
								<?php echo asfbase_icon( 'plus' ); // phpcs:ignore WordPress.Security.EscapeOutput ?>
							</button>
						<?php else : ?>
							<a class="hm-nav__link" href="<?php echo esc_url( asfbase_url( $asfbase_item['url'] ) ); ?>"<?php echo $asfbase_current ? ' aria-current="page"' : ''; ?>><?php echo esc_html( $asfbase_item['label'] ); ?></a>
						<?php endif; ?>
					</li>
				<?php endforeach; ?>
			</ul>
		</nav>

		<div class="hm-header__actions">
			<a class="hm-btn hm-btn--sm hm-header__cta" href="<?php echo esc_url( asfbase_url( $asfbase_cta['url'] ) ); ?>" data-cta="header"><?php echo esc_html( $asfbase_cta['label'] ); ?><?php echo asfbase_icon( 'arrow' ); // phpcs:ignore ?></a>
			<button class="hm-burger" type="button" aria-expanded="false" aria-controls="hm-mobile">
				<span class="hm-burger__label">Menu</span>
				<span class="hm-burger__lines" aria-hidden="true"><i></i><i></i></span>
			</button>
		</div>
	</div>

	<div class="hm-mega" id="hm-mega-services" hidden>
		<div class="hm-mega__inner">
			<div class="hm-mega__intro">
				<p class="hm-label"><?php echo esc_html( $asfbase_mega_item['label'] ); ?></p>
				<p class="hm-mega__title"><?php echo wp_kses( $asfbase_nav['mega']['title'] ?? '', array( 'em' => array() ) ); ?></p>
				<a class="hm-link-arrow" href="<?php echo esc_url( asfbase_url( $asfbase_mega_item['url'] ) ); ?>">All <?php echo esc_html( strtolower( $asfbase_mega_item['label'] ) ); ?> <?php echo asfbase_icon( 'arrow' ); // phpcs:ignore ?></a>
			</div>
			<div class="hm-mega__groups">
				<?php foreach ( $asfbase_nav['services'] as $asfbase_i => $asfbase_group ) : ?>
					<div class="hm-mega__group">
						<p class="hm-label"><span class="hm-label__num"><?php echo esc_html( sprintf( '%02d', $asfbase_i + 1 ) ); ?></span> <?php echo esc_html( $asfbase_group['group'] ); ?></p>
						<ul>
							<?php foreach ( $asfbase_group['items'] as $asfbase_link ) : ?>
								<li>
									<a href="<?php echo esc_url( asfbase_url( $asfbase_link['url'] ) ); ?>">
										<span class="hm-mega__ico" aria-hidden="true"><?php echo asfbase_icon( $asfbase_link['icon'] ?? 'arrow' ); // phpcs:ignore ?></span>
										<span class="hm-mega__name"><?php echo esc_html( $asfbase_link['label'] ); ?></span>
										<span class="hm-mega__desc"><?php echo esc_html( $asfbase_link['desc'] ); ?></span>
									</a>
								</li>
							<?php endforeach; ?>
						</ul>
					</div>
				<?php endforeach; ?>
			</div>
			<?php $asfbase_feature = $asfbase_nav['feature'] ?? array(); ?>
			<?php if ( ! empty( $asfbase_feature['url'] ) ) : ?>
				<a class="hm-mega__feature" href="<?php echo esc_url( asfbase_url( $asfbase_feature['url'] ) ); ?>">
					<span class="hm-label"><?php echo esc_html( $asfbase_feature['eyebrow'] ); ?></span>
					<span class="hm-mega__feature-title"><?php echo esc_html( $asfbase_feature['title'] ); ?></span>
					<span class="hm-mega__feature-client"><?php echo esc_html( $asfbase_feature['client'] ); ?> <?php echo asfbase_icon( 'arrow-ne' ); // phpcs:ignore ?></span>
				</a>
			<?php endif; ?>
			<?php if ( ! empty( $asfbase_nav['mega']['footer'] ) ) : ?>
				<div class="hm-mega__footer">
					<span><?php echo esc_html( $asfbase_nav['mega']['footer'] ); ?></span>
					<a href="<?php echo esc_url( asfbase_url( $asfbase_next['url'] ) ); ?>"><?php echo esc_html( $asfbase_next['mega'] ); ?></a>
				</div>
			<?php endif; ?>
		</div>
	</div>

	<div class="hm-mobile" id="hm-mobile" hidden>
		<nav class="hm-mobile__nav" aria-label="Mobile">
			<ul>
				<?php foreach ( $asfbase_nav['primary'] as $asfbase_item ) : ?>
					<li><a href="<?php echo esc_url( asfbase_url( $asfbase_item['url'] ) ); ?>"><?php echo esc_html( $asfbase_item['label'] ); ?></a></li>
				<?php endforeach; ?>
				<li><a href="<?php echo esc_url( asfbase_url( $asfbase_next['url'] ) ); ?>"><?php echo esc_html( $asfbase_next['label'] ); ?></a></li>
			</ul>
			<ul class="hm-mobile__services">
				<?php foreach ( $asfbase_nav['services'] as $asfbase_group ) : ?>
					<?php foreach ( $asfbase_group['items'] as $asfbase_link ) : ?>
						<li><a href="<?php echo esc_url( asfbase_url( $asfbase_link['url'] ) ); ?>"><?php echo esc_html( $asfbase_link['label'] ); ?></a></li>
					<?php endforeach; ?>
				<?php endforeach; ?>
			</ul>
		</nav>
		<div class="hm-mobile__foot">
			<a class="hm-btn" href="<?php echo esc_url( asfbase_url( $asfbase_cta['url'] ) ); ?>" data-cta="mobile-menu"><?php echo esc_html( $asfbase_cta['label'] ); ?> <?php echo asfbase_icon( 'arrow' ); // phpcs:ignore ?></a>
			<a class="hm-mobile__phone" href="tel:<?php echo esc_attr( asfbase_entity( 'phone_e164' ) ); ?>"><?php echo esc_html( asfbase_entity( 'phone' ) ); ?></a>
		</div>
	</div>
</header>
