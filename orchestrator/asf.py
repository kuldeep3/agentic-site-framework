#!/usr/bin/env python3
"""asf: the Agentic Site Framework orchestrator for one client project.

    bin/asf status              where the project is, gate by gate
    bin/asf next  [--json]      the one thing to do next (what the /asf command acts on)
    bin/asf check [G1..G5]      run a gate's automated checks (default: the current gate)
    bin/asf approve G1 --by "Name" [--note "…"] [--override "reason"]
                                record a human sign-off; refused while automated checks fail
    bin/asf skip G1 audit --reason "no current site"
    bin/asf set deploy.staging_url https://staging.example.com
    bin/asf set --local site_url http://acme.test
                                a value for this machine only (asf.local.json, git-ignored)
    bin/asf team [add|remove <role> "Name" [--github handle]]
                                who holds each role: lead, designer, developer, content, qa, client
    bin/asf confirm G3 2 --by "Name"
                                one person confirms the gate items they own, before the lead signs
    bin/asf report [--to 2026-11-15] [--no-crawl]
                                collect the week's numbers and draft docs/reports/<date>.md
    bin/asf campaign new|links|check|list|report|close …
                                one offer, one landing page, tagged links, results (see campaigns.py)
    bin/asf change new|list|check|set|confirm|approve|drop|board|pr …
                                after launch: one change, one issue, one pull request, its own gates C1–C4 (see changes.py)
    bin/asf intake sources|add|done|list
                                requirements from email, calls, issues and docs, one tracked item each (see intake.py)
    bin/asf github init|sync|confirm-issues [--dry-run]
                                labels, gate milestones, a Projects board and a gate tracker issue (see github_board.py)
    bin/asf log                 every sign-off, confirmation, skip and setting, with who and when
    bin/asf init --name "Acme" --kind agency --site-url http://acme.test   (the starter runs this)

State lives in asf.json at the project root, and the audit trail in docs/log/, one file per person
(commit both). Stages, gates, roles and checks come from workflow.json. Standard library only.
"""
import argparse
import datetime
import glob as globlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE_FILE = "asf.json"
LOCAL_FILE = "asf.local.json"   # this machine only (git-ignored): `asf set --local site_url …`
LOG_DIR = "docs/log"            # the audit trail: one append-only .jsonl per person, so branches never conflict
LOG_EARLIER = "0-earlier.jsonl"  # entries that were in asf.json before the log moved here
_LOADED = {}                    # root → what load_state read, so save_state writes only what changed
# An unfilled template placeholder: [like this]. Not a checkbox, a link, or a [CONFIRM: …] chip.
PLACEHOLDER = re.compile(r"\[(?!\s\]|[xX]\]|CONFIRM)([^\]\n]{1,200})\](?!\()")
HEADING = re.compile(r"^(#{1,4})\s+(.*)$", re.M)


# ── state ──────────────────────────────────────────────────────────────────────
def find_root():
    here = Path.cwd().resolve()
    for d in (here, *here.parents):
        if (d / STATE_FILE).exists():
            return d
    sys.exit(f"No {STATE_FILE} here or above. Run `asf init` in the project root (the starter does this).")


def actor():
    """Who is running this command: ASF_USER, else git's user.name, else the login name."""
    who = os.environ.get("ASF_USER", "").strip()
    if not who:
        try:
            who = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, timeout=5).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            who = ""
    return who or os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"


def _flat(data, prefix=""):
    for k, v in data.items():
        if isinstance(v, dict):
            yield from _flat(v, f"{prefix}{k}.")
        else:
            yield prefix + k, v


def _when(entry):
    try:
        return datetime.datetime.fromisoformat(entry.get("at", "")).timestamp()
    except (TypeError, ValueError):
        return 0.0


def load_log(root):
    """Every entry in docs/log/*.jsonl. A line git or a person mangled is skipped, never fatal."""
    entries = []
    for f in sorted((root / LOG_DIR).glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(e, dict):
                entries.append(e)
    return entries


def load_state(root):
    """asf.json, plus the log from docs/log/ and this machine's asf.local.json laid over it.

    The log is one append-only file per person, so two people on two branches never touch the same
    lines. asf.local.json holds what differs per machine (a local site address); it's git-ignored
    and save_state never copies its values into asf.json.
    """
    state = json.loads((root / STATE_FILE).read_text(encoding="utf-8"))
    legacy = state.pop("log", None) or []  # projects made before the log moved to docs/log/
    log = sorted(legacy + load_log(root), key=_when)
    local, under = {}, {}
    if (root / LOCAL_FILE).exists():
        local = dict(_flat(json.loads((root / LOCAL_FILE).read_text(encoding="utf-8"))))
        for key, value in local.items():
            under[key] = dotted_get(state, key)
            dotted_set(state, key, value)
    state["log"] = log
    _LOADED[str(root)] = {"n": len(log), "legacy": legacy, "local": local, "under": under}
    return state


def save_state(root, state):
    info = _LOADED.get(str(root)) or {"n": 0, "legacy": [], "local": {}, "under": {}}
    log = state.get("log", [])
    out = json.loads(json.dumps({k: v for k, v in state.items() if k != "log"}))
    for key, value in info["local"].items():  # this machine's values stay in asf.local.json
        if dotted_get(out, key) == value:
            dotted_set(out, key, info["under"][key]) if info["under"][key] is not None else dotted_del(out, key)
    (root / STATE_FILE).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    logdir = root / LOG_DIR
    new = log[info["n"]:]
    if info["legacy"] and not (logdir / LOG_EARLIER).exists():
        logdir.mkdir(parents=True, exist_ok=True)
        (logdir / LOG_EARLIER).write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in info["legacy"]), encoding="utf-8")
    if new:
        who = actor()
        logdir.mkdir(parents=True, exist_ok=True)
        name = re.sub(r"[^a-z0-9]+", "-", who.lower()).strip("-") or "unknown"
        with open(logdir / f"{name}.jsonl", "a", encoding="utf-8") as f:
            for e in new:
                e.setdefault("by", who)
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    _LOADED[str(root)] = {**info, "n": len(log), "legacy": []}


def load_workflow(root):
    """workflow.json, with every manual item split into its text (`manual`) and who confirms it (`manual_roles`)."""
    local = root / "docs/framework/orchestrator/workflow.json"
    wf = json.loads((local if local.exists() else HERE / "workflow.json").read_text(encoding="utf-8"))
    for s in wf["stages"]:
        s.setdefault("signs", "lead")
        items = [m if isinstance(m, dict) else {"text": m} for m in s["manual"]]
        s["manual"] = [m["text"] for m in items]
        s["manual_roles"] = [m.get("role") or s["signs"] for m in items]
    return wf


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="minutes")


def dotted_del(data, key):
    parts = key.split(".")
    for part in parts[:-1]:
        data = data.get(part)
        if not isinstance(data, dict):
            return
    data.pop(parts[-1], None)


def dotted_get(data, key):
    for part in key.split("."):
        if not isinstance(data, dict) or part not in data:
            return None
        data = data[part]
    return data


def dotted_set(data, key, value):
    parts = key.split(".")
    for part in parts[:-1]:
        data = data.setdefault(part, {})
    data[parts[-1]] = value


def stage_by(workflow, key):
    for s in workflow["stages"]:
        if key in (s["id"], s["gate"], s["gate"].lower()):
            return s
    sys.exit(f"Unknown stage or gate: {key}")


# ── team: who holds each role, and what each person has confirmed ─────────────────────
def people(state, role):
    return [p for p in (state.get("team") or {}).get(role, []) if p.get("name")]


def roles_of(state, name):
    return {role for role in (state.get("team") or {}) if any(p["name"].lower() == name.lower() for p in people(state, role))}


def confirmations(state, stage):
    """{item number: log entry} for the gate's manual items confirmed with `asf confirm` since the gate
    was last signed. An item whose wording has changed since doesn't count."""
    rec = state["gates"].get(stage["gate"])
    last = rec[-1] if isinstance(rec, list) and rec else rec if isinstance(rec, dict) else None
    since = _when(last) if last else -1.0
    out = {}
    for e in state.get("log", []):
        c = e.get("confirm")
        if isinstance(c, dict) and c.get("gate") == stage["gate"] and _when(e) > since:
            n = c.get("n")
            if isinstance(n, int) and 1 <= n <= len(stage["manual"]) and stage["manual"][n - 1] == c.get("text"):
                out[n] = e
    return out


def manual_items(state, stage):
    """The gate's manual items with the role that confirms each, who holds it, and who has confirmed."""
    done = confirmations(state, stage)
    out = []
    for n, (text, role) in enumerate(zip(stage["manual"], stage["manual_roles"]), 1):
        e = done.get(n)
        out.append({"n": n, "text": text, "role": role, "people": [p["name"] for p in people(state, role)],
                    "confirmed_by": e["confirm"].get("by") if e else None, "confirmed_at": e["at"][:10] if e else None})
    return out


def manual_line(item):
    who = item["role"] + (": " + ", ".join(item["people"]) if item["people"] else "")
    done = f" · confirmed by {item['confirmed_by']}, {item['confirmed_at']}" if item["confirmed_by"] else ""
    return f"[{'x' if item['confirmed_by'] else ' '}] {item['n']}. {item['text']}  ({who}{done})"


# ── markdown helpers ────────────────────────────────────────────────────────────
def section(text, name):
    """Body under the first heading containing `name` (case-insensitive), up to the next heading of the same or higher level."""
    for m in HEADING.finditer(text):
        if name.lower() in m.group(2).lower():
            level = len(m.group(1))
            rest = text[m.end():]
            for n in HEADING.finditer(rest):
                if len(n.group(1)) <= level:
                    return rest[: n.start()]
            return rest
    return None


def table_rows(body):
    rows = [ln.strip() for ln in body.splitlines() if ln.strip().startswith("|")]
    rows = [r for r in rows if not re.fullmatch(r"\|[\s:|-]+\|?", r)]  # drop separators
    return rows[1:]  # drop the header row


def filled_row(row):
    cells = [c.strip() for c in row.strip("|").split("|")]
    return not PLACEHOLDER.search(row) and sum(1 for c in cells if c) >= 2


# ── checks ──────────────────────────────────────────────────────────────────────
def run_check(root, state, check):
    """Return (passed: bool, detail: str)."""
    t = check["type"]
    if t in ("no_placeholders", "section_filled", "table_rows", "media_mapped", "ia_pages"):
        path = root / check["path"]
        if not path.exists():
            return False, f"{check['path']} doesn't exist yet"
        text = path.read_text(encoding="utf-8")
    if t == "file_exists":
        ok = (root / check["path"]).exists()
        return ok, "" if ok else f"{check['path']} doesn't exist yet"
    if t == "no_placeholders":
        left = PLACEHOLDER.findall(text)
        return not left, "" if not left else f"{len(left)} unfilled, e.g. [{left[0][:60]}]"
    if t == "section_filled":
        body = section(text, check["section"])
        if body is None:
            return False, f"no section matching \"{check['section']}\""
        lines = [ln for ln in body.splitlines() if ln.strip() and not ln.strip().startswith("*")]
        content = " ".join(lines)
        if PLACEHOLDER.search(content):
            return False, "still has template [placeholders]"
        return len(re.sub(r"[^A-Za-z]", "", content)) >= 30, "" if content else "empty"
    if t == "table_rows":
        body = section(text, check["section"])
        if body is None:
            return False, f"no section matching \"{check['section']}\""
        n = sum(1 for r in table_rows(body) if filled_row(r))
        return n >= check["min"], f"{n} of {check['min']} rows filled"
    if t == "media_mapped":
        media = [p.name for p in (root / "content/media").glob("*") if p.is_file() and not p.name.startswith(".") and p.name != "replace-hero.png"]
        missing = [m for m in media if m not in text]
        if not media:
            return True, "no images yet"
        return not missing, "" if not missing else f"{len(missing)} of {len(media)} not mapped, e.g. {missing[0]}"
    if t == "analytics_live":
        # The ID recorded with `asf set measurement.analytics` must be on the live home page.
        rec = str(dotted_get(state, "measurement.analytics") or "")
        ids = re.findall(r"\b(G-[A-Z0-9]{6,}|GTM-[A-Z0-9]{4,})\b", rec)
        if not ids:
            return False, "`asf set measurement.analytics \"GA4 G-XXXX\"` not done (with the real ID)"
        url = (dotted_get(state, "deploy.production_url") or state.get("site_url") or "").rstrip("/") + "/"
        try:
            import urllib.request
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ASF-check/1.0"}), timeout=20) as r:
                html = r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001 (any network failure is a failed check)
            return False, f"couldn't load {url}: {str(e)[:80]}"
        found = [i for i in ids if i in html]
        return bool(found), f"{found[0]} found on {url}" if found else f"{ids[0]} isn't on {url} (wp-config ASF_GA4_ID / ASF_GTM_ID on production?)"
    if t == "ia_pages":
        # The IA's sitemap (§1) against content/pages: planned pages that don't exist, and skeleton
        # pages nobody planned. Archives, [x] patterns, legal pages and campaign landing pages are skipped,
        # on both sides: legal-* files aren't counted as pages, so IA rows with a legal recipe aren't planned.
        body = section(text, "sitemap")
        if body is None:
            return False, "no Sitemap section in the IA"
        planned = set()
        for row in table_rows(body):
            cells = [c.strip().strip("`") for c in row.strip().strip("|").split("|")]
            recipe = cells[2].lower() if len(cells) > 2 else ""
            if not cells or not cells[0].startswith("/") or "[" in cells[0] or "archive" in recipe or "legal" in recipe:
                continue
            planned.add(cells[0].strip("/") or "home")
        pages = {}
        for f in sorted((root / "content/pages").glob("*.html")):
            head = f.read_text(encoding="utf-8")[:800]
            m = re.search(r"^slug:\s*(\S+)", head, re.M)
            if m and not f.name.startswith("legal-") and "template: page-landing" not in head:
                pages[m.group(1).strip("/")] = f.name
        missing, extra = sorted(planned - set(pages)), sorted(set(pages) - planned)
        parts = ([f"no page for " + ", ".join(f"/{s}/" for s in missing[:4])] if missing else []) + \
                ([f"not in the IA: " + ", ".join(pages[s] for s in extra[:4])] if extra else [])
        return not parts, "; ".join(parts) or f"{len(planned)} planned pages, all present"
    if t == "glob_min":
        n = len(globlib.glob(str(root / check["glob"])))
        return n >= check["min"], f"{n} found, need {check['min']}"
    if t == "briefs_max_sections":
        over = []
        for f in globlib.glob(str(root / check["glob"])):
            body = section(Path(f).read_text(encoding="utf-8"), "sections") or ""
            if len(table_rows(body)) > check["max"]:
                over.append(Path(f).name)
        files = globlib.glob(str(root / check["glob"]))
        if not files:
            return False, "no briefs yet"
        return not over, "" if not over else "too long: " + ", ".join(over)
    if t == "not_contains":
        files = globlib.glob(str(root / check["glob"]))
        if not files:
            return False, f"nothing matches {check['glob']}"
        hit = [Path(f).relative_to(root).as_posix() for f in files if check["text"] in Path(f).read_text(encoding="utf-8")]
        return not hit, "" if not hit else f"still in {hit[0]}"
    if t == "command":
        # {site_url}, {deploy.staging_url}, {rest_namespace}…: any value from asf.json.
        missing = [k for k in re.findall(r"\{([a-z_.]+)\}", check["run"]) if not dotted_get(state, k)]
        if missing:
            return False, f"needs `asf set {missing[0]} …` first"
        cmd = re.sub(r"\{([a-z_.]+)\}", lambda m: str(dotted_get(state, m.group(1))), check["run"])
        try:
            r = subprocess.run(shlex.split(cmd), cwd=root, capture_output=True, text=True, timeout=900)
        except (OSError, subprocess.TimeoutExpired) as e:
            return False, f"couldn't run: {e}"
        last = ((r.stdout.strip() or r.stderr.strip()).splitlines() or [""])[-1][:120]
        return r.returncode == 0, last
    if t == "state_set":
        v = dotted_get(state, check["key"])
        return bool(v), str(v) if v else f"`asf set {check['key']} …` not done"
    if t == "latest_no_placeholders":
        files = [Path(f) for f in globlib.glob(str(root / check["glob"]))]
        if not files:
            return False, "none yet"
        newest = max(files, key=lambda p: p.stat().st_mtime)
        left = PLACEHOLDER.findall(newest.read_text(encoding="utf-8"))
        return not left, "" if not left else f"{newest.name} still has {len(left)} blanks, e.g. [{left[0][:50]}]"
    if t == "campaigns":
        sys.path.insert(0, str(HERE))
        import campaigns  # noqa: E402  (beside this file)
        return campaigns.gate(root, state, sys.modules[__name__])
    if t == "changes":
        sys.path.insert(0, str(HERE))
        import changes  # noqa: E402  (beside this file)
        return changes.gate(root, state, sys.modules[__name__])
    if t == "intake_clear":
        sys.path.insert(0, str(HERE))
        import intake  # noqa: E402  (beside this file)
        return intake.gate_check(root, state)
    if t == "recent_file":
        files = [Path(f) for f in globlib.glob(str(root / check["glob"]))]
        if not files:
            return False, "none yet"
        newest = max(files, key=lambda p: p.stat().st_mtime)
        age = (datetime.datetime.now().timestamp() - newest.stat().st_mtime) / 86400
        return age <= check["days"], f"newest is {newest.name}, {age:.0f} days old"
    return False, f"unknown check type {t}"


def evaluate(root, state, stage):
    skips = state.get("skips", {}).get(stage["gate"], {})
    results = []
    for c in stage["checks"]:
        if c["id"] in skips:
            results.append({**c, "status": "skipped", "detail": skips[c["id"]]})
            continue
        ok, detail = run_check(root, state, c)
        results.append({**c, "status": "pass" if ok else "fail", "detail": detail})
    return results


# ── commands ──────────────────────────────────────────────────────────────────────
def cmd_init(args):
    root = Path.cwd()
    if (root / STATE_FILE).exists():
        sys.exit(f"{STATE_FILE} already exists.")
    state = {
        "framework": "Agentic Site Framework",
        "client": args.name, "kind": args.kind, "site_url": args.site_url, "rest_namespace": args.rest_namespace,
        "created": now(), "stage": "truth",
        "gates": {}, "skips": {}, "deploy": {}, "measurement": {}, "team": {},
    }
    save_state(root, state)
    print(f"Created {STATE_FILE}: {args.name} ({args.kind}), stage 1 (Truth).")


def gate_line(state, stage, current):
    g = state["gates"].get(stage["gate"])
    if stage.get("repeat") and isinstance(g, list) and g:
        return f"✓ last signed {g[-1]['at'][:10]} by {g[-1]['by']} ({len(g)} so far)"
    if isinstance(g, dict):
        return f"✓ signed {g['at'][:10]} by {g['by']}" + (" (override)" if g.get("override") else "")
    return "← current" if stage["id"] == current else "·"


def cmd_status(args):
    root = find_root(); state = load_state(root); wf = load_workflow(root)
    cur = stage_by(wf, state["stage"])
    print(f"{state['client']} · {state['kind']} · {state.get('site_url', '')}")
    for i, s in enumerate(wf["stages"], 1):
        print(f"  {i}. {s['title']:<7} {s['gate']}  {gate_line(state, s, cur['id'])}")
    res = evaluate(root, state, cur)
    passed = sum(1 for r in res if r["status"] != "fail")
    print(f"\nNow: stage {wf['stages'].index(cur) + 1}, {cur['title']}: {cur['question']}")
    print(f"Gate {cur['gate']}: {passed}/{len(res)} automated checks pass · {len(cur['manual'])} items for a human to confirm")
    for k in ("deploy", "measurement"):
        if state.get(k):
            print(f"{k.capitalize()}: " + ", ".join(f"{a}={b}" for a, b in state[k].items()))
    team = [f"{role}: {', '.join(p['name'] for p in people(state, role))}" for role in wf.get("roles", {}) if people(state, role)]
    print("Team: " + (" · ".join(team) if team else "nobody named yet (`asf team add lead \"Name\"`)"))
    if (root / "docs/changes").exists() and any((root / "docs/changes").glob("*.md")):
        sys.path.insert(0, str(HERE))
        import changes  # noqa: E402  (beside this file)
        cfg = changes.config(root)
        open_ = [s for s in changes.slugs(root) if changes.standing(state, cfg, changes.read(root, s))["status"] == "open"]
        print(f"Changes: {len(open_)} open" + (" (" + ", ".join(open_[:5]) + ("…" if len(open_) > 5 else "") + "): `asf change list`" if open_ else ""))
    if state.get("framework_version"):
        print(f"Framework: {state['framework_version']}")
    print("Next: `asf next`")


def cmd_check(args):
    root = find_root(); state = load_state(root); wf = load_workflow(root)
    stage = stage_by(wf, args.gate or state["stage"])
    res = evaluate(root, state, stage)
    if args.json:
        print(json.dumps({"gate": stage["gate"], "stage": stage["id"], "checks": res, "manual": stage["manual"],
                          "manual_items": manual_items(state, stage)}, indent=2, ensure_ascii=False))
        return
    print(f"Gate {stage['gate']} ({stage['title']}): automated checks")
    for r in res:
        mark = {"pass": "✓", "fail": "✗", "skipped": "–"}[r["status"]]
        line = f"  {mark} {r['label']}"
        if r["detail"] and r["status"] != "pass":
            line += f"  ({r['detail']})"
        print(line)
        if r["status"] == "fail":
            print(f"      → {r['hint']}")
    print(f"For a person to confirm (`asf confirm {stage['gate']} <number> --by \"Name\"`), before the {stage['signs']} signs:")
    for item in manual_items(state, stage):
        print(f"  {manual_line(item)}")
    sys.exit(0 if all(r["status"] != "fail" for r in res) else 1)


def cmd_next(args):
    root = find_root(); state = load_state(root); wf = load_workflow(root)
    stage = stage_by(wf, state["stage"])
    res = evaluate(root, state, stage)
    failing = [r for r in res if r["status"] == "fail"]
    out = {
        "client": state["client"], "kind": state["kind"],
        "stage": stage["id"], "title": stage["title"], "gate": stage["gate"], "question": stage["question"],
        "doc": stage["doc"], "agents": stage["agents"],
        "prompts": [f"docs/framework/prompts/{p}.md" for p in stage["prompts"]],
        "todo": [{"id": r["id"], "label": r["label"], "detail": r["detail"], "hint": r["hint"]} for r in failing],
        "ready_for_signoff": not failing,
        "manual": stage["manual"],
        "manual_items": manual_items(state, stage),
        "signs": {"role": stage["signs"], "people": [p["name"] for p in people(state, stage["signs"])]},
    }
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return
    print(f"Stage: {stage['title']} ({stage['gate']}). {stage['question']}")
    print(f"Playbook: {stage['doc']}" + (f" · agents: {', '.join(stage['agents'])}" if stage["agents"] else ""))
    if failing:
        print("To do before the gate:")
        for r in failing:
            print(f"  ✗ {r['label']}" + (f" ({r['detail']})" if r["detail"] else ""))
            print(f"      → {r['hint']}")
    else:
        print(f"Automated checks pass. Each owner confirms their items (`asf confirm {stage['gate']} <number> --by \"Name\"`), "
              f"then the {stage['signs']} signs: `asf approve {stage['gate']} --by \"Name\"`:")
        for item in manual_items(state, stage):
            print(f"  {manual_line(item)}")


def cmd_approve(args):
    root = find_root(); state = load_state(root); wf = load_workflow(root)
    stage = stage_by(wf, args.gate)
    if stage["id"] != state["stage"] and not stage.get("repeat"):
        sys.exit(f"{stage['gate']} isn't the current gate (the project is at {stage_by(wf, state['stage'])['gate']}).")
    res = evaluate(root, state, stage)
    failing = [r for r in res if r["status"] == "fail"]
    if failing and not args.override:
        print(f"Not signed: {len(failing)} automated check(s) fail:")
        for r in failing:
            print(f"  ✗ {r['label']}" + (f" ({r['detail']})" if r["detail"] else ""))
        sys.exit("Fix them, or sign with --override \"reason\" (recorded in the log).")
    # Items another role owns need that person's own confirmation, once someone holds the role.
    items = manual_items(state, stage)
    mine = roles_of(state, args.by) | {stage["signs"]}
    waiting = [i for i in items if i["people"] and not i["confirmed_by"] and i["role"] not in mine]
    if waiting and not args.override:
        print(f"Not signed: {len(waiting)} item(s) are waiting for the person who owns them:")
        for i in waiting:
            print(f"  {manual_line(i)}")
        sys.exit(f"They confirm with `asf confirm {stage['gate']} <number> --by \"Name\"`, or sign with --override \"reason\" (recorded in the log).")
    signers = [p["name"] for p in people(state, stage["signs"])]
    if signers and args.by.lower() not in [n.lower() for n in signers]:
        print(f"  Note: {stage['gate']} is the {stage['signs']}'s to sign ({', '.join(signers)}); recorded as signed by {args.by}.")
    record = {"by": args.by, "at": now(), "note": args.note or "", "manual_confirmed": stage["manual"]}
    confirmed = {i["text"]: i["confirmed_by"] for i in items if i["confirmed_by"]}
    if confirmed:
        record["confirmed_by"] = confirmed
    if failing or waiting:
        record["override"] = args.override
    if failing:
        record["failing"] = [r["id"] for r in failing]
    if waiting:
        record["unconfirmed"] = [i["text"] for i in waiting]
    if stage.get("repeat"):
        state["gates"].setdefault(stage["gate"], []).append(record)
    else:
        state["gates"][stage["gate"]] = record
        ids = [s["id"] for s in wf["stages"]]
        state["stage"] = ids[min(ids.index(stage["id"]) + 1, len(ids) - 1)]
    state["log"].append({"at": record["at"], "event": f"{stage['gate']} signed by {args.by}" + (" (override)" if failing or waiting else ""), "note": args.note or args.override or ""})
    save_state(root, state)
    nxt = stage_by(wf, state["stage"])
    print(f"✓ {stage['gate']} ({stage['title']}) signed by {args.by}. Now: {nxt['title']} ({nxt['gate']}).")
    sys.path.insert(0, str(HERE))
    import github_board  # noqa: E402  (beside this file)
    github_board.after_approve(root, state, sys.modules[__name__])


def cmd_skip(args):
    root = find_root(); state = load_state(root); wf = load_workflow(root)
    stage = stage_by(wf, args.gate)
    if args.check not in [c["id"] for c in stage["checks"]]:
        sys.exit(f"{stage['gate']} has no check called {args.check}. Checks: " + ", ".join(c["id"] for c in stage["checks"]))
    state.setdefault("skips", {}).setdefault(stage["gate"], {})[args.check] = args.reason
    state["log"].append({"at": now(), "event": f"{stage['gate']}/{args.check} skipped", "note": args.reason})
    save_state(root, state)
    print(f"– {stage['gate']}/{args.check} skipped: {args.reason}")


def cmd_set(args):
    root = find_root(); state = load_state(root)
    try:  # lists and numbers (e.g. measurement.prompts) can be given as JSON
        value = json.loads(args.value) if args.value[:1] in "[{0123456789" else args.value
    except json.JSONDecodeError:
        value = args.value
    if args.local:  # this machine only: never written to asf.json, never logged
        path = root / LOCAL_FILE
        local = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        dotted_set(local, args.key, value)
        path.write_text(json.dumps(local, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{args.key} = {args.value}  (this machine only: {LOCAL_FILE})")
        try:
            ignored = subprocess.run(["git", "check-ignore", "-q", LOCAL_FILE], cwd=root, timeout=5).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            ignored = True
        if not ignored:
            print(f"  Add `/{LOCAL_FILE}` to .gitignore so it's never committed.")
        return
    dotted_set(state, args.key, value)
    state["log"].append({"at": now(), "event": f"set {args.key}", "note": args.value})
    save_state(root, state)
    print(f"{args.key} = {args.value}")


def cmd_report(args):
    root = find_root(); state = load_state(root)
    sys.path.insert(0, str(HERE))
    import measure  # noqa: E402  (beside this file)
    data, data_path, md_path, wrote = measure.run(root, state, args.to, args.frm, not args.no_crawl, args.force)
    rel = lambda p: p.relative_to(root).as_posix()  # noqa: E731
    print(f"Week {data['from']} → {data['to']}")
    for name, src in data["sources"].items():
        print(f"  {name:<15} {src.get('status')}" + (f"  ({src.get('how') or src.get('error')})" if src.get("status") not in ("ok", "for the agent", "none running") else ""))
    print(f"Data:  {rel(data_path)}")
    print(f"Draft: {rel(md_path)}" + ("" if wrote else "  (already existed; kept. Use --force to redraft)"))
    print("Next: write \"The three things\" and fill the [blanks] from the data, review, then send it to the client.")
    state["log"].append({"at": now(), "event": f"report collected for {data['from']}–{data['to']}", "note": rel(md_path)})
    save_state(root, state)


def cmd_campaign(args):
    root = find_root(); state = load_state(root)
    sys.path.insert(0, str(HERE))
    import campaigns  # noqa: E402  (beside this file)
    core = sys.modules[__name__]
    if args.action != "list" and not args.slug:
        sys.exit(f"`bin/asf campaign {args.action} <slug>`")
    if args.action == "new":
        campaigns.new(root, state, args, core)
    elif args.action == "links":
        campaigns.links(root, state, args, core)
    elif args.action == "list":
        campaigns.listing(state)
        return
    elif args.action == "check":
        marks = {"ok": "✓", "warning": "·", "error": "✗"}
        results = campaigns.check(root, state, args.slug, core, args.url)
        for level, msg in results:
            print(f"  {marks[level]} {msg}")
        errors = sum(1 for lvl, _ in results if lvl == "error")
        print(f"{args.slug}: {errors} error(s) · {sum(1 for lvl, _ in results if lvl == 'warning')} warning(s)")
        sys.exit(1 if errors else 0)
    elif args.action == "report":
        campaigns.report(root, state, args.slug, args.write)
        return
    elif args.action == "close":
        if not args.outcome:
            sys.exit("--outcome keep|redirect|unpublish")
        campaigns.close(root, state, args, core)
    save_state(root, state)


def cmd_change(args):
    root = find_root(); state = load_state(root)
    sys.path.insert(0, str(HERE))
    import changes  # noqa: E402  (beside this file)
    changes.main(root, state, args, sys.modules[__name__])


def cmd_intake(args):
    root = find_root(); state = load_state(root)
    sys.path.insert(0, str(HERE))
    import intake  # noqa: E402  (beside this file)
    core = sys.modules[__name__]
    if args.action == "sources":
        intake.sources(root, state, args.json)
    elif args.action == "add":
        if not args.title:
            sys.exit('`bin/asf intake add "Title" --type … --source … --ref …`')
        intake.add(root, state, args, core)
    elif args.action == "done":
        if not args.files:
            sys.exit("`bin/asf intake done docs/intake/raw/<file> …`")
        intake.done(root, state, args.files, args.note, core)
    elif args.action == "list":
        intake.listing(root, state)


def cmd_github(args):
    root = find_root(); state = load_state(root)
    sys.path.insert(0, str(HERE))
    import github_board  # noqa: E402  (beside this file)
    core = sys.modules[__name__]
    try:
        {"init": github_board.init, "sync": github_board.sync, "confirm-issues": github_board.confirm_issues}[args.action](root, state, args, core)
    except github_board.GhError as e:
        sys.exit(f"GitHub: {e}")


def cmd_log(args):
    root = find_root(); state = load_state(root)
    for e in state.get("log", []):
        print(f"{e.get('at', '')[:16]}  {e.get('by', ''):<14.14} {e.get('event', '')}" + (f"  · {e['note']}" if e.get("note") else ""))


def cmd_team(args):
    root = find_root(); state = load_state(root); wf = load_workflow(root)
    roles = wf.get("roles", {})
    if args.action == "list":
        for role, what in roles.items():
            names = ", ".join(p["name"] + (f" (@{p['github']})" if p.get("github") else "") for p in people(state, role))
            print(f"  {role:<10} {names or '—':<32} {what}")
        print('Add someone: `asf team add designer "Name" --github handle`. One person can hold several roles.')
        return
    if args.role not in roles:
        sys.exit(f"Roles: {', '.join(roles)}")
    if not args.name:
        sys.exit(f'`bin/asf team {args.action} {args.role} "Name"`')
    members = [p for p in state.setdefault("team", {}).get(args.role, []) if p.get("name", "").lower() != args.name.lower()]
    if args.action == "add":
        members.append({"name": args.name, **({"github": args.github.lstrip("@")} if args.github else {})})
    state["team"][args.role] = members
    state["log"].append({"at": now(), "event": f"team: {args.name} {'is' if args.action == 'add' else 'is no longer'} {args.role}", "note": ""})
    save_state(root, state)
    print(f"{args.role}: " + (", ".join(p["name"] for p in members) or "—"))
    sys.path.insert(0, str(HERE))
    import github_board  # noqa: E402  (beside this file)
    github_board.after_approve(root, state, sys.modules[__name__])


def cmd_confirm(args):
    """One person confirms the gate items they own. The sign-off itself stays with `asf approve`."""
    root = find_root(); state = load_state(root); wf = load_workflow(root)
    stage = stage_by(wf, args.gate)
    if not args.items:
        for item in manual_items(state, stage):
            print(f"  {manual_line(item)}")
        return
    if not args.by:
        sys.exit('--by "Name" is required: a confirmation is one person\'s word.')
    bad = [n for n in args.items if not 1 <= n <= len(stage["manual"])]
    if bad:
        sys.exit(f"{stage['gate']} has items 1 to {len(stage['manual'])} (`asf confirm {stage['gate']}` lists them).")
    for n in args.items:
        text, role = stage["manual"][n - 1], stage["manual_roles"][n - 1]
        holders = [p["name"] for p in people(state, role)]
        if holders and args.by.lower() not in [h.lower() for h in holders]:
            print(f"  Note: item {n} is the {role}'s ({', '.join(holders)}); recorded as confirmed by {args.by}.")
        state["log"].append({"at": now(), "event": f"{stage['gate']} item {n} confirmed by {args.by}", "note": args.note or text,
                             "confirm": {"gate": stage["gate"], "n": n, "text": text, "by": args.by}})
        print(f"✓ {stage['gate']} item {n} confirmed by {args.by}: {text}")
    save_state(root, state)
    sys.path.insert(0, str(HERE))
    import github_board  # noqa: E402  (beside this file)
    github_board.after_approve(root, state, sys.modules[__name__])


def main():
    ap = argparse.ArgumentParser(prog="asf", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("--name", required=True); p.add_argument("--kind", default="agency"); p.add_argument("--site-url", default=""); p.add_argument("--rest-namespace", default="")
    sub.add_parser("status")
    p = sub.add_parser("check"); p.add_argument("gate", nargs="?"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("next"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("approve"); p.add_argument("gate"); p.add_argument("--by", required=True); p.add_argument("--note"); p.add_argument("--override")
    p = sub.add_parser("skip"); p.add_argument("gate"); p.add_argument("check"); p.add_argument("--reason", required=True)
    p = sub.add_parser("set"); p.add_argument("key"); p.add_argument("value")
    p.add_argument("--local", action="store_true", help="for this machine only (asf.local.json, git-ignored), e.g. a local site address")
    p = sub.add_parser("team"); p.add_argument("action", nargs="?", choices=["list", "add", "remove"], default="list")
    p.add_argument("role", nargs="?"); p.add_argument("name", nargs="?"); p.add_argument("--github", help="GitHub handle, so their issues are assigned to them")
    p = sub.add_parser("confirm"); p.add_argument("gate"); p.add_argument("items", nargs="*", type=int, help="item numbers, as `asf check` lists them")
    p.add_argument("--by"); p.add_argument("--note")
    p = sub.add_parser("report"); p.add_argument("--to"); p.add_argument("--from", dest="frm"); p.add_argument("--no-crawl", action="store_true"); p.add_argument("--force", action="store_true")
    p = sub.add_parser("campaign"); p.add_argument("action", choices=["new", "links", "check", "list", "report", "close"]); p.add_argument("slug", nargs="?")
    p.add_argument("--name"); p.add_argument("--landing"); p.add_argument("--start"); p.add_argument("--end")
    p.add_argument("--goal", type=int); p.add_argument("--budget", type=float); p.add_argument("--channels"); p.add_argument("--cta", default="Get started")
    p.add_argument("--index", action="store_true", help="let search engines index the landing page (default: noindex)")
    p.add_argument("--content", help="creative names for utm_content, comma-separated"); p.add_argument("--url", help="check this site instead of the recorded one")
    p.add_argument("--write", action="store_true"); p.add_argument("--outcome", choices=["keep", "redirect", "unpublish"]); p.add_argument("--to"); p.add_argument("--note")
    p = sub.add_parser("change"); p.add_argument("action", choices=["new", "list", "check", "status", "set", "confirm", "approve", "drop", "board", "pr"])
    p.add_argument("rest", nargs="*", help="the change's slug, then a gate (C1–C4), item numbers, or a key and value")
    p.add_argument("--title"); p.add_argument("--kind"); p.add_argument("--issue"); p.add_argument("--pages", help="the URLs it touches, comma-separated: /pricing/,/services/")
    p.add_argument("--by"); p.add_argument("--note"); p.add_argument("--override"); p.add_argument("--reason")
    p.add_argument("--offline", action="store_true", help="skip the checks that need the running site"); p.add_argument("--json", action="store_true")
    p.add_argument("--all", action="store_true", help="for `list`: finished and dropped changes too"); p.add_argument("--dry-run", action="store_true")
    p.add_argument("--base", help="for `pr`: the branch to compare with (default origin/main)")
    p = sub.add_parser("intake"); p.add_argument("action", choices=["sources", "add", "done", "list"]); p.add_argument("title", nargs="?")
    p.add_argument("files", nargs="*", help="for `done`: raw files to mark processed"); p.add_argument("--type"); p.add_argument("--source"); p.add_argument("--ref")
    p.add_argument("--quote"); p.add_argument("--body"); p.add_argument("--page"); p.add_argument("--stage"); p.add_argument("--note")
    p.add_argument("--assign", help="a role (designer, developer…) or a GitHub handle; default: the role the type implies")
    p.add_argument("--local", action="store_true", help="file it in docs/intake/items/ even when GitHub is set up"); p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true", help="for `sources`: machine-readable, for /asf intake")
    p = sub.add_parser("github"); p.add_argument("action", choices=["init", "sync", "confirm-issues"])
    p.add_argument("--repo", help="owner/name (default: the repo of the current folder)"); p.add_argument("--owner", help="who owns the board (an org shares one board across clients)")
    p.add_argument("--project", type=int, help="use this existing project number instead of creating one"); p.add_argument("--dry-run", action="store_true")
    sub.add_parser("log")
    a = ap.parse_args()
    if a.cmd == "intake" and a.action == "done" and a.title:  # `intake done <file> …`: the first file lands in `title`
        a.files = [a.title, *a.files]
    {"init": cmd_init, "status": cmd_status, "check": cmd_check, "next": cmd_next, "approve": cmd_approve,
     "skip": cmd_skip, "set": cmd_set, "report": cmd_report, "campaign": cmd_campaign, "log": cmd_log,
     "intake": cmd_intake, "github": cmd_github, "team": cmd_team, "confirm": cmd_confirm, "change": cmd_change}[a.cmd](a)


if __name__ == "__main__":
    main()
