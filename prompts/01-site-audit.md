# Prompt 01: Site audit

**Stage:** 1 Truth · **Run by:** the Researcher subagent (`site-researcher`) · **Needs:** a browser tool and web fetch

## Prompt
```text
Audit the current website of [CLIENT] at [URL] for a rebuild. The client is a US marketing
agency (or an agency's client). The rebuild's goal is in docs/00-goal.md. Read it first.

1. Crawl every URL: the sitemap, the navigation, the footer, and orphan landing pages found
   through internal links or a site: search. List each one with its title, purpose and status.
2. For each URL decide: keep / merge into [url] / redirect to [url] / drop, with a reason.
3. Fill this audit table (area → finding → impact on the goal), with specific evidence such as
   quoted lines, URLs and numbers, never generic advice:
   Positioning · Hidden strengths · Proof · Landing pages · Offers and prices · Content freshness ·
   Tech and speed · Conversion friction · AI search (llms.txt, schema, answer-first copy)
4. List every public claim on the site (numbers, client names, quotes) with its URL. These seed
   the claims register.
5. List every image URL with the page it's on and what the filename suggests. Mark it
   "unverified". The orchestrator will open each one.

Rules: quote, don't paraphrase, when you cite their copy. Flag lorem ipsum, typos, [TO CONFIRM]
notes and copy-paste errors (the same testimonial on two clients). Don't propose new messaging
yet; that is stage 2.
Write the result to docs/audit.md.
```

## Expected output
`docs/audit.md`: URL inventory with decisions, the audit table, a public-claims list and an image list.

## Check before accepting
- Does it find at least one hidden strength on a page that's not in the main nav? (On the first project, the client's strongest capability lived only on orphan pages.)
- Is every finding backed by a quote or a URL?
