# Stage 4: Ship

**Question:** is it right, fast, accessible and finished?
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

### 4.5 Performance and accessibility
Lighthouse (mobile) on home, one service page and one case study: target ≥ 90 for performance, accessibility, best practices and SEO. Keyboard-only pass through the header, the mega menu and the form. Check colour contrast on every accent-on-white text.

### 4.6 Launch checklist
`docs/07-deployment.md`: DNS, SSL, production SMTP, the lead email address, analytics IDs, Search Console, 301 map live, the SEO plugin decision, backups, and removing the noindex.

## Gate G4: Ship

- [ ] `lint_content.py` and `crawl.py` pass with zero errors
- [ ] Responsive sweep clean at 375 / 768 / 1440 / 1920
- [ ] Editor validation: zero invalid blocks
- [ ] Form tested end to end on staging
- [ ] **Zero `[CONFIRM]` chips** on the site (every one confirmed by the client, or the claim removed)
- [ ] Lighthouse ≥ 90 on the three templates
- [ ] White-label scan clean (no partner names anywhere: copy, metadata, schema, llms.txt, file names)
- [ ] Client sign-off on staging, in writing
