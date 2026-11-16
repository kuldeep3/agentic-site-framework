# Stage 2: Story

**Question:** what do we say, to whom, in what order, and on which page?
**Time:** 2–4 days, including one client review round. **Lead:** a human strategist. **AI:** the Strategist subagent.

---

## Inputs
Everything from Stage 1 (goal, truth file, audit, references). Don't start without G1.

## Steps

### 2.1 Positioning
Prompt: [`prompts/04-positioning-messaging.md`](../prompts/04-positioning-messaging.md). From the business arc, write:

- **Who it's for (ICP):** 2–4 segments ranked by revenue potential, each with its pain, proof and entry offer → expansion (the strategy template §4 shows the format).
- **What defines them:** one sentence that would be **false for most competitors**. Test it: if a rival agency could put it on their site unchanged, it's not positioning.
- **Revenue model:** leads × close rate × first-year value, with a target for each lever and the site feature that moves it.

### 2.2 Messaging routes
Ask for **three routes**, each built on the formula in [`patterns/messaging.md`](../patterns/messaging.md):

1. Stakes hero (second person)
2. Who-we-are line
3. Proof
4. The one contrast ("Most agencies… We…")
5. Closing echo
6. Price anchor

Each route must cite which truth-file lines it comes from. Present all three to the client and **ask them which one defines their business**, not which one they like best.
> On the first project the client rejected the first three routes ("these don't define the business"). The fourth was rebuilt from the arc in their internal notes, and it landed. Budget for this round.

### 2.3 Information architecture
Prompt: [`prompts/05-ia-page-recipes.md`](../prompts/05-ia-page-recipes.md). Fill [`templates/ia.md`](../templates/ia.md):

- **Sitemap:** pages mapped to ICP segments and services, plus legal pages and conversion pages (start, audit, thank-you).
- **One idea, one home:** a table listing every recurring idea (process, team, pricing, FAQ topics) and the *single* page that owns it. Every other page links to it.
- **Navigation:** header, mega menu, footer.
- **URL map:** old URL → new URL (301), from the Stage 1 inventory.
- **Primary query** for each page (SEO/AEO).

### 2.4 Page briefs
One brief per page ([`templates/page-brief.md`](../templates/page-brief.md)), using a recipe from [`patterns/page-recipes.md`](../patterns/page-recipes.md). A brief lists the page's job, reader, primary query, sections (≤ 8) with the one idea each carries, the proof it uses (with claim IDs from the truth file), its CTA and its price anchor.

### 2.5 Strategy document
Assemble `docs/01-strategy.md` from [`templates/strategy.md`](../templates/strategy.md): brief, audit summary, positioning, messaging, ICP, revenue model, offer ladder, voice, proof inventory.

## Outputs
- `docs/01-strategy.md`
- `docs/02-information-architecture.md`
- `docs/briefs/*.md` (one per page)

## Gate G2: Story

- [ ] The client chose a messaging route **and said it defines their business** (write down their words)
- [ ] The "defines them" sentence fails the competitor test (a rival couldn't use it unchanged)
- [ ] Every claim in the messaging has a truth-file ID
- [ ] Every recurring idea has exactly one home page
- [ ] Every brief has ≤ 8 sections, one primary CTA and a price anchor (or a decision not to publish prices)
- [ ] Old → new URL map is complete

**Common failure:** clever lines about *us* ("We're your growth engine"). They read well internally and fail in three seconds with a buyer. Lead with the reader's stake.
