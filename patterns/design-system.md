# Design system patterns

How to give each client a design that is unmistakably theirs, and look like a top studio made it. The framework ships **no design**: the base (`base/`) is a wireframe, and stage 3 builds every client's look from their own raw data. These are the rules for doing that well.

## 1. Design from raw data, never from a template
Every client's palette, type, layout and signature components come from **their** material, gathered in stage 1:

| Look in | For |
|---|---|
| The logo, packaging, products, uniforms, premises | Colours and textures that already belong to them |
| Their photos and culture (`content/media/`, truth file §5–6) | The mood, and the one motif |
| Where they sell (geography) | Colour meanings, heritage cues, climate, legal needs (GDPR and fonts in the UK/EU) |
| Who buys and what they judge on | Density, tone, how technical the page should feel |
| The competitor teardown (`docs/references.md`) | What to avoid: read their CSS for real colours, don't guess |
| Price position | What "trustworthy" looks like for this buyer |

Two examples from real projects:

- **A US marketing agency.** Its own culture photography (leather and felt textures) gave a warm palette of near-black, copper, brass and a deep red-brown, with soft shapes.
- **A UK car care brand for enthusiasts.** British racing green came from motorsport heritage, and an aqua "bead" from water beading off paint. It got wide livery capitals, technical corners and a twin stripe as its motif.

Same framework, unrelated designs. A third client must look like neither.

## 2. Where to look for craft
Study these for *moves*, not layouts to clone:

| Site | Take from it |
|---|---|
| Stripe | Product visuals that explain |
| Linear / Vercel | Restraint, precise spacing |
| Superside | Agency-meets-product clarity; proof everywhere |
| Omniscient | Message structure (see `messaging.md`) |
| Apple | One idea per tile |
| Pentagram / Collins / Instrument | Typographic confidence, real work at large sizes |

## 3. Palette by role
Define roles, then fill them from the brief:

1. **Text** and **dark surface** (often near-black, tinted toward the brand).
2. **Accent on light**: must reach **4.5:1 on white**, both as text and as a button with white text.
3. **Accent on dark**: the spark on dark surfaces (≥ 4.5:1 with the dark).
4. **One rich moment**: used once per page (a closing band, case covers).
5. **Soft ground** and white. Keep soft grounds neutral-tinted, never cream (cream + serif is an AI-look tell).
6. Optional **data colour** for charts only, never page chrome.

Flat colour only. Check every pair with a contrast calculator and write the ratios in `docs/04-design-system.md`.

## 4. Type
- **Display:** a face with character that fits the brief: a width axis for livery or editorial looks, a serif only if it's genuinely theirs. **UI/body:** a clean, legible face.
- Self-host woff2 (Latin subset), `font-display: swap`. Two files is the target. Free, licensed faces only (SIL OFL or similar).
- Accent words in headlines are `<em>`, styled by the design, never italic by default.

## 5. Anti-"AI look" checklist (the G3 design review)
Fail the review if any of these appear without a deliberate reason:

- [ ] Cream / beige / parchment backgrounds with serif-italic accent words
- [ ] Monospace "eyebrow" labels everywhere, or "// SECTION 01"-style labels
- [ ] Fake terminal panels, "readout" cards, code-like stat displays on a non-technical brand
- [ ] Grain / noise overlays, glowing orbs, purple-blue gradients on dark
- [ ] Near-black with one bright accent and nothing else
- [ ] The same rhythm repeated on every section: eyebrow → H2 → paragraph → 3 cards
- [ ] Emoji or generic icon sets as the main visuals
- [ ] Stock photos, AI-generated people, or mockups of a different client
- [ ] Centred headings sitting above left-aligned content
- [ ] More than one CTA style competing on a screen
- [ ] Headline case: Title Case Everywhere (sentence case, or deliberate capitals)
- [ ] **A re-skin:** the same layout, section rhythm and components as the wireframe or another client, with new colours

Pass signals: real client work at large sizes, real faces, one accent used with restraint, generous whitespace, section rhythms chosen for this content (split, full-bleed image, list rows, quote, spec band), and one motif nobody else has.

## 6. The calm-hero rule
One message (≤ 2 lines at desktop), one supporting line, **one** primary CTA + one text link, social proof in one line, **one** real image. No collages, floating badges, stat cards or carousels in the hero.
> On one project, a photo + dashboard + phone + badge composition was called cluttered. A single strong image won.

## 7. The layout frame
```css
.hm-section > * { max-width: var(--max); margin-left: max(0px, (100% - var(--max)) / 2) !important; margin-right: auto !important; }
```
- Every section child aligns to the same left edge, at every width (this rule is in the wireframe; keep it).
- Labels that sit directly in a section must be block-level: inline boxes ignore auto margins and drift off the grid.
- If the design uses panels, header, footer and panels share one frame width.
- Verify at 375 / 768 / 1440 / 1920 with `qa/responsive.js`.

## 8. Imagery
- Open every image before using it, and map it to the client it really shows. Filenames lie.
- Show a client's work only on that client's pages and cards.
- No photo for a case? Use a **typographic stat cover** (big number + label). It looks deliberate; a borrowed image is a lie.
- Ask for a real photo session (team, product, place) early. It's the single highest-impact visual upgrade.

## 9. Motion and accessibility
- Below-the-fold reveals only. Content on screen at load is never hidden. Respect `prefers-reduced-motion`.
- Visible focus rings. Decorative visuals are `aria-hidden`; their facts also appear as text.
- Keep the wireframe's `[hidden]{display:none!important}`: components that set `display` would otherwise override `hidden` (a real mobile-menu bug).

## 10. The design layer
- `base/` gives every site `assets/css/main.css`, a **wireframe**: layout and function only (`ASF:WIREFRAME`). Rules marked `FUNCTION` there (menu and form states, the honeypot, the content edge) must survive any design.
- The client's design lives in `assets/css/brand.css`, loaded after it, plus `theme.json` (palette for the editor, self-hosted fonts). It may restyle every component, change grids and rhythm, add components, or replace `main.css` entirely.
- Components read **roles**: `--accent`, `--fill` / `--on-fill`, `--accent-soft`, `--muted`, `--line`. Dark sections redefine them, so a design that sets the roles works on light and dark.
- While directions are compared, each lives in `assets/css/directions/<a|b|c>.css` and is previewed with `/?asf_direction=<x>` (never on production); only the chosen one becomes `brand.css` (`stages/3-system.md` §3.2a).
- A new site's `brand.css` starts as a placeholder marked `ASF:UNBRANDED`. `lint_content.py` warns while it's there and gate G3 fails.
