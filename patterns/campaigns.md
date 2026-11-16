# Campaigns

A campaign is a time-boxed push (paid search or social, an email, an event, a partner mailing) that sends people to **one landing page with one offer**. The site's job is to keep the ad's promise, make one action easy, and say afterwards which channel and which creative produced the leads.

Campaigns run after launch, in stage 5. They're usually how a retainer grows: the monthly improvement proposal is often a campaign.

```
brief ──► landing page ──► check ──► tagged links ──► live (weekly report) ──► close (keep, redirect or unpublish) + results
```

```bash
bin/asf campaign new spring-audit --name "Spring growth audit" --landing /spring-audit/ --start 2026-12-01 --end 2026-12-31 --goal 20 --budget 3000 --channels google/cpc,linkedin/paid-social,newsletter/email --cta "Get the audit"
```

That writes the brief (`docs/campaigns/spring-audit.md`) and the page skeleton (`content/pages/spring-audit.html`). Then: fill the brief with the client, write the page with [prompt 10](../prompts/10-campaign.md), publish it, `bin/asf campaign check spring-audit`, `bin/asf campaign links spring-audit --content headline-a,headline-b`. Everything else is below.

---

## 1. The brief comes first
One page, filled with the client before anything is written ([`templates/campaign-brief.md`](../templates/campaign-brief.md)): goal and affordable cost per lead, audience, **the promise**, offer, proof, call to action, channels, indexing, what happens after it ends, and what success looks like. `campaign check` fails while any of those is still a blank.

The affordable cost per lead comes from the goal document: what a client is worth in the first year × how often a lead becomes a client. If nobody knows, say so in the brief; the first campaign is how you find out.

## 2. Message match
Whatever the person clicked (the ad headline, the email subject, the post) is what the landing page's H1 says. Same words, not a clever variation. People who don't see the promise they clicked within a second go back. `campaign check` compares the H1 with the brief's promise and warns when they share no words.

Testing creatives? Each ad gets its own `utm_content`. If headlines differ a lot, give each its own landing page; if they're variations of one promise, one page is fine.

## 3. The landing page
Recipe in [`page-recipes.md`](page-recipes.md) § Campaign landing page. The rules:
- **Template `page-landing`**: logo, one button to the form, and a footer with only the legal links. No menu: every link away is a lead lost. `campaign check` warns at more than three links leading away.
- **The form is on the page**, anchored `#form`. It converts better than a click away, and on UK/EU sites it's attributed even before the visitor accepts cookies (§5).
- **One action.** One offer, one form, one button label repeated.
- **Proof near the ask**: one number, one real quote from the truth file. No new claims; anything unverified is a `[CONFIRM]` chip, and a live campaign with chips fails its check.
- **Objections as FAQ**: price, time, commitment, in the buyer's words.
- **No fake urgency.** A deadline only if it's real (the brief's end date, a limited number of slots the client will honour).
- **Indexing**: noindex by default, so a paid-only page doesn't compete with the service pages in search. An evergreen offer can be indexed (`--index`).
- Short: six sections at most. The skeleton has six.

## 4. Tags (UTM conventions)
Every link that points at the site carries `utm_source`, `utm_medium` and `utm_campaign` (the campaign slug), and `utm_content` for the creative. `bin/asf campaign links` writes them all; use only those, because one hand-typed `Google` next to `google` splits the report.

| Tag | Values | Examples |
|---|---|---|
| `utm_source` | where the link sits: the platform or the sender | `google`, `linkedin`, `meta`, `newsletter`, `partner-name` |
| `utm_medium` | the kind of traffic | `cpc` (paid search), `paid-social`, `social` (organic), `email`, `display`, `referral`, `qr`, `print` |
| `utm_campaign` | the campaign slug | `spring-audit` |
| `utm_content` | the creative or placement | `headline-a`, `carousel`, `footer-link` |

Lowercase, hyphens, no spaces. The tool normalises what you type. Google Ads' `gclid` and Meta's `fbclid` are kept too.

## 5. Attribution and consent
The theme remembers the first page of a visit, the outside referrer and the tags for the browser session, and every lead carries them. A visitor who lands on `/spring-audit/` from an ad, reads a case study and then sends the form from `/contact/` is still credited to the ad, the creative and the landing page. The lead email and the Leads list show the source and campaign.

Where consent is required (UK/EU, the default when analytics is on), nothing is stored until the consent banner calls `window.asfConsent.grant()`. Leads sent from the landing page itself are attributed either way, which is one more reason the form lives there.

## 6. While it runs
- `bin/asf campaign report spring-audit`: leads so far against the goal and a straight-line pace, by creative, source, medium, the page they landed on and the page they sent the form from, and by day. With spend recorded (`bin/asf set campaigns.spring-audit.spend 1450`), cost per lead. With GA4 connected, sessions and the visit-to-lead rate.
- The weekly report has a Campaigns table: this week, to date, pace, cost per lead, best creative.
- Behind pace at the end of week two? Change one thing, in this order: the promise (headline), the offer, the audience or targeting, then the page. Record it in the brief.
- Gate G5 checks every live campaign each week (page live, copy confirmed, form and tracking present, no accessibility or performance errors) and fails while a finished campaign is left open.

## 7. Close it
```bash
bin/asf campaign close spring-audit --outcome redirect --to /services/audit/ --note "20 booked; LinkedIn carousel won"
```
- **keep**: the page stays (an evergreen offer); decide whether it should now be indexed and linked.
- **redirect**: adds the 301 to the core plugin's redirect map (deploy it), then unpublish the page.
- **unpublish**: set it to Draft and remove it from `content/pages/`.

With the Application Password set, closing also writes `docs/campaigns/<slug>-results.md`. Fill "What we learned" and "Next time" before the next campaign's brief: that's the part the client pays for.
