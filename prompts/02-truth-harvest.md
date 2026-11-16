# Prompt 02: Truth harvest

**Stage:** 1 Truth · **Run by:** the Researcher subagent · **Needs:** read access to internal notes (OS repo, CRM exports, call transcripts)

## Prompt
```text
Build the truth file for [CLIENT] from these sources:
- docs/audit.md (public claims from the live site)
- [paths to internal notes: OS-core project folders, call transcripts, proposals, retros]
- [interview transcripts]

Use the template at docs/framework/templates/truth-file.md and write docs/truth.md.

Most important: section 1, the business arc. Read the engagement history and answer:
how do clients arrive, what do they buy first, what do they buy next, and why do they stay?
Use the client's own words wherever they exist, and cite the file and line for each.

Then:
- Claims register: every number, client name, quote and superlative, each with its source
  and a status: public (already published by the client), private (needs written OK) or
  confirm (unverified). Internal figures such as revenue or customer counts from our
  own project notes are PRIVATE until the owner approves them.
- Voice bank: 10–20 verbatim lines from founders, staff and their clients. No paraphrase.
- Offers today, people, constraints.

Never name our own company, our team or any delivery partner in a field marked for public use.
Don't invent anything. A gap is written as a gap.
```

## Expected output
`docs/truth.md`, filled in.

## Check before accepting
- Read the business arc aloud to the founder. Do they say "yes, that's us"? If they correct it, the correction goes in verbatim.
- Spot-check five claims against their sources.
