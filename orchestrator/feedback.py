"""Feedback: what people said about the work, what was done about it, and what became a rule.

A comment that is acted on once and forgotten gets made again. So every piece of feedback is
recorded with who gave it and what happened, and feedback that should hold from now on is promoted
to docs/lessons.md, which the agents read before every stage and every change.

    bin/asf feedback add "What they said" --from "Name" [--role designer] [--area design|copy|build|process]
                         [--on <change or page>] [--tag line-breaks] [--ref <link>]
                         [--outcome applied|declined|overruled --note "…"]
        Record one comment. Without --outcome it stays open until it's closed.
    bin/asf feedback close <id> --outcome applied|declined|overruled --note "…"
        applied    done as asked
        declined   not done; the note is the reason the person was given
        overruled  done as asked although the evidence said otherwise; the note is the concern,
                   so the result can be checked later
    bin/asf feedback promote <id> --rule "The rule, in one sentence" [--scope project|framework]
        Make it a rule: appended to docs/lessons.md. --scope framework marks a lesson that would
        hold on any site, to propose to the framework itself.
    bin/asf feedback list [--all]         open feedback (or everything)
    bin/asf feedback patterns             what keeps coming back, and what was overruled
    bin/asf feedback reviewed --by "Name" record that the learning pass was done (/asf learn)

Feedback lives in the project log (docs/log/, one file per person), so it merges without conflicts.
"""
import datetime
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRAMEWORK = HERE.parent
AREAS = ["design", "copy", "build", "process"]
OUTCOMES = ["applied", "declined", "overruled"]
LESSONS = "docs/lessons.md"


def when(entry):
    try:
        return datetime.datetime.fromisoformat(entry.get("at", ""))
    except (TypeError, ValueError):
        return None


def items(state):
    """{id: record} for every piece of feedback, with its current outcome."""
    out = {}
    for e in state.get("log", []):
        f = e.get("feedback")
        if not isinstance(f, dict):
            continue
        if f.get("action") == "add":
            out[f["id"]] = {"id": f["id"], "text": f.get("text", ""), "from": f.get("from", ""), "role": f.get("role", ""),
                            "area": f.get("area", "design"), "on": f.get("on", ""), "tag": f.get("tag", ""), "ref": f.get("ref", ""),
                            "outcome": f.get("outcome") or "open", "note": f.get("note", ""), "rule": "", "at": e.get("at", ""),
                            "closed_at": e.get("at", "") if f.get("outcome") else ""}
        elif f.get("action") in ("close", "promote") and f.get("id") in out:
            rec = out[f["id"]]
            rec["closed_at"] = e.get("at", "")
            if f.get("action") == "close":
                rec.update(outcome=f.get("outcome", rec["outcome"]), note=f.get("note", ""))
            else:
                rec.update(rule=f.get("rule", ""), scope=f.get("scope", "project"))
                if rec["outcome"] == "open":
                    rec["outcome"] = "applied"
    return out


def last_review(state):
    stamps = [when(e) for e in state.get("log", []) if isinstance(e.get("feedback"), dict) and e["feedback"].get("action") == "reviewed"]
    stamps = [s for s in stamps if s]
    return max(stamps) if stamps else None


def find(state, key):
    recs = items(state)
    hits = [r for i, r in recs.items() if i.startswith(key)]
    if len(hits) != 1:
        sys.exit(f"No single piece of feedback matches \"{key}\" (`bin/asf feedback list --all` shows the ids).")
    return hits[0]


# ── gate checks ──────────────────────────────────────────────────────────────────
def gate_closed(state, on=None, area=None):
    """No feedback left open (optionally only for one change or page, or one area)."""
    left = [r for r in items(state).values() if r["outcome"] == "open" and (not on or r["on"] == on) and (not area or r["area"] == area)]
    if left:
        return False, f"{len(left)} open, e.g. \"{left[0]['text'][:60]}\" from {left[0]['from'] or '?'} (`asf feedback close {left[0]['id']} …`)"
    return True, "no feedback left open"


def gate_learning(state, days=35):
    """Feedback closed since the last learning pass mustn't sit unread for more than `days`."""
    since = last_review(state)
    waiting = [r for r in items(state).values() if r["outcome"] != "open" and not r["rule"] and when({"at": r["closed_at"]})
               and (since is None or when({"at": r["closed_at"]}) > since)]
    if not waiting:
        return True, "nothing new since the last learning pass"
    oldest = min(when({"at": r["closed_at"]}) for r in waiting)
    age = (datetime.datetime.now().astimezone() - oldest).days
    return age <= days, f"{len(waiting)} piece(s) of feedback not looked at for rules, the oldest {age} days old"


# ── commands ──────────────────────────────────────────────────────────────────────
def add(root, state, a, core, quiet=False):
    text = " ".join(a.rest).strip()
    if not text or not a.frm:
        sys.exit('`bin/asf feedback add "What they said" --from "Name" [--area …] [--on <change or page>]`')
    area = a.area or "design"
    if area not in AREAS:
        sys.exit(f"--area is one of: {', '.join(AREAS)}")
    if a.outcome and a.outcome not in OUTCOMES:
        sys.exit(f"--outcome is one of: {', '.join(OUTCOMES)}")
    if a.outcome in ("declined", "overruled") and not a.note:
        sys.exit("--note is required: for declined, the reason the person was given; for overruled, the concern that was raised.")
    at = core.now()
    fid = hashlib.sha1(f"{at}{text}".encode()).hexdigest()[:6]
    state["log"].append({"at": at, "event": f"feedback from {a.frm} ({area})", "note": text[:140],
                         "feedback": {"action": "add", "id": fid, "text": text, "from": a.frm, "role": a.role or "", "area": area,
                                      "on": a.on or "", "tag": (a.tag or "").lower(), "ref": a.ref or "",
                                      "outcome": a.outcome or "", "note": a.note or ""}})
    core.save_state(root, state)
    if not quiet:
        print(f"✓ Feedback {fid} recorded ({a.outcome or 'open'}): {text[:90]}")
    return fid


def close(root, state, a, core):
    if not a.rest or a.outcome not in OUTCOMES or not a.note:
        sys.exit('`bin/asf feedback close <id> --outcome applied|declined|overruled --note "what was done, or why not"`')
    rec = find(state, a.rest[0])
    state["log"].append({"at": core.now(), "event": f"feedback {rec['id']} {a.outcome}", "note": a.note,
                         "feedback": {"action": "close", "id": rec["id"], "outcome": a.outcome, "note": a.note}})
    core.save_state(root, state)
    print(f"✓ {rec['id']} {a.outcome}: {rec['text'][:80]}")
    if a.outcome == "overruled":
        print("  Built as asked, with the concern on record. The learning pass will ask how it turned out.")


def promote(root, state, a, core):
    if not a.rest or not a.rule:
        sys.exit('`bin/asf feedback promote <id> --rule "The rule, in one sentence" [--scope project|framework]`')
    scope = a.scope or "project"
    if scope not in ("project", "framework"):
        sys.exit("--scope is project or framework")
    rec = find(state, a.rest[0])
    path = root / LESSONS
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text((FRAMEWORK / "templates/lessons.md").read_text(encoding="utf-8"), encoding="utf-8")
    line = (f"- **{a.rule.strip().rstrip('.')}.** ({rec['area']}; from {rec['from'] or 'the team'}, {core.now()[:10]}; feedback `{rec['id']}`"
            + ("; **for the framework too**" if scope == "framework" else "") + ")\n")
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^## Rules\s*\n", text, re.M)
    if m:
        rest = text[m.end():]
        nxt = re.search(r"^## ", rest, re.M)
        body = rest[: nxt.start()] if nxt else rest
        body = re.sub(r"^\*No rules yet\.\*\s*\n?", "", body.lstrip("\n"), flags=re.M).rstrip("\n")
        text = text[: m.end()] + "\n" + (body + "\n" if body else "") + line + ("\n" + rest[nxt.start():] if nxt else "")
    else:
        text = text.rstrip("\n") + "\n\n## Rules\n\n" + line
    path.write_text(text, encoding="utf-8")
    state["log"].append({"at": core.now(), "event": f"feedback {rec['id']} became a rule", "note": a.rule,
                         "feedback": {"action": "promote", "id": rec["id"], "rule": a.rule, "scope": scope}})
    core.save_state(root, state)
    print(f"✓ Added to {LESSONS}: {a.rule}")
    if scope == "framework":
        print("  Marked for the framework too: propose it there (PRINCIPLES.md or the pattern it belongs in), with what happened.")


def listing(root, state, a, core):
    recs = sorted(items(state).values(), key=lambda r: r["at"])
    shown = recs if a.all else [r for r in recs if r["outcome"] == "open"]
    if not shown:
        print("No feedback recorded yet." if not recs else "No open feedback. `--all` shows everything.")
        return
    for r in shown:
        what = "rule" if r["rule"] else r["outcome"]
        print(f"  {r['id']}  {r['at'][:10]}  {what:<9} {r['area']:<7} {(r['from'] or '?'):<12.12} " + (f"[{r['on']}] " if r["on"] else "") + r["text"][:90])
        if r["note"] and a.all:
            print(f"          → {r['note'][:120]}")
    print(f"{sum(1 for r in recs if r['outcome'] == 'open')} open · {len(recs)} in all · {sum(1 for r in recs if r['rule'])} became rules")


def patterns(root, state, a, core):
    """What the learning pass starts from: feedback that recurs, and feedback that was overruled."""
    recs = [r for r in items(state).values() if not r["rule"]]
    groups = {}
    for r in recs:
        groups.setdefault(r["tag"] or f"({r['area']}, untagged)", []).append(r)
    repeats = {k: v for k, v in groups.items() if len(v) >= 2 and not k.startswith("(")}
    since = last_review(state)
    print("Learning pass: last done " + (since.date().isoformat() if since else "never") + ".")
    if repeats:
        print("\nSaid more than once, and not a rule yet:")
        for tag, rs in sorted(repeats.items(), key=lambda kv: -len(kv[1])):
            print(f"  {tag} ({len(rs)}×, from {', '.join(sorted({r['from'] or '?' for r in rs}))})")
            for r in rs:
                print(f"    {r['id']}  {r['at'][:10]}  " + (f"[{r['on']}] " if r["on"] else "") + r["text"][:90])
    over = [r for r in recs if r["outcome"] == "overruled"]
    if over:
        print("\nBuilt as asked although the evidence said otherwise. How did each turn out?")
        for r in over:
            print(f"  {r['id']}  {r['at'][:10]}  " + (f"[{r['on']}] " if r["on"] else "") + r["text"][:80] + f"\n          concern: {r['note'][:120]}")
    untagged = [r for r in recs if not r["tag"]]
    if untagged:
        print(f"\n{len(untagged)} piece(s) with no tag: read them for themes the tags missed (`bin/asf feedback list --all`).")
    if not repeats and not over and not untagged:
        print("Nothing recurring, nothing overruled.")
    print("\nPromote what should hold from now on: `bin/asf feedback promote <id> --rule \"…\"`. Then `bin/asf feedback reviewed --by \"Name\"`.")


def reviewed(root, state, a, core):
    if not a.by:
        sys.exit('`bin/asf feedback reviewed --by "Name"` (a person decides which feedback becomes a rule)')
    state["log"].append({"at": core.now(), "event": f"learning pass done by {a.by}", "note": a.note or "", "feedback": {"action": "reviewed", "by": a.by}})
    core.save_state(root, state)
    print(f"✓ Learning pass recorded ({a.by}).")


def main(root, state, a, core):
    {"add": add, "close": close, "promote": promote, "list": listing, "patterns": patterns, "reviewed": reviewed}[a.action](root, state, a, core)
