# QA scripts

Five checks, no dependencies (Python 3.9+ standard library, and a browser for the two `.js` files). Run them from the project root. In a project made by `starter/new-site.sh` they live at `docs/framework/qa/`.

| Script | Runs on | Catches |
|---|---|---|
| `launch.py` | the running site (local, staging or production) | **Security** (HTTPS, certificate, security headers, exposed files, login-name and version leaks, XML-RPC, PHP errors on pages), **performance** (response time, compression, page weight, images, render-blocking scripts, caching, fonts), **accessibility** (language, alt text, names, labels, headings, landmarks, skip link, zoom), **launch settings** (indexing right for the environment, robots, sitemap, 404s, privacy link, local URLs left behind, forms and email), and optionally **Lighthouse** via PageSpeed Insights |
| `contrast.js` | each page, in a browser | Text below WCAG AA contrast against what's really behind it; links, buttons and fields with no visible focus style |
| `lint_content.py` | the `content/` files | Broken block markup (what the editor flags as "unexpected content"), front-matter and SEO length limits, > 8 sections, several H1s, missing media, white-label terms, buzzwords, `[CONFIRM]` chips, the contrast used twice, text and quotes repeated across pages |
| `crawl.py` | the running site | Non-200 pages, H1 count, titles, meta descriptions, canonicals, JSON-LD that doesn't parse, broken internal links and images, white-label terms in the HTML/meta/schema/llms.txt, missing robots.txt or llms.txt |
| `responsive.js` | each page, in a browser | Horizontal overflow, elements sticking out of the viewport, section content off the shared grid edge |

```bash
python3 docs/framework/qa/lint_content.py content
```

```bash
python3 docs/framework/qa/crawl.py http://acme.test
```

```bash
python3 docs/framework/qa/launch.py https://staging.acme.com --env staging
```

All three exit with code 1 when there are errors, so they can gate CI. Add `--strict` in launch week to turn `[CONFIRM]` chips into errors. `lint_content.py content --list-confirm` prints every chip for the content checklist.

**responsive.js:** in Claude Code, open the page in the browser tool, set the width (375, 768, 1440, 1920), and run the file's contents with the JavaScript tool. Resizing doesn't reload the page, so you can define the check once as a function and call it at each width. `pass: true` at all four widths is the gate.

**launch.py:**
- `--only security,performance,accessibility,launch,lighthouse` picks groups (default: all but Lighthouse). `--env local|staging|production` sets what "right" means (staging should be hidden from search engines, production must not be); it's guessed from the host name otherwise. `--json FILE` (or `-`) writes the results for the weekly report.
- A local site skips what belongs to the host (HTTPS, HSTS, compression, caching, response time).
- With `ASF_WP_USER` and `ASF_WP_APP_PASSWORD` (an Application Password) it also reads the core plugin's private `/wp-json/<slug>/v1/health`: pending updates, error display, admin accounts, sample content and failed emails.
- `--only lighthouse` sends the home page and two inner pages to Google PageSpeed Insights (public URLs only; local and private addresses are refused). `PSI_API_KEY` raises the rate limit.
- It only reads: GET requests to the site's own pages and a fixed list of well-known file paths. Run it on sites you're responsible for.

**contrast.js:** paste it on each key template, once per colour context (light, dark, footer, header over a dark hero). It returns failing colour pairs with an example and a count, text it can't measure (over images or gradients) for a check by eye, and controls with no focus style.

## Config (`config.json`)
- `forbidden`: names that must never appear (white-label). **Add the client's own sensitive names**: the delivery partner, offshore team, tools, and any client that can't be named.
- `buzzwords`: words the voice rules ban. They show as warnings.
- `contrast_phrase`, `max_sections`, `seo_title_max`, `description_max`, `dupe_min_chars`, `ignore_files` (legal pages are carried over verbatim, so they're skipped by the duplicate check), `crawl_max_pages`.
- `launch`: the budgets `launch.py` holds the site to. Pairs are [warning, error]: `page_weight_kb`, `requests`, `image_kb`, `ttfb_ms`, `cert_days` (days left). Also `pages` (sampled for performance), `html_kb`, `cache_min_days`, `max_fonts`, `lighthouse_min`, `lighthouse_paths` (extra paths for Lighthouse) and `privacy_words` (how the privacy policy link is recognised, in the site's languages).

## Known false positives
- **Laravel Valet serves `/robots.txt` with HTTP 404** (its nginx routes it through the 404 handler; the content is right). `crawl.py` reports a warning; confirm it returns 200 on staging or with `bin/serve.sh`.
- Labels that repeat by design ("Who this is for", "The challenge") are ignored by the duplicate check because they're short. Raise `dupe_min_chars` if more slip through.

## Tested on
**launch.py**, on three local WordPress builds (one made by the starter): it found a login name leaked by `/?author=1`, a public `debug.log`, missing security headers, XML-RPC on, the WordPress version in the feed, 600 KB+ images, images without dimensions and skipped heading levels. With the base plugin's hardening, the starter-made site passed every security check a local site can run, apart from its own local `debug.log`. The HTTPS, HSTS, certificate-chain and compression checks, and the PageSpeed Insights call, haven't yet been run against a live staging site.

**contrast.js**, on the starter-made site in Chrome: it found light text on a white panel in the wireframe itself (fixed), then caught a planted 2.8:1 grey and buttons whose focus outline had been removed, and left the page's stylesheets as it found them.

**The others:**
A real agency build (33 content files, 49 URLs, 173 links and images): `lint_content.py` 0 errors; `crawl.py` 0 errors; `responsive.js` passes on home at all four widths. Planted faults (bad JSON, unclosed block, className not on its wrapper, tagName mismatch, two H1s, missing media, a white-label name, an off-grid heading, a 1600px element) were all caught.
