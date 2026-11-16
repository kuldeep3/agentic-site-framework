# __NAME__ website: instructions for Claude Code

This project is built with the **Agentic Site Framework** (`docs/framework/`). Read `docs/framework/README.md` and `docs/framework/PRINCIPLES.md` before doing anything else.

## How work runs here
- Work goes stage by stage: Truth → Story → System → Ship → Run (`docs/framework/stages/`). **Stop at each gate** and ask the lead to sign it off. Don't start a stage whose inputs don't exist yet (no copy before `docs/truth.md`; no build before `docs/01-strategy.md` is approved).
- Specialist subagents are in `.claude/agents/`: `site-researcher` (stage 1), `site-strategist` (stage 2), `site-copywriter` (stage 3, one per page family, in parallel), `site-qa` (stage 4). Brief them with the matching prompt from `docs/framework/prompts/`.
- Templates for every document are in `docs/framework/templates/`.

## Rules that are never broken
1. **White-label:** never name the delivery partner, offshore team, internal tools or rates anywhere public: copy, metadata, schema, llms.txt, file names, commit messages in client repos.
2. **Truth first:** every number, client name and quote comes from `docs/truth.md` with status "public". Anything else is wrapped as `<mark class="hm-confirm">[CONFIRM: …]</mark>`. Private client data needs the owner's written OK.
3. **Real images only:** open an image and check who it shows before using it. Never use stock. No photo → typographic stat cover.
4. **One idea, one home; ≤ 8 sections per page.** One contrast line per page. One primary CTA, worded the same everywhere (the footer's `footer_cta` button). The footer closes every page.
5. **Its own design, never the reference's:** the site starts unbranded (`assets/css/brand.css` says `ASF:UNBRANDED`). Stage 3 writes the client's brand layer from a design brief: geography, buyer, category, price position, the colours in their work. No "AI look": see `docs/framework/patterns/design-system.md` §4.
6. **Content is code:** pages are `content/**/*.html` block markup; client facts are in the plugin's `inc/entity.php`; navigation is in the theme's `inc/navigation.php`. Nothing client-specific is hard-coded in templates.
7. Commit or push only when asked.

## Commands
```bash
bin/setup.sh
```
```bash
bin/setup.sh --reseed
```
```bash
python3 docs/framework/qa/lint_content.py content
```
```bash
python3 docs/framework/qa/crawl.py http://__SLUG__.test
```
Responsive check: run `docs/framework/qa/responsive.js` in the browser at 375, 768, 1440 and 1920.
