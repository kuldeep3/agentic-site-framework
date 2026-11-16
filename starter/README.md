# Starter: a new client site in one command

```bash
starter/new-site.sh acme-growth "Acme Growth Co" ~/Projects/acme-website --short "Acme" --mark "AG"
```

Add `--kind product-brand` for a client that makes products and sells through retailers or dealers. It uses its own skeleton (`skeleton/product-brand/`): product lines instead of services, customer builds instead of case studies, "Where to buy" as the main action and a fitment/dealer enquiry form.

It copies the **wireframe base** (`../base/`, or `--reference <path>`) and makes it the new client's:

| Step | Result |
|---|---|
| Rename | Theme `asfbase` → `acmegrowth` (also the PHP prefix and text domain), plugin `asfbase-core` → `acme-growth-core`, REST `asfbase/v1` → `acme-growth/v1`, local URL `acme-growth.test` |
| Client files | `inc/entity.php` (facts) and `inc/navigation.php` from the skeleton for its kind, with `[CONFIRM]` chips |
| Content | Skeleton pages from [`skeleton/content/`](skeleton/content/) (agency) or [`skeleton/product-brand/content/`](skeleton/product-brand/content/), built on the page recipes |
| Design | **None.** The base is a wireframe (greys, system fonts, plain layout) and `assets/css/brand.css` is a placeholder marked `ASF:UNBRANDED`. Stage 3 designs the client from their raw data |
| Images | Plain placeholders: `content/media/replace-hero.png`, the plugin's `og-default.png` and `logo.png` |
| Docs | `docs/` filled from the framework templates, plus the base's authoring and deployment guides |
| Framework | `docs/framework/` (everything except `starter/`, `base/` and `examples/`), `.claude/agents/` for the four subagents, and a project `CLAUDE.md` |
| Leak check | Fails if a base identifier (`asfbase`, `ASF Base`) or a name from `private-leak-patterns.txt` is left anywhere outside `docs/framework/` |

Then:

```bash
cd ~/Projects/acme-website && bin/setup.sh
```

## Keeping your client list private
Create `starter/private-leak-patterns.txt` (it's git-ignored) with one regular expression per line: other clients, your delivery partner, internal tools. The starter refuses to finish if any of them reaches a new site. Add the same names to the project's `docs/framework/qa/config.json` → `forbidden`, so the content and crawl checks catch them later too.

## What it doesn't do (on purpose)
- **No design.** Every client's look is created in stage 3 from their own material (`stages/3-system.md`): palette, type, layout and section rhythm, components, motif. `lint_content.py` warns, and gate G3 fails, until `brand.css` is the client's own.
- **No client content.** Every page is placeholders until stage 1 (truth) and stage 2 (story) are done.

## Maintaining the base
`base/` must stay client-free and design-free. When you improve shared code on a client project (a block, the plugin, the seed), port the change back to `base/` with the base's identifiers, then rerun the starter: the leak check tells you if a client name came along.
