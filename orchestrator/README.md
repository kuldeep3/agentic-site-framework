# Orchestrator

Runs one client project from requirements to deployment and measurement: it knows which stage the project is in, checks each gate automatically where a file or a script can prove it, tells you (or Claude) exactly what to do next, and records every human sign-off.

```
 /asf run ──► agents do the stage's work ──► bin/asf check ──► gate ready? ──► a person signs: bin/asf approve G1
     ▲                                                                                        │
     └────────────────────────────────────── next stage ◄─────────────────────────────────────┘
```

## Pieces
| File | What it is |
|---|---|
| `workflow.json` | The framework as data: five stages, each with its playbook, agents, prompts, **automated checks** (with a fix hint each) and **manual items** a person must confirm |
| `asf.py` | The command-line tool (`bin/asf` in each project). Standard-library Python |
| `claude-command.md` | The `/asf` command for Claude Code, installed as `.claude/commands/asf.md` |
| `intake.py` | Requirements intake (`bin/asf intake`): every request from any channel becomes one tracked item with its source |
| `github_board.py` | The project manager's view (`bin/asf github`): labels, gate milestones, a Projects board and a gate tracker issue |
| `board-sync.yml` | Optional GitHub Action that keeps the gate tracker in step; copy to `.github/workflows/` in the project |
| `asf.json` (in each project) | The project's state and audit trail: stage, sign-offs (who, when, what they confirmed), skips with reasons, deploy URLs, analytics. Commit it |

## Use it
In Claude Code, inside a project made by the starter:

- `/asf`: where the project is and what's next
- `/asf run`: do the current stage's work up to its gate (agents in parallel where they can be; it asks you for anything only the client can provide)
- `/asf approve G1`: record a sign-off after you confirm the manual items

Or from a terminal:

```bash
bin/asf status
```

```bash
bin/asf next
```

```bash
bin/asf approve G1 --by "Jane Lead" --note "Kickoff signed by the founder"
```

Other commands: `bin/asf check [G2]`, `bin/asf skip G1 audit --reason "no current site"`, `bin/asf set deploy.staging_url https://…`, `bin/asf intake …` and `bin/asf github …` (below), `bin/asf campaign …` (below), `bin/asf log`.

## Gates
| Gate | Checked automatically | Confirmed by a person |
|---|---|---|
| **G1 Truth** | Goal document filled; audit done (or skipped with a reason); business arc written; ≥ 5 claims and ≥ 10 voice lines; every image mapped; teardown done; every raw intake source read | Client signed the goal; founder agrees with the arc; constraints written |
| **G2 Story** | Strategy and IA filled; the client's own words choosing the message recorded; ≥ 3 briefs; every brief ≤ 8 sections | Route chosen as "defines our business"; competitor test; one idea, one home |
| **G3 System** | Client facts filled; design brief and three directions written; directions shared for review (`design.figma_url`) and the choice recorded (`design.direction`); the client's own design layer in place (not `ASF:UNBRANDED`); every page the IA plans exists and no unplanned skeleton page is left; content lint clean | Review-file comments resolved or filed; anti-AI-look review; not a re-skin; client approved pages in the browser |
| **G4 Ship** | Nothing the client sent left unread; strict lint (no `[CONFIRM]` left in pages, front matter or theme templates); strict crawl (none on any live page, title or meta description); staging URL recorded; `launch.py`: accessibility (local), then security, performance and launch settings on staging; Lighthouse 90+ (public staging) | Responsive, contrast and keyboard, editor, form and email end to end, backups with a tested restore, uptime monitoring, admins on 2FA, written sign-off |
| **G5 Run** (weekly) | Production URL recorded; production scan (security, launch settings) clean; live campaigns pass their checks and finished ones are closed; the analytics ID recorded is on the live home page; a report in the last 7 days | Report sent; one concrete action |

`approve` is refused while automated checks fail. `--override "reason"` exists for real exceptions, and the reason is kept in the log.

## Check types (for editing `workflow.json`)
`file_exists` · `no_placeholders` (no unfilled `[template brackets]`; links, checkboxes and `[CONFIRM]` don't count) · `section_filled` (a heading's section has real text) · `table_rows` (min filled rows under a heading) · `media_mapped` (every file in `content/media/` named in the truth file) · `glob_min` · `briefs_max_sections` · `not_contains` · `command` (exit code 0; `{site_url}`, `{deploy.staging_url}` or any other `asf.json` value in braces is filled in, and the check fails with "needs `asf set …`" while it's empty) · `state_set` (a value set with `asf set`) · `recent_file` (newest match within N days) · `ia_pages` (the IA's sitemap against `content/pages/`, both ways) · `analytics_live` (the GA4/GTM ID in `measurement.analytics` appears on the live home page) · `campaigns` (every live campaign passes `asf campaign check`; none left open a week after it ends) · `intake_clear` (every file in `docs/intake/raw/` processed with `asf intake done`).

## Design review (stage 3)
Clients can't choose between directions described in a document, so each direction is shown on the real pages and reviewed where everyone can comment (playbook: `stages/3-system.md` §3.2a; prompts: `prompts/07-design-direction.md` A, C, D).

| Step | How |
|---|---|
| Preview | Each direction is `assets/css/directions/<a\|b\|c>.css`. `/?asf_direction=b` shows any page in direction B on a local or staging site (never production), noindex, with a "Design review" label |
| Share | The directions go into one Figma file (Figma connector in Claude Code: rendered page or code → frames at 1440 and 375). `bin/asf set design.figma_url …` |
| Comment | The client and designer comment in Figma. `/asf intake` files each comment as a `type:design` issue with the comment link |
| Decide | `bin/asf set design.direction "B, chosen by … on …"`; the chosen file becomes `brand.css` |
| Final review | The built home page and one inner page go into the same file for the G3 sign-off |

Figma is where people review; the design itself lives in `brand.css` and `theme.json`. A change made in Figma comes back through the connector into the CSS.

## Requirements intake (all stages)
Requirements arrive by email, on calls, in GitHub issues, in chat and in documents, all project long. Each request becomes **one tracked item with its source**: a GitHub issue labelled `intake`, `type:*` and `source:*`, on the board in its Stage (or a file in `docs/intake/items/` when the project isn't on GitHub). A request isn't a fact: it reaches `docs/truth.md`, and the site, only when the client confirms it, with the issue as its source.

| Command | What it does |
|---|---|
| `/asf intake` (Claude Code) | Reads what's new: `docs/intake/raw/`, a connected inbox (`intake.email_query`), meeting transcripts, unlabelled or form-filed issues, Figma comments. Drafts one item per request with the client's words and an exact reference, and files the ones the lead approves |
| `bin/asf intake sources` | Raw files in `docs/intake/raw/` (git-ignored: client correspondence stays private) and which are processed |
| `bin/asf intake add "Title" --type … --source … --ref "…" [--quote "…"] [--page /…/] [--stage …] [--local] [--dry-run]` | Files one item. Types: fact, question, content, page, design, bug, campaign. Sources: email, call, meeting, issue, chat, doc, figma, other |
| `bin/asf intake done <file> …` | Marks raw files processed (G1 and G4 check that none are left) |
| `bin/asf intake list` | Open items |

Clients and the team can also file directly with the issue forms every project gets in `.github/ISSUE_TEMPLATE/` (client request, design feedback, bug); `/asf intake` adds their `type:*` label and Stage.

**After a client call** (the steps are in each project's `docs/intake/README.md`):
- The recording goes to the team's shared drive, never into the repo. `.gitignore` also blocks audio and video files anywhere under `docs/`.
- The timestamped transcript goes in `docs/intake/raw/`, named date first (`2026-11-17-call-admissions.vtt`). Its first two lines give the recording link and who was on the call.
- `/asf intake` then files one item per request, quoting the client with a reference like "Call 2026-11-17, recording 14:32, <link>".
- `bin/asf intake sources` flags an audio or video file left in `raw/`: intake reads text, so it needs a transcript first.

## Project board on GitHub (all stages)
The project manager's view: which request, page and fix is where. **`asf.json` stays the record of sign-offs; GitHub mirrors it one way**, so there's never a second source of truth to reconcile.

| What | Where it comes from |
|---|---|
| **Projects board** with a **Stage** field: Inbox → Requirement → Story → Design → Development → Testing → Launch → Live → Done | `bin/asf github init`. Intake items land in the Stage their type implies (fact → Requirement, design → Design, bug → Testing…). A board shared across clients (`--owner org --project N`) also gets a **Client** field |
| **Milestones G1–G5**, one per gate | `init`; `sync` closes a gate's milestone when it's signed |
| **Gate tracker** issue (pinned) | `sync` rewrites it (every gate's status, the current gate's automated checks as checkboxes, the manual items, sign-offs and links) and moves its card to the current stage. `asf approve` runs `sync` too |
| **"Facts to confirm" issues**, one per page | `bin/asf github confirm-issues`, once the pages are written (stage 3): every `[CONFIRM]` chip as a checkbox, on milestone G4. Pages that already have an open issue are skipped |
| Pull requests | Link them to issues (`Closes #12`); the board shows what's in review |

Setup: the GitHub CLI logged in with the `project` scope (`gh auth refresh -s project`), then `bin/asf github init --repo owner/name --dry-run` to see every call, and again without `--dry-run`. In the project's board settings, turn on the built-in workflow "Auto-add to project" for `label:intake`, so form-filed issues appear in Inbox. To keep the tracker current without anyone running it, copy `board-sync.yml` to `.github/workflows/asf-board-sync.yml`.

## Measurement (stage 5, weekly)
`bin/asf report` collects last week's numbers into `docs/reports/data/<date>.json` and drafts `docs/reports/<date>.md`. `/asf report` then has the agent fill the gaps and write "The three things"; a person reviews and sends it. G5 checks that this week's data exists and the report has no blanks left.

| Source | What it gives | How to connect |
|---|---|---|
| **The site's own leads** (first-party, always available) | Enquiries and sign-ups, this week vs last, by need, page, source (UTM or referrer) and budget | The base plugin's private `GET /wp-json/<slug>/v1/metrics`. Create an Application Password for an admin (Users → Profile → Application Passwords), then set `ASF_WP_USER` and `ASF_WP_APP_PASSWORD` |
| **Site health** | Home page status and response time, a full crawl, and a rescan of the live site (`qa/launch.py`: security, performance, accessibility, launch settings, pending updates, failed emails), with anything new since last week listed | Automatic, against `deploy.production_url` (or `site_url`). The Application Password above adds the inside checks; `PSI_API_KEY` adds Lighthouse scores and Core Web Vitals |
| **GA4** | Sessions, users, engagement, and the site's events (`lead_submit`, `cta_click`, `book_call_open`, `phone_click`, `newsletter_signup`, `offer_view`) | On the site: `define( 'ASF_GA4_ID', 'G-…' )` (or `ASF_GTM_ID`) in wp-config. For the report: `GA4_PROPERTY_ID` + `GOOGLE_ACCESS_TOKEN`, or a connector in Claude Code |
| **Search Console** | Clicks, impressions, average position, top queries | `GSC_SITE_URL` + `GOOGLE_ACCESS_TOKEN`, or a connector |
| **AI search** | Whether assistants cite the client for 5 tracked prompts | `bin/asf set measurement.prompts '["…", "…"]'`; the agent checks them through an AI-visibility connector, or a web search as a proxy |

Privacy: analytics never loads on local sites, and defaults to Consent Mode "denied" until the site's consent banner calls `window.asfConsent.grant()` (UK/EU sites need that banner). Credentials only ever come from environment variables, never from files in the repo. The GA4 and Search Console calls follow Google's documented API but haven't yet been run against a live property; errors land in the data file rather than being hidden.

**Running it every week:**
- **Unattended numbers:** copy `weekly-report.yml` to the project as `.github/workflows/asf-weekly-report.yml` and add the secrets. Every Monday it opens a pull request with the data and the draft.
- **Unattended narrative too:** schedule a Claude Code routine on the project that runs `/asf report` weekly (`/schedule` in Claude Code).

## Campaigns (stage 5)
`campaigns.py`, through `bin/asf campaign`. Playbook: [`patterns/campaigns.md`](../patterns/campaigns.md).

| Command | What it does |
|---|---|
| `new <slug> --name … --landing /… --start … --end … [--goal 20] [--budget 3000] [--channels google/cpc,…] [--cta "…"] [--index]` | Records the campaign, writes `docs/campaigns/<slug>.md` (the brief) and `content/pages/<landing>.html` (a six-section page on the `page-landing` template, noindex unless `--index`) |
| `links <slug> [--content a,b] [--channels …]` | The tagged link for every channel × creative, written into the brief. Tags are normalised (lowercase, hyphens) |
| `check <slug> [--url …]` | Brief filled; copy confirmed; page live; H1 matches the promise; indexing as decided; form and lead script on the page; few links away; `launch.py` accessibility and performance on that page; links issued; spend recorded for paid channels; not left open after it ends |
| `report <slug> [--write]` | Leads to date against the goal and pace, by creative, source, medium, landing page, enquiry page and day; cost per lead; GA4 sessions and visit-to-lead rate when connected |
| `close <slug> --outcome keep\|redirect\|unpublish [--to /…] [--note …]` | Records the outcome, adds the 301 to the plugin's redirect map, writes the results file when the Application Password is set |
| `list` | Every campaign with its status (planned, live, ended, closed) |

Leads are matched to a campaign by their `utm_campaign` tag, which the theme carries from the landing page to whichever page the form is sent from. The metrics endpoint takes `?campaign=<slug>`. The weekly report adds a Campaigns table, and G5's `campaigns` check runs `check` on every live campaign.

## What plugs in next
Deployment is already a stage with checks (`deploy.staging_url`, `deploy.production_url`); today you deploy by hand and record it with `asf set`. A deploy adapter will do it and set the same values, so the workflow doesn't change.
