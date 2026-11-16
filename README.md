# Agentic Site Framework (ASF)

**A repeatable way to research, write, design, build, ship and run a marketing agency's website with AI tools: fast, but grounded in the client's truth and finished to a top-agency standard.**

In ASF the website is the artifact and the weekly measurement is the service: Stage 5 (Run) exists for that reason.

- **Who it's for:** agencies, studios and their delivery partners building or rebuilding a site for an agency, or for an agency's own clients (often white-label).
- **Tools it assumes:** Claude Code (main session plus subagents), a browser the AI can drive, WP-CLI or the stack's CLI, and Python 3.
- **Base build:** [`base/`](base/), a design-neutral WordPress wireframe (block theme + functionality plugin + content seed) that every new site starts from. Each client's design is created in stage 3 from their own raw data, never copied. [`examples/`](examples/) has what two real projects (anonymised) taught us.

---

## The five stages

```
 1 TRUTH  ──►  2 STORY  ──►  3 SYSTEM  ──►  4 SHIP  ──►  5 RUN
 What is      What do we    How does it    Is it right,   Is it
 true and     say, in what  look and       fast and       working?
 provable?    order?        work?          finished?      (weekly)
   G1            G2            G3             G4            G5
```

| Stage | Output | Gate (must pass to move on) | Doc |
|---|---|---|---|
| **1 Truth** | Goal document, site audit, truth file (every claim, its source and whether it's public), verified image inventory, voice bank (the client's own words) | **G1:** goals signed off; every claim sourced; every image mapped to the client it really shows | [`stages/1-truth.md`](stages/1-truth.md) |
| **2 Story** | Positioning, messaging (stakes hero, who-we-are line, contrast, echo, price anchor), IA, page recipes | **G2:** the client approves the message and agrees it defines *their* business; ≤ 8 sections per page; one idea per page | [`stages/2-story.md`](stages/2-story.md) |
| **3 System** | Design tokens, components, page copy, the working build (theme + plugin + seed), AI-search layer, lead capture, analytics events | **G3:** design review passes the anti-"AI look" list; copy passes lint; the build seeds with one command | [`stages/3-system.md`](stages/3-system.md) |
| **4 Ship** | Automated QA report, editor validation, form end-to-end test, launch checklist, handoff docs | **G4:** all checks green; zero `[CONFIRM]` chips; client sign-off | [`stages/4-ship.md`](stages/4-ship.md) |
| **5 Run** | Weekly report, monthly improvement proposal | **G5 (every week):** report sent, whether the client asked or not | [`stages/5-run.md`](stages/5-run.md) |

## Roles

| Role | Who | Owns |
|---|---|---|
| **Lead** | A human (PM or strategist) | Every gate, client conversations, final say on message and design |
| **Orchestrator** | The main Claude Code session | Running stages, briefing specialists, integrating their work, running QA |
| **Researcher** | Subagent ([`agents/site-researcher.md`](agents/site-researcher.md)) | Stage 1: audits, internal notes, reference teardowns |
| **Strategist** | Subagent ([`agents/site-strategist.md`](agents/site-strategist.md)) | Stage 2: positioning, messaging, IA |
| **Writers** | Parallel subagents or forks ([`agents/site-copywriter.md`](agents/site-copywriter.md)) | Stage 3: page copy, one page family each |
| **QA** | Subagent ([`agents/site-qa.md`](agents/site-qa.md)) + [`qa/`](qa/) scripts | Stage 4: automated checks and review |
| **Designer** | A human, who reviews and doesn't push pixels | G3 design review |

## Get it

You need [Claude Code](https://claude.com/claude-code), PHP 8.1+ (with `pdo_sqlite`), [WP-CLI](https://wp-cli.org) 2.9+, Python 3, rsync, curl and unzip. No database server: local sites run on SQLite. [Laravel Valet](https://laravel.com/docs/valet) is optional.

```bash
git clone https://github.com/kuldeep3/agentic-site-framework.git
```

## Quick start: a new client site

```bash
# 1. Make the project: the wireframe base renamed for the client, skeleton pages, docs, framework and agents
starter/new-site.sh acme-growth "Acme Growth Co" ~/Projects/acme-website --short "Acme" --mark "AG"
```

```bash
# 2. Run the local site (WordPress on SQLite, no database server needed)
cd ~/Projects/acme-website && bin/setup.sh && bin/serve.sh
```

For a client that makes products and sells through retailers or dealers, add `--kind product-brand`: product lines, customer builds, "Where to buy" and dealer enquiries instead of services and strategy calls (recipes in [`patterns/page-recipes.md`](patterns/page-recipes.md)).

Details and what was tested: [`starter/README.md`](starter/README.md).

Then open the new project folder in Claude Code and run **`/asf`**. The [orchestrator](orchestrator/) knows which stage the project is in, checks each gate automatically where it can, tells you what's next, and records every sign-off in `asf.json`:

- `/asf run`: does the current stage's work up to its gate, briefing the stage's agents with its prompts and asking you for anything only the client can provide
- `/asf approve G1`: records a gate sign-off after the lead confirms the manual items
- `bin/asf status` / `bin/asf next`: the same from a terminal

Each stage doc lists the exact prompts ([`prompts/`](prompts/)), the templates to fill in ([`templates/`](templates/)) and the gate checklist.

**The site starts with no design.** The base is a wireframe (greys, system fonts, plain layout) so every client's look is created in stage 3 from their own raw data: logo, products, photos, geography, buyers and the competitor teardown. Nothing is copied from another client. See [`stages/3-system.md`](stages/3-system.md) and [`patterns/design-system.md`](patterns/design-system.md).

## What's in this folder

```
README.md            ← you are here
PRINCIPLES.md        the 14 rules learned on real projects (read before anything else)
stages/              how to run each stage: inputs, steps, AI roles, prompts, outputs, gate
patterns/            messaging formulas, page recipes, design system rules, AI-search (AEO) checklist
templates/           goal document, truth file, strategy, IA, page brief, content checklist, weekly report, decisions log
prompts/             copy-paste prompts for each step (with inputs and expected outputs)
agents/              Claude Code subagent definitions → copy into the project's .claude/agents/
orchestrator/        runs a project end to end: workflow.json (stages, gates, checks), bin/asf, the /asf command
qa/                  automated checks: content lint (block markup, SEO limits, duplicates, words), site crawl, responsive/grid sweep
starter/             new-site.sh: spin up a client site from the base (agency or product-brand skeleton)
base/                the design-neutral wireframe build every new site starts from
examples/            two real projects, anonymised: what happened, what clients pushed back on, what changed
```

## Stack choice

The stages, principles, patterns and prompts are **stack-agnostic**. The starter and the QA markup check are WordPress-specific today (block theme + functionality plugin + seed), with this rule of thumb:

- **WordPress:** existing sites with SEO/plugin history, or clients whose team edits in WordPress. *This is what `base/` and the starter implement today.*
- **EmDash / Astro:** greenfield or migrating clients. Reuse everything except `base/`, `starter/` and the block-markup checks in `qa/lint_content.py`. The content model, components and AEO layer map one to one.

## Licence

[MIT](LICENSE). Use it, change it and build client sites with it, commercial work included. Things the starter downloads keep their own licences: WordPress core and the SQLite integration plugin (GPL), and any fonts you add (check each one; the base ships none).
