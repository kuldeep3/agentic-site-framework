# 05 — Content authoring (pages, case studies, sections)

*Last updated 2026-10-29*

All content is **standard Gutenberg block markup**: the exact format WordPress stores. In the editor every section is a normal Group block with a class name, so editors can duplicate, reorder and edit sections without a developer. The files in `content/` are the seed for local builds; `bin/setup.sh --reseed` re-imports them.

---

## 1. File format

```html
<!--
title: Example Service                     ← page title (also the H1 unless the content sets one)
slug: services/example-service             ← full path; the parent must exist
seo_title: Example Service Optimization | ASF Base   (≤ 60 chars)
description: Meta description, written as an answer. (≤ 155 chars)
order: 5
dark_hero: true                                    ← only if the first section is .hm-dark
template: page-landing                             ← optional: page-prose (text pages) or page-landing (campaign pages: no menu)
cta: Get the audit                                 ← page-landing only: the header button, which jumps to #form
noindex: true                                      ← optional: keep the page out of search (campaign pages default to it)
-->
<!-- wp:group {"tagName":"section","align":"full","className":"hm-section …","layout":{"type":"default"}} -->
<section class="wp-block-group alignfull hm-section …"> … </section>
<!-- /wp:group -->
```

Case studies add: `client`, `year`, `stat`, `stat_label`, `services` (comma-separated term names), `industry`, `image` (a file in `content/media/`) and `excerpt`.

Placeholders: `{{booking}}` (Calendly), `{{phone}}`, `{{phone-e164}}`, `{{email}}`, `{{media:file.jpg}}` (large), `{{media-thumbnail:…}}` / `{{media-medium_large:…}}` / `{{media-full:…}}`, `{{media-id:file.jpg}}`. Media URLs are site-relative, so they work on any host.

---

## 2. Section vocabulary

Every top-level section is a full-width Group: `tagName: section`, `align: full`, `layout: default`, `className: hm-section` plus modifiers. Inside, every child aligns to one content edge at every width. **Class names are content hooks, not a look:** how each one looks is decided by the client's design (stage 3), and the base only gives it a readable wireframe.

| Class | Use |
|---|---|
| `hm-section` | Base section with vertical rhythm. Adds a hairline divider between two plain sections. |
| `hm-dark` / `hm-orange` / `hm-bone` | Section emphasis: `hm-dark` = a dark section, `hm-orange` = the page's one rich/brand moment, `hm-bone` = a soft section. The client design decides the colours and shapes. |
| `is-tight`, `is-flush-top`, `is-narrow` | Modifiers: less padding · no top padding · 980px max (`no-rule` is legacy and harmless) |
| `hm-hero` (+ `hm-dark`) | Home hero only: `hm-hero__grid` → `hm-hero__copy` (label, H1 with `<br>` lines, lead, buttons, `hm-trust`) + `asfbase/hero-visual`. |
| `hm-page-hero` (+ optional `hm-dark`, `is-large`) | Interior page hero: `hm-label` → H1 → `hm-hero__foot` |

### Components (inner Groups / blocks)

| Class | Block | Children |
|---|---|---|
| `hm-label` | Paragraph | Small label above a heading (eyebrow). `hm-label--plain` for a quieter variant. |
| `hm-lead`, `hm-statement`, `hm-muted` | Paragraph | Lead text · big display statement · muted |
| `hm-head` | Group | Section header: `hm-label` + H2 (8 cols) + paragraph or buttons (4 cols, right) |
| `hm-split` | Group | Two Groups: left (sticky title) 5 cols, right content 6 cols |
| `hm-hero__foot` | Group | Two Groups: left (intro/answer + buttons), right (readout / facts) |
| `hm-answer` | Paragraph | **AEO summary.** 40–60 words that answer "what is it, who's it for, what changes". Required on every service and industry page. |
| `hm-facts` | List | "For / Outcome / Starting at" rows: `<li><strong>For</strong>Founder-led DTC brands</li>` |
| `hm-index` › `hm-index__row` | Group › Group | Big linked list rows: `hm-index__num` paragraph, H3 with a link (whole row becomes clickable), paragraph, `hm-tags` list |
| `hm-features` (+ `cols-3`) › `hm-feature` | Group › Group | Auto-numbered features: H3 + paragraph (+ optional `is-style-checks` list) |
| `hm-pains` › `hm-pain` | Group › Paragraph | "Sound familiar?" lines in quote cards |
| `hm-compare` › Group, Group `is-us` | Group | Two columns; list items `Label <em>Tag</em>`, then `hm-compare__sum` paragraph |
| `hm-stats` › `hm-stat` | Group › Group | `hm-stat__num` (a number; wrap a unit in `<em>`: `20<em>k/hr</em>`), `hm-stat__label`, `hm-stat__src` |
| `hm-steps` › `hm-step` | Group › Group | `hm-step__num` ("01"), H3, paragraph. The full version lives on `/approach/`. Home carries a one-line-per-step summary that links there; no other page repeats it. |
| `hm-quote` (+ `is-compact`) | Quote | Testimonial; `<cite>` = source. `is-compact` sits under a work grid. Use each quote on one page only. |
| `hm-offers` › `hm-offer` (+ `is-featured`) | Group › Group | `hm-label` (tier), H3, `hm-offer__price` (`From $1,000/mo <em>· plus setup</em>`), paragraph, optional `is-style-checks` list, buttons |
| `hm-faq` | Group of Details blocks | Summary = question, inner paragraph = answer. **Auto-generates FAQPage schema.** |
| `hm-grid` (+ `cols-2`, `cols-4`) › `hm-card` | Group › Group | Generic card grid |
| `hm-tags` | List | Small tags |
| `hm-marquee` | Section with a List | A row of client or partner names (only with permission) |
| `hm-bento` › `hm-tile` | Group › Group | Offer tiles: `hm-tile__tag` paragraph, H3 with link (whole tile clicks), paragraph, optional image. Sizes `span-4/5/6/7/8`; `is-dark`, `is-orange`; `is-wide` wraps the text in `hm-tile__text` |
| `hm-gallery` (+ `cols-2`, `cols-4`) | Group of Image blocks | First image large (2×2), others fill. Used in case studies and service showcases |
| `hm-creatives` | Group of Image blocks | A strip of images (ads, social posts, product shots) |
| `hm-culture` › `hm-culture__text`, `hm-culture__photo` | Group | Team/culture split with `hm-faces` |
| `hm-faces` › `hm-face` | Group › Group | Image + paragraph `<strong>Name</strong>Role` |
| `hm-trust` › `hm-trust__faces` | Group | Small avatars + one line of social proof (hero) |
| `hm-testimonials` › `hm-testimonial` (+ `is-featured`) | Group › Group | `hm-testimonial__quote` paragraph (wrap the proof clause in `<strong>`) + `hm-testimonial__who` (`<strong>Name</strong>Role`) |
| `hm-fit` › `is-good`, `is-not` | Group › Groups | "A good fit if" / "Not a fit if": H3 + list, 4 bullets each. Required on every service page. |
| `hm-note` | Paragraph | Small print: price anchors, "Works best with:" cross-links |

### Dynamic blocks
- `<!-- wp:asfbase/hero-visual {"image":"{{media:file.jpg}}"} /-->`: one calm hero image. Add `"photoCase":"<case-slug>","photoChip":"label"` to show a results card (currently off by request).
- `<!-- wp:hm/work-grid {"count":4,"layout":"featured"} /-->`: case study cards. `"service":"example-service"` filters by term slug; `"layout":"grid"` gives two columns.
- `<!-- wp:hm/brief-form /-->`: the 3-step qualifying form (`{"variant":"audit"}` for the audit page).

### Block styles (sidebar → Styles)
Buttons: default (primary), **Outline**, **Text + arrow** (`is-style-link`). Lists: **Checks**. Paragraph/Heading: **Eyebrow**, **Lead**.

---

## 3. Service taxonomy (case studies)

| Term name (use in `services:`) | Slug (use in work-grid `service`) | Service page |
|---|---|---|
| Example service | `example-service` | /services/example-service/ |

---

## 4. Writing rules (summary of `01-strategy.md` §7)

1. **Headlines:** short and declarative, with the key phrase in `<em>` (the accent; the client design decides how it looks). "Proof, *not promises.*"
2. **First 100 words** of a service page contain its primary query (see `03-seo-aeo.md`).
3. **Numbers need a source.** Only use figures from the proof inventory, or mark them `<mark class="hm-confirm">[CONFIRM: …]</mark>`.
4. **No buzzwords:** revolutionize, synergy, leverage, cutting-edge, world-class, seamless, unlock.
5. **White-label:** never mention outsourcing, offshore teams or partner companies. It's "our development team" / "our engineers".
6. **Voice:** follow `01-strategy.md` §3 (stakes headline in second person, proof before pitch, one "Most agencies… We…" contrast per page, one primary CTA "Get a strategy call", price anchor at the close).
7. **Every page ends on the footer CTA** automatically. Don't add another closing CTA section.
8. **One idea, one home.** If a section already exists on another page (process, team, pricing table), link to it instead of repeating it. Aim for ≤ 8 sections per page.
9. **Images:** only show a client's own work for that client (verified list in `04-design-system.md` §5). No stock.

---

## Appendix: markup for each component

Images: write an image block's `src` as `{{media:file.jpg}}` (or a size, `{{media-large:…}}`). The seed links it to the Media Library entry, so WordPress adds width, height, `srcset` and lazy-loading, and re-imports a file when it changes in `content/media/`.

Copy these exactly: the block comments, attribute JSON and wrapper classes must match, or the editor shows "This block contains unexpected content". Placeholders are `[CONFIRM: …]` chips; replace them with copy from the truth file. Extracted from the starter's skeleton pages.

### `hm-hero`: Home hero (dark), with the hero visual and the trust line
```html
<!-- wp:group {"tagName":"section","align":"full","className":"hm-section hm-hero hm-dark","layout":{"type":"default"}} -->
<section class="wp-block-group alignfull hm-section hm-hero hm-dark"><!-- wp:group {"className":"hm-hero__grid","layout":{"type":"default"}} -->
<div class="wp-block-group hm-hero__grid"><!-- wp:group {"className":"hm-hero__copy","layout":{"type":"default"}} -->
<div class="wp-block-group hm-hero__copy"><!-- wp:paragraph {"className":"hm-label"} -->
<p class="hm-label"><mark class="hm-confirm">[CONFIRM: category in 3–6 words]</mark></p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":1} -->
<h1 class="wp-block-heading"><mark class="hm-confirm">[CONFIRM: stakes headline, second person, 4–9 words]</mark></h1>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: who-we-are line, ≤45 words: ASF Base is a [category] that [defining difference]: [what you do]. [One proof].]</mark></p>
<!-- /wp:paragraph -->

<!-- wp:buttons -->
<div class="wp-block-buttons"><!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="/contact/">Get a strategy call</a></div>
<!-- /wp:button -->

<!-- wp:button {"className":"is-style-outline"} -->
<div class="wp-block-button is-style-outline"><a class="wp-block-button__link wp-element-button" href="/work/">See our work</a></div>
<!-- /wp:button --></div>
<!-- /wp:buttons -->

<!-- wp:group {"className":"hm-trust","layout":{"type":"default"}} -->
<div class="wp-block-group hm-trust"><!-- wp:paragraph {"className":"hm-trust__text"} -->
<p class="hm-trust__text"><strong><mark class="hm-confirm">[CONFIRM: one line of social proof]</mark></strong></p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->

<!-- wp:asfbase/hero-visual {"photoCase":"","image":"{{media:replace-hero.png}}"} /--></div>
<!-- /wp:group --></section>
<!-- /wp:group -->
```

### `hm-page-hero`: Page hero
```html
<!-- wp:group {"tagName":"section","align":"full","className":"hm-section hm-page-hero is-large","layout":{"type":"default"}} -->
<section class="wp-block-group alignfull hm-section hm-page-hero is-large"><!-- wp:paragraph {"className":"hm-label"} -->
<p class="hm-label">About</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":1} -->
<h1 class="wp-block-heading"><mark class="hm-confirm">[CONFIRM: the culture line]</mark></h1>
<!-- /wp:heading -->

<!-- wp:paragraph {"className":"hm-lead hm-mt-l"} -->
<p class="hm-lead hm-mt-l"><mark class="hm-confirm">[CONFIRM: one paragraph in the founders’ words]</mark></p>
<!-- /wp:paragraph --></section>
<!-- /wp:group -->
```

### `hm-head`: Section head: label + H2
```html
<!-- wp:group {"className":"hm-head","layout":{"type":"default"}} -->
<div class="wp-block-group hm-head"><!-- wp:paragraph {"className":"hm-label"} -->
<p class="hm-label">The method</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2 class="wp-block-heading">Four steps, <em>in this order.</em></h2>
<!-- /wp:heading --></div>
<!-- /wp:group -->
```

### `hm-trust`: Trust line
```html
<!-- wp:group {"className":"hm-trust","layout":{"type":"default"}} -->
<div class="wp-block-group hm-trust"><!-- wp:paragraph {"className":"hm-trust__text"} -->
<p class="hm-trust__text"><strong><mark class="hm-confirm">[CONFIRM: one line of social proof]</mark></strong></p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->
```

### `hm-answer`: Answer paragraph (40–60 words, for AI search)
```html
<!-- wp:paragraph {"className":"hm-answer"} -->
<p class="hm-answer"><mark class="hm-confirm">[CONFIRM: 40–60 words: what it is, who it’s for, what changes. The primary query goes in sentence one.]</mark></p>
<!-- /wp:paragraph -->
```

### `hm-facts`: Facts row (For / Outcome / Starting at)
```html
<!-- wp:list {"className":"hm-facts"} -->
<ul class="wp-block-list hm-facts"><!-- wp:list-item -->
<li><strong>For</strong><mark class="hm-confirm">[CONFIRM: who]</mark></li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Outcome</strong><mark class="hm-confirm">[CONFIRM: what changes]</mark></li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Starting at</strong><mark class="hm-confirm">[CONFIRM: price signal]</mark></li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->
```

### `hm-features`: Features
```html
<!-- wp:group {"className":"hm-features cols-3","layout":{"type":"default"}} -->
<div class="wp-block-group hm-features cols-3"><!-- wp:group {"className":"hm-feature","layout":{"type":"default"}} -->
<div class="wp-block-group hm-feature"><!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading"><mark class="hm-confirm">[CONFIRM: margin or pricing]</mark></h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: one line]</mark></p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->

<!-- wp:group {"className":"hm-feature","layout":{"type":"default"}} -->
<div class="wp-block-group hm-feature"><!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading"><mark class="hm-confirm">[CONFIRM: support]</mark></h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: training, marketing assets, stock]</mark></p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->

<!-- wp:group {"className":"hm-feature","layout":{"type":"default"}} -->
<div class="wp-block-group hm-feature"><!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading"><mark class="hm-confirm">[CONFIRM: demand]</mark></h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: why drivers ask for it]</mark></p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
```

### `hm-grid`: Card grid
```html
<!-- wp:group {"className":"hm-grid cols-2","layout":{"type":"default"}} -->
<div class="wp-block-group hm-grid cols-2"><!-- wp:group {"className":"hm-card","layout":{"type":"default"}} -->
<div class="wp-block-group hm-card"><!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading"><a href="/services/example-service/">Example service</a></h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>One line on what changes for the client.</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
```

### `hm-fit`: Good fit / not a fit
```html
<!-- wp:group {"className":"hm-fit","layout":{"type":"default"}} -->
<div class="wp-block-group hm-fit"><!-- wp:group {"className":"is-good","layout":{"type":"default"}} -->
<div class="wp-block-group is-good"><!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">A good fit if</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list"><!-- wp:list-item -->
<li><mark class="hm-confirm">[CONFIRM: fit 1]</mark></li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><mark class="hm-confirm">[CONFIRM: fit 2]</mark></li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><mark class="hm-confirm">[CONFIRM: fit 3]</mark></li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><mark class="hm-confirm">[CONFIRM: fit 4]</mark></li>
<!-- /wp:list-item --></ul>
<!-- /wp:list --></div>
<!-- /wp:group -->

<!-- wp:group {"className":"is-not","layout":{"type":"default"}} -->
<div class="wp-block-group is-not"><!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Not a fit if</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list"><!-- wp:list-item -->
<li><mark class="hm-confirm">[CONFIRM: not 1]</mark></li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><mark class="hm-confirm">[CONFIRM: not 2]</mark></li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><mark class="hm-confirm">[CONFIRM: not 3]</mark></li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><mark class="hm-confirm">[CONFIRM: not 4]</mark></li>
<!-- /wp:list-item --></ul>
<!-- /wp:list --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
```

### `hm-offers`: Offers with prices
```html
<!-- wp:group {"className":"hm-offers","layout":{"type":"default"}} -->
<div class="wp-block-group hm-offers"><!-- wp:group {"className":"hm-offer","layout":{"type":"default"}} -->
<div class="wp-block-group hm-offer"><!-- wp:paragraph {"className":"hm-label"} -->
<p class="hm-label">Free</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2 class="wp-block-heading"><mark class="hm-confirm">[CONFIRM: entry offer]</mark></h2>
<!-- /wp:heading -->

<!-- wp:paragraph {"className":"hm-offer__price"} -->
<p class="hm-offer__price">$0 <em>· no commitment</em></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: what they get]</mark></p>
<!-- /wp:paragraph -->

<!-- wp:buttons -->
<div class="wp-block-buttons"><!-- wp:button {"className":"is-style-outline"} -->
<div class="wp-block-button is-style-outline"><a class="wp-block-button__link wp-element-button" href="/contact/">Request it</a></div>
<!-- /wp:button --></div>
<!-- /wp:buttons --></div>
<!-- /wp:group -->

<!-- wp:group {"className":"hm-offer is-featured","layout":{"type":"default"}} -->
<div class="wp-block-group hm-offer is-featured"><!-- wp:paragraph {"className":"hm-label"} -->
<p class="hm-label">Flagship</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2 class="wp-block-heading"><mark class="hm-confirm">[CONFIRM: flagship retainer]</mark></h2>
<!-- /wp:heading -->

<!-- wp:paragraph {"className":"hm-offer__price"} -->
<p class="hm-offer__price"><mark class="hm-confirm">[CONFIRM: price signal]</mark></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: what they get]</mark></p>
<!-- /wp:paragraph -->

<!-- wp:buttons -->
<div class="wp-block-buttons"><!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="/contact/">Get a strategy call</a></div>
<!-- /wp:button --></div>
<!-- /wp:buttons --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
```

### `hm-steps`: Steps
```html
<!-- wp:group {"className":"hm-steps","layout":{"type":"default"}} -->
<div class="wp-block-group hm-steps"><!-- wp:group {"className":"hm-step","layout":{"type":"default"}} -->
<div class="wp-block-group hm-step"><!-- wp:paragraph {"className":"hm-step__num"} -->
<p class="hm-step__num">01</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading"><mark class="hm-confirm">[CONFIRM: step 1 name]</mark></h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: what happens and what you get]</mark></p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->

<!-- wp:group {"className":"hm-step","layout":{"type":"default"}} -->
<div class="wp-block-group hm-step"><!-- wp:paragraph {"className":"hm-step__num"} -->
<p class="hm-step__num">02</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading"><mark class="hm-confirm">[CONFIRM: step 2 name]</mark></h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: what happens and what you get]</mark></p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->

<!-- wp:group {"className":"hm-step","layout":{"type":"default"}} -->
<div class="wp-block-group hm-step"><!-- wp:paragraph {"className":"hm-step__num"} -->
<p class="hm-step__num">03</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading"><mark class="hm-confirm">[CONFIRM: step 3 name]</mark></h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: what happens and what you get]</mark></p>
<!-- /wp:paragraph --></div>
<!-- /wp:group -->

<!-- wp:group {"className":"hm-step","layout":{"type":"default"}} -->
<div class="wp-block-group hm-step"><!-- wp:paragraph {"className":"hm-step__num"} -->
<p class="hm-step__num">04</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading"><mark class="hm-confirm">[CONFIRM: step 4 name]</mark></h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: what happens and what you get]</mark></p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
```

### `hm-testimonials`: Testimonials
```html
<!-- wp:group {"className":"hm-testimonials","layout":{"type":"default"}} -->
<div class="wp-block-group hm-testimonials"><!-- wp:group {"className":"hm-testimonial is-featured","layout":{"type":"default"}} -->
<div class="wp-block-group hm-testimonial is-featured"><!-- wp:paragraph {"className":"hm-testimonial__quote"} -->
<p class="hm-testimonial__quote">“<mark class="hm-confirm">[CONFIRM: a real client quote from the truth file, with the proof clause in bold]</mark>”</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph {"className":"hm-testimonial__who"} -->
<p class="hm-testimonial__who"><strong>Client name</strong>Role, company</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
```

### `hm-faq`: FAQ (feeds FAQPage schema)
```html
<!-- wp:group {"className":"hm-faq","layout":{"type":"default"}} -->
<div class="wp-block-group hm-faq"><!-- wp:details -->
<details class="wp-block-details"><summary>What does ASF Base do?</summary><!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: answer-first: the first sentence stands on its own for AI search]</mark></p>
<!-- /wp:paragraph --></details>
<!-- /wp:details -->

<!-- wp:details -->
<details class="wp-block-details"><summary>Who do you work with?</summary><!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: the ICP, in the buyer's words]</mark></p>
<!-- /wp:paragraph --></details>
<!-- /wp:details --></div>
<!-- /wp:group -->
```

### `hm-split`: Two-column split
```html
<!-- wp:group {"className":"hm-split","layout":{"type":"default"}} -->
<div class="wp-block-group hm-split"><!-- wp:group {"layout":{"type":"default"}} -->
<div class="wp-block-group"><!-- wp:paragraph {"className":"hm-label"} -->
<p class="hm-label">Our story</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2 class="wp-block-heading"><mark class="hm-confirm">[CONFIRM: founding arc headline]</mark></h2>
<!-- /wp:heading --></div>
<!-- /wp:group -->

<!-- wp:group {"layout":{"type":"default"}} -->
<div class="wp-block-group"><!-- wp:paragraph -->
<p><mark class="hm-confirm">[CONFIRM: the business arc from docs/truth.md, in the founders’ words]</mark></p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
```

### `hm-bento` › `hm-tile`: offer tiles
```html
<!-- wp:group {"className":"hm-bento","layout":{"type":"default"}} -->
<div class="wp-block-group hm-bento"><!-- wp:group {"className":"hm-tile span-7 is-dark","layout":{"type":"default"}} -->
<div class="wp-block-group hm-tile span-7 is-dark"><!-- wp:paragraph {"className":"hm-tile__tag"} -->
<p class="hm-tile__tag">[CONFIRM: tag]</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading"><a href="/services/[slug]/">[CONFIRM: service name]</a></h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>[CONFIRM: one line on what changes for the client]</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
```

### `hm-faces` › `hm-face`: people
```html
<!-- wp:group {"className":"hm-faces","layout":{"type":"default"}} -->
<div class="wp-block-group hm-faces"><!-- wp:group {"className":"hm-face","layout":{"type":"default"}} -->
<div class="wp-block-group hm-face"><!-- wp:image {"sizeSlug":"medium"} -->
<figure class="wp-block-image size-medium"><img src="{{media:person.jpg}}" alt="[Name], [role]"/></figure>
<!-- /wp:image -->

<!-- wp:paragraph -->
<p><strong>[Name]</strong>[Role]</p>
<!-- /wp:paragraph --></div>
<!-- /wp:group --></div>
<!-- /wp:group -->
```

### `hm-quote`: one quote
```html
<!-- wp:quote {"className":"hm-quote"} -->
<blockquote class="wp-block-quote hm-quote"><!-- wp:paragraph -->
<p>“[CONFIRM: a real client quote from the truth file]”</p>
<!-- /wp:paragraph --><cite>[Name], [role, company]</cite></blockquote>
<!-- /wp:quote -->
```

### `hm-marquee`: client names (with permission only)
```html
<!-- wp:group {"tagName":"section","align":"full","className":"hm-section hm-marquee","layout":{"type":"default"}} -->
<section class="wp-block-group alignfull hm-section hm-marquee"><!-- wp:list -->
<ul class="wp-block-list"><!-- wp:list-item -->
<li>[Client name]</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list --></section>
<!-- /wp:group -->
```

### `hm/brief-form` and `hm/work-grid` (dynamic blocks)
```html
<!-- wp:hm/brief-form /-->
<!-- wp:hm/brief-form {"variant":"audit"} /-->
<!-- wp:hm/work-grid {"count":4,"layout":"featured"} /-->
<!-- wp:hm/work-grid {"count":-1,"layout":"grid","service":"[service-slug]","titleLevel":2} /-->
```
