# Stage 5: Run

**Question:** is the site doing its job, and what do we change next?
**Cadence:** weekly report, monthly proposal, quarterly review. **Lead:** the account owner. **AI:** the orchestrator drafts; a human sends.

> "The report is the service." A site with no report is a one-off project. A site with a weekly report is a retainer.

---

## Weekly (≈ 30 minutes with AI)
Prompt: [`prompts/09-weekly-report.md`](../prompts/09-weekly-report.md). Template: [`templates/weekly-report.md`](../templates/weekly-report.md).

1. Pull the numbers: sessions, leads (brief-form submissions), booked calls, top pages, top queries, conversion rate by page. Pull AI-search presence too: is the client cited for their 5 tracked prompts in ChatGPT, Perplexity and Google AI Overviews?
2. Compare against last week and against the goal document baseline.
3. Write **three things**: what happened, why we think so, and what we'll do this week.
4. Send it. Every week, even when nothing changed. A quiet week gets a short report.

## Monthly
- **One improvement proposal**, sized and priced: a new case study, a landing page for a query that's gaining, a page test, a new offer page. This is how the engagement grows.
- Content: one case study or one answer-first article mapped to an ICP query.
- Refresh `[CONFIRM]` items and outdated numbers in `entity.php` and on pages.

## Quarterly
- Review against the goal document: is each revenue lever moving?
- Re-run `crawl.py` and the responsive sweep (plugins, themes and content drift).
- Re-check positioning against the truth file: has the business arc changed?

## Gate G5 (every week)
- [ ] Report sent on the agreed day
- [ ] Every number in it has a source (an analytics view, a lead record or a screenshot)
- [ ] One concrete action for the coming week
