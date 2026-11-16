# Stage 4: Ship

**Question:** is it right, secure, fast, accessible and finished?
**Time:** 2–4 days. **Lead:** a human. **AI:** the QA subagent plus the [`qa/`](../qa/) scripts.

Automated checks find what humans miss (an unclosed block comment, a duplicate quote on two pages). Humans find what scripts miss (a headline that's true but flat). Do both.

---

## Steps

### 4.1 Automated QA
Run from the project root, against the local site:

```bash
python3 docs/framework/qa/lint_content.py content --config docs/framework/qa/config.json
```

```bash
python3 docs/framework/qa/crawl.py http://<slug>.test --config docs/framework/qa/config.json
```

Then run the responsive sweep: open the site in the browser tool, and at **375, 768, 1440 and 1920** widths paste [`qa/responsive.js`](../qa/responsive.js) on every key template (home, a service, an industry, about, a case study, contact). The script reports horizontal overflow and any section content off the grid edge.

| Check | Script | Fails on |
|---|---|---|
| Block markup balanced, JSON attributes valid | `lint_content.py` | Editor shows "This block contains unexpected content" |
| Front matter: title, slug, SEO title ≤ 60, description ≤ 155 | `lint_content.py` | Missing or too long |
| ≤ 8 top-level sections per page | `lint_content.py` | Long pages |
| Duplicate paragraphs/headings across pages, quote reused | `lint_content.py` | "One idea, one home" broken |
| Banned words (buzzwords), banned names (white-label) | both | Any hit |
| `[CONFIRM]` chips remaining | both | Any (they're warnings before launch week, errors at launch) |
| Missing media references | `lint_content.py` | File not in `content/media/` |
| HTTP 200, one H1, title, meta description, canonical, JSON-LD parses | `crawl.py` | Any page |
| Broken internal links and images | `crawl.py` | Any |
| llms.txt and robots.txt present | `crawl.py` | Missing |
| Overflow, grid alignment | `responsive.js` | Any element wider than the viewport; any section child off the edge |
| Security, performance, accessibility, launch settings | `launch.py` | See 4.5 |
| Colour contrast, visible keyboard focus | `contrast.js` | Text under 4.5:1 (3:1 large); a control with no focus style |

### 4.2 Editor validation (WordPress)
Open each page in the block editor and confirm there are no "unexpected content" or "attempt recovery" warnings. With the browser tool, run this snippet on each page's editor screen:
```js
wp.data.select('core/block-editor').getBlocks().flatMap(function f(b){return [b,...b.innerBlocks.flatMap(f)]}).filter(b=>!b.isValid).map(b=>b.name)
```
An empty array means valid.

### 4.3 Forms, end to end
Submit the brief form with test data. Check the lead appears in the dashboard, the email arrives (or is logged locally), the thank-you page loads, and the honeypot, minimum-time and rate-limit checks reject bad submissions.

### 4.4 Human review (QA subagent + Lead)
Prompt: [`prompts/08-qa-review.md`](../prompts/08-qa-review.md). Read every page as the ICP buyer, in order: home → a service → a case study → start. Look for repetition, flat or generic lines, claims without proof, pages that run too long, and dead ends with no next step.

### 4.5 Launch readiness: security, performance, accessibility
One script checks the site from outside, the way an attacker, a search engine and a screen reader meet it: [`qa/launch.py`](../qa/launch.py). Run accessibility on the local site while you build, and everything on staging before sign-off:

```bash
python3 docs/framework/qa/launch.py http://<slug>.test --only accessibility
```

```bash
python3 docs/framework/qa/launch.py https://staging.<domain> --env staging
```

| Group | What it checks | Fixed by default in the base |
|---|---|---|
| **Security** | HTTPS and the http→https redirect, certificate expiry, HSTS, nosniff, framing (clickjacking), Referrer-Policy, Permissions-Policy, CSP, mixed content; exposed files (`.git`, `.env`, wp-config copies, `debug.log`, backups, phpinfo, and this project's own `asf.json`, `CLAUDE.md` and `docs/`); directory listing; WordPress version leaks; login names leaked by `/?author=1`, the users API and the users sitemap; XML-RPC; PHP errors printed on pages | Headers, version hiding, author archives and the users API closed to visitors, XML-RPC off, the file editor off, vague login errors (`inc/hardening.php`) |
| **Performance** | Response time, compression, page weight and requests (budget 1.5 MB / 60), image weight, format and dimensions, lazy-loading (and *not* lazy-loading the first image), render-blocking scripts, cache lifetimes, web-font count and `font-display` | Fonts, scripts and hero image set up right; image weight is content work |
| **Accessibility** | Page language, alt text, link, button and iframe names, form labels, heading order, one `<main>`, skip link, zoom not blocked, positive tabindex, duplicate ids, autoplaying sound | Skip link, landmarks, labelled form and menu |
| **Launch** | Search engines discouraged on staging and allowed in production, robots.txt, sitemap, real 404s, favicon, social image, a privacy policy link, no local or staging URLs left in pages, the enquiry endpoint registered, a lead email address, an SMTP plugin, failed emails | |
| **Lighthouse** (`--only lighthouse`) | Mobile scores for performance, accessibility, best practices and SEO (target 90), and real-user Core Web Vitals once there's traffic. Uses Google PageSpeed Insights, so the URL must be public; `PSI_API_KEY` raises the rate limit | |

**Inside checks.** With an Application Password (`ASF_WP_USER`, `ASF_WP_APP_PASSWORD`), the scan also reads the core plugin's private `/wp-json/<slug>/v1/health`: pending WordPress, plugin and theme updates, errors shown on screen, an `admin` login, too many administrators, open registration, sample content, comments, and the last email that failed to send. It returns counts and yes/no answers only.

**In the browser.** Paste [`qa/contrast.js`](../qa/contrast.js) on each key template, once per colour context (light sections, dark sections, the footer, the header over a dark hero). It measures the real contrast of every visible text element against what's behind it, and checks that every link, button and field shows a focus style. Text over photos is listed for a check by eye. Then do a keyboard-only pass: Tab through the header, the menu and the form, and make sure nothing traps focus.

**Where the server matters.** A local site skips HTTPS, HSTS, compression, caching and response time: those belong to the host, so they're checked on staging. Things only the host can fix (HTTP→HTTPS, compression, cache headers, `readme.html`, directory listing, server version headers) go to the host's support with the scan's wording.

**Turning hardening off.** Some clients need XML-RPC (Jetpack, the WordPress app) or author pages. Each piece has a wp-config switch (`ASF_ALLOW_XMLRPC`, `ASF_AUTHOR_ARCHIVES`, `ASF_SECURITY_HEADERS`, `ASF_HSTS`, `DISALLOW_FILE_EDIT`); a Content-Security-Policy is written per site and tried with `ASF_CSP_REPORT_ONLY` before `ASF_CSP` enforces it. Record each change in `docs/decisions.md`.

**What no script can check**, and the gate asks a person to confirm: backups run daily and a restore has been tested, uptime monitoring alerts someone, and every admin has a personal login, a strong password and two-factor authentication.

### 4.6 Launch checklist
`docs/07-deployment.md`: DNS, SSL, production SMTP, the lead email address, analytics IDs, Search Console, 301 map live, the SEO plugin decision, backups, and removing the noindex. On launch day, run `launch.py` against production with `--env production`: it fails if the site is still noindexed, links to staging, or has no privacy policy link.

## Gate G4: Ship

- [ ] `lint_content.py --strict` and `crawl.py --strict` pass with zero errors (no `[CONFIRM]` in pages, titles, meta descriptions or theme templates)
- [ ] `launch.py` on staging: zero errors in security, performance, accessibility and launch settings
- [ ] Lighthouse ≥ 90 on home and two inner pages (or the DevTools scores recorded with a skip, if staging isn't public)
- [ ] Responsive sweep clean at 375 / 768 / 1440 / 1920
- [ ] `contrast.js` clean in every colour context; keyboard-only pass done
- [ ] Editor validation: zero invalid blocks
- [ ] Form tested end to end on staging, and the email arrives (not in spam)
- [ ] **Zero `[CONFIRM]` chips** on the site (every one confirmed by the client, or the claim removed)
- [ ] White-label scan clean (no partner names anywhere: copy, metadata, schema, llms.txt, file names)
- [ ] Backups daily with a tested restore; uptime monitoring on; every admin on a personal login with 2FA
- [ ] Client sign-off on staging, in writing

`bin/asf check G4` runs every automated line above; `/asf approve G4` asks a person for the rest.
