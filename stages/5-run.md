# Stage 5: Run

**Question:** is the site doing its job, and what do we change next?
**Cadence:** weekly report, monthly proposal, quarterly review. **Lead:** the account owner. **AI:** the orchestrator drafts; a human sends.

> "The report is the service." A site with no report is a one-off project. A site with a weekly report is a retainer.

---

## Before the first report (once, at launch)
- Analytics on the live site: `define( 'ASF_GA4_ID', 'G-…' )` (or `ASF_GTM_ID`) in wp-config, plus a consent banner that calls `window.asfConsent.grant()` where consent is required (UK/EU). Then `bin/asf set measurement.analytics "GA4 G-…"`.
- An Application Password for the report (WordPress admin: Users → Profile → Application Passwords), stored as `ASF_WP_USER` / `ASF_WP_APP_PASSWORD` wherever the report runs.
- Five prompts buyers would ask an AI assistant: `bin/asf set measurement.prompts '["…", "…"]'`.
- The goal baseline from `docs/00-goal.md`: `bin/asf set measurement.baseline '{"leads_per_week": 3, "target": 6}'`.
- Optional: the weekly schedule (`docs/framework/orchestrator/weekly-report.yml`, or a scheduled `/asf report` routine). See [`orchestrator/README.md`](../orchestrator/README.md) § Measurement.

## Weekly (≈ 15 minutes with AI)
Run **`/asf report`** in Claude Code. Prompt: [`prompts/09-weekly-report.md`](../prompts/09-weekly-report.md). Template: [`templates/weekly-report.md`](../templates/weekly-report.md).

1. `bin/asf report` pulls the numbers: enquiries and sign-ups from the site itself (by need, page and source), plus GA4 and Search Console when connected, compared with the previous week. It also rescans the live site (`qa/launch.py`: security, performance, accessibility, launch settings, pending updates, failed emails; Lighthouse and Core Web Vitals with `PSI_API_KEY`) and lists any error that's new since last week. A plugin update, a host change or an expiring certificate can undo launch work; this is where it shows.
2. The agent adds what the script can't reach (connectors for analytics, Search Console, AI visibility) and checks the tracked prompts: is the client cited in ChatGPT, Perplexity and Google AI Overviews?
3. It writes **three things**: what happened, why we think so, and what we'll do this week, using only sourced numbers.
4. A person reviews and sends it. Every week, even when nothing changed. A quiet week gets a short report.

## Campaigns (when the client runs one)
A campaign gets one landing page, one offer, tagged links and a result: [`patterns/campaigns.md`](../patterns/campaigns.md), prompt [`10-campaign.md`](../prompts/10-campaign.md).

1. `bin/asf campaign new <slug> --name … --landing /… --start … --end … --goal … --channels google/cpc,…` writes the brief and the page skeleton.
2. Fill the brief with the client (the promise, the offer, the proof), write the page with prompt 10, publish it before the start date.
3. `bin/asf campaign check <slug>` (brief, copy, live page, message match, form, tracking, accessibility, performance), then `bin/asf campaign links <slug> --content …` for the only links anyone should use.
4. While it runs: the weekly report's Campaigns table, `bin/asf campaign report <slug>` for detail, spend recorded with `bin/asf set campaigns.<slug>.spend …`.
5. When it ends: `bin/asf campaign close <slug> --outcome keep|redirect|unpublish`, and write "What we learned" in the results file.

## Monthly
- **One improvement proposal**, sized and priced: a new case study, a landing page for a query that's gaining, a page test, a new offer page. This is how the engagement grows.
- Content: one case study or one answer-first article mapped to an ICP query.
- Refresh `[CONFIRM]` items and outdated numbers in `entity.php` and on pages.

## Quarterly
- Review against the goal document: is each revenue lever moving?
- Re-run `crawl.py`, the responsive sweep and `contrast.js` (plugins, themes and content drift).
- Review admin accounts, Application Passwords and plugins nobody uses; test a backup restore.
- Re-check positioning against the truth file: has the business arc changed?

## Gate G5 (every week)
- [ ] Production scan clean (`launch.py --env production --only security,launch`; checked by `bin/asf check G5`)
- [ ] Every live campaign passes `bin/asf campaign check`; finished ones are closed
- [ ] Report sent on the agreed day
- [ ] Every number in it has a source (an analytics view, a lead record or a screenshot)
- [ ] One concrete action for the coming week
