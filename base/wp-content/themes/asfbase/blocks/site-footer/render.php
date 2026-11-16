<?php
/**
 * Site footer with the closing CTA every page ends on.
 *
 * The CTA is hidden on /contact/ and /thank-you/ (they *are* the CTA).
 *
 * @package asfbase
 */

defined( 'ABSPATH' ) || exit;

$asfbase_nav      = asfbase_nav();
$asfbase_show_cta = ! empty( $attributes['showCta'] ) && ! is_page( array( 'contact', 'thank-you' ) );
$asfbase_booking  = asfbase_entity( 'booking' );
$asfbase_cta_copy = wp_parse_args( (array) asfbase_fact( 'footer_cta', array() ), array( 'title' => 'Let’s build what’s <em>next.</em>', 'text' => '', 'anchor' => '', 'button' => 'Book a call', 'url' => '', 'secondary' => 'Send a brief', 'secondary_url' => '/contact/' ) );
// The primary button goes to footer_cta['url'] when set, else the booking link; only off-site links open a new tab.
$asfbase_cta_url      = $asfbase_cta_copy['url'] ? $asfbase_cta_copy['url'] : $asfbase_booking;
$asfbase_cta_external = (bool) preg_match( '#^https?://#', $asfbase_cta_url ) && ! str_starts_with( $asfbase_cta_url, home_url() );
?>
<footer class="hm-footer">
	<?php if ( $asfbase_show_cta ) : ?>
		<section class="hm-footer__cta" aria-labelledby="hm-footer-cta-title">
			<p class="hm-label" data-reveal>Next step</p>
			<h2 id="hm-footer-cta-title" class="hm-footer__cta-title" data-reveal><?php echo wp_kses( $asfbase_cta_copy['title'], array( 'em' => array() ) ); ?></h2>
			<div class="hm-footer__cta-row" data-reveal>
				<p><?php echo esc_html( $asfbase_cta_copy['text'] ); ?><?php if ( $asfbase_cta_copy['anchor'] ) : ?><br><span class="hm-footer__anchor"><?php echo esc_html( $asfbase_cta_copy['anchor'] ); ?></span><?php endif; ?></p>
				<div class="hm-footer__cta-actions">
					<a class="hm-btn hm-btn--orange" href="<?php echo esc_url( asfbase_url( $asfbase_cta_url ) ); ?>"<?php echo $asfbase_cta_external ? ' target="_blank" rel="noopener"' : ''; ?> data-cta="footer-book" data-booking><?php echo esc_html( $asfbase_cta_copy['button'] ); ?> <?php echo asfbase_icon( 'arrow-ne' ); // phpcs:ignore ?></a>
					<a class="hm-btn hm-btn--ghost" href="<?php echo esc_url( asfbase_url( $asfbase_cta_copy['secondary_url'] ) ); ?>" data-cta="footer-brief"><?php echo esc_html( $asfbase_cta_copy['secondary'] ); ?></a>
				</div>
			</div>
		</section>
	<?php endif; ?>

	<div class="hm-footer__main">
		<div class="hm-footer__contact">
			<p class="hm-label">Talk to us</p>
			<?php if ( asfbase_entity( 'phone' ) ) : ?>
				<a class="hm-footer__big-link" href="tel:<?php echo esc_attr( asfbase_entity( 'phone_e164' ) ); ?>" data-cta="footer-phone"><?php echo esc_html( asfbase_entity( 'phone' ) ); ?></a>
			<?php endif; ?>
			<?php if ( asfbase_entity( 'email' ) ) : ?>
				<a class="hm-footer__big-link" href="mailto:<?php echo esc_attr( asfbase_entity( 'email' ) ); ?>"><?php echo esc_html( asfbase_entity( 'email' ) ); ?></a>
			<?php endif; ?>
			<p class="hm-footer__note"><?php echo esc_html( (string) asfbase_fact( 'location_note', '' ) ); ?></p>

			<form class="hm-newsletter" data-newsletter novalidate>
				<label class="hm-label" for="hm-newsletter-email"><?php echo esc_html( (string) asfbase_fact( 'newsletter_label', 'One useful idea a month' ) ); ?></label>
				<div class="hm-newsletter__row">
					<input id="hm-newsletter-email" name="email" type="email" autocomplete="email" placeholder="you@company.com" required>
					<input type="text" name="company_url" tabindex="-1" autocomplete="off" class="hm-hp" aria-hidden="true">
					<button type="submit" aria-label="Subscribe"><?php echo asfbase_icon( 'arrow' ); // phpcs:ignore ?></button>
				</div>
				<p class="hm-newsletter__msg" role="status" aria-live="polite"></p>
			</form>
		</div>

		<nav class="hm-footer__cols" aria-label="Footer">
			<?php foreach ( $asfbase_nav['footer'] as $asfbase_col ) : ?>
				<div class="hm-footer__col">
					<p class="hm-label"><?php echo esc_html( $asfbase_col['title'] ); ?></p>
					<ul>
						<?php foreach ( $asfbase_col['links'] as $asfbase_link ) : ?>
							<li><a href="<?php echo esc_url( asfbase_url( $asfbase_link['url'] ) ); ?>"><?php echo esc_html( $asfbase_link['label'] ); ?></a></li>
						<?php endforeach; ?>
					</ul>
				</div>
			<?php endforeach; ?>
			<?php if ( array_filter( array( asfbase_entity( 'instagram' ), asfbase_entity( 'facebook' ), asfbase_entity( 'linkedin' ) ) ) ) : ?>
			<div class="hm-footer__col">
				<p class="hm-label">Follow</p>
				<ul>
					<?php foreach ( array( 'instagram' => 'Instagram', 'facebook' => 'Facebook', 'linkedin' => 'LinkedIn' ) as $asfbase_key => $asfbase_label ) : ?>
						<?php $asfbase_href = asfbase_entity( $asfbase_key ); ?>
						<?php if ( $asfbase_href ) : ?>
							<li><a href="<?php echo esc_url( $asfbase_href ); ?>" rel="noopener me" target="_blank"><?php echo esc_html( $asfbase_label ); ?></a></li>
						<?php endif; ?>
					<?php endforeach; ?>
				</ul>
			</div>
			<?php endif; ?>
		</nav>
	</div>

	<div class="hm-footer__wordmark" aria-hidden="true">
		<?php foreach ( (array) asfbase_fact( 'wordmark', explode( ' ', asfbase_entity( 'name' ) ) ) as $asfbase_word ) : ?><span><?php echo esc_html( $asfbase_word ); ?></span><?php endforeach; ?>
	</div>

	<div class="hm-footer__legal">
		<p>© <?php echo esc_html( gmdate( 'Y' ) . ' ' . asfbase_entity( 'name' ) . '. ' . (string) asfbase_fact( 'footer_note', '' ) ); ?></p>
		<ul>
			<?php foreach ( $asfbase_nav['legal'] as $asfbase_link ) : ?>
				<li><a href="<?php echo esc_url( asfbase_url( $asfbase_link['url'] ) ); ?>"><?php echo esc_html( $asfbase_link['label'] ); ?></a></li>
			<?php endforeach; ?>
		</ul>
	</div>
</footer>
