# Stage 3: System

**Question:** how does it look, and how does it work?
**Time:** 1–2 weeks. **Lead:** a human, with a designer for review. **AI:** the orchestrator builds; Writer subagents draft pages in parallel.

---

## Inputs
G2 artifacts: strategy, IA, page briefs. Verified media. The starter project (`starter/new-site.sh`).

## Steps

### 3.1 Spin up the project
```bash
starter/new-site.sh <slug> "<Client name>" <target-folder> [--kind agency|product-brand]
```
This gives you the **wireframe base** with the client's names: working WordPress, content model, SEO and AI-search layer, lead form and QA, but **no design** (greys, system fonts, plain layout). It also adds skeleton pages, the framework docs in `docs/framework/` and the agents in `.claude/agents/`. Fill `inc/entity.php` (the plugin's facts file) from the truth file **first**: name, tagline, description, contacts, founders, socials, facts, footer CTA and price anchor. Footer, schema and llms.txt all read from it.

### 3.2 Design from the client's raw data
**Every client gets a design of its own, never a re-skin.** The base has no look on purpose, and no design is copied from another client: not the palette, not the type pairing, not the layout, section rhythm or signature components. The design is built from what Stage 1 collected:

| Raw data (from `truth.md`, `references.md`, the media folder) | What it decides |
|---|---|
| **Geography:** where they sell | Colour meanings, local cues (heritage, climate, culture), legal needs such as self-hosting fonts under GDPR in the UK/EU |
| **Buyer:** who decides and what they judge on | Density and tone: spec-heavy for enthusiasts, calm and reassuring for owners, fast for trade |
| **Category codes:** the teardown of competitors' sites | What everyone else looks like, so the brand can stand apart (verify by reading competitors' CSS, not from memory) |
| **Price position:** premium, mid-market or budget | What "trustworthy" looks like for this buyer |
| **Their own world:** logo, products, packaging, photos, place, founders' language | The palette, textures and the one motif. Look here first |

Write the brief in `docs/04-design-system.md` §1, then compare **three directions** side by side against it, recommend one, and let the client choose. Each direction covers palette, type, **layout and section rhythm**, component shapes, one motif, imagery and motion. It's not just colour.
> On a UK car care brand, the brief (enthusiasts, mid-market, UK) gave British racing green with an aqua "bead" for water beading. The competitor teardown then showed one rival already used a close teal, so the accent was checked again. Test the direction against the teardown, not against assumptions.

Prompt: [`prompts/07-design-direction.md`](../prompts/07-design-direction.md).

### 3.3 Build the design layer
Write the chosen design into the **design layer**: `assets/css/brand.css` (loaded after the wireframe `main.css`) and `theme.json` (palette for the editor, self-hosted fonts). It may restyle every component, change grids and section rhythm, add components, or replace `main.css` entirely; keep only the rules marked `FUNCTION` there (menu and form states, the honeypot, the single content edge). Re-render the share image and logo mark in the new design.

The `hm-*` class names are **content hooks, not a look** (purpose of each: `docs/05-content-authoring.md`). Add a component only when a brief needs one, and document it.

Then run the **anti-"AI look" review** ([`patterns/design-system.md`](../patterns/design-system.md) §4) on one designed page (home hero + two sections) before building every page.
> On the first project, the first direction (cream, serif italics, mono labels) was rejected twice as "looks like Claude design."

Layout frame rules (non-negotiable, whatever the design):

- Every section child aligns to the same content edge
- Header, footer and any panels share one frame width
- No section is wider or narrower than the frame unless it's a deliberate full-bleed image

### 3.4 Write the pages (Writers, in parallel)
Prompt: [`prompts/06-page-copy.md`](../prompts/06-page-copy.md). Split the pages by family (home; services; industries; about/approach; conversion pages; case studies) and give each family to one Writer subagent (or a fork) with:

- its page briefs
- the strategy doc (messaging + voice)
- the truth file (claims + voice bank)
- the component vocabulary and its markup appendix (`docs/05-content-authoring.md`)
- the rule: *unverified number → `<mark class="hm-confirm">[CONFIRM: …]</mark>`*

First make the pages match the IA: rename skeleton pages to the planned URLs (`services-example-service.html` → the real service; update `inc/navigation.php` and any links), delete the ones the IA doesn't plan, and reseed (`bin/setup.sh --reseed`). G3 checks both directions. The archive pages' intro lines live in the theme's templates (`templates/archive-case_study.html`, `home.html`, `index.html`, `archive.html`); write them there or in Appearance → Editor. Lint flags any `[CONFIRM]` left in templates.

Writers produce `content/pages/*.html` directly as block markup. The orchestrator then reads every page in order, as one buyer would, and removes repetition across families (Writers can't see each other's pages).

### 3.5 AI-search layer
Follow [`patterns/aeo.md`](../patterns/aeo.md). It's mostly already built into the starter: entity facts → Organization schema + llms.txt; `hm-faq` → FAQPage schema; `hm-answer` → the answer-first summary on every service and industry page; robots.txt allows AI crawlers.

### 3.6 Lead capture and analytics
The brief form posts to the plugin's REST endpoint, stores a private lead and emails it. Wire analytics events for every CTA (`data-cta`), form step and booking click. List the events in `docs/03-seo-aeo.md` § Measurement. Stage 5 reads them.

### 3.7 Seed and rebuild
`bin/setup.sh --fresh` must rebuild the whole site from files in about two minutes. Run it at least once a day during the build.

## Outputs
- Working local site (`http://<slug>.test` or `localhost:8088`)
- `content/` complete, `inc/entity.php` filled
- `docs/03-seo-aeo.md`, `docs/04-design-system.md`, `docs/05-content-authoring.md`
- `docs/06-content-checklist.md` (every `[CONFIRM]`, missing asset and open decision)

## Gate G3: System

- [ ] The design is the client's own: `brand.css` no longer says `ASF:UNBRANDED`; the brief in `docs/04-design-system.md` cites the raw data it came from; three directions were compared and the client chose one
- [ ] **Not a re-skin:** palette, type pairing, layout and section rhythm, and signature components differ from the wireframe and from every other client built with this framework
- [ ] Designer review passes the anti-"AI look" checklist ([`patterns/design-system.md`](../patterns/design-system.md) §4)
- [ ] The home hero has one message, one image, one primary CTA (calm-hero rule)
- [ ] Every page the IA plans exists, and no skeleton page is left that it doesn't (`bin/asf check G3`)
- [ ] `python3 docs/framework/qa/lint_content.py content` passes with no errors (warnings listed in the checklist)
- [ ] `bin/setup.sh --fresh` rebuilds the site with no errors
- [ ] The client has seen and approved the home page and one service page in the browser
- [ ] Nothing client-specific is hard-coded in the theme (all of it comes from `entity.php`, `navigation.php` or `content/`)
