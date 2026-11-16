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

Other commands: `bin/asf check [G2]`, `bin/asf skip G1 audit --reason "no current site"`, `bin/asf set deploy.staging_url https://…`, `bin/asf campaign …` (below), `bin/asf log`.

## Gates
| Gate | Checked automatically | Confirmed by a person |
|---|---|---|
| **G1 Truth** | Goal document filled; audit done (or skipped with a reason); business arc written; ≥ 5 claims and ≥ 10 voice lines; every image mapped; teardown done | Client signed the goal; founder agrees with the arc; constraints written |
| **G2 Story** | Strategy and IA filled; the client's own words choosing the message recorded; ≥ 3 briefs; every brief ≤ 8 sections | Route chosen as "defines our business"; competitor test; one idea, one home |
| **G3 System** | Client facts filled; design brief and three directions written; the client's own design layer in place (not `ASF:UNBRANDED`); every page the IA plans exists and no unplanned skeleton page is left; content lint clean | Anti-AI-look review; not a re-skin; client approved pages in the browser |
| **G4 Ship** | Strict lint (no `[CONFIRM]` left in pages, front matter or theme templates); strict crawl (none on any live page, title or meta description); staging URL recorded; `launch.py`: accessibility (local), then security, performance and launch settings on staging; Lighthouse 90+ (public staging) | Responsive, contrast and keyboard, editor, form and email end to end, backups with a tested restore, uptime monitoring, admins on 2FA, written sign-off |
| **G5 Run** (weekly) | Production URL recorded; production scan (security, launch settings) clean; live campaigns pass their checks and finished ones are closed; the analytics ID recorded is on the live home page; a report in the last 7 days | Report sent; one concrete action |

`approve` is refused while automated checks fail. `--override "reason"` exists for real exceptions, and the reason is kept in the log.

## Check types (for editing `workflow.json`)
`file_exists` · `no_placeholders` (no unfilled `[template brackets]`; links, checkboxes and `[CONFIRM]` don't count) · `section_filled` (a heading's section has real text) · `table_rows` (min filled rows under a heading) · `media_mapped` (every file in `content/media/` named in the truth file) · `glob_min` · `briefs_max_sections` · `not_contains` · `command` (exit code 0; `{site_url}`, `{deploy.staging_url}` or any other `asf.json` value in braces is filled in, and the check fails with "needs `asf set …`" while it's empty) · `state_set` (a value set with `asf set`) · `recent_file` (newest match within N days) · `ia_pages` (the IA's sitemap against `content/pages/`, both ways) · `analytics_live` (the GA4/GTM ID in `measurement.analytics` appears on the live home page) · `campaigns` (every live campaign passes `asf campaign check`; none left open a week after it ends).

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
