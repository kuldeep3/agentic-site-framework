"""Changes: after launch, every piece of work gets its own small set of gates.

The project's gates (G1–G5) take a site to launch once. After that, a new page, a restyle, a copy
edit or a fix is a *change*: one issue, one branch, one pull request, and the gates that fit its kind
(workflow.json → "change"):

    C1 Brief    what are we changing, and why?     signed by the lead
    C2 Design   how does it look?                  signed by the designer
    C3 Build    is it right?                       signed by QA
    C4 Release  is it live, and safe?              signed by the lead

    bin/asf change new <slug> --title "…" --kind fix|content|page|design|rework [--issue 12] [--pages /pricing/]
        Writes the brief, docs/changes/<slug>.md, and puts the issue's card on the board.
    bin/asf change list [--all]
        Every open change: its gate, who it waits on, how long it's been open.
    bin/asf change check <slug> [C3] [--offline] [--json]
        The gate's automated checks and the items a person confirms (default: the current gate).
        --offline skips the checks that need the running site.
    bin/asf change set <slug> issue|pages|review|client_review|pr|staging|released|result|title|review_after <value>
        review: the team's review page (a Claude artifact). client_review: the client's review issue.
    bin/asf change confirm <slug> C3 [1 2 …] --by "Name"
        One person confirms the items they own (no numbers: list them).
    bin/asf change approve <slug> C3 --by "Name" [--note "…"] [--override "reason"]
        The gate's signer signs it. Refused while checks fail or another owner hasn't confirmed.
    bin/asf change drop <slug> --reason "…"
    bin/asf change board <slug> [--dry-run]
        Puts the change's issue where it now stands: its Stage on the board, its role label, one
        status comment (each gate, who signed, who it waits on) and its assignees. `new`, `confirm`,
        `approve` and `drop` do this too, so nobody has to run a command to see progress.
    bin/asf change pr [--base origin/main]
        For CI: a pull request that changes the site must carry a change whose gates are signed
        up to Build. Before launch it passes: the project's own gates apply.

A change is one file, and its confirmations and sign-offs are lines in each person's own log
(docs/log/). Five changes on five branches never touch the same lines, and the record travels
with the pull request.
"""
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRAMEWORK = HERE.parent
DIR = "docs/changes"
FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)
KEYS = ["issue", "pages", "review", "client_review", "pr", "staging", "released", "result", "title", "review_after", "figma"]
SITE_CODE = ("content/", "wp-content/")  # what a pull request touches when it changes the site
CONFIRM_CHIP = re.compile(r"hm-confirm|\[CONFIRM")


# ── the workflow's "change" section ───────────────────────────────────────────────
def config(root):
    local = root / "docs/framework/orchestrator/workflow.json"
    wf = json.loads((local if local.exists() else HERE / "workflow.json").read_text(encoding="utf-8"))
    cfg = wf.get("change")
    if not cfg:
        sys.exit("This project's workflow.json has no \"change\" section: copy the current orchestrator/ into docs/framework/.")
    return cfg


def gates_for(cfg, kind):
    return [g for g in cfg["gates"] if g["gate"] in cfg["kinds"][kind]]


def gate_by(cfg, c, name):
    for g in gates_for(cfg, c["kind"]):
        if g["gate"].lower() == str(name).lower():
            return g
    sys.exit(f"A {c['kind']} change has gates {', '.join(cfg['kinds'][c['kind']])}, not {name}.")


def applies(item, kind):
    return not isinstance(item, dict) or not item.get("kinds") or kind in item["kinds"]


def manual_of(gate, kind):
    """[(text, role)] for the gate's manual items that apply to this kind of change."""
    out = []
    for m in gate["manual"]:
        if applies(m, kind):
            out.append((m["text"], m.get("role") or gate["signs"]) if isinstance(m, dict) else (m, gate["signs"]))
    return out


# ── one change: its file and its history ────────────────────────────────────────────
def read(root, slug):
    path = root / DIR / f"{slug}.md"
    if not path.exists():
        known = ", ".join(p.stem for p in sorted((root / DIR).glob("*.md"))) or "none yet"
        sys.exit(f"No change \"{slug}\" (changes: {known}). Start one with `bin/asf change new {slug} --title … --kind …`.")
    text = path.read_text(encoding="utf-8")
    m = FRONT.match(text)
    front = {}
    for line in (m.group(1).splitlines() if m else []):
        k, sep, v = line.partition(":")
        if sep:
            v = v.strip()
            try:
                front[k.strip()] = json.loads(v) if v[:1] == '"' else v
            except json.JSONDecodeError:
                front[k.strip()] = v
    return {"slug": slug, "path": path, "front": front, "body": text[m.end():] if m else text,
            "kind": front.get("kind", "fix"), "title": front.get("title") or slug}


def write(c):
    order = ["change", "title", "kind", "issue", "pages", "opened", "assigned", "review", "client_review", "figma", "pr", "staging", "released", "review_after", "result"]
    keys = [k for k in order if k in c["front"]] + [k for k in c["front"] if k not in order]
    lines = [f"{k}: {json.dumps(c['front'][k], ensure_ascii=False) if k in ('title', 'result') else c['front'][k]}" for k in keys]
    c["path"].write_text("---\n" + "\n".join(lines) + "\n---\n" + c["body"], encoding="utf-8")


def slugs(root):
    return [p.stem for p in sorted((root / DIR).glob("*.md"))] if (root / DIR).exists() else []


def events(state, slug):
    return [e for e in state.get("log", []) if isinstance(e.get("change"), dict) and e["change"].get("slug") == slug]


def when(entry):
    try:
        return datetime.datetime.fromisoformat(entry.get("at", ""))
    except (TypeError, ValueError):
        return None


def standing(state, cfg, c):
    """Where a change stands: its signed gates, its current gate, and whether it's open, done or dropped."""
    evs = events(state, c["slug"])
    signed = {e["change"]["gate"]: e for e in evs if e["change"].get("action") == "sign"}
    gates = gates_for(cfg, c["kind"])
    current = next((g for g in gates if g["gate"] not in signed), None)
    dropped = next((e for e in evs if e["change"].get("action") == "drop"), None)
    stamps = [w for w in (when(e) for e in evs) if w]
    return {"signed": signed, "current": current, "gates": gates,
            "status": "dropped" if dropped else "done" if current is None else "open",
            "last": max(stamps) if stamps else None, "opened": c["front"].get("opened", "")}


def manual_items(state, c, gate, core):
    done = {e["change"].get("text"): e for e in events(state, c["slug"])
            if e["change"].get("action") == "confirm" and e["change"].get("gate") == gate["gate"]}
    out = []
    for n, (text, role) in enumerate(manual_of(gate, c["kind"]), 1):
        e = done.get(text)
        out.append({"n": n, "text": text, "role": role, "people": [p["name"] for p in core.people(state, role)],
                    "confirmed_by": e["change"].get("by") if e else None, "confirmed_at": e["at"][:10] if e else None})
    return out


# ── checks ──────────────────────────────────────────────────────────────────────
def pages_of(c):
    return [p.strip() for p in str(c["front"].get("pages") or "").split(",") if p.strip()]


def page_sources(root):
    """{slug: file} for every content file, by the slug in its front matter (the home page is "home")."""
    out = {}
    for folder in ("content/pages", "content/work"):
        for f in sorted((root / folder).glob("*.html")):
            m = re.search(r"^slug:\s*(\S+)", f.read_text(encoding="utf-8")[:800], re.M)
            if m:
                out[m.group(1).strip("/")] = f
    return out


def check_pages(root, c):
    pages = pages_of(c)
    if not pages:
        return False, f"no pages named (`bin/asf change set {c['slug']} pages /…/`)"
    sources = page_sources(root)
    found = {p: sources.get(p.strip("/") or "home") for p in pages}
    if c["kind"] in ("page", "rework") and not any(found.values()):
        return False, f"no source file in content/ for {', '.join(pages[:3])}"
    chips = [f.relative_to(root).as_posix() for f in found.values() if f and CONFIRM_CHIP.search(f.read_text(encoding="utf-8"))]
    return not chips, f"[CONFIRM] left in {', '.join(chips[:3])}" if chips else f"{sum(1 for f in found.values() if f)} source file(s), no chips"


def check_urls(root, state, c, check):
    pages = pages_of(c)
    if not pages:
        return False, f"no pages named (`bin/asf change set {c['slug']} pages /…/`)"
    dep = state.get("deploy", {})
    if check.get("env") == "production":
        base = dep.get("production_url")
        if not base:
            return False, "needs `asf set deploy.production_url …` first"
    else:
        base = dep.get("staging_url") or state.get("site_url")
        if not base:
            return False, "needs `asf set deploy.staging_url …` (or a local site_url) first"
    base = base.rstrip("/")
    sys.path.insert(0, str(FRAMEWORK / "qa"))
    import launch  # noqa: E402
    http = launch.Http(insecure=launch.detect_env(base) == "local")
    for p in pages:
        r = http.get(base + p, cache=False)
        if r.status != 200:
            return False, f"{base + p} returns HTTP {r.status or 'no answer'}"
    try:
        run = subprocess.run([sys.executable, str(FRAMEWORK / "qa/launch.py"), base, "--pages", ",".join(pages),
                              "--only", "accessibility,performance", "--json", "-"], cwd=root, capture_output=True, text=True, timeout=600)
        res = json.loads(run.stdout)
        errs = [f"{g}: {f['message']}" for g, grp in res["groups"].items() for f in grp["findings"] if f["level"] == "error"]
    except (subprocess.TimeoutExpired, ValueError, KeyError) as e:
        return False, f"the page scan didn't run: {str(e)[:80]}"
    return not errs, " · ".join(errs[:2])[:200] if errs else f"{len(pages)} page(s) on {base}"


def run_checks(root, state, c, gate, core, offline=False):
    rel = c["path"].relative_to(root).as_posix()
    fill = lambda v: v.replace("{change.file}", rel).replace("{change.slug}", c["slug"]) if isinstance(v, str) else v  # noqa: E731
    results = []
    for raw in gate["checks"]:
        if not applies(raw, c["kind"]):
            continue
        check = {k: fill(v) for k, v in raw.items()}
        t = check["type"]
        if t == "change_urls" and offline:
            results.append({**check, "status": "skipped", "detail": "needs the running site"})
            continue
        if t == "front_set":
            v = next((c["front"].get(k) for k in (check.get("keys") or [check["key"]]) if c["front"].get(k)), None)
            ok, detail = bool(v), str(v) if v else "not recorded"
        elif t == "change_pages":
            ok, detail = check_pages(root, c)
        elif t == "change_urls":
            ok, detail = check_urls(root, state, c, check)
        else:
            ok, detail = core.run_check(root, state, check)
        results.append({**check, "status": "pass" if ok else "fail", "detail": detail})
    return results


# ── commands ──────────────────────────────────────────────────────────────────────
def new(root, state, a, core):
    cfg = config(root)
    slug = a.rest[0] if a.rest else ""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,60}", slug):
        sys.exit('`bin/asf change new <slug> --title "…" --kind …` (slug: lowercase letters, numbers and hyphens)')
    if a.kind not in cfg["kinds"]:
        sys.exit("--kind is one of:\n" + "\n".join(f"  {k:<8} {cfg['kind_help'].get(k, '')}  ({', '.join(g)})" for k, g in cfg["kinds"].items()))
    if not a.title:
        sys.exit('--title "…" is required.')
    path = root / DIR / f"{slug}.md"
    if path.exists():
        sys.exit(f"{DIR}/{slug}.md already exists.")
    body = (FRAMEWORK / "templates/change-brief.md").read_text(encoding="utf-8").replace("# Change: [title]", f"# Change: {a.title}").replace("[slug]", slug)
    front = {"change": slug, "title": a.title, "kind": a.kind, "issue": (a.issue or "").lstrip("#"), "pages": a.pages or "",
             "opened": core.now()[:10], "review_after": cfg.get("review_after_days", 28)}
    c = {"slug": slug, "path": path, "front": front, "body": "\n" + body, "kind": a.kind, "title": a.title}
    path.parent.mkdir(parents=True, exist_ok=True)
    write(c)
    state["log"].append({"at": core.now(), "event": f"change {slug} opened ({a.kind})", "note": a.title,
                         "change": {"slug": slug, "action": "open", "kind": a.kind}})
    core.save_state(root, state)
    gates = gates_for(cfg, a.kind)
    print(f"✓ {DIR}/{slug}.md · {a.kind}: " + " → ".join(f"{g['gate']} {g['title']}" for g in gates))
    if state.get("stage") != "run":
        print("  Note: this project hasn't launched yet (G4 isn't signed): its own gates still apply to the whole site.")
    board(root, state, c, core, quiet=True)
    print(f"Next: `bin/asf change check {slug}` shows what {gates[0]['gate']} {gates[0]['title']} needs.")


def set_value(root, state, a, core):
    if len(a.rest) < 3 or a.rest[1] not in KEYS:
        sys.exit(f"`bin/asf change set <slug> <{'|'.join(KEYS)}> <value>`")
    c = read(root, a.rest[0])
    key, value = a.rest[1], " ".join(a.rest[2:])
    c["front"][key] = value.lstrip("#") if key == "issue" else value
    write(c)
    state["log"].append({"at": core.now(), "event": f"change {c['slug']}: {key} set", "note": value,
                         "change": {"slug": c["slug"], "action": "set", "key": key}})
    core.save_state(root, state)
    print(f"{c['slug']}: {key} = {value}")


def waiting_on(state, c, st, core):
    """Who a change waits on: the owners with unconfirmed items, else the gate's signer."""
    g = st["current"]
    if not g:
        return ""
    roles = list(dict.fromkeys(i["role"] for i in manual_items(state, c, g, core) if not i["confirmed_by"])) or [g["signs"]]
    return "; ".join(r + (": " + ", ".join(p["name"] for p in core.people(state, r)) if core.people(state, r) else "") for r in roles)


def age(st):
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(st["opened"])).days
    except ValueError:
        return 0


def listing(root, state, a, core):
    cfg = config(root)
    rows = []
    for slug in slugs(root):
        c = read(root, slug)
        st = standing(state, cfg, c)
        if st["status"] != "open" and not a.all:
            continue
        gate = f"{st['current']['gate']} {st['current']['title']}" if st["status"] == "open" else st["status"]
        rows.append((slug, c["kind"], gate, waiting_on(state, c, st, core) if st["status"] == "open" else "", f"{age(st)}d",
                     ("#" + str(c["front"]["issue"])) if str(c["front"].get("issue", "")).isdigit() else ""))
    if not rows:
        print("No open changes." if not a.all else "No changes yet.")
        return
    print(f"{'Change':<26} {'Kind':<8} {'Gate':<12} {'Waiting on':<34} {'Open':<5} Issue")
    for r in rows:
        print(f"{r[0]:<26.26} {r[1]:<8} {r[2]:<12} {r[3]:<34.34} {r[4]:<5} {r[5]}")


def check(root, state, a, core):
    cfg = config(root)
    if not a.rest:
        sys.exit("`bin/asf change check <slug> [C3]`")
    c = read(root, a.rest[0])
    st = standing(state, cfg, c)
    gate = gate_by(cfg, c, a.rest[1]) if len(a.rest) > 1 else st["current"] if st["status"] == "open" else None
    if gate is None:
        print(f"{c['slug']}: {st['status']}. Every gate is signed." if st["status"] == "done" else f"{c['slug']}: {st['status']}.")
        return
    res = run_checks(root, state, c, gate, core, a.offline)
    items = manual_items(state, c, gate, core)
    if a.json:
        print(json.dumps({"change": c["slug"], "title": c["title"], "kind": c["kind"], "status": st["status"], "gate": gate["gate"],
                          "gate_title": gate["title"], "question": gate["question"], "signed": sorted(st["signed"]),
                          "gates": [g["gate"] for g in st["gates"]], "file": c["path"].relative_to(root).as_posix(),
                          "checks": res, "manual_items": items,
                          "signs": {"role": gate["signs"], "people": [p["name"] for p in core.people(state, gate["signs"])]},
                          "ready_for_signoff": all(r["status"] != "fail" for r in res)}, indent=2, ensure_ascii=False))
        return
    trail = " → ".join(("✓ " if g["gate"] in st["signed"] else "") + f"{g['gate']} {g['title']}" for g in st["gates"])
    print(f"{c['title']} ({c['slug']}, {c['kind']}): {trail}")
    print(f"Gate {gate['gate']} ({gate['title']}): {gate['question']}")
    if gate.get("why"):
        print(f"Why this gate: {gate['why']}")
    for r in res:
        mark = {"pass": "✓", "fail": "✗", "skipped": "–"}[r["status"]]
        print(f"  {mark} {r['label']}" + (f"  ({r['detail']})" if r["detail"] and r["status"] != "pass" else ""))
        if r["status"] == "fail":
            print(f"      → {r['hint']}")
    print(f"For a person to confirm (`asf change confirm {c['slug']} {gate['gate']} <number> --by \"Name\"`), before the {gate['signs']} signs:")
    for item in items:
        print(f"  {core.manual_line(item)}")
    sys.exit(0 if all(r["status"] != "fail" for r in res) else 1)


def confirm(root, state, a, core):
    cfg = config(root)
    if len(a.rest) < 2:
        sys.exit('`bin/asf change confirm <slug> C3 [1 2 …] --by "Name"`')
    c = read(root, a.rest[0])
    gate = gate_by(cfg, c, a.rest[1])
    items = manual_items(state, c, gate, core)
    numbers = a.rest[2:]
    if not numbers:
        for item in items:
            print(f"  {core.manual_line(item)}")
        return
    if not a.by:
        sys.exit('--by "Name" is required: a confirmation is one person\'s word.')
    if not all(n.isdigit() and 1 <= int(n) <= len(items) for n in numbers):
        sys.exit(f"{gate['gate']} has items 1 to {len(items)} for a {c['kind']} change (`asf change confirm {c['slug']} {gate['gate']}` lists them).")
    for n in map(int, numbers):
        item = items[n - 1]
        if item["people"] and a.by.lower() not in [p.lower() for p in item["people"]]:
            print(f"  Note: item {n} is the {item['role']}'s ({', '.join(item['people'])}); recorded as confirmed by {a.by}.")
        state["log"].append({"at": core.now(), "event": f"change {c['slug']}: {gate['gate']} item {n} confirmed by {a.by}", "note": a.note or item["text"],
                             "change": {"slug": c["slug"], "action": "confirm", "gate": gate["gate"], "text": item["text"], "by": a.by}})
        print(f"✓ {c['slug']} {gate['gate']} item {n} confirmed by {a.by}: {item['text']}")
    core.save_state(root, state)
    board(root, state, c, core, quiet=True)


def approve(root, state, a, core):
    cfg = config(root)
    if len(a.rest) < 2 or not a.by:
        sys.exit('`bin/asf change approve <slug> C3 --by "Name"`')
    c = read(root, a.rest[0])
    st = standing(state, cfg, c)
    gate = gate_by(cfg, c, a.rest[1])
    if st["status"] != "open":
        sys.exit(f"{c['slug']} is {st['status']}.")
    if gate["gate"] != st["current"]["gate"]:
        sys.exit(f"{gate['gate']} isn't this change's current gate (it's at {st['current']['gate']} {st['current']['title']}).")
    failing = [r for r in run_checks(root, state, c, gate, core) if r["status"] == "fail"]
    if failing and not a.override:
        print(f"Not signed: {len(failing)} automated check(s) fail:")
        for r in failing:
            print(f"  ✗ {r['label']}" + (f" ({r['detail']})" if r["detail"] else ""))
        if gate.get("why"):
            print(f"Why this gate: {gate['why']}")
        sys.exit("Fix them, or sign with --override \"reason\" (recorded in the log).")
    items = manual_items(state, c, gate, core)
    mine = core.roles_of(state, a.by) | {gate["signs"]}
    waiting = [i for i in items if i["people"] and not i["confirmed_by"] and i["role"] not in mine]
    if waiting and not a.override:
        print(f"Not signed: {len(waiting)} item(s) are waiting for the person who owns them:")
        for i in waiting:
            print(f"  {core.manual_line(i)}")
        sys.exit(f"They confirm with `asf change confirm {c['slug']} {gate['gate']} <number> --by \"Name\"`, or sign with --override \"reason\".")
    signers = [p["name"] for p in core.people(state, gate["signs"])]
    if signers and a.by.lower() not in [n.lower() for n in signers]:
        print(f"  Note: {gate['gate']} is the {gate['signs']}'s to sign ({', '.join(signers)}); recorded as signed by {a.by}.")
    record = {"slug": c["slug"], "action": "sign", "gate": gate["gate"], "by": a.by, "manual_confirmed": [i["text"] for i in items]}
    if failing or waiting:
        record["override"] = a.override
        record["failing"] = [r["id"] for r in failing]
        record["unconfirmed"] = [i["text"] for i in waiting]
    state["log"].append({"at": core.now(), "event": f"change {c['slug']}: {gate['gate']} {gate['title']} signed by {a.by}" + (" (override)" if failing or waiting else ""),
                         "note": a.note or a.override or "", "change": record})
    core.save_state(root, state)
    after = standing(state, cfg, c)
    if after["status"] == "done":
        print(f"✓ {c['slug']}: {gate['gate']} ({gate['title']}) signed by {a.by}. The change is done."
              f" The weekly report will ask what it moved in {c['front'].get('review_after', cfg.get('review_after_days', 28))} days.")
    else:
        nxt = after["current"]
        print(f"✓ {c['slug']}: {gate['gate']} ({gate['title']}) signed by {a.by}. Now: {nxt['gate']} {nxt['title']} ({waiting_on(state, c, after, core)}).")
        if gate["gate"] == cfg.get("merge_after"):
            print("  The pull request can be merged now; release follows the merge.")
    board(root, state, c, core, quiet=True)


def drop(root, state, a, core):
    if not a.rest or not a.reason:
        sys.exit('`bin/asf change drop <slug> --reason "…"`')
    c = read(root, a.rest[0])
    state["log"].append({"at": core.now(), "event": f"change {c['slug']} dropped", "note": a.reason, "change": {"slug": c["slug"], "action": "drop"}})
    core.save_state(root, state)
    print(f"– {c['slug']} dropped: {a.reason}")
    board(root, state, c, core, quiet=True)


def board(root, state, c, core, dry=False, quiet=False):
    """Put the change's issue where the change stands: its Stage on the board, and the label of who acts next."""
    import github_board as gb  # noqa: E402  (beside this file)
    issue = str(c["front"].get("issue") or "")
    if not (gb.configured(state) or dry) or not issue:
        if not quiet:
            print("Nothing to move: " + ("no issue is linked to this change." if not issue else "GitHub isn't set up (`bin/asf github init`)."))
        return
    g = gb.cfg(state)
    repo = g.get("repo", "<owner/repo>")
    st = standing(state, config(root), c)
    stage = st["current"]["board"] if st["status"] == "open" else "Done"
    role = None
    if st["status"] == "open":  # the label names who acts next: an owner with an open item, else the signer
        role = next((i["role"] for i in manual_items(state, c, st["current"], core) if not i["confirmed_by"]), st["current"]["signs"])
    url = issue if issue.startswith("http") else f"https://github.com/{repo}/issues/{issue}"
    number = str(gb.issue_number(url) or issue)
    try:
        gb.add_to_board(state, url, stage, dry)
        edit = ["issue", "edit", number, "--repo", repo]
        for r in gb.ROLES:
            edit += ["--add-label" if r == role else "--remove-label", f"role:{r}"]
        gb.gh(edit, dry)
        who = issue_status(root, state, c, st, core, gb, repo, number, dry)
        if not quiet or dry:
            print(f"✓ #{number}: {stage}" + (f", role:{role}" if role else "") + (f", assigned to {', '.join(who)}" if who else "") + (" (dry run)" if dry else ""))
    except (gb.GhError, OSError, subprocess.TimeoutExpired) as e:
        print(f"  GitHub not updated ({str(e)[:120]}). Run `bin/asf change board {c['slug']}` when you're online.")


def status_comment(state, c, st, core, plain):
    """The change's standing, for its issue: each gate, who signed it, and who it waits on now.
    `plain` (a repository the client can open) leaves out item wording, which can name private files."""
    lines = [f"<!-- change-status: {c['slug']} -->", f"**Where this stands** (updated automatically; {core.now()[:10]})", "",
             "| Step | Status |", "|---|---|"]
    for g in st["gates"]:
        e = st["signed"].get(g["gate"])
        if e:
            status = f"Signed by {e['change'].get('by', '')}, {e['at'][:10]}"
        elif st["status"] == "dropped":
            status = "Dropped"
        elif st["current"] and g["gate"] == st["current"]["gate"]:
            items = manual_items(state, c, g, core)
            done = sum(1 for i in items if i["confirmed_by"])
            status = f"**In progress**: {done} of {len(items)} confirmed. Waiting on {waiting_on(state, c, st, core)}"
        else:
            status = "Not started"
        lines.append(f"| {g['title']} | {status} |")
    cur = st["current"] if st["status"] == "open" else None
    if cur and not plain:
        lines += ["", f"**{cur['title']}: to confirm**", ""] + ["- " + core.manual_line(i) for i in manual_items(state, c, cur, core)]
    elif cur:
        got = [f"{i['confirmed_by']} ({i['role']})" for i in manual_items(state, c, cur, core) if i["confirmed_by"]]
        if got:
            lines += ["", "Confirmed so far: " + ", ".join(dict.fromkeys(got)) + "."]
    return "\n".join(lines) + "\n"


def issue_status(root, state, c, st, core, gb, repo, number, dry):
    """Keep one status comment on the change's issue, and assign the issue to whoever it waits on."""
    g = gb.cfg(state)
    body = status_comment(state, c, st, core, bool(g.get("client_visible")))
    marker = f"<!-- change-status: {c['slug']} -->"
    existing = None
    if not dry:
        for cm in gb.gh(["api", f"repos/{repo}/issues/{number}/comments?per_page=100"], parse=True) or []:
            if marker in (cm.get("body") or ""):
                existing = cm["id"]
    if existing:
        gb.gh(["api", "-X", "PATCH", f"repos/{repo}/issues/comments/{existing}", "-F", "body=@-"], dry, stdin=body, parse=True)
    else:
        gb.gh(["issue", "comment", number, "--repo", repo, "--body-file", "-"], dry, stdin=body)
    # Assign it to whoever acts next. Only people this tool assigned earlier are ever removed.
    want = []
    if st["status"] == "open":
        roles = list(dict.fromkeys(i["role"] for i in manual_items(state, c, st["current"], core) if not i["confirmed_by"])) or [st["current"]["signs"]]
        want = list(dict.fromkeys(p["github"] for r in roles for p in core.people(state, r) if p.get("github")))
    mine = [h for h in str(c["front"].get("assigned") or "").split(",") if h]
    drop = [h for h in mine if h not in want]
    if want or drop:
        edit = ["issue", "edit", number, "--repo", repo]
        if want:
            edit += ["--add-assignee", ",".join(want)]
        if drop:
            edit += ["--remove-assignee", ",".join(drop)]
        try:
            gb.gh(edit, dry)
        except gb.GhError as e:  # someone who can't be assigned there mustn't stop the rest
            print(f"  (assignees not changed: {str(e)[:110]})")
            want = mine
    if not dry and ",".join(want) != ",".join(mine):
        c["front"]["assigned"] = ",".join(want)
        write(c)
    return want


def pr_check(root, state, a, core):
    """For CI. Exit 1 when a pull request changes the site without a change record signed up to Build."""
    cfg = config(root)
    if state.get("stage") != "run":
        print("The project hasn't launched yet: its own gates (G1–G4) apply, not per-change gates.")
        return
    base = a.base or "origin/main"
    r = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"Couldn't compare with {base}: {r.stderr.strip()[:200]}")
    files = [f for f in r.stdout.splitlines() if f.strip()]
    site = [f for f in files if f.startswith(SITE_CODE)]
    touched = [Path(f).stem for f in files if f.startswith(DIR + "/") and f.endswith(".md") and (root / f).exists()]
    if not site:
        print("This pull request doesn't change the site (nothing under content/ or wp-content/).")
        return
    if not touched:
        sys.exit(f"✗ {len(site)} site file(s) changed (e.g. {site[0]}) but no change carries them.\n"
                 f"  Start one on this branch: `bin/asf change new <slug> --title \"…\" --kind fix|content|page|design|rework --issue <n>`")
    need_upto = cfg.get("merge_after", "C3")
    bad = 0
    for slug in touched:
        c = read(root, slug)
        st = standing(state, cfg, c)
        if st["status"] == "dropped":
            continue
        names = [g["gate"] for g in st["gates"]]
        upto = names[: names.index(need_upto) + 1] if need_upto in names else names
        missing = [g for g in upto if g not in st["signed"]]
        if missing:
            bad += 1
            print(f"✗ {slug} ({c['kind']}): not signed yet: {', '.join(missing)}  (`bin/asf change check {slug}`)")
        else:
            print(f"✓ {slug} ({c['kind']}): signed up to {need_upto}; ready to merge")
    sys.exit(1 if bad else 0)


# ── the weekly gate and the weekly report ─────────────────────────────────────────────
def gate(root, state, core):
    """G5: no open change idle for `stale_days`; none signed at Build and unreleased for `release_days`."""
    if not slugs(root):
        return True, "no changes yet"
    cfg = config(root)
    now = datetime.datetime.now().astimezone()
    problems, n_open = [], 0
    for slug in slugs(root):
        c = read(root, slug)
        st = standing(state, cfg, c)
        if st["status"] != "open":
            continue
        n_open += 1
        built = st["signed"].get(cfg.get("merge_after", "C3"))
        if built and when(built) and (now - when(built)).days > cfg.get("release_days", 7):
            problems.append(f"{slug}: built {(now - when(built)).days} days ago, not released")
        elif st["last"] and (now - st["last"]).days > cfg.get("stale_days", 14):
            problems.append(f"{slug}: nothing for {(now - st['last']).days} days at {st['current']['gate']} {st['current']['title']}")
    if problems:
        return False, "; ".join(problems[:3])
    return True, f"{n_open} open change(s), none stuck"


def should_move(c):
    """The first real line under "What it should move" in the brief."""
    m = re.search(r"^## What it should move\s*\n(.*?)(?=^## |\Z)", c["body"], re.S | re.M)
    for line in (m.group(1).splitlines() if m else []):
        line = line.strip()
        if line and not line.startswith("*") and not (line.startswith("[") and line.endswith("]")):
            return line[:160]
    return ""


def weekly(root, state, rng):
    """For the weekly report: what shipped this week, what's in progress, and what's due a look."""
    if not slugs(root):
        return {"shipped": [], "open": [], "follow_up": []}
    cfg = config(root)
    frm, to = datetime.date.fromisoformat(rng[0]), datetime.date.fromisoformat(rng[1])
    out = {"shipped": [], "open": [], "follow_up": []}
    last_gate = lambda st: st["signed"].get(st["gates"][-1]["gate"])  # noqa: E731
    for slug in slugs(root):
        c = read(root, slug)
        st = standing(state, cfg, c)
        row = {"change": slug, "title": c["title"], "kind": c["kind"], "pages": c["front"].get("pages", ""), "should_move": should_move(c)}
        if st["status"] == "open":
            out["open"].append({**row, "gate": f"{st['current']['gate']} {st['current']['title']}", "days_open": age(st)})
        elif st["status"] == "done" and when(last_gate(st)):
            done = when(last_gate(st)).date()
            if frm <= done <= to:
                out["shipped"].append({**row, "released": done.isoformat()})
            try:
                due = done + datetime.timedelta(days=int(c["front"].get("review_after") or cfg.get("review_after_days", 28)))
            except ValueError:
                due = done + datetime.timedelta(days=28)
            if due <= to and not c["front"].get("result"):
                out["follow_up"].append({**row, "released": done.isoformat(), "due": due.isoformat()})
    return out


def main(root, state, a, core):
    actions = {"new": new, "set": set_value, "list": listing, "check": check, "status": check, "confirm": confirm,
               "approve": approve, "drop": drop, "pr": pr_check}
    if a.action == "board":
        if not a.rest:
            sys.exit("`bin/asf change board <slug> [--dry-run]`")
        board(root, state, read(root, a.rest[0]), core, dry=a.dry_run)
        return
    actions[a.action](root, state, a, core)
