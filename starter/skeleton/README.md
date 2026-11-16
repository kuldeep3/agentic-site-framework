# __NAME__: website

A WordPress build made with the **Agentic Site Framework** (`docs/framework/`): a block theme (`wp-content/themes/__THEME__`), a functionality plugin (`wp-content/plugins/__PLUGIN__`) and content stored as files in `content/`, seeded with one command.

> **White-label rule.** The engineering partner is never named anywhere: not in copy, metadata, schema, llms.txt, commits to client repos or file names.

## Quick start (about 2 minutes)
Requirements: **PHP 8.1+** (with `pdo_sqlite`), **WP-CLI 2.9+**, `curl` and `unzip`. No database server is needed: the local site runs on SQLite.

```bash
bin/setup.sh
```

```bash
bin/serve.sh
```

- Site: **http://localhost:8088** · Admin: `/wp-admin` (the local login is printed by `setup.sh`; local only).
- **Laravel Valet** (optional): `ln -sfn "$PWD/wordpress" ~/.config/valet/Sites/__SLUG__` gives you **http://__SLUG__.test**.
- After editing `content/`: `bin/setup.sh --reseed`. To start from zero: `bin/setup.sh --fresh`.

## Where things are
| What | Where |
|---|---|
| Client facts (name, contacts, tagline, footer CTA, price anchor, form choices) | `wp-content/plugins/__PLUGIN__/inc/entity.php` |
| Navigation (header, mega menu, footer) | `wp-content/themes/__THEME__/inc/navigation.php` |
| Old → new URL redirects | `wp-content/plugins/__PLUGIN__/inc/redirects.php` |
| Pages, case studies, posts | `content/pages/`, `content/work/`, `content/posts/posts.json` |
| Verified images | `content/media/` |
| The client's design | `assets/css/brand.css` + `theme.json` (`main.css` is the shared wireframe) |
| Strategy, IA, SEO, design, authoring, checklist, deployment | `docs/` |
| The framework (stages, prompts, QA) | `docs/framework/` |

## Status
Fresh from the starter. Every placeholder is a `[CONFIRM]` chip: `python3 docs/framework/qa/lint_content.py content --list-confirm` lists them. Begin with stage 1: `docs/framework/stages/1-truth.md`.

**To replace before launch:** `content/media/replace-hero.png`, and `assets/og-default.png` and `assets/logo.png` in the plugin (plain placeholders), plus the design: the site runs on the wireframe base until stage 3 writes the client's own design layer (`assets/css/brand.css` + `theme.json`).
