"""Requirements intake: every request, from any channel, becomes one tracked item with its source.

Clients send requirements by email, on calls, in GitHub issues, in chat and in documents.
Intake turns each request into one GitHub issue (labels `intake`, `type:*`, `source:*`, on the
board in the right Stage), or a file in docs/intake/items/ when the project isn't on GitHub.
Nothing becomes a fact on the site until the client confirms it: an answered `type:fact` issue
is copied into docs/truth.md with the issue as its source.

    bin/asf intake sources
        Raw material waiting in docs/intake/raw/ (emails, call transcripts, notes), and which
        of it has been processed. That folder is git-ignored: client correspondence stays private.
        Call recordings belong on the team's shared drive; an audio or video file found here is
        flagged, because intake reads text and needs its transcript.
    bin/asf intake add "Title" --type fact|question|content|page|design|bug|campaign --source email|call|meeting|issue|chat|doc|figma|other
                       --ref "where it came from" [--quote "the client's exact words"] [--body "…"] [--page /about/]
                       [--stage Requirement] [--local] [--dry-run]
        File one request. --ref says exactly where (an email's date and sender, a recording and
        timestamp, an issue or Figma comment link) so anyone can go back to the original.
    bin/asf intake done <file> […]  [--note "…"]
        Mark raw files as processed (gate G1 and G4 checks want none left unread).
    bin/asf intake list
        Open intake items.

The /asf intake command (claude-command.md) does the reading: it pulls new emails, transcripts,
unlabelled issues and Figma comments, drafts one item per request, shows the list to the lead
and files the approved ones with `add`.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

TYPES = ["fact", "question", "content", "page", "design", "bug", "campaign"]
SOURCES = ["email", "call", "meeting", "issue", "chat", "doc", "figma", "other"]
RAW = "docs/intake/raw"
ITEMS = "docs/intake/items"
# Recordings: intake can't read them; their transcripts carry the requests.
AV = {".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac", ".mp4", ".mov", ".webm", ".mkv", ".avi"}


def _sha(path):
    return hashlib.sha1(path.read_bytes()).hexdigest()[:12]


def raw_files(root):
    base = root / RAW
    if not base.exists():
        return []
    return sorted(p for p in base.rglob("*") if p.is_file() and not p.name.startswith("."))


def unprocessed(root, state):
    done = (state.get("intake") or {}).get("processed", {})
    return [p for p in raw_files(root) if done.get(p.relative_to(root).as_posix()) != _sha(p)]


def gate_check(root, state):
    """For workflow.json check type `intake_clear`: no raw source left unread."""
    left = unprocessed(root, state)
    if not raw_files(root):
        return True, "no raw sources in docs/intake/raw/"
    return not left, "" if not left else f"{len(left)} unread, e.g. {left[0].relative_to(root).as_posix()} (`/asf intake`)"


def sources(root, state):
    files = raw_files(root)
    if not files:
        print(f"Nothing in {RAW}/. Drop emails (.eml/.md/.txt), call transcripts and notes there, then run /asf intake.")
        return
    left = set(unprocessed(root, state))
    recordings = [p for p in files if p in left and p.suffix.lower() in AV]
    for p in files:
        note = "  (recording: needs its transcript)" if p in recordings else ""
        print(f"  {'·' if p in left else '✓'} {p.relative_to(root).as_posix()}{note}")
    print(f"{len(left)} to process · {len(files) - len(left)} done")
    if recordings:
        print("Intake reads text, not sound. Put each call's timestamped transcript in raw/, starting with the recording's "
              "shared-drive link (docs/intake/README.md § After a client call), and keep the recording itself on the shared drive.")


def done(root, state, paths, note, core):
    intake = state.setdefault("intake", {})
    processed = intake.setdefault("processed", {})
    for raw in paths:
        p = (root / raw) if not Path(raw).is_absolute() else Path(raw)
        if not p.exists():
            sys.exit(f"No such file: {raw}")
        processed[p.resolve().relative_to(root.resolve()).as_posix()] = _sha(p)
        state["log"].append({"at": core.now(), "event": f"intake: processed {p.name}", "note": note or ""})
    core.save_state(root, state)
    print(f"✓ {len(paths)} marked processed")


def body_for(args, state, on_github=True):
    lines = [f"**Source:** {args.source} · {args.ref}", f"**Type:** {args.type}"]
    if args.page:
        lines.append(f"**Page:** {args.page}")
    if args.quote:
        lines += ["", "The client's words:", "", "> " + args.quote.replace("\n", "\n> ")]
    if args.body:
        lines += ["", args.body]
    it = "this issue" if on_github else "this file"
    change = "a pull request that says `Closes #<this issue>`" if on_github else "the change itself (then set `status: done` above)"
    lines += ["", "---",
              f"When this is answered: a fact goes into `docs/truth.md` (claims register, with {it} as its source); "
              f"a decision into `docs/decisions.md`; a change into {change}."]
    return "\n".join(lines) + "\n"


def add(root, state, args, core):
    if args.type not in TYPES:
        sys.exit(f"--type must be one of: {', '.join(TYPES)}")
    if args.source not in SOURCES:
        sys.exit(f"--source must be one of: {', '.join(SOURCES)}")
    if not args.ref:
        sys.exit("--ref is required: say exactly where this came from (email date + sender, recording + timestamp, link).")
    import github_board as gb  # noqa: E402  (beside this file)
    stage = args.stage or gb.TYPE_STAGE.get(args.type, "Inbox")
    if stage not in gb.STAGE_OPTIONS:
        sys.exit(f"--stage must be one of: {', '.join(gb.STAGE_OPTIONS)}")
    on_github = gb.configured(state) and not args.local
    body = body_for(args, state, on_github)
    record = {"at": core.now(), "title": args.title, "type": args.type, "source": args.source, "ref": args.ref, "stage": stage}
    if on_github:
        g = gb.cfg(state)
        cmd = ["issue", "create", "--repo", g["repo"], "--title", args.title, "--body-file", "-",
               "--label", "intake", "--label", f"type:{args.type}", "--label", f"source:{args.source}"]
        url = gb.gh(cmd, args.dry_run, stdin=body)
        gb.add_to_board(state, url or "<issue-url>", stage, args.dry_run)
        record["issue"] = url
        where = url or "(dry run)"
    else:
        items = root / ITEMS
        n = len(list(items.glob("*.md"))) + 1 if items.exists() else 1
        slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")[:50]
        path = items / f"{n:03d}-{slug}.md"
        front = f"---\ntitle: {json.dumps(args.title, ensure_ascii=False)}\ntype: {args.type}\nsource: {args.source}\nstage: {stage}\nstatus: open\nfiled: {record['at'][:10]}\n---\n\n"
        if args.dry_run:
            print(f"  would write {path.relative_to(root).as_posix()}")
        else:
            items.mkdir(parents=True, exist_ok=True)
            path.write_text(front + body, encoding="utf-8")
        record["file"] = path.relative_to(root).as_posix()
        where = record["file"]
    if args.dry_run:
        print(body)
        print("Dry run: nothing filed.")
        return
    state.setdefault("intake", {}).setdefault("items", []).append(record)
    state["log"].append({"at": record["at"], "event": f"intake: {args.type} from {args.source}", "note": args.title})
    core.save_state(root, state)
    print(f"✓ Filed ({stage}): {where}")


def listing(root, state):
    import github_board as gb  # noqa: E402
    if gb.configured(state):
        g = gb.cfg(state)
        rows = gb.gh(["issue", "list", "--repo", g["repo"], "--label", "intake", "--state", "open", "--limit", "200",
                      "--json", "number,title,labels"], parse=True) or []
        for i in rows:
            labels = ", ".join(l["name"] for l in i["labels"] if l["name"] != "intake")
            print(f"  #{i['number']:<5} {i['title']}" + (f"  [{labels}]" if labels else ""))
        print(f"{len(rows)} open")
        return
    items = sorted((root / ITEMS).glob("*.md")) if (root / ITEMS).exists() else []
    open_items = [p for p in items if "\nstatus: open\n" in p.read_text(encoding="utf-8")]
    for p in open_items:
        title = re.search(r"^title: (.*)$", p.read_text(encoding="utf-8"), re.M)
        print(f"  {p.name}  {json.loads(title.group(1)) if title else ''}")
    print(f"{len(open_items)} open (set `status: done` in a file to close it)")
