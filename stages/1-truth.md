# Stage 1: Truth

**Question:** what is true about this business, and what can we prove in public?
**Time:** 1–3 days. **Lead:** a human. **AI:** the Researcher subagent plus the orchestrator.

Nothing in later stages may say something that isn't in this stage's output. On the first project, every message that failed came from skipping this stage and writing from agency clichés. Every message that worked came from the client's own notes.

---

## Inputs

| Input | From | Notes |
|---|---|---|
| Current website URL | Client | Crawl it fully, including orphan landing pages. That's where the real strengths hide. |
| Internal notes | Your team's notes, CRM, project repos | Engagement history, call notes, retros, what clients actually bought and kept buying |
| Client interviews | 2 × 30 min (founder + one account lead) | Use the question list below. Record and transcribe them. |
| Analytics / Search Console / ad accounts | Client (read access) | Baseline for the goal document. Reaching this gate without a baseline means Stage 5 has nothing to compare against. |
| Their clients' words | Reviews, testimonials, emails, case notes | Goes into the voice bank |
| 3–5 reference sites | Lead's choice, or the Researcher proposes | Best-in-class agencies in the same segment. We study their structure, not their words. |

Requirements keep arriving after kickoff, by email, on calls, in GitHub issues and in chat. Each one becomes one tracked item with its source, through **requirements intake** (`/asf intake`, see `orchestrator/README.md`): raw material goes in `docs/intake/raw/` (git-ignored), every request becomes a GitHub issue (or a file in `docs/intake/items/`), and a fact reaches `truth.md` only once the client confirms it, with the issue as its source. After a call, the recording goes to the team's shared drive and its timestamped transcript into `docs/intake/raw/` (steps in the project's `docs/intake/README.md`).

## Steps

### 1.1 Goal document
Fill [`templates/goal-document.md`](../templates/goal-document.md) with the client on the kickoff call: revenue goal, which lever the site moves (lead volume, close rate, deal size), baseline numbers, the primary conversion, and who signs off.
> Rule: no build starts without a signed goal document.

### 1.2 Site audit (Researcher)
Prompt: [`prompts/01-site-audit.md`](../prompts/01-site-audit.md). The output is an audit table (area → finding → impact) and the URL inventory with a keep / merge / redirect / drop decision for each URL. The redirect map is built from this inventory.

### 1.3 Truth harvest (Researcher)
Prompt: [`prompts/02-truth-harvest.md`](../prompts/02-truth-harvest.md). Read every internal source and fill [`templates/truth-file.md`](../templates/truth-file.md):

- **Business arc:** how clients actually arrive, what they buy first, what they buy next, why they stay. *This is usually where the positioning lives.*
- **Claims register:** every number, client name and quote, with its source and a public / private / needs-OK status.
- **Voice bank:** 10–20 verbatim phrases from the founders and their clients.
- **Offer inventory:** what's sold today, at what price signal, and what's productized.
- **Constraints:** white-label rules, names that can't appear, regulated claims. Add every name that must never appear to `docs/framework/qa/config.json` → `forbidden`: that's what lint and the crawl check.

### 1.4 Image inventory (orchestrator, with a browser)
Download every image from the live site into `content/media/`. Then **open each one and look at it.** Record in the truth file which client or person it really shows, and drop stock, duplicates and anything under 800px that has to carry a hero.
> On the first project, 3 of 48 images were misattributed by filename and 17 were stock or unused. Only looking at them catches this.

### 1.5 Reference teardown (Researcher)
Prompt: [`prompts/03-reference-teardown.md`](../prompts/03-reference-teardown.md). For each reference site, record its section order, hero formula, proof placement, CTA pattern, pricing transparency and what makes it look expensive. The output is patterns to adapt, never words to copy.

### 1.6 Interview questions (Lead, with AI-drafted follow-ups)
1. When a client stays with you for years, what are they really buying?
2. What do clients come to you for first? What do they end up buying?
3. What do you do that a cheaper agency doesn't?
4. Who is a bad fit? Who did you turn away or lose, and why?
5. Which result are you proudest of? Can we name the client and the number?
6. What do your best clients say about you to other people?
7. What do you never want the site to say?

## Outputs
- `docs/00-goal.md` (goal document, signed)
- `docs/truth.md` (truth file: arc, claims register, voice bank, offers, constraints, image map)
- `docs/audit.md` (audit table + URL inventory)
- `docs/references.md` (teardown notes)
- `content/media/` (verified images only)

## Gate G1: Truth

- [ ] Goal document filled in with baseline numbers and signed by the client
- [ ] Every claim in the register has a source and a status (public / private / needs OK)
- [ ] The business arc is written in one paragraph, in the client's words, and the founder agrees with it
- [ ] Every image in `content/media/` was opened, mapped to the client it shows, or deleted
- [ ] Constraints (white-label, names, regulated claims) are written down, and the names are in `qa/config.json` → `forbidden`
- [ ] Voice bank has at least 10 verbatim lines
- [ ] Every raw source in `docs/intake/raw/` was read, and each request in it filed (`bin/asf intake sources`)

**Common failure:** skipping 1.3 because "we know this client." On the first project, the delivery team had years of shared work with the client, and the first messaging still came out generic.
