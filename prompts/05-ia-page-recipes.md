# Prompt 05: Information architecture and page briefs

**Stage:** 2 Story · **Run by:** the Strategist subagent

## Prompt
```text
Design the information architecture and write a brief for every page of [CLIENT]'s site.

Read: docs/01-strategy.md (approved route), docs/truth.md, docs/audit.md (URL inventory),
docs/framework/patterns/page-recipes.md, docs/framework/patterns/aeo.md.

1. docs/02-information-architecture.md, from docs/framework/templates/ia.md:
   - Sitemap: every page with its recipe, ICP segment, primary query and section count.
   - One idea, one home: list every recurring idea (process, pricing, team, each testimonial,
     each FAQ topic) and the single page that owns it.
   - Navigation: header, mega menu, footer.
   - Redirect map: every old URL from the audit → its new URL.
2. docs/briefs/<page>.md for each page, from docs/framework/templates/page-brief.md.
   Each brief has ≤ 8 sections, each with ONE idea, its component and its proof (claim IDs).
   One "Most agencies… We…" contrast per page. One primary CTA. A price anchor or a link to /start/.

Rules: no section may appear on two pages in full. If two briefs need the same idea, one owns
it and the other links to it. Testimonials are assigned to exactly one page each.
```

## Expected output
`docs/02-information-architecture.md` and `docs/briefs/*.md`.

## Check before accepting
- Count sections per brief (≤ 8).
- Scan the "one idea, one home" table: is anything owned twice?
