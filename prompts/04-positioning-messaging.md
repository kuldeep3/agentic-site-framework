# Prompt 04: Positioning and messaging routes

**Stage:** 2 Story · **Run by:** the Strategist subagent (`site-strategist`)

## Prompt
```text
Write positioning and three messaging routes for [CLIENT].

Read, in this order: docs/00-goal.md, docs/truth.md (especially §1, the business arc, and §3,
the voice bank), docs/audit.md, docs/references.md, and
docs/framework/patterns/messaging.md.

Positioning:
1. ICP: 2–4 segments ranked by revenue potential, each with its pain, proof (claim IDs) and
   entry offer → expansion.
2. The defining difference: one sentence that would be FALSE for most competitors. Show the
   competitor test: name two typical rivals and explain why they couldn't say it.
3. Revenue model: leads × close rate × first-year value, with a target and a site feature for each lever.

Three messaging routes. Each one gives the full message stack:
stakes hero (second person, 4–9 words) · who-we-are line (≤ 45 words) · the contrast
("Most agencies… We…") · closing echo · price anchor · tagline.
For each route: cite the truth-file lines it comes from, then score it on the five headline
tests in patterns/messaging.md §2.

Rules:
- No route may be generic. If a line would fit any full-service agency, rewrite it.
- Use the client's own phrases from the voice bank where they're strong.
- Use only claims with status "public". Mark anything else [CONFIRM].
- Banned words: see patterns/messaging.md §6.
Write docs/01-strategy.md from docs/framework/templates/strategy.md, with the three routes in §3,
marked "for client choice".
```

## Expected output
Draft `docs/01-strategy.md` with three routes for the client to choose from.

## Check before accepting
- Ask the client which route **defines their business**. If none does, go back to the business arc, not to more taglines. (The first project needed a fourth round, rebuilt from the client's own notes.)
