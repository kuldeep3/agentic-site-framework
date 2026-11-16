# Messaging patterns

The structure the best agency sites share (studied on Omniscient, Superside and others), adapted for small and mid-sized business buyers. Use the structure; never copy their words.

## 1. The message stack (every site has these six, in this order)

| # | Element | Formula | Example (a fictional agency for trades businesses) |
|---|---|---|---|
| 1 | **Stakes hero** | The reader's cost or goal, in second person. 4–9 words. | "Your next job is searching right now. *Are you there?*" |
| 2 | **Who-we-are line** | `[Name] is a [category] that [the defining difference]: [what you do, plainly]. [One proof].` ≤ 45 words. | "Fieldnote is a marketing agency for trades businesses that books the job, not just the lead: ads, website and a call team that answers in five minutes. Forty roofing firms run on it." |
| 3 | **Proof** | Results, then the client's customers' words. Before any list of services. | Results band, then three testimonials |
| 4 | **The contrast** | "Most agencies [do the common thing]. We [do the defining thing]." Once per page, never twice. | "Most agencies send you leads. *We send you booked jobs.*" |
| 5 | **Closing echo** | The hero's idea, restated as an invitation. Lives in the footer CTA on every page. | "Be there *first.*" |
| 6 | **Price anchor** | The lowest real starting price + how everything else is scoped. | "Plans start at $1,500 a month. Everything else is scoped on a call." |

**Where the "defining difference" comes from:** the business arc in the truth file (how clients arrive, what they buy next, why they stay). If the sentence would be true for most competitors, it's not the defining difference.

## 2. Headline tests
Run every H1 and H2 through these before it ships:

1. **The 3-second test:** a busy owner gets it without reading the paragraph under it.
2. **The "you" test:** heroes and service headlines speak to the reader's stake. Section headings can be about us only after the stake is clear.
3. **The competitor test:** a rival couldn't put it on their site unchanged.
4. **The proof test:** if it makes a claim, a number or a quote within one scroll backs it up.
5. **The plain test:** no metaphor needs explaining.

| Rejected | Why | Shipped instead (real lessons, fictional wording) |
|---|---|---|
| "Your growth engine." | About the agency, and a metaphor | "Your next job is searching right now." |
| "One team. No hand-offs." | True of any full-service agency | The contrast line above |
| "Growth, engineered." | Means nothing to an owner | — |
| "Ads that convert" (service hero) | Every ad agency says it | "You're paying for clicks you can't trace." |

## 3. Service page lines

- **Hero:** the pain the service removes, as a "You can't… you can't…" or "Your… doesn't…" line. ("You can't scale ads your website can't convert.")
- **Answer paragraph (`hm-answer`):** 40–60 words saying what it is, who it's for and what changes. The first sentence contains the page's primary query.
- **Contrast:** one "Most agencies… We…" per page.
- **Fit lists (`hm-fit`):** 4 × "A good fit if…" and 4 × "Not a fit if…". It qualifies leads and builds trust.
- **Cross-sell:** "Works best with:" plus two links to the next service in the client journey.

## 4. Proof rules
- Real numbers with a named client, or a `[CONFIRM]` chip. Never a rounded "up to 300%".
- Each testimonial on **one page only**. Wrap the proof clause in `<strong>`.
- Private client data (revenue, margins) needs the client's written OK, even if it's the strongest proof you have.
- Stats need a source line (`hm-stat__src`).

## 5. CTAs
- **One primary CTA site-wide**, worded the same everywhere ("Get a strategy call"). Everything else is a text link.
- The footer CTA closes every page, so pages don't add their own closing CTA section.
- Entry offers (audit, sprint, launch) sit on `/start/` with prices. Service pages link there.

## 6. Voice
- Plainspoken and specific: "Shop pages averaged over 6 seconds" beats "lightning-fast experiences."
- Confident, never loud: no exclamation marks.
- Short sentences. "You" and "we".
- Honest about fit: "We'll tell you if we're not the right fit."
- **Banned words** (also in `qa/config.json`): revolutionize, synergy, leverage, cutting-edge, world-class, seamless, unlock, empower, elevate, supercharge, game-changer, best-in-class, next-level, in today's fast-paced, delve, tapestry, holistic, robust.

## 7. Narrative order for a home page
Stakes → who we are → proof (results, logos, voices) → the contrast → method summary → people → FAQ → footer echo + price anchor. See [`page-recipes.md`](page-recipes.md).
