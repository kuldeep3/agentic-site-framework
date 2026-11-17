<?php
/**
 * Brief form: three short steps so a call starts informed.
 *
 * Step 1 qualifies the need, step 2 the budget/timing (lets the team route and
 * prioritise), step 3 is contact. Works without JS as one long form posting to
 * the same REST endpoint (see leads.php). Step logic lives in the theme's site.js.
 *
 * @package hm
 */

defined( 'ABSPATH' ) || exit;

$hm_variant = ( $attributes['variant'] ?? 'brief' ) === 'audit' ? 'audit' : 'brief';
$hm_uid     = wp_unique_id( 'hm-brief-' );

// The choices are client copy, so they live with the other facts in inc/entity.php.
$hm_form    = (array) hm_entity( 'brief_form' );
$hm_needs   = (array) ( $hm_form['needs'] ?? array( 'unsure' => 'Not sure yet, help me figure it out' ) );
$hm_budgets = (array) ( $hm_form['budgets'] ?? array( 'project' => 'A one-off project' ) );
$hm_timelines = (array) ( $hm_form['timelines'] ?? array( 'asap' => 'As soon as possible', '1-3m' => 'In 1–3 months', 'this-year' => 'Later this year', 'exploring' => 'Just exploring' ) );
// Questions and small print, overridable per client in brief_form['copy'].
$hm_copy = wp_parse_args(
	(array) ( $hm_form['copy'] ?? array() ),
	array(
		'needs_q'       => 'What can we help you build?',
		'needs_q_audit' => 'Where should we look first?',
		'budget_q'      => 'What’s the monthly investment you have in mind?',
		'timeline_q'    => 'When do you want to start?',
		'message_hint'  => 'Goals, what’s not working, links…',
		'submit'        => 'Send my brief',
		'fine'          => 'A strategist reads every brief and replies within one business day. No spam, no newsletter unless you ask.',
		'contact_q'     => 'Last step. Where do we reach you?',
		// Step 3 fields, in order: a key keeps its default label, key => label relabels it.
		'fields'        => array( 'name', 'email', 'company', 'website', 'phone', 'message' ),
	)
);

// Optional translation hook: a site that defines hm_t() (e.g. an i18n layer) gets the fixed labels translated.
$hm_t = static fn( string $s ): string => function_exists( 'hm_t' ) ? hm_t( $s ) : $s;

// Step 3 inputs. Name and email always show: leads.php refuses a brief without them.
$hm_inputs = array(
	'name'    => array( 'Your name *', 'autocomplete="name" required' ),
	'email'   => array( 'Work email *', 'type="email" autocomplete="email" required' ),
	'company' => array( 'Company', 'autocomplete="organization"' ),
	'website' => array( 'Website', 'type="url" inputmode="url" placeholder="https://"' ),
	'phone'   => array( 'Phone', 'type="tel" autocomplete="tel" inputmode="tel"' ),
	'message' => array( 'Anything else we should know?', '' ),
);
$hm_fields = array();
foreach ( (array) $hm_copy['fields'] as $hm_key => $hm_label ) {
	$hm_name = is_int( $hm_key ) ? (string) $hm_label : (string) $hm_key;
	if ( isset( $hm_inputs[ $hm_name ] ) ) {
		$hm_fields[ $hm_name ] = is_int( $hm_key ) ? $hm_inputs[ $hm_name ][0] : (string) $hm_label;
	}
}
$hm_fields = array_diff_key( array( 'name' => $hm_inputs['name'][0], 'email' => $hm_inputs['email'][0] ), $hm_fields ) + $hm_fields;

$hm_q1 = 'audit' === $hm_variant ? $hm_copy['needs_q_audit'] : $hm_copy['needs_q'];
?>
<form <?php echo get_block_wrapper_attributes( array( 'class' => 'hm-form' ) ); // phpcs:ignore ?> data-brief method="post" action="<?php echo esc_url( rest_url( 'asfbase/v1/leads' ) ); ?>" novalidate>
	<input type="hidden" name="variant" value="<?php echo esc_attr( $hm_variant ); ?>">
	<input type="text" name="company_url" class="hm-hp" tabindex="-1" autocomplete="off" aria-hidden="true">

	<div class="hm-form__step" data-step="1">
		<fieldset>
			<legend><?php echo esc_html( $hm_q1 ); ?> <span class="hm-form__hint"><?php echo esc_html( $hm_t( 'Pick all that apply' ) ); ?></span></legend>
			<div class="hm-chips">
				<?php $hm_first = true; ?>
				<?php foreach ( $hm_needs as $hm_value => $hm_label ) : ?>
					<label class="hm-chip"><input type="checkbox" name="needs[]" value="<?php echo esc_attr( $hm_value ); ?>"<?php echo $hm_first ? ' required' : ''; ?>><span><?php echo esc_html( $hm_label ); ?></span></label>
					<?php $hm_first = false; ?>
				<?php endforeach; ?>
			</div>
		</fieldset>
	</div>

	<div class="hm-form__step" data-step="2">
		<fieldset>
			<legend><?php echo esc_html( $hm_copy['budget_q'] ); ?></legend>
			<div class="hm-chips">
				<?php foreach ( $hm_budgets as $hm_value => $hm_label ) : ?>
					<label class="hm-chip"><input type="radio" name="budget" value="<?php echo esc_attr( $hm_value ); ?>" required><span><?php echo esc_html( $hm_label ); ?></span></label>
				<?php endforeach; ?>
			</div>
		</fieldset>
		<fieldset class="hm-form__then">
			<legend><?php echo esc_html( $hm_copy['timeline_q'] ); ?></legend>
			<div class="hm-chips">
				<?php foreach ( $hm_timelines as $hm_value => $hm_label ) : ?>
					<label class="hm-chip"><input type="radio" name="timeline" value="<?php echo esc_attr( $hm_value ); ?>" required><span><?php echo esc_html( $hm_label ); ?></span></label>
				<?php endforeach; ?>
			</div>
		</fieldset>
	</div>

	<div class="hm-form__step" data-step="3">
		<p class="hm-form__q"><?php echo esc_html( $hm_copy['contact_q'] ); ?></p>
		<div class="hm-fields">
			<?php foreach ( $hm_fields as $hm_name => $hm_label ) : ?>
				<?php $hm_id = $hm_uid . '-' . $hm_name; ?>
				<?php if ( 'message' === $hm_name ) : ?>
					<div class="hm-field is-full"><label for="<?php echo esc_attr( $hm_id ); ?>"><?php echo esc_html( $hm_t( $hm_label ) ); ?></label><textarea id="<?php echo esc_attr( $hm_id ); ?>" name="message" placeholder="<?php echo esc_attr( $hm_copy['message_hint'] ); ?>"></textarea></div>
				<?php else : ?>
					<div class="hm-field"><label for="<?php echo esc_attr( $hm_id ); ?>"><?php echo esc_html( $hm_t( $hm_label ) ); ?></label><input id="<?php echo esc_attr( $hm_id ); ?>" name="<?php echo esc_attr( $hm_name ); ?>" <?php echo $hm_inputs[ $hm_name ][1]; // phpcs:ignore -- fixed attributes from $hm_inputs above. ?>></div>
				<?php endif; ?>
			<?php endforeach; ?>
		</div>
	</div>

	<div class="hm-form__nav">
		<div class="hm-form__progress" aria-hidden="true"><i></i><i></i><i></i> <span class="hm-form__count">1 / 3</span></div>
		<div class="hm-form__buttons">
			<button type="button" class="hm-form__back" hidden><?php echo esc_html( $hm_t( 'Back' ) ); ?></button>
			<button type="button" class="hm-btn" data-next><?php echo esc_html( $hm_t( 'Continue' ) ); ?> <?php echo function_exists( 'asfbase_icon' ) ? asfbase_icon( 'arrow' ) : '→'; // phpcs:ignore ?></button>
			<button type="submit" class="hm-btn hm-btn--orange" hidden><?php echo esc_html( $hm_copy['submit'] ); ?> <?php echo function_exists( 'asfbase_icon' ) ? asfbase_icon( 'arrow' ) : '→'; // phpcs:ignore ?></button>
		</div>
	</div>
	<p class="hm-form__msg" role="status" aria-live="polite"></p>
	<p class="hm-form__fine"><?php echo esc_html( $hm_copy['fine'] ); ?></p>
</form>
