"""Campaigns: one offer, one landing page, tagged links, and a result. Used by `bin/asf campaign …`.

    bin/asf campaign new spring-audit --name "Spring growth audit" --landing /spring-audit/ \\
        --start 2026-12-01 --end 2026-12-31 --goal 20 --budget 3000 \\
        --channels google/cpc,linkedin/paid-social,newsletter/email
    bin/asf campaign links spring-audit --content headline-a,headline-b
    bin/asf campaign check spring-audit
    bin/asf campaign list
    bin/asf campaign report spring-audit [--write]
    bin/asf campaign close spring-audit --outcome redirect --to /services/audit/ --note "…"
    bin/asf set campaigns.spring-audit.spend 1450        (spend so far, for cost per lead)

State lives in asf.json under "campaigns". The brief is docs/campaigns/<slug>.md, the page is
content/pages/<landing>.html (made from the framework's templates). Leads are attributed by their
utm_campaign tag, which the theme carries from the landing page to the form. Standard library only.
"""
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRAMEWORK = HERE.parent
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PAID = {"cpc", "ppc", "paid-social", "paid-search", "display", "paid", "video", "affiliate"}
STOP = set("the a an and or for to of in on with your you our we is are be get at by from this that it its how what into".split())


def as_dict(value):
    """A breakdown from the metrics endpoint. Older plugins send an empty one as [] instead of {}."""
    return value if isinstance(value, dict) else {}


def tag(value):
    """A tag value: lowercase, hyphens, nothing else. One spelling per source, or reports split it."""
    return re.sub(r"[^a-z0-9._-]+", "-", (value or "").strip().lower()).strip("-")


def day(s):
    return datetime.date.fromisoformat(s)


def status(c, on=None):
    on = on or datetime.date.today()
    if c.get("closed"):
        return "closed"
    if on < day(c["start"]):
        return "planned"
    return "live" if on <= day(c["end"]) else "ended"


def page_file(root, landing):
    return root / "content/pages" / (landing.strip("/").replace("/", "-") + ".html")


def site_for(state, live=True):
    dep = state.get("deploy", {})
    url = (dep.get("production_url") if live else None) or dep.get("production_url") or dep.get("staging_url") or state.get("site_url") or ""
    return url.rstrip("/")


def get(state, slug):
    c = state.get("campaigns", {}).get(slug)
    if not c:
        known = ", ".join(state.get("campaigns", {})) or "none yet"
        sys.exit(f"No campaign \"{slug}\" (campaigns: {known}). Start one with `bin/asf campaign new {slug} …`.")
    return c


# ── new ─────────────────────────────────────────────────────────────────────────────────
def new(root, state, a, core):
    slug = a.slug
    if not slug or not SLUG.match(slug):
        sys.exit("The campaign slug becomes utm_campaign: lowercase letters, digits and hyphens (e.g. spring-audit).")
    camps = state.setdefault("campaigns", {})
    if slug in camps:
        sys.exit(f"\"{slug}\" exists. `bin/asf campaign check {slug}`.")
    try:
        start, end = day(a.start), day(a.end)
    except (TypeError, ValueError):
        sys.exit("--start and --end are dates: 2026-12-01")
    if end < start:
        sys.exit("--end is before --start.")
    landing = "/" + (a.landing or slug).strip("/") + "/"
    channels = []
    for ch in (a.channels or "").split(","):
        if not ch.strip():
            continue
        parts = [tag(p) for p in ch.split("/")]
        if len(parts) != 2 or not all(parts):
            sys.exit(f"Channel \"{ch}\" should be source/medium, e.g. google/cpc or newsletter/email.")
        channels.append("/".join(parts))
    c = {
        "name": a.name or slug.replace("-", " ").capitalize(), "landing": landing, "start": a.start, "end": a.end,
        "goal_leads": a.goal, "budget": a.budget, "spend": None, "channels": channels, "index": bool(a.index),
        "cta": a.cta, "created": core.now(), "links": [],
    }
    camps[slug] = c

    brief = root / "docs/campaigns" / f"{slug}.md"
    if not brief.exists():
        brief.parent.mkdir(parents=True, exist_ok=True)
        rows = "\n".join(f"| {ch.split('/')[0]} | {ch.split('/')[1]} | | |" for ch in channels) or "| | | | |"
        text = (FRAMEWORK / "templates/campaign-brief.md").read_text(encoding="utf-8")
        text = (text.replace("__NAME__", c["name"]).replace("__SLUG__", slug).replace("__LANDING__", landing)
                .replace("__START__", a.start).replace("__END__", a.end)
                .replace("__GOAL__", str(a.goal) if a.goal else "[number of leads]")
                .replace("__BUDGET__", f"{a.budget:,.0f}" if a.budget else "[amount and currency]")
                .replace("__CHANNEL_ROWS__", rows)
                .replace("__INDEX__", "Indexed: this offer stays useful after the campaign, so search engines may list the page." if c["index"]
                         else "Not indexed (noindex): the page exists for this campaign's traffic and shouldn't compete with the main service pages in search."))
        brief.write_text(text, encoding="utf-8")
    page = page_file(root, landing)
    if not page.exists():
        page.parent.mkdir(parents=True, exist_ok=True)
        text = (FRAMEWORK / "templates/campaign-landing.html").read_text(encoding="utf-8")
        text = (text.replace("__TITLE__", c["name"]).replace("__PAGE_SLUG__", landing.strip("/"))
                .replace("__CTA__", c["cta"]).replace("__CLIENT__", state.get("client", ""))
                .replace("__NOINDEX__", "" if c["index"] else "noindex: true\n"))
        page.write_text(text, encoding="utf-8")
    parent = landing.strip("/").rsplit("/", 1)[0] if "/" in landing.strip("/") else ""
    if parent and not page_file(root, "/" + parent + "/").exists():
        print(f"! /{parent}/ has no page in content/pages/: the seed needs the parent first. Create it, or use a top-level URL like /{landing.strip('/').split('/')[-1]}/.")
    state["log"].append({"at": core.now(), "event": f"campaign {slug} created", "note": f"{landing} · {a.start} → {a.end}"})
    rel = lambda p: p.relative_to(root).as_posix()  # noqa: E731
    print(f"Campaign {slug}: {c['name']}, {a.start} → {a.end}, landing page {landing}")
    print(f"  Brief: {rel(brief)}\n  Page:  {rel(page)} (template page-landing{'' if c['index'] else ', noindex'})")
    print("Next:\n  1. Fill the brief with the client (prompt docs/framework/prompts/10-campaign.md writes the page from it)."
          "\n  2. Seed the page locally (bin/setup.sh --reseed), check it, then publish it on the live site before the start date."
          f"\n  3. `bin/asf campaign links {slug} --content …` for the tagged links; `bin/asf campaign check {slug}` before anything goes out.")


# ── links ───────────────────────────────────────────────────────────────────────────────
def links(root, state, a, core):
    slug = a.slug
    c = get(state, slug)
    if a.channels:
        for ch in a.channels.split(","):
            parts = [tag(p) for p in ch.split("/")]
            if len(parts) == 2 and all(parts) and "/".join(parts) not in c["channels"]:
                c["channels"].append("/".join(parts))
    if not c["channels"]:
        sys.exit(f"No channels yet: `bin/asf campaign links {slug} --channels google/cpc,newsletter/email`.")
    contents = [tag(x) for x in a.content.split(",") if tag(x)] if a.content else (c.get("contents") or [""])
    c["contents"] = [x for x in contents if x]
    base = site_for(state)
    if not state.get("deploy", {}).get("production_url"):
        print(f"! No production URL recorded: links point to {base or '(nothing)'}. Set deploy.production_url before sending them.")
    rows = []
    for ch in c["channels"]:
        source, medium = ch.split("/")
        for content in contents:
            q = {"utm_source": source, "utm_medium": medium, "utm_campaign": slug}
            if content:
                q["utm_content"] = content
            rows.append({"source": source, "medium": medium, "content": content, "url": f"{base}{c['landing']}?{urllib.parse.urlencode(q)}"})
    c["links"] = rows
    table = ["| Source | Medium | Creative | Link |", "|---|---|---|---|"] + [f"| {r['source']} | {r['medium']} | {r['content'] or '–'} | {r['url']} |" for r in rows]
    brief = root / "docs/campaigns" / f"{slug}.md"
    if brief.exists():
        text = brief.read_text(encoding="utf-8")
        block = "<!-- asf:links -->\n" + "\n".join(table) + "\n<!-- /asf:links -->"
        text, n = re.subn(r"<!-- asf:links -->.*?<!-- /asf:links -->", lambda m: block, text, flags=re.S)
        if not n:
            text = text.rstrip() + "\n\n## Tracking links\n" + block + "\n"
        brief.write_text(text, encoding="utf-8")
    state["log"].append({"at": core.now(), "event": f"campaign {slug} links", "note": f"{len(rows)} links"})
    print("\n".join(table))
    print(f"\n{len(rows)} links, also in docs/campaigns/{slug}.md. Use only these: a hand-typed tag splits the report.")


# ── check ───────────────────────────────────────────────────────────────────────────────
BRIEF_SECTIONS = ["audience", "the promise", "offer", "proof", "call to action", "after it ends", "success"]


def promise_of(brief_text, core):
    body = core.section(brief_text, "the promise") or ""
    m = re.search(r"^>\s*(.+)$", body, re.M)
    return m.group(1).strip() if m else ""


def words(text):
    return {w for w in re.findall(r"[a-z0-9']{4,}", text.lower()) if w not in STOP}


def check(root, state, slug, core, url=None):
    """Return a list of (level, message): level is error, warning or ok."""
    c = get(state, slug)
    out = []
    st = status(c)
    # The brief.
    brief = root / "docs/campaigns" / f"{slug}.md"
    promise = ""
    if not brief.exists():
        out.append(("error", f"No brief: docs/campaigns/{slug}.md"))
    else:
        text = brief.read_text(encoding="utf-8")
        empty = [s for s in BRIEF_SECTIONS if (b := core.section(text, s)) is None or core.PLACEHOLDER.search(b)
                 or len(re.sub(r"[^A-Za-z]", "", " ".join(ln for ln in b.splitlines() if not ln.strip().startswith("*")))) < 12]
        out.append(("error", "Brief not filled: " + ", ".join(empty)) if empty else ("ok", "Brief filled"))
        promise = promise_of(text, core)
    # The page source.
    src = page_file(root, c["landing"])
    if not src.exists():
        out.append(("error", f"No page source: {src.relative_to(root).as_posix()}"))
    else:
        s = src.read_text(encoding="utf-8")
        if "template: page-landing" not in s:
            out.append(("warning", "The page doesn't use the page-landing template (it shows the full menu, so visitors wander off)."))
        chips = s.count("hm-confirm")
        out.append(("error" if st in ("live", "ended") else "warning", f"{chips} [CONFIRM] chip(s) left in the page") if chips else ("ok", "Page copy confirmed"))
    # Dates and money.
    if st == "ended":
        late = (datetime.date.today() - day(c["end"])).days
        out.append(("error" if late > 7 else "warning", f"Ended {late} day(s) ago: `bin/asf campaign close {slug}` (keep, redirect or unpublish the page)."))
    paid = any(ch.split("/")[1] in PAID for ch in c["channels"])
    if paid and st in ("live", "ended") and c.get("spend") is None:
        out.append(("warning", f"Paid channels but no spend recorded: `bin/asf set campaigns.{slug}.spend 1450` (for cost per lead)."))
    out.append(("ok", f"{len(c['links'])} tracking links") if c["links"] else ("warning", f"No tracking links yet: `bin/asf campaign links {slug}`."))

    # The live page.
    base = (url or site_for(state)).rstrip("/")
    if not base:
        out.append(("error", "No site URL to check (set site_url or deploy.production_url)."))
        return out
    sys.path.insert(0, str(FRAMEWORK / "qa"))
    import launch  # noqa: E402
    env = launch.detect_env(base)
    http = launch.Http(insecure=env == "local")
    page_url = base + c["landing"]
    r = http.get(page_url, cache=False)
    if r.status != 200:
        out.append(("error", f"{page_url} returns HTTP {r.status}: publish the page{' before ' + c['start'] if st == 'planned' else ''}."))
        return out
    d = launch.parse(r.text)
    out.append(("ok", f"Live at {page_url}"))
    h1 = next((t for lvl, t in d.headings if lvl == 1), "")
    if core.PLACEHOLDER.search(promise) or "CONFIRM" in h1:
        promise = ""  # not written yet: the brief and page checks above already say so
    if promise and h1:
        shared = words(promise) & words(h1)
        out.append(("ok", f"Message match: H1 and promise share \"{', '.join(sorted(shared))}\"") if shared
                   else ("warning", f"Message match: the H1 (\"{h1[:60]}\") shares no words with the promise (\"{promise[:60]}\")."))
    noindex = "noindex" in d.meta.get("robots", "")
    if c.get("index") and noindex:
        out.append(("error", "The brief says indexed, but the page is noindex."))
    elif not c.get("index") and not noindex:
        out.append(("warning", "The page is indexable; the brief says noindex (add `noindex: true` to its front matter and reseed, or tick it in the SEO panel)."))
    else:
        out.append(("ok", "Indexing as the brief says"))
    has_form = "data-brief" in r.text or bool(d.forms)
    out.append(("ok", "Form on the page") if has_form else ("error", "No form on the page: put it there (it's attributed even before consent, and it converts better than a click away)."))
    if has_form and 'id="form"' not in r.text:
        out.append(("warning", "No element with id=\"form\": the header button jumps to #form."))
    out.append(("ok", "Lead capture script present") if "leadEndpoint" in r.text else ("error", "The theme's lead script isn't on the page: enquiries won't carry the campaign tag."))
    exits = {x[0].get("href") for x, zone in zip(d.anchors, d.anchor_zones) if zone == "body"
             and not x[0].get("href", "").startswith(("#", "tel:", "mailto:")) and x[0].get("href", "").rstrip("/") not in (page_url.rstrip("/"), c["landing"].rstrip("/"))}
    out.append(("warning", f"{len(exits)} links lead away from the page (keep it to the form, and at most a few): " + ", ".join(sorted(exits)[:4]))
               if len(exits) > 3 else ("ok", f"{len(exits)} link(s) lead away"))
    # Accessibility and performance of this one page.
    scanner = FRAMEWORK / "qa/launch.py"
    try:
        p = subprocess.run([sys.executable, str(scanner), base, "--pages", c["landing"], "--only", "accessibility,performance", "--json", "-"],
                           cwd=root, capture_output=True, text=True, timeout=300)
        res = json.loads(p.stdout)
        errs = [f"{g}: {f['message']}" for g, grp in res["groups"].items() for f in grp["findings"] if f["level"] == "error"]
        out.append(("error", "Page scan: " + " · ".join(errs[:3])) if errs else ("ok", "Page scan: no accessibility or performance errors"))
    except (subprocess.TimeoutExpired, ValueError, KeyError) as e:
        out.append(("warning", f"Page scan didn't run: {str(e)[:80]}"))
    return out


# ── results ─────────────────────────────────────────────────────────────────────────────
def results(state, slug, upto=None):
    """Leads for one campaign from its start to `upto` (default: today, or its end), from the site's metrics."""
    sys.path.insert(0, str(HERE))
    import measure  # noqa: E402
    c = get(state, slug)
    end = min(day(c["end"]), day(upto) if upto else datetime.date.today())
    if end < day(c["start"]):
        return {"status": "not started", "campaign": slug}
    wp = measure.wp_metrics(state, c["start"], end.isoformat(), campaign=slug)
    if wp.get("status") != "ok":
        return {**wp, "campaign": slug}
    leads = wp["data"]["leads"]
    span = (day(c["end"]) - day(c["start"])).days + 1
    elapsed = (end - day(c["start"])).days + 1
    expected = round(c["goal_leads"] * elapsed / span, 1) if c.get("goal_leads") else None
    out = {"status": "ok", "campaign": slug, "from": c["start"], "to": end.isoformat(), "elapsed_days": elapsed, "days": span,
           "leads": leads["total"], "expected_by_now": expected, "goal": c.get("goal_leads"),
           "cost_per_lead": round(c["spend"] / leads["total"], 2) if c.get("spend") and leads["total"] else None,
           "spend": c.get("spend"), **{k: as_dict(leads.get(k)) for k in ("by_content", "by_source", "by_medium", "by_landing", "by_page", "by_day")}}
    sessions = measure.ga4_campaign_sessions([slug], c["start"], end.isoformat())
    if sessions.get("status") == "ok":
        n = sessions["sessions"].get(slug, 0)
        out["sessions"] = n
        out["conversion_rate"] = round(leads["total"] / n * 100, 1) if n else None
    return out


def pace_word(r):
    if r.get("expected_by_now") is None:
        return "–"
    if r.get("elapsed_days", 0) < 7 and r["expected_by_now"] < 2:
        return "too early to tell"
    if r["leads"] >= r["expected_by_now"]:
        return "on pace"
    return "behind" if r["leads"] >= 0.6 * r["expected_by_now"] else "well behind"


def report_text(state, slug, r):
    c = get(state, slug)
    lines = [f"# Campaign results: {c['name']}", "",
             f"*`{slug}` · {c['landing']} · {c['start']} → {c['end']} · as of {r.get('to', '–')}*", ""]
    if r.get("status") != "ok":
        return "\n".join(lines + [f"Not collected: {r.get('status')} ({r.get('how') or r.get('error') or ''})", ""])
    goal = f" of {r['goal']}" if r.get("goal") else ""
    lines += ["| Measure | Value |", "|---|---|",
              f"| Leads | {r['leads']}{goal} |",
              f"| Expected by now (straight line) | {r['expected_by_now'] if r['expected_by_now'] is not None else '–'} ({pace_word(r)}) |",
              f"| Spend | {r['spend'] if r.get('spend') is not None else 'not recorded'} |",
              f"| Cost per lead | {r['cost_per_lead'] if r.get('cost_per_lead') is not None else '–'} |"]
    if "sessions" in r:
        lines.append(f"| Sessions (GA4) | {r['sessions']} |")
        lines.append(f"| Visit → lead | {r['conversion_rate'] if r.get('conversion_rate') is not None else '–'}% |")
    for title, key in (("By creative (utm_content)", "by_content"), ("By source", "by_source"), ("By medium", "by_medium"),
                       ("Where they landed", "by_landing"), ("Where they sent the enquiry", "by_page")):
        rows = list(r.get(key, {}).items())[:8]
        if rows:
            lines += ["", f"### {title}", "| | Leads |", "|---|---|"] + [f"| {k} | {v} |" for k, v in rows]
    if r["by_day"]:
        lines += ["", "### By day", " · ".join(f"{d[5:]}: {n}" for d, n in r["by_day"].items())]
    lines += ["", "## What we learned", "[the creative or channel that worked, the one that didn't, and why we think so]",
              "", "## Next time", "[keep, change or stop: one line each]", ""]
    return "\n".join(lines)


def report(root, state, slug, write=False):
    r = results(state, slug)
    text = report_text(state, slug, r)
    print(text)
    if write:
        path = root / "docs/campaigns" / f"{slug}-results.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"Written: {path.relative_to(root).as_posix()}")
    return r


# ── close ───────────────────────────────────────────────────────────────────────────────
def close(root, state, a, core):
    slug = a.slug
    c = get(state, slug)
    if a.outcome == "redirect" and not a.to:
        sys.exit("--outcome redirect needs --to /where-it-goes/")
    c.update(closed=datetime.date.today().isoformat(), outcome=a.outcome, note=a.note or "")
    if a.to:
        c["redirect_to"] = a.to
    msg = []
    if a.outcome == "redirect":
        files = sorted(root.glob("wp-content/plugins/*-core/inc/redirects.php"))
        line = f"\t\t'{c['landing']}' => '{a.to}', // campaign {slug}, closed {c['closed']}\n"
        done = False
        if files:
            text = files[0].read_text(encoding="utf-8")
            m = re.search(r"function hm_redirect_map\(\)[^{]*\{\s*return array\(\n", text)
            if m and c["landing"] not in text:
                files[0].write_text(text[: m.end()] + line + text[m.end():], encoding="utf-8")
                done = True
                msg.append(f"Added {c['landing']} → {a.to} to {files[0].relative_to(root).as_posix()} (deploy the plugin, or add it to the redirect tool in use).")
        if not done:
            msg.append(f"Add this redirect: {c['landing']} → {a.to} (inc/redirects.php hm_redirect_map(), or the redirect tool in use).")
        msg.append("Then unpublish the page in WordPress.")
    elif a.outcome == "unpublish":
        msg.append(f"Unpublish {c['landing']} in WordPress (Draft), and remove it from content/pages/ so a reseed doesn't bring it back.")
    else:
        msg.append(f"The page stays at {c['landing']}. If it should be found in search, remove `noindex` and link it from a service page.")
    r = None
    if os.environ.get("ASF_WP_USER") and os.environ.get("ASF_WP_APP_PASSWORD"):
        r = report(root, state, slug, write=True)
        c["result"] = {k: r.get(k) for k in ("leads", "goal", "spend", "cost_per_lead", "sessions", "conversion_rate")} if r.get("status") == "ok" else None
    else:
        msg.append(f"Results not collected (set ASF_WP_USER and ASF_WP_APP_PASSWORD, then `bin/asf campaign report {slug} --write`).")
    state["log"].append({"at": core.now(), "event": f"campaign {slug} closed ({a.outcome})", "note": a.note or ""})
    print(f"Closed {slug}: {a.outcome}" + (f" → {a.to}" if a.to else ""))
    for m in msg:
        print("  " + m)


# ── list, gate, weekly ──────────────────────────────────────────────────────────────────
def listing(state):
    camps = state.get("campaigns", {})
    if not camps:
        print("No campaigns yet. `bin/asf campaign new <slug> --name … --landing /… --start … --end …`")
        return
    print(f"{'Campaign':<22} {'Status':<8} {'Dates':<25} {'Landing':<24} {'Goal':>5} {'Links':>5}")
    for slug, c in camps.items():
        print(f"{slug:<22} {status(c):<8} {c['start'] + ' → ' + c['end']:<25} {c['landing']:<24} {c.get('goal_leads') or '–':>5} {len(c['links']):>5}")


def gate(root, state, core):
    """G5: every live campaign passes its checks; no campaign ended more than a week ago is still open."""
    camps = state.get("campaigns", {})
    live = [s for s, c in camps.items() if status(c) == "live"]
    stale = [s for s, c in camps.items() if status(c) == "ended" and (datetime.date.today() - day(c["end"])).days > 7]
    problems = [f"{s}: close it" for s in stale]
    for s in live:
        errs = [m for lvl, m in check(root, state, s, core) if lvl == "error"]
        if errs:
            problems.append(f"{s}: {errs[0][:80]}")
    if problems:
        return False, "; ".join(problems[:3])
    return True, f"{len(live)} live campaign(s) pass" if live else "no live campaigns"


def weekly(state, rng, week_leads):
    """Rows for the weekly report: campaigns running at any point in the report's week."""
    rows = []
    frm, to = day(rng[0]), day(rng[1])
    for slug, c in state.get("campaigns", {}).items():
        if day(c["start"]) > to or day(c["end"]) < frm - datetime.timedelta(days=7):
            continue
        if c.get("closed") and day(c["closed"]) < frm:
            continue
        r = results(state, slug, upto=rng[1])
        this_week = as_dict(week_leads.get("by_campaign")).get(slug, 0) if week_leads else None
        best = next(iter(r.get("by_content", {}) or {}), None) if r.get("status") == "ok" else None
        rows.append({"campaign": slug, "name": c["name"], "status": status(c, to), "this_week": this_week,
                     "to_date": r.get("leads"), "goal": c.get("goal_leads"), "pace": pace_word(r) if r.get("status") == "ok" else "–",
                     "cost_per_lead": r.get("cost_per_lead"), "best_creative": best if best and best != "(none)" else None,
                     "conversion_rate": r.get("conversion_rate"), "collected": r.get("status")})
    return rows
