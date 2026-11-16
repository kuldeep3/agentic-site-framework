#!/usr/bin/env python3
"""asf: the Agentic Site Framework orchestrator for one client project.

    bin/asf status              where the project is, gate by gate
    bin/asf next  [--json]      the one thing to do next (what the /asf command acts on)
    bin/asf check [G1..G5]      run a gate's automated checks (default: the current gate)
    bin/asf approve G1 --by "Name" [--note "…"] [--override "reason"]
                                record a human sign-off; refused while automated checks fail
    bin/asf skip G1 audit --reason "no current site"
    bin/asf set deploy.staging_url https://staging.example.com
    bin/asf log                 every sign-off, skip and setting, with dates
    bin/asf init --name "Acme" --kind agency --site-url http://acme.test   (the starter runs this)

State lives in asf.json at the project root (commit it: it's the project's audit trail).
Stages, gates and checks come from workflow.json. Standard library only.
"""
import argparse
import datetime
import glob as globlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE_FILE = "asf.json"
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


def load_state(root):
    return json.loads((root / STATE_FILE).read_text(encoding="utf-8"))


def save_state(root, state):
    (root / STATE_FILE).write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_workflow(root):
    local = root / "docs/framework/orchestrator/workflow.json"
    return json.loads((local if local.exists() else HERE / "workflow.json").read_text(encoding="utf-8"))


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="minutes")


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
    if t in ("no_placeholders", "section_filled", "table_rows", "media_mapped"):
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
        cmd = check["run"].replace("{site_url}", state.get("site_url", ""))
        try:
            r = subprocess.run(shlex.split(cmd), cwd=root, capture_output=True, text=True, timeout=900)
        except (OSError, subprocess.TimeoutExpired) as e:
            return False, f"couldn't run: {e}"
        last = ((r.stdout.strip() or r.stderr.strip()).splitlines() or [""])[-1][:120]
        return r.returncode == 0, last
    if t == "state_set":
        v = dotted_get(state, check["key"])
        return bool(v), str(v) if v else f"`asf set {check['key']} …` not done"
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
        "client": args.name, "kind": args.kind, "site_url": args.site_url,
        "created": now(), "stage": "truth",
        "gates": {}, "skips": {}, "deploy": {}, "measurement": {}, "log": [],
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
    print("Next: `asf next`")


def cmd_check(args):
    root = find_root(); state = load_state(root); wf = load_workflow(root)
    stage = stage_by(wf, args.gate or state["stage"])
    res = evaluate(root, state, stage)
    if args.json:
        print(json.dumps({"gate": stage["gate"], "stage": stage["id"], "checks": res, "manual": stage["manual"]}, indent=2, ensure_ascii=False))
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
    print("For a human to confirm at sign-off:")
    for m in stage["manual"]:
        print(f"  [ ] {m}")
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
        print(f"Automated checks pass. Ready for sign-off: confirm these with the lead, then `asf approve {stage['gate']} --by \"Name\"`:")
        for m in stage["manual"]:
            print(f"  [ ] {m}")


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
    record = {"by": args.by, "at": now(), "note": args.note or "", "manual_confirmed": stage["manual"]}
    if failing:
        record["override"] = args.override
        record["failing"] = [r["id"] for r in failing]
    if stage.get("repeat"):
        state["gates"].setdefault(stage["gate"], []).append(record)
    else:
        state["gates"][stage["gate"]] = record
        ids = [s["id"] for s in wf["stages"]]
        state["stage"] = ids[min(ids.index(stage["id"]) + 1, len(ids) - 1)]
    state["log"].append({"at": record["at"], "event": f"{stage['gate']} signed by {args.by}" + (" (override)" if failing else ""), "note": args.note or args.override or ""})
    save_state(root, state)
    nxt = stage_by(wf, state["stage"])
    print(f"✓ {stage['gate']} ({stage['title']}) signed by {args.by}. Now: {nxt['title']} ({nxt['gate']}).")


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
    dotted_set(state, args.key, args.value)
    state["log"].append({"at": now(), "event": f"set {args.key}", "note": args.value})
    save_state(root, state)
    print(f"{args.key} = {args.value}")


def cmd_log(args):
    root = find_root(); state = load_state(root)
    for e in state.get("log", []):
        print(f"{e['at'][:16]}  {e['event']}" + (f"  · {e['note']}" if e.get("note") else ""))


def main():
    ap = argparse.ArgumentParser(prog="asf", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("--name", required=True); p.add_argument("--kind", default="agency"); p.add_argument("--site-url", default="")
    sub.add_parser("status")
    p = sub.add_parser("check"); p.add_argument("gate", nargs="?"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("next"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("approve"); p.add_argument("gate"); p.add_argument("--by", required=True); p.add_argument("--note"); p.add_argument("--override")
    p = sub.add_parser("skip"); p.add_argument("gate"); p.add_argument("check"); p.add_argument("--reason", required=True)
    p = sub.add_parser("set"); p.add_argument("key"); p.add_argument("value")
    sub.add_parser("log")
    a = ap.parse_args()
    {"init": cmd_init, "status": cmd_status, "check": cmd_check, "next": cmd_next, "approve": cmd_approve,
     "skip": cmd_skip, "set": cmd_set, "log": cmd_log}[a.cmd](a)


if __name__ == "__main__":
    main()
