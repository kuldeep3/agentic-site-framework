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

Other commands: `bin/asf check [G2]`, `bin/asf skip G1 audit --reason "no current site"`, `bin/asf set deploy.staging_url https://…`, `bin/asf log`.

## Gates
| Gate | Checked automatically | Confirmed by a person |
|---|---|---|
| **G1 Truth** | Goal document filled; audit done (or skipped with a reason); business arc written; ≥ 5 claims and ≥ 10 voice lines; every image mapped; teardown done | Client signed the goal; founder agrees with the arc; constraints written |
| **G2 Story** | Strategy and IA filled; the client's own words choosing the message recorded; ≥ 3 briefs; every brief ≤ 8 sections | Route chosen as "defines our business"; competitor test; one idea, one home |
| **G3 System** | Client facts filled; design brief and three directions written; the client's own design layer in place (not `ASF:UNBRANDED`); content lint clean | Anti-AI-look review; not a re-skin; client approved pages in the browser |
| **G4 Ship** | Strict lint (no `[CONFIRM]` left); crawl clean; staging URL recorded | Responsive, editor, form end to end, Lighthouse, written sign-off |
| **G5 Run** (weekly) | Production URL and analytics recorded; a report in the last 7 days | Report sent; one concrete action |

`approve` is refused while automated checks fail. `--override "reason"` exists for real exceptions, and the reason is kept in the log.

## Check types (for editing `workflow.json`)
`file_exists` · `no_placeholders` (no unfilled `[template brackets]`; links, checkboxes and `[CONFIRM]` don't count) · `section_filled` (a heading's section has real text) · `table_rows` (min filled rows under a heading) · `media_mapped` (every file in `content/media/` named in the truth file) · `glob_min` · `briefs_max_sections` · `not_contains` · `command` (exit code 0; `{site_url}` is filled from `asf.json`) · `state_set` (a value set with `asf set`) · `recent_file` (newest match within N days).

## What plugs in next
Deployment and measurement are already stages with checks (`deploy.staging_url`, `deploy.production_url`, `measurement.analytics`, a weekly report). Today you do those steps by hand and record them with `asf set`. Deploy adapters and a scheduled reporting agent will do them and set the same values, so the workflow doesn't change.
