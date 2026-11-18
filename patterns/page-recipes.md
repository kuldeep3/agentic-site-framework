# Page recipes

Section-by-section blueprints. **≤ 8 sections per page.** The footer CTA (closing echo + price anchor) closes every page automatically, so it isn't listed here. Component names are the `hm-*` content hooks (their purpose is in the project's `docs/05-content-authoring.md`); how they look is decided by each client's design.

Each recipe was used on a real project. Recipes set the **story order**, not the layout: the client's design decides how each section looks and how sections alternate. The "idea" column is the one thing each section must say. If it can't be said in a sentence, cut the section.

---

## Home (8)
| # | Section | Component | Idea |
|---|---|---|---|
| 1 | Hero | `hm-hero hm-dark` + `hero-visual` | Stakes headline, who-we-are line, one CTA, one-line social proof (`hm-trust`), **one** real image of the flagship client, with its `alt` text |
| 2 | Logos | `hm-marquee` | "Trusted by…" (named clients with permission only) |
| 3 | Results | `hm-dark` + `hm/work-grid` | 3–4 case cards with one number each |
| 4 | Voices | `hm-testimonials` | 3 client quotes, proof clause in bold |
| 5 | The contrast | `hm-head` + `hm-bento` | "Most agencies… We…" + service tiles with UI mocks |
| 6 | Method | `hm-bone` + `hm-steps` | 4 steps, one line each → link to /approach/ |
| 7 | People | `hm-split` + `hm-faces` | Real faces, one culture line |
| 8 | FAQ | `hm-faq` | 4–6 buyer questions (feeds FAQPage schema) |

## Service (7)
| # | Section | Component | Idea |
|---|---|---|---|
| 1 | Hero | `hm-page-hero` + `hm-hero__foot` | Pain headline; `hm-answer` (40–60 words); `hm-facts` (For / Outcome / Starting at) |
| 2 | Showcase | `hm-gallery` | Real work for this service |
| 3 | The contrast + what you get | `hm-head` + `hm-features` | "Most agencies… We…" + 4–6 features |
| 4 | Proof | `hm-dark` + `hm/work-grid {"service":…}` + `hm-quote is-compact` | Case studies filtered to this service + one unique quote |
| 5 | Fit | `hm-fit` | Good fit / not a fit, 4 each |
| 6 | Ways to start | `hm-offers` or a link row to /start/ | Entry offer + price |
| 7 | FAQ | `hm-faq` | Service questions |

## Industry (6)
Hero (pain in that industry's words) → showcase → contrast + what we do for this industry → proof (the one deep case) → fit → FAQ.

## About (6)
Hero (the culture line) → values (one card each; the heading count matches the cards) → story (founding arc, in the founders' words) → how we hold ourselves accountable → people → about-us facts (answer-first, for AI search).
> On one project the heading said "Four motivators" above three cards. Count your cards.

## Approach (4)
Hero → the steps in full (what happens, what you get) → working with us (communication, ownership, tools) → FAQ about engagements. **The only page with the full process.**

## Start / pricing (4)
Hero ("Start small. Grow together.") → the offer ladder (`hm-offers`, featured flagship) → "Which one fits you?" chooser → pricing plainly (what's fixed, what's scoped, minimums).

## Case study (CPT, ≤ 6)
`hm/case-header` (client, year, services, the stat) → the problem (2–3 sentences) → what we did (`hm-features` or prose) → gallery (verified images only) → the result (stats with sources) + quote → `hm/case-next`.
No photo? The work grid uses a **typographic stat cover**. Never use another client's image.

## Contact (3)
Hero with the phone number, email and booking link → `hm/brief-form` → faces of who'll answer.

## Growth audit / lead magnet (4)
Hero (what you'll get, in writing) → what we look at → sample of the output → `hm/brief-form {"variant":"audit"}`.

## Thank-you (1)
What happens next and when, the booking link, and one case study to read while they wait.

## Campaign landing page (6)
Template `page-landing` (logo, one button to the form, legal links only). Made by `bin/asf campaign new`; playbook in [`campaigns.md`](campaigns.md).

| # | Section | Component | Idea |
|---|---|---|---|
| 1 | Hero | `hm-page-hero` + one button to `#form` + `hm-trust` | The ad's promise as the H1, word for word; who it's for and what they get; one proof line |
| 2 | What you get | `hm-head` + checks list | Three concrete deliverables and when they arrive |
| 3 | Proof | `hm-testimonial` | One real quote that backs the promise |
| 4 | How it works | `hm-steps` | Three steps from asking to having it |
| 5 | The form | section `#form` + `hm/brief-form` | The ask, the reassurance (reply time, who replies), the form on the page |
| 6 | Questions | `hm-faq` | The three objections: price, time, commitment |

## Legal pages
Carry over verbatim from the live site. Changing legal text is the client's lawyer's job, not ours. Mark new drafts clearly as drafts.

---

# Product brands (marketing site, no checkout)

For an agency's clients that make physical products and sell through retailers, dealers or installers (first used for a UK car care brand). Start with `starter/new-site.sh <slug> "<Name>" <folder> --kind product-brand`. The primary action is **Where to buy**; the form handles fitment, dealer, bulk and warranty enquiries.

| Agency site | Product brand |
|---|---|
| Services hub + service pages | Products hub + product-line pages (`/products/<line>/`) |
| Case studies | Customer builds (the vehicle, what went on it, the result) |
| Get a strategy call | Where to buy · Become a dealer |
| Approach, Ways to start | Where to buy, Dealers, Support (install guides, warranty) |
| Price anchor in the footer | The promise buyers care about most (warranty, fitment, shipping) |

## Home (7)
Stakes hero (the driver's stake, one product image) → product lines (cards) → why us (one contrast + 3 proof-backed features: fit, quality, support) → builds (`hm/work-grid`) → reviews (named, sourced) → where to buy (`hm-bone` band + become a dealer) → FAQ (fitment, warranty, where to buy).

## Product line (6)
Hero with `hm-answer` (the search phrase first) and `hm-facts` (Fits · Made from · Warranty · From) → what's in the range (`hm-features`) → fitment (`hm-fit` with "Made for" / "Not for") → builds filtered to the line → FAQ. Always two actions: Where to buy, Check fitment.

## Where to buy (3)
Hero → online retailers + dealers and installers (by region, or "ask us") → become a dealer band.

## Dealers (3)
Hero (the shop owner's stake) → why stock it (margin, support, demand) → requirements + the enquiry form.

## Support (4)
Hero → install guides (cards linking to PDFs or videos) → warranty in plain words → owner FAQ.

## Build (CPT, ≤ 5)
Stat → the vehicle → what went on it (linked to product lines) → the result in the owner's words, with their photos and permission.

