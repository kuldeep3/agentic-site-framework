<?php
/**
 * Analytics: loads GA4 (gtag.js) or a Google Tag Manager container, with Consent Mode.
 *
 * Set it per environment (staging and production differ), never in the theme:
 *   wp-config.php   define( 'ASF_GA4_ID', 'G-XXXXXXX' );   or   define( 'ASF_GTM_ID', 'GTM-XXXXXX' );
 *                   define( 'ASF_ANALYTICS_CONSENT', 'required' );   // or 'not_required'
 *   or an option    wp option update hm_analytics '{"ga4":"G-XXXXXXX","consent":"required"}' --format=json
 *
 * Consent: 'required' (the default, and what UK/EU sites need) starts with analytics and ad
 * storage denied (Google Consent Mode v2). The site's consent banner calls
 * window.asfConsent.grant() when the visitor agrees. 'not_required' grants from the start.
 * Nothing loads on local sites unless ASF_ANALYTICS_LOCAL is true, so test visits stay out.
 *
 * The theme already pushes events to the dataLayer (cta_click, lead_submit, book_call_open,
 * phone_click, offer_view, newsletter_signup). In gtag mode they are sent to GA4 as events; in
 * GTM mode they are there for the container's triggers.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

/** @return array{ga4: string, gtm: string, consent: string} Only well-formed IDs survive. */
function hm_analytics_config(): array {
	$opt = (array) get_option( 'hm_analytics', array() );
	$ga4 = defined( 'ASF_GA4_ID' ) ? (string) ASF_GA4_ID : (string) ( $opt['ga4'] ?? '' );
	$gtm = defined( 'ASF_GTM_ID' ) ? (string) ASF_GTM_ID : (string) ( $opt['gtm'] ?? '' );
	$con = defined( 'ASF_ANALYTICS_CONSENT' ) ? (string) ASF_ANALYTICS_CONSENT : (string) ( $opt['consent'] ?? 'required' );
	return array(
		'ga4'     => preg_match( '/^G-[A-Z0-9]{4,}$/', $ga4 ) ? $ga4 : '',
		'gtm'     => preg_match( '/^GTM-[A-Z0-9]{4,}$/', $gtm ) ? $gtm : '',
		'consent' => 'not_required' === $con ? 'not_required' : 'required',
	);
}

function hm_analytics_active(): bool {
	if ( is_admin() || is_preview() || is_customize_preview() ) {
		return false;
	}
	if ( 'local' === wp_get_environment_type() && ! ( defined( 'ASF_ANALYTICS_LOCAL' ) && ASF_ANALYTICS_LOCAL ) ) {
		return false;
	}
	$c = hm_analytics_config();
	return '' !== $c['ga4'] || '' !== $c['gtm'];
}

add_action(
	'wp_head',
	function () {
		if ( ! hm_analytics_active() ) {
			return;
		}
		$c     = hm_analytics_config();
		$state = 'required' === $c['consent'] ? 'denied' : 'granted';
		$defaults = array(
			'ad_storage'         => $state,
			'ad_user_data'       => $state,
			'ad_personalization' => $state,
			'analytics_storage'  => $state,
			'wait_for_update'    => 500,
		);
		echo "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('consent','default'," . wp_json_encode( $defaults ) . ');'
			. 'window.asfConsentRequired=' . ( 'required' === $c['consent'] ? 'true' : 'false' ) . ';'
			// grant() also lets the theme remember where the visit came from (campaign attribution).
			. "window.asfConsent={grant:function(){gtag('consent','update',{ad_storage:'granted',ad_user_data:'granted',ad_personalization:'granted',analytics_storage:'granted'});window.asfConsentGranted=true;document.dispatchEvent(new Event('asf:consent'));}};</script>\n";
		if ( $c['gtm'] ) {
			printf(
				"<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s);j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer',%s);</script>\n",
				wp_json_encode( $c['gtm'] )
			);
			return;
		}
		printf( '<script async src="%s"></script>' . "\n", esc_url( 'https://www.googletagmanager.com/gtag/js?id=' . $c['ga4'] ) );
		// asfGtagEvents tells the theme to send its dataLayer events to GA4 as well.
		printf( "<script>gtag('js',new Date());gtag('config',%s);window.asfGtagEvents=true;</script>\n", wp_json_encode( $c['ga4'] ) );
	},
	1
);

add_action(
	'wp_body_open',
	function () {
		$c = hm_analytics_config();
		if ( hm_analytics_active() && $c['gtm'] ) {
			printf( '<noscript><iframe src="%s" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>' . "\n", esc_url( 'https://www.googletagmanager.com/ns.html?id=' . $c['gtm'] ) );
		}
	}
);
