"""Requirements intake: every request, from any channel, becomes one tracked item with its source.

Clients send requirements by email, on calls, in GitHub issues, in chat and in documents.
Intake turns each request into one GitHub issue (labels `intake`, `type:*`, `source:*`, on the
board in the right Stage), or a file in docs/intake/items/ when the project isn't on GitHub.
Nothing becomes a fact on the site until the client confirms it: an answered `type:fact` issue
is copied into docs/truth.md with the issue as its source.

    bin/asf intake sources [--json]
        Raw material waiting in docs/intake/raw/ (emails, call transcripts, notes), and which
        of it has been processed. That folder is git-ignored: client correspondence stays private.
        Call recordings belong on the team's shared drive; an audio or video file found here is
        flagged, because intake reads text and needs its transcript.
        With a team, the shared drive folder is the inbox (`bin/asf set intake.drive_folder <link>`):
        everyone drops material there and /asf intake copies what's new into raw/ before reading.
        Files a teammate already processed are listed too, so nobody reads them twice.
    bin/asf intake add "Title" --type fact|question|content|page|design|bug|campaign --source email|call|meeting|issue|chat|doc|figma|other
                       --ref "where it came from" [--quote "the client's exact words"] [--body "…"] [--page /about/]
                       [--stage Requirement] [--assign role|handle] [--local] [--dry-run]
        File one request. --ref says exactly where (an email's date and sender, a recording and
        timestamp, an issue or Figma comment link) so anyone can go back to the original.
        The issue gets the label of the role that acts on it (`role:designer`…) and is assigned to
        whoever holds that role (`bin/asf team`), unless --assign names another role or handle.
    bin/asf intake done <file> […]  [--note "…"]
        Mark raw files as processed (gate G1 and G4 checks want none left unread).
    bin/asf intake list
        Open intake items.

The /asf intake command (claude-command.md) does the reading: it copies new files from the shared
drive folder, pulls new emails, transcripts, unlabelled issues and Figma comments, drafts one item
per request, shows the list to the lead and files the approved ones with `add`.

What's processed is recorded by the file's contents (a hash) in the project log, which is committed:
the same transcript is "done" on every teammate's machine, whatever folder or name it has there.
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


def processed(state):
    """{content hash: {"file", "by", "at"}} for every raw file anyone on the team has marked done."""
    out = {sha: {"file": path, "by": "", "at": ""}  # asf.json's own list, from before the log held this
           for path, sha in ((state.get("intake") or {}).get("processed") or {}).items()}
    for e in state.get("log", []):
        d = e.get("processed")
        if isinstance(d, dict) and d.get("sha"):
            out[d["sha"]] = {"file": d.get("file", ""), "by": e.get("by", ""), "at": e.get("at", "")}
    return out


def unprocessed(root, state):
    done = processed(state)
    return [p for p in raw_files(root) if _sha(p) not in done]


def elsewhere(root, state):
    """Files a teammate processed that aren't on this machine: don't fetch them from the drive again."""
    here = {_sha(p) for p in raw_files(root)}
    return sorted((d for sha, d in processed(state).items() if sha not in here and d["file"]), key=lambda d: d["file"])


def gate_check(root, state):
    """For workflow.json check type `intake_clear`: no raw source left unread."""
    left = unprocessed(root, state)
    if not raw_files(root):
        return True, "no raw sources in docs/intake/raw/"
    return not left, "" if not left else f"{len(left)} unread, e.g. {left[0].relative_to(root).as_posix()} (`/asf intake`)"


def sources(root, state, as_json=False):
    files = raw_files(root)
    left = set(unprocessed(root, state))
    away = elsewhere(root, state)
    drive = (state.get("intake") or {}).get("drive_folder")
    recordings = [p for p in files if p in left and p.suffix.lower() in AV]
    if as_json:  # for /asf intake: what to copy from the drive folder, and what to read
        rel = lambda p: p.relative_to(root).as_posix()  # noqa: E731
        print(json.dumps({"drive_folder": drive, "raw": RAW,
                          "to_process": [rel(p) for p in files if p in left and p not in recordings],
                          "recordings_without_transcript": [rel(p) for p in recordings],
                          "done_here": [rel(p) for p in files if p not in left],
                          "done_elsewhere": away}, indent=2, ensure_ascii=False))
        return
    if drive:
        print(f"Shared folder: {drive}\n  (/asf intake copies new files from it into {RAW}/ first)")
    else:
        print(f"No shared folder set. Working as a team? `bin/asf set intake.drive_folder <link>`: {RAW}/ is this machine only.")
    if not files and not away:
        print(f"Nothing in {RAW}/. Drop emails (.eml/.md/.txt), call transcripts and notes there"
              + (" or in the shared folder" if drive else "") + ", then run /asf intake.")
        return
    for p in files:
        note = "  (recording: needs its transcript)" if p in recordings else ""
        print(f"  {'·' if p in left else '✓'} {p.relative_to(root).as_posix()}{note}")
    for d in away:
        print(f"  ✓ {d['file']}  (not on this machine: done" + (f" by {d['by']}" if d["by"] else "") + (f", {d['at'][:10]}" if d["at"] else "") + ")")
    print(f"{len(left)} to process · {len(files) - len(left) + len(away)} done")
    if recordings:
        print("Intake reads text, not sound. Put each call's timestamped transcript in raw/, starting with the recording's "
              "shared-drive link (docs/intake/README.md § After a client call), and keep the recording itself on the shared drive.")


def done(root, state, paths, note, core):
    for raw in paths:
        p = (root / raw) if not Path(raw).is_absolute() else Path(raw)
        if not p.exists():
            sys.exit(f"No such file: {raw}")
        rel = p.resolve().relative_to(root.resolve()).as_posix()
        state["log"].append({"at": core.now(), "event": f"intake: processed {p.name}", "note": note or "",
                             "processed": {"file": rel, "sha": _sha(p)}})
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
    # Who acts on it: the role its type implies, or --assign (a role, or a GitHub handle).
    asked = (getattr(args, "assign", None) or "").lstrip("@")
    role = asked if asked in gb.ROLES else gb.TYPE_ROLE.get(args.type, "lead")
    handle = asked if asked and asked not in gb.ROLES else next((p["github"] for p in core.people(state, role) if p.get("github")), None)
    record = {"at": core.now(), "title": args.title, "type": args.type, "source": args.source, "ref": args.ref, "stage": stage, "role": role}
    if on_github:
        g = gb.cfg(state)
        cmd = ["issue", "create", "--repo", g["repo"], "--title", args.title, "--body-file", "-",
               "--label", "intake", "--label", f"type:{args.type}", "--label", f"source:{args.source}", "--label", f"role:{role}"]
        try:
            url = gb.gh(cmd + (["--assignee", handle] if handle else []), args.dry_run, stdin=body)
        except gb.GhError as e:
            if not handle:
                raise
            # A handle GitHub can't assign (not a collaborator yet) mustn't lose the request.
            print(f"  (couldn't assign @{handle}: {str(e)[:100]}; filed unassigned)")
            handle, url = None, gb.gh(cmd, args.dry_run, stdin=body)
        if handle:
            record["assignee"] = handle
        gb.add_to_board(state, url or "<issue-url>", stage, args.dry_run)
        record["issue"] = url
        where = url or "(dry run)"
    else:
        items = root / ITEMS
        # Named by date and title, not by a running number: two people filing on two branches never collide.
        slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")[:50]
        path = items / f"{record['at'][:10]}-{slug}.md"
        n = 2
        while path.exists():
            path, n = items / f"{record['at'][:10]}-{slug}-{n}.md", n + 1
        owner = ", ".join(p["name"] for p in core.people(state, role))
        front = (f"---\ntitle: {json.dumps(args.title, ensure_ascii=False)}\ntype: {args.type}\nsource: {args.source}\nstage: {stage}\n"
                 f"role: {role}\nowner: {json.dumps(owner, ensure_ascii=False)}\nstatus: open\nfiled: {record['at'][:10]}\n---\n\n")
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
    state["log"].append({"at": record["at"], "event": f"intake: {args.type} from {args.source}", "note": args.title, "item": record})
    core.save_state(root, state)
    print(f"✓ Filed ({stage}, {role}" + (f", @{record['assignee']}" if record.get("assignee") else "") + f"): {where}")


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
