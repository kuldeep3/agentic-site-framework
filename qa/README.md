# QA scripts

Three checks, no dependencies (Python 3.9+ standard library, and a browser for the third). Run them from the project root. In a project made by `starter/new-site.sh` they live at `docs/framework/qa/`.

| Script | Runs on | Catches |
|---|---|---|
| `lint_content.py` | the `content/` files | Broken block markup (what the editor flags as "unexpected content"), front-matter and SEO length limits, > 8 sections, several H1s, missing media, white-label terms, buzzwords, `[CONFIRM]` chips, the contrast used twice, text and quotes repeated across pages |
| `crawl.py` | the running site | Non-200 pages, H1 count, titles, meta descriptions, canonicals, JSON-LD that doesn't parse, broken internal links and images, white-label terms in the HTML/meta/schema/llms.txt, missing robots.txt or llms.txt |
| `responsive.js` | each page, in a browser | Horizontal overflow, elements sticking out of the viewport, section content off the shared grid edge |

```bash
python3 docs/framework/qa/lint_content.py content
```

```bash
python3 docs/framework/qa/crawl.py http://acme.test
```

Both exit with code 1 when there are errors, so they can gate CI. Add `--strict` in launch week to turn `[CONFIRM]` chips into errors. `lint_content.py content --list-confirm` prints every chip for the content checklist.

**responsive.js:** in Claude Code, open the page in the browser tool, set the width (375, 768, 1440, 1920), and run the file's contents with the JavaScript tool. Resizing doesn't reload the page, so you can define the check once as a function and call it at each width. `pass: true` at all four widths is the gate.

## Config (`config.json`)
- `forbidden`: names that must never appear (white-label). **Add the client's own sensitive names**: the delivery partner, offshore team, tools, and any client that can't be named.
- `buzzwords`: words the voice rules ban. They show as warnings.
- `contrast_phrase`, `max_sections`, `seo_title_max`, `description_max`, `dupe_min_chars`, `ignore_files` (legal pages are carried over verbatim, so they're skipped by the duplicate check), `crawl_max_pages`.

## Known false positives
- **Laravel Valet serves `/robots.txt` with HTTP 404** (its nginx routes it through the 404 handler; the content is right). `crawl.py` reports a warning; confirm it returns 200 on staging or with `bin/serve.sh`.
- Labels that repeat by design ("Who this is for", "The challenge") are ignored by the duplicate check because they're short. Raise `dupe_min_chars` if more slip through.

## Tested on
A real agency build (33 content files, 49 URLs, 173 links and images): `lint_content.py` 0 errors; `crawl.py` 0 errors; `responsive.js` passes on home at all four widths. Planted faults (bad JSON, unclosed block, className not on its wrapper, tagName mismatch, two H1s, missing media, a white-label name, an off-grid heading, a 1600px element) were all caught.
