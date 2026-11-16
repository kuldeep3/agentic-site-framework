# Prompt 09: Weekly report

**Stage:** 5 Run · **Run by:** the orchestrator (can be scheduled) · **A human reviews and sends it**

## Prompt
```text
Draft this week's website report for [CLIENT], week of [date], from
docs/framework/templates/weekly-report.md.

Data:
- Analytics: [GA4 property / export path / connector] for this week, last week and the last 4 weeks
- Leads: the site's lead log (Dashboard → Leads, or [export path])
- Bookings: [Calendly export / CRM]
- Search Console: top queries and pages, gains and losses
- AI search: ask each of these 5 prompts in [engines] and record whether [CLIENT] is cited:
  [prompt list from docs/03-seo-aeo.md]
- Goal: docs/00-goal.md (baseline and targets)

Write "The three things" first: what happened (with the number), why we think so (the cause
we can see in the data, or "unclear" if it isn't), and what we'll do this week (one action,
an owner, a day). Then fill in the tables.

Rules: every number links to its source. No vanity framing: if leads fell, say so first.
A quiet week gets a short report, not a padded one.
```
