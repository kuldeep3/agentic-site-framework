"""GitHub as the project manager's view: labels, gate milestones, a Projects board and a gate tracker issue.

    bin/asf github init [--repo owner/name] [--owner org] [--project N] [--dry-run]
        Labels (intake, type:*, source:*), milestones G1–G5, a GitHub Projects board linked to
        the repo with a "Stage" field (and "Client" when the board is shared across clients),
        and a pinned "Gate tracker" issue. Settings are kept in asf.json → github.
    bin/asf github sync [--dry-run]
        Rewrites the gate tracker from asf.json and the current gate's checks, and closes the
        milestone of every signed gate. `asf approve` runs it too, when GitHub is set up.
    bin/asf github review <file.pdf> [--title "…"] [--ask "…"] [--change <slug>] [--dry-run]
        Sends a design review to the client: one issue that links the PDF (committed in the repo,
        usually docs/reviews/) and says how to reply. Their comments on it are their feedback;
        /asf intake files each point as a type:design item.
    bin/asf github confirm-issues [--dry-run]
        One "Facts to confirm" issue per page, listing its [CONFIRM] chips as checkboxes, on the
        board under Requirement. Pages that already have an open issue are skipped.

asf.json stays the record of sign-offs (who, when, what they confirmed); the board mirrors it
one way, so nobody keeps two sources of truth. Uses the GitHub CLI (`gh`), logged in with the
`project` scope (`gh auth refresh -s project`). --dry-run prints every gh call instead of running it.
"""
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

# The board's columns. Each framework stage maps to one or two of them.
STAGE_OPTIONS = ["Inbox", "Requirement", "Story", "Design", "Development", "Testing", "Launch", "Live", "Done"]
STAGE_HELP = {
    "Inbox": "New request, not triaged yet",
    "Requirement": "Stage 1 Truth: facts, goals, the client's words",
    "Story": "Stage 2: positioning, messaging, IA, briefs",
    "Design": "Stage 3: design directions and review",
    "Development": "Stage 3: build and page copy",
    "Testing": "Stage 4: QA and launch readiness",
    "Launch": "Stage 4: deploy and sign-off",
    "Live": "Stage 5: weekly report, campaigns, improvements",
    "Done": "Shipped or answered",
}
# Where a request of each type starts on the board.
TYPE_STAGE = {"fact": "Requirement", "question": "Requirement", "content": "Development", "page": "Development",
              "design": "Design", "bug": "Testing", "campaign": "Live"}
GATE_STAGE = {"truth": "Requirement", "story": "Story", "system": "Development", "ship": "Launch", "run": "Live"}
# Who acts on a request of each type, so every function can filter the board to its own queue (label role:*).
ROLES = ["lead", "designer", "developer", "content", "qa", "client"]
TYPE_ROLE = {"fact": "client", "question": "client", "content": "content", "page": "developer",
             "design": "designer", "bug": "developer", "campaign": "lead"}

LABELS = [("intake", "ededed", "Came in through /asf intake or an issue form")]
LABELS += [(f"type:{t}", c, d) for t, c, d in [
    ("fact", "fbca04", "A fact or number the site states; needs a source"),
    ("question", "fbca04", "Something only the client can answer"),
    ("content", "1d76db", "Copy or page change"),
    ("page", "1d76db", "A new page"),
    ("design", "d876e3", "Design feedback"),
    ("bug", "d73a4a", "Something broken"),
    ("campaign", "0e8a16", "Campaign work (stage 5)"),
]]
LABELS += [(f"source:{s}", "c5def5", f"Arrived by {s}") for s in ("email", "call", "meeting", "issue", "chat", "doc", "artifact", "figma", "other")]
LABELS += [("review", "5319e7", "A design review sent to the client; their feedback goes in its comments")]
LABELS += [(f"role:{r}", "bfdadc", f"Next step is with {who}") for r, who in zip(ROLES, (
    "the lead", "the designer", "a developer", "the content owner", "QA", "the client"))]


class GhError(RuntimeError):
    pass


def gh(args, dry=False, stdin=None, parse=False):
    """Run one gh command. In dry-run mode print it and return a placeholder."""
    if dry:
        shown = " ".join(_quote(a) for a in args)
        print(f"  $ gh {shown}" + ("   <<body>>" if stdin else ""))
        return {} if parse else ""
    if not shutil.which("gh"):
        raise GhError("the GitHub CLI isn't installed (https://cli.github.com)")
    r = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise GhError(f"gh {' '.join(args[:3])}…: {(r.stderr or r.stdout).strip()[:300]}")
    out = r.stdout.strip()
    return json.loads(out or "null") if parse else out


def _quote(a):
    return a if re.fullmatch(r"[\w@%+=:,./-]+", a) else "'" + a.replace("'", "'\\''") + "'"


def cfg(state):
    return state.get("github") or {}


def configured(state):
    return bool(cfg(state).get("repo"))


# ── setup ─────────────────────────────────────────────────────────────────────────
def init(root, state, args, core):
    dry = args.dry_run
    g = state.setdefault("github", {}) if not dry else dict(cfg(state))
    repo = args.repo or g.get("repo") or (None if dry else gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]))
    if not repo:
        sys.exit("No repo: pass --repo owner/name (the project's GitHub repository).")
    owner = args.owner or g.get("owner") or repo.split("/")[0]
    g.update({"repo": repo, "owner": owner})
    print(f"GitHub board for {state['client']}: repo {repo}, project owner {owner}" + (" (dry run)" if dry else ""))

    print("→ Labels")
    for name, color, desc in LABELS:
        gh(["label", "create", name, "--repo", repo, "--color", color, "--description", desc, "--force"], dry)

    print("→ Milestones (one per gate)")
    wf = core.load_workflow(root)
    existing = {} if dry else {m["title"]: m["number"] for m in gh(["api", f"repos/{repo}/milestones?state=all&per_page=100"], parse=True) or []}
    milestones = {}
    for s in wf["stages"]:
        title = milestone_title(s)
        if title in existing:
            milestones[s["gate"]] = existing[title]
            continue
        made = gh(["api", f"repos/{repo}/milestones", "-f", f"title={title}", "-f", f"description={s['question']}"], dry, parse=True)
        milestones[s["gate"]] = (made or {}).get("number")
    g["milestones"] = milestones

    print("→ Project board")
    if args.project or g.get("project", {}).get("number"):
        number = args.project or g["project"]["number"]
        view = gh(["project", "view", str(number), "--owner", owner, "--format", "json"], dry, parse=True)
    else:
        view = gh(["project", "create", "--owner", owner, "--title", f"{state['client']} website", "--format", "json"], dry, parse=True)
        number = (view or {}).get("number", "N")
    gh(["project", "link", str(number), "--owner", owner, "--repo", repo], dry)
    project = {"number": number, "id": (view or {}).get("id", ""), "url": (view or {}).get("url", "")}
    fields = {f["name"]: f for f in (gh(["project", "field-list", str(number), "--owner", owner, "--format", "json"], dry, parse=True) or {}).get("fields", [])}
    if "Stage" not in fields:
        gh(["project", "field-create", str(number), "--owner", owner, "--name", "Stage", "--data-type", "SINGLE_SELECT",
            "--single-select-options", ",".join(STAGE_OPTIONS)], dry)
    if args.project and "Client" not in fields:  # a board shared across clients needs to say whose card it is
        gh(["project", "field-create", str(number), "--owner", owner, "--name", "Client", "--data-type", "TEXT"], dry)
    if not dry:
        fields = {f["name"]: f for f in gh(["project", "field-list", str(number), "--owner", owner, "--format", "json"], parse=True).get("fields", [])}
        project["fields"] = {name: {"id": f["id"], "options": {o["name"]: o["id"] for o in f.get("options", [])}} for name, f in fields.items() if name in ("Stage", "Client")}
    g["project"] = project

    print("→ Gate tracker issue")
    if not g.get("tracker"):
        url = gh(["issue", "create", "--repo", repo, "--title", f"Gate tracker: {state['client']}", "--body-file", "-"],
                 dry, stdin=tracker_body(root, state, core))
        g["tracker"] = issue_number(url) if url else None
        if g["tracker"] or dry:
            gh(["issue", "pin", str(g["tracker"] or "<tracker>"), "--repo", repo], dry)
            add_to_board(state, url or "<tracker-url>", GATE_STAGE.get(state["stage"], "Requirement"), dry, g)
    if dry:
        print("Dry run: nothing was created and asf.json is unchanged.")
        return
    state["log"].append({"at": core.now(), "event": "GitHub board set up", "note": project.get("url") or repo})
    core.save_state(root, state)
    print(f"✓ Board: {project.get('url') or 'project ' + str(number)} · tracker issue #{g.get('tracker')}")
    print("Next: `bin/asf github confirm-issues` to put every [CONFIRM] chip on the board.")


def milestone_title(stage):
    return f"{stage['gate']} {stage['title']}"


def issue_number(url):
    m = re.search(r"/issues/(\d+)", url or "")
    return int(m.group(1)) if m else None


def add_to_board(state, issue_url, stage_name, dry=False, g=None):
    """Add an issue to the project and set its Stage (and Client, on a shared board)."""
    g = g or cfg(state)
    p = g.get("project", {})
    if not p.get("number"):
        return
    item = gh(["project", "item-add", str(p["number"]), "--owner", g["owner"], "--url", issue_url, "--format", "json"], dry, parse=True)
    fields = p.get("fields", {})
    stage = fields.get("Stage", {})
    if not dry and item and stage.get("options", {}).get(stage_name):
        gh(["project", "item-edit", "--id", item["id"], "--project-id", p["id"], "--field-id", stage["id"],
            "--single-select-option-id", stage["options"][stage_name]])
    elif dry:
        gh(["project", "item-edit", "--id", "<item>", "--project-id", "<project>", "--field-id", "<Stage>", "--single-select-option-id", f"<{stage_name}>"], dry)
    client = fields.get("Client")
    if client and not dry and item:
        gh(["project", "item-edit", "--id", item["id"], "--project-id", p["id"], "--field-id", client["id"], "--text", state["client"]])


# ── the gate tracker ───────────────────────────────────────────────────────────────
def tracker_body(root, state, core):
    wf = core.load_workflow(root)
    cur = core.stage_by(wf, state["stage"])
    lines = [f"**{state['client']}**: where the website project stands. Written by `bin/asf github sync` from `asf.json` "
             "and the gate checks; edits here are overwritten. Sign-offs happen with `bin/asf approve`.", "",
             "| Stage | Gate | Status |", "|---|---|---|"]
    for i, s in enumerate(wf["stages"], 1):
        lines.append(f"| {i}. {s['title']} | {s['gate']} | {core.gate_line(state, s, cur['id']).replace('|', '/')} |")
    res = core.evaluate(root, state, cur)
    lines += ["", f"## Now: {cur['title']} ({cur['gate']})", f"_{cur['question']}_", "", "**Automated checks**", ""]
    for r in res:
        box = "x" if r["status"] != "fail" else " "
        extra = f" ({r['detail']})" if r["detail"] and r["status"] == "fail" else (" (skipped: " + r["detail"] + ")" if r["status"] == "skipped" else "")
        lines.append(f"- [{box}] {r['label']}{extra}")
    lines += ["", f"**For a person to confirm** (`bin/asf confirm {cur['gate']} <number> --by \"Name\"`), before the {cur['signs']} signs", ""]
    lines += ["- " + core.manual_line(i) for i in core.manual_items(state, cur)]
    team = [f"- {role}: " + ", ".join(p["name"] + (f" (@{p['github']})" if p.get("github") else "") for p in core.people(state, role))
            for role in wf.get("roles", {}) if core.people(state, role)]
    if team:
        lines += ["", "## Team", ""] + team
    signed = [(s, state["gates"].get(s["gate"])) for s in wf["stages"] if state["gates"].get(s["gate"])]
    if signed:
        lines += ["", "## Sign-offs", ""]
        for s, rec in signed:
            for r in (rec if isinstance(rec, list) else [rec]):
                lines.append(f"- {s['gate']} {s['title']}: {r['by']}, {r['at'][:10]}" + (f": {r['note']}" if r.get("note") else "") + (" (override)" if r.get("override") else ""))
    extra = {k: v for k, v in {"Design review": core.dotted_get(state, "design.review_url") or core.dotted_get(state, "design.figma_url"),
                               "Client review": core.dotted_get(state, "design.client_review"), "Direction chosen": core.dotted_get(state, "design.direction"),
                               "Staging": core.dotted_get(state, "deploy.staging_url"), "Production": core.dotted_get(state, "deploy.production_url")}.items() if v}
    if extra:
        lines += ["", "## Links", ""] + [f"- {k}: {v}" for k, v in extra.items()]
    lines += ["", f"<sub>Last synced {core.now()}</sub>"]
    return "\n".join(lines) + "\n"


def sync(root, state, args, core, quiet=False):
    if not configured(state):
        sys.exit("GitHub isn't set up for this project: `bin/asf github init --repo owner/name` first.")
    g, dry = cfg(state), getattr(args, "dry_run", False)
    wf = core.load_workflow(root)
    if g.get("tracker"):
        gh(["issue", "edit", str(g["tracker"]), "--repo", g["repo"], "--body-file", "-"], dry, stdin=tracker_body(root, state, core))
        # The tracker's card follows the project's current stage. Needs the `project` scope, which the
        # Actions token doesn't have, so a failure here only skips the card move.
        try:
            add_to_board(state, f"https://github.com/{g['repo']}/issues/{g['tracker']}", GATE_STAGE.get(state["stage"], "Requirement"), dry)
        except GhError as e:
            if not quiet:
                print(f"  (tracker card not moved on the board: {str(e)[:120]})")
    for s in wf["stages"]:
        number = (g.get("milestones") or {}).get(s["gate"])
        if not number or s.get("repeat"):
            continue
        want = "closed" if isinstance(state["gates"].get(s["gate"]), dict) else "open"
        gh(["api", "-X", "PATCH", f"repos/{g['repo']}/milestones/{number}", "-f", f"state={want}"], dry, parse=True)
    if not quiet:
        print(f"✓ Synced: tracker #{g.get('tracker')} and {len(g.get('milestones') or {})} milestones" + (" (dry run)" if dry else ""))


def after_approve(root, state, core):
    """Called by `asf approve`, `asf confirm` and `asf team`: mirror the change on GitHub. Never fails the command."""
    if not configured(state):
        return
    try:
        sync(root, state, type("A", (), {"dry_run": False})(), core, quiet=True)
        print("  GitHub: tracker and milestones updated.")
    except (GhError, OSError, subprocess.TimeoutExpired) as e:
        print(f"  GitHub not updated ({e}). Run `bin/asf github sync` when you're online.")


# ── a design review for the client: a PDF in the repo, feedback on one issue ──────────────
def review(root, state, args, core):
    dry = args.dry_run
    if not configured(state) and not dry:
        sys.exit("GitHub isn't set up for this project: `bin/asf github init --repo owner/name` first.")
    if not args.file:
        sys.exit('`bin/asf github review docs/reviews/<name>.pdf [--title "…"] [--ask "…"] [--change <slug>]`')
    pdf = (root / args.file) if not Path(args.file).is_absolute() else Path(args.file)
    if not pdf.exists() or pdf.suffix.lower() != ".pdf":
        sys.exit(f"No PDF at {args.file}. Build it first (docs/framework/prompts/07-design-direction.md E).")
    try:
        rel = pdf.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        sys.exit("The PDF must be inside the project (docs/reviews/), so the client can open it on GitHub.")
    g = cfg(state)
    repo = g.get("repo", "<owner/repo>")
    git = lambda *a: subprocess.run(["git", *a], cwd=root, capture_output=True, text=True)  # noqa: E731
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "main"
    tracked = git("ls-files", "--error-unmatch", rel).returncode == 0
    clean = tracked and not git("status", "--porcelain", "--", rel).stdout.strip()
    ahead = git("log", f"origin/{branch}..HEAD", "--oneline", "--", rel)
    pushed = clean and ahead.returncode == 0 and not ahead.stdout.strip()
    not_there = (f"{rel} " + ("isn't committed yet" if not tracked else "has changes that aren't pushed yet") + f" on `{branch}`")
    if not pushed and not dry:  # the issue notifies the client at once: its link must already work
        sys.exit(f"Not sent: {not_there}. Commit and push the PDF first, so the client's link opens.")
    url = f"https://github.com/{repo}/blob/{urllib.parse.quote(branch)}/{urllib.parse.quote(rel)}"
    title = args.title or f"Design review: {pdf.stem.replace('-', ' ')}"
    ask = (args.ask or "Please look through it and tell us what you think.").strip()
    body = (f"**For your review:** [{pdf.name}]({url}) (open it, then use the download button for the full file)\n\n{ask}\n\n"
            "**How to reply**\n"
            "- Comment on this issue, one point per comment. Every screen in the PDF has a number: say which one you mean.\n"
            "- To approve, or to choose between options, say so here in your own words.\n\n"
            "Each point becomes a tracked item. Nothing changes on the site until it's agreed.\n")
    cmd = ["issue", "create", "--repo", repo, "--title", title, "--body-file", "-", "--label", "review", "--label", "type:design", "--label", "role:client"]
    handle = next((p["github"] for p in core.people(state, "client") if p.get("github")), None)
    try:
        issue = gh(cmd + (["--assignee", handle] if handle else []), dry, stdin=body)
    except GhError as e:
        if not handle:
            raise
        print(f"  (couldn't assign @{handle}: {str(e)[:100]}; filed unassigned)")
        issue = gh(cmd, dry, stdin=body)
    add_to_board(state, issue or "<issue-url>", "Design", dry, g)
    if dry:
        print(body)
        print("Dry run: nothing was created.")
    else:
        if args.change:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import changes  # noqa: E402  (beside this file)
            c = changes.read(root, args.change)
            c["front"]["client_review"] = issue
            changes.write(c)
        else:
            core.dotted_set(state, "design.client_review", issue)
        state["log"].append({"at": core.now(), "event": "design review sent to the client" + (f" (change {args.change})" if args.change else ""), "note": f"{rel} · {issue}"})
        core.save_state(root, state)
        print(f"✓ Review issue: {issue}")
    if not pushed:
        print(f"  Before the real run: {not_there}. Commit and push the PDF first.")


# ── [CONFIRM] chips → issues ────────────────────────────────────────────────────────
def confirm_issues(root, state, args, core):
    if not configured(state) and not args.dry_run:
        sys.exit("GitHub isn't set up for this project: `bin/asf github init --repo owner/name` first.")
    g, dry = cfg(state), args.dry_run
    lint = root / "docs/framework/qa/lint_content.py"
    r = subprocess.run([sys.executable, str(lint), "content", "--list-confirm"], cwd=root, capture_output=True, text=True)
    pages = {}
    for line in r.stdout.splitlines():
        m = re.match(r"^(\S+\.html):\s+(\[CONFIRM.*\])\s*$", line.strip())
        if m:
            pages.setdefault(m.group(1), []).append(m.group(2))
    if not pages:
        print("No [CONFIRM] chips in content/. Nothing to file.")
        return
    repo = g.get("repo", "<owner/repo>")
    open_titles = set()
    if not dry:
        open_titles = {i["title"] for i in gh(["issue", "list", "--repo", repo, "--state", "open", "--label", "type:fact", "--limit", "500", "--json", "title"], parse=True) or []}
    milestone = milestone_title(core.stage_by(core.load_workflow(root), "ship"))  # chips must be gone before G4
    made = 0
    for page, chips in sorted(pages.items()):
        title = f"Facts to confirm: {page.split('/')[-1].removesuffix('.html')}"
        if title in open_titles:
            continue
        body = (f"`content/{page}` shows {len(chips)} `[CONFIRM]` chip(s). Each needs an answer from the client, "
                "with its source added to `docs/truth.md`. Gate G4 can't pass while any are left.\n\n"
                + "\n".join(f"- [ ] {c}" for c in dict.fromkeys(chips)) + "\n")
        url = gh(["issue", "create", "--repo", repo, "--title", title, "--body-file", "-", "--label", "type:fact",
                  "--label", "intake", "--milestone", milestone], dry, stdin=body)
        add_to_board(state, url or "<issue-url>", "Requirement", dry, g)
        made += 1
    print(f"{made} issue(s) {'would be ' if dry else ''}filed for {len(pages)} page(s) with chips.")
