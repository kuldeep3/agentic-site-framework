# Prompt 10: Campaign landing page

**Stage:** 5 Run (campaigns) · **Run by:** the orchestrator, or the copywriter subagent (`site-copywriter`) · **Playbook:** [`patterns/campaigns.md`](../patterns/campaigns.md)

Run it after `bin/asf campaign new <slug> …` has written the brief and the page skeleton, and after the client has filled (or approved) the brief's goal, audience, offer and promise.

## Prompt
```text
Write the landing page for the campaign in docs/campaigns/[SLUG].md, into
content/pages/[LANDING].html (the skeleton is already there: keep its block markup, sections and
front matter; replace the [CONFIRM: …] chips with copy).

Read first: the campaign brief, docs/truth.md (claims register and voice bank),
docs/01-strategy.md (ICP and messaging), the closest service page in content/pages/, and
docs/framework/patterns/campaigns.md §2–3.

Rules:
- The H1 is the brief's promise, word for word. The SEO title starts with it.
- One offer, one action. The button label everywhere is the brief's call to action (also the
  front matter `cta:`).
- Every number, name and quote comes from the truth file's claims register (cite the claim ID in an
  HTML comment next to it). Anything not in it stays a [CONFIRM: …] chip. No new claims.
- Proof sits near the ask: the trust line in the hero and the testimonial before the form.
- "What you get" is concrete: things they'll hold, and when.
- The FAQ answers the brief's likely objections (price, time, commitment) in the buyer's words.
- A deadline or scarcity only if the brief says it's real.
- Keep the six sections. Don't add links that lead away from the page.
- Voice: the client's, from the voice bank. No buzzwords (qa/config.json).

Then, separately, for each channel in the brief: three headline options and two short descriptions
that say the same promise (message match). These are suggestions for the person running the ads;
they don't go on the site.

Finally run:
  python3 docs/framework/qa/lint_content.py content
  bin/asf campaign check [SLUG] --url [LOCAL URL]
and fix what they report (after reseeding: bin/setup.sh --reseed).
```

## Expected output
- The landing page with copy in place, chips only where the truth file can't support a line.
- Ad headline and description options per channel, as a list in the reply.
- `campaign check` clean apart from what only a person can do: approve the copy, publish the page on the live site, issue the links.
