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

### 3.2a Show the directions and collect feedback
Directions described in a document can't be judged: people have to see them, on the client's own content, and comment where the comment is kept. The team reviews on a **review page** (a Claude artifact); the client gets the same screens as a **PDF on GitHub** and replies on one issue. So before any page is built in the chosen look:

1. **Write each direction as a preview stylesheet:** `assets/css/directions/a.css`, `b.css`, `c.css`. Each restyles the same wireframe (palette, type, section rhythm, the motif) well enough for the home hero and two sections. Self-host any font a direction needs inside its own file.
2. **Preview them on the real site:** `/?asf_direction=a` (and `b`, `c`) swaps the brand layer on any non-production site; the page is noindex and labelled "Design review · direction A". The home page plus one inner page is enough.
3. **Build one review page** (prompt 07 C): for each direction, a full-page screen of each previewed page at desktop (1440) and phone (375), side by side, every screen numbered (A1, A2, B1…) so a comment can name it. Add a "Decision" section with the three home heroes side by side, the brief from `docs/04-design-system.md` §1 and each direction's one-sentence idea. Working files go in `docs/reviews/_work/` (git-ignored).
4. **The team reviews it as a Claude artifact.** Publish the review page from Claude Code (it's private until the lead shares it), record it with `bin/asf set design.review_url https://claude.ai/…`, and the lead shares it with the designer. The designer comments on the artifact; a comment sent to Claude reaches the session, which can make the change, reply and resolve the thread. Do this first: the client should never see a direction the designer would fail.
5. **The client reviews a PDF on GitHub** (prompt 07 E). Print the same page to `docs/reviews/<date>-directions.pdf`, commit and push it, then `bin/asf github review docs/reviews/<date>-directions.pdf --ask "Which direction is yours?"`. That opens one issue (labels `review`, `role:client`) linking the PDF and saying how to reply. The client comments there, or files the "Design feedback" form. A project that isn't on GitHub sends the PDF by email and records `design.client_review` by hand.
6. **Collect the feedback.** `/asf intake` (prompt 07 D) reads the artifact's comment threads and the comments on the review issue, and files each separate point as a `type:design` issue with its link (`--source artifact` or `--source issue`), so design feedback sits on the board with everything else.
7. **Record the choice in the client's words:** `bin/asf set design.direction "B, chosen by <name> on <date>"`, and §4 of `docs/04-design-system.md`. The chosen file becomes `brand.css`; delete the other two.

The review page and the PDF are where people review, not the source of truth: the design lives in `brand.css` and `theme.json`, and every agreed comment becomes a change there. After 3.3–3.4, add the built home page and one inner page to the review page ("Build review") and send the client a second PDF for the G3 sign-off.

Projects that already review in Figma can keep it: `design.figma_url` still satisfies the gate, and `/asf intake` accepts `--source figma`.

### 3.3 Build the design layer
Write the chosen design into the **design layer**: `assets/css/brand.css` (loaded after the wireframe `main.css`) and `theme.json` (palette for the editor, self-hosted fonts). It may restyle every component, change grids and section rhythm, add components, or replace `main.css` entirely; keep only the rules marked `FUNCTION` there (menu and form states, the honeypot, the single content edge). Re-render the share image and logo mark in the new design.

The client's own logo file goes in the theme's `assets/brand/`, wired through `entity.php` → `logo` (`img` for the header, `img_dark` for the dark footer, `width` and `height`); without it the header shows the mark and word. Mega-menu items in `inc/navigation.php` can carry `'tile' => 'x'`, a plain square the design colours through `.is-x`, instead of an icon.

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
- [ ] The directions were shared for review (`design.review_url`: the team's review page; the client's PDF and review issue), the choice is recorded (`design.direction`), and every review comment is resolved or filed as a `type:design` issue
- [ ] **Not a re-skin:** palette, type pairing, layout and section rhythm, and signature components differ from the wireframe and from every other client built with this framework
- [ ] Designer review passes the anti-"AI look" checklist ([`patterns/design-system.md`](../patterns/design-system.md) §4)
- [ ] The home hero has one message, one image, one primary CTA (calm-hero rule)
- [ ] Every page the IA plans exists, and no skeleton page is left that it doesn't (`bin/asf check G3`)
- [ ] `python3 docs/framework/qa/lint_content.py content` passes with no errors (warnings listed in the checklist)
- [ ] `bin/setup.sh --fresh` rebuilds the site with no errors
- [ ] The client has seen and approved the home page and one service page in the browser
- [ ] Nothing client-specific is hard-coded in the theme (all of it comes from `entity.php`, `navigation.php` or `content/`)
