# Campaign: __NAME__

*Campaign tag (utm_campaign): `__SLUG__` · Landing page: `__LANDING__` · __START__ → __END__ · Made with `bin/asf campaign new`. Playbook: `docs/framework/patterns/campaigns.md`.*

## Goal
| Measure | Target |
|---|---|
| Leads from this campaign | __GOAL__ |
| Budget (media + production) | __BUDGET__ |
| Cost per lead we can afford | [from docs/00-goal.md: average first-year value × close rate ÷ 3, or the client's own number] |

## Audience
[Who exactly: the ICP segment, where they'll see this, and what they're doing or worried about at that moment. One short paragraph, in the buyer's words where the voice bank has them.]

## The promise
The ad, the email subject or the post says this, and the landing page's H1 says the same thing (message match). Pick one; keep the others for testing.

> [The promise, in the buyer's words, 10 words or fewer]

## Offer
[What they get, how long it takes, what it costs (or that it's free), and what happens after they ask. Concrete enough to picture.]

## Proof
[One or two facts from docs/truth.md that make the promise believable: a number, a named client (with permission), a quote. Cite the claim IDs. No new claims.]

## Call to action
[The button label (it's also the landing page's header button) and the form: the brief or audit variant, plus any one question to add. One action only.]

## Channels
Tag values are lowercase with hyphens, one spelling per source (`docs/framework/patterns/campaigns.md` §4).

| Source (utm_source) | Medium (utm_medium) | Creatives (utm_content) | Owner |
|---|---|---|---|
__CHANNEL_ROWS__

## Indexing
__INDEX__

## After it ends
[Keep the page (an evergreen offer), redirect it (to which URL), or unpublish it. Decide now, so the page doesn't linger.]

## Success
[What result makes this worth running again, and what we'll change if it's behind pace by the end of week two.]

## Tracking links
<!-- asf:links -->
Run `bin/asf campaign links __SLUG__` to fill this in. Use only these links in ads, emails and posts.
<!-- /asf:links -->
