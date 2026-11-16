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
