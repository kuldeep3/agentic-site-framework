"""Weekly measurement for one client project: collect the numbers, then draft the report.

Used by `bin/asf report`. Standard library only. Sources, each optional:

  wordpress       leads from the site's private metrics endpoint (first-party: enquiries, needs,
                  pages, sources). Needs ASF_WP_USER and ASF_WP_APP_PASSWORD (an Application Password).
  health          the home page's status and response time, a full crawl (qa/crawl.py) and the launch
                  scan (qa/launch.py: security, performance, accessibility, launch settings; plus
                  Lighthouse and Core Web Vitals when PSI_API_KEY is set). New problems since last
                  week's scan are listed separately.
  ga4             sessions, users, engagement and the site's events, from the GA4 Data API.
                  Needs GA4_PROPERTY_ID and GOOGLE_ACCESS_TOKEN (e.g. `gcloud auth print-access-token`
                  or a CI auth step with the analytics.readonly scope).
  search_console  clicks, impressions and top queries. Needs GSC_SITE_URL and GOOGLE_ACCESS_TOKEN
                  (webmasters.readonly scope).
  ai_search       the tracked prompts from asf.json (measurement.prompts). Checking whether AI
                  assistants cite the client is left to the agent (/asf report) or a connector.

The GA4 and Search Console calls follow Google's documented request shapes but have not yet been
run against a live property; a failure is reported in the data file, never hidden.
"""
import base64
import datetime
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

EVENTS = ["lead_submit", "cta_click", "book_call_open", "phone_click", "newsletter_signup", "offer_view"]


def week(to=None, frm=None):
    """Default: the 7 days ending yesterday. Returns (from, to, prev_from, prev_to) as ISO dates."""
    end = datetime.date.fromisoformat(to) if to else datetime.date.today() - datetime.timedelta(days=1)
    start = datetime.date.fromisoformat(frm) if frm else end - datetime.timedelta(days=6)
    days = (end - start).days + 1
    p_end = start - datetime.timedelta(days=1)
    p_start = p_end - datetime.timedelta(days=days - 1)
    return start.isoformat(), end.isoformat(), p_start.isoformat(), p_end.isoformat()


def http_json(url, *, method="GET", body=None, headers=None, timeout=30):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"User-Agent": "ASF-report/1.0", **(headers or {})})
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def site_url(state):
    return (state.get("deploy", {}).get("production_url") or state.get("site_url") or "").rstrip("/") + "/"


# ── sources ──────────────────────────────────────────────────────────────────────
def src_wordpress(state, rng):
    user, pw = os.environ.get("ASF_WP_USER"), os.environ.get("ASF_WP_APP_PASSWORD")
    if not (user and pw):
        return {"status": "not connected", "how": "Set ASF_WP_USER and ASF_WP_APP_PASSWORD (an Application Password for an admin)."}
    ns = state.get("rest_namespace", "")
    url = f"{site_url(state)}wp-json/{ns}/metrics?" + urllib.parse.urlencode({"from": rng[0], "to": rng[1]})
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    try:
        return {"status": "ok", "data": http_json(url, headers={"Authorization": f"Basic {token}"})}
    except (urllib.error.URLError, ValueError) as e:
        return {"status": "error", "error": str(e)[:200], "url": url}


def src_health(state, root, crawl=True):
    url = site_url(state)
    out = {"status": "ok", "url": url}
    try:
        t = time.time()
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ASF-report/1.0"}), timeout=30) as r:
            out["home_status"] = r.status
        out["home_ms"] = round((time.time() - t) * 1000)
    except urllib.error.HTTPError as e:
        out.update(status="error", home_status=e.code)
    except urllib.error.URLError as e:
        return {"status": "error", "url": url, "error": str(e)[:200]}
    if crawl:
        crawler = root / "docs/framework/qa/crawl.py"
        r = subprocess.run([sys.executable, str(crawler), url], capture_output=True, text=True, timeout=900)
        summary = (r.stdout.strip().splitlines() or [""])[-1]
        m = re.search(r"(\d+) pages .*?(\d+) error\(s\) · (\d+) warning", summary)
        out["crawl"] = {"summary": summary, **({"pages": int(m.group(1)), "errors": int(m.group(2)), "warnings": int(m.group(3))} if m else {})}
        out["launch"] = launch_scan(root, state, url)
    return out


def launch_scan(root, state, url):
    """Security, performance, accessibility and launch settings (qa/launch.py), kept small for the data file."""
    scanner = root / "docs/framework/qa/launch.py"
    if not scanner.exists():
        return {"status": "not run", "why": "docs/framework/qa/launch.py is missing (update the framework copy)"}
    groups = "security,performance,accessibility,launch" + (",lighthouse" if os.environ.get("PSI_API_KEY") else "")
    cmd = [sys.executable, str(scanner), url, "--only", groups, "--json", "-"]
    if state.get("deploy", {}).get("production_url"):
        cmd += ["--env", "production"]
    try:
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=900)
        full = json.loads(r.stdout)
    except (subprocess.TimeoutExpired, ValueError) as e:
        return {"status": "error", "error": str(e)[:200]}
    groups_out = {}
    for name, g in full["groups"].items():
        keep = [f for f in g["findings"] if f["level"] in ("error", "warning")]
        groups_out[name] = {"errors": g["errors"], "warnings": g["warnings"], "passed": g["passed"],
                            "findings": [{"level": f["level"], "message": f["message"]} for f in keep[:12]]}
    return {"status": "ok", "env": full["env"], "groups": groups_out, "facts": full["facts"]}


def previous_scan(root, to):
    """Last week's launch scan, from the newest data file before this one."""
    files = sorted(p for p in (root / "docs/reports/data").glob("*.json") if p.stem < to)
    for p in reversed(files):
        try:
            launch = json.loads(p.read_text(encoding="utf-8"))["sources"]["health"].get("launch", {})
        except (ValueError, KeyError):
            continue
        if launch.get("status") == "ok":
            return launch
    return None


def src_ga4(rng):
    prop, token = os.environ.get("GA4_PROPERTY_ID"), os.environ.get("GOOGLE_ACCESS_TOKEN")
    if not (prop and token):
        return {"status": "not connected", "how": "Set GA4_PROPERTY_ID and GOOGLE_ACCESS_TOKEN, or let the agent pull GA4 through a connector."}
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport"
    headers = {"Authorization": f"Bearer {token}"}
    ranges = [{"startDate": rng[0], "endDate": rng[1], "name": "this"}, {"startDate": rng[2], "endDate": rng[3], "name": "previous"}]

    def by_range(resp, metric_names):
        out = {"this": {}, "previous": {}}
        for row in resp.get("rows", []):
            dims = [d.get("value") for d in row.get("dimensionValues", [])]
            which = "this" if "this" in dims else "previous" if "previous" in dims else None
            key = next((d for d in dims if d not in ("this", "previous")), None)
            if not which:
                continue
            vals = [float(m.get("value", 0)) for m in row.get("metricValues", [])]
            if key:
                out[which][key] = vals[0]
            else:
                out[which].update(dict(zip(metric_names, vals)))
        return out

    try:
        traffic = http_json(url, method="POST", headers=headers, body={"dateRanges": ranges, "metrics": [{"name": "sessions"}, {"name": "totalUsers"}, {"name": "engagementRate"}]})
        events = http_json(url, method="POST", headers=headers, body={
            "dateRanges": ranges, "dimensions": [{"name": "eventName"}], "metrics": [{"name": "eventCount"}],
            "dimensionFilter": {"filter": {"fieldName": "eventName", "inListFilter": {"values": EVENTS}}},
        })
        return {"status": "ok", "traffic": by_range(traffic, ["sessions", "totalUsers", "engagementRate"]), "events": by_range(events, ["eventCount"])}
    except (urllib.error.URLError, ValueError) as e:
        return {"status": "error", "error": str(e)[:200]}


def src_search_console(rng):
    site, token = os.environ.get("GSC_SITE_URL"), os.environ.get("GOOGLE_ACCESS_TOKEN")
    if not (site and token):
        return {"status": "not connected", "how": "Set GSC_SITE_URL and GOOGLE_ACCESS_TOKEN, or let the agent pull Search Console through a connector."}
    url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{urllib.parse.quote(site, safe='')}/searchAnalytics/query"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        totals = http_json(url, method="POST", headers=headers, body={"startDate": rng[0], "endDate": rng[1]})
        prev = http_json(url, method="POST", headers=headers, body={"startDate": rng[2], "endDate": rng[3]})
        queries = http_json(url, method="POST", headers=headers, body={"startDate": rng[0], "endDate": rng[1], "dimensions": ["query"], "rowLimit": 10})
        pick = lambda r: (r.get("rows") or [{}])[0]  # noqa: E731
        return {"status": "ok", "this": pick(totals), "previous": pick(prev), "top_queries": queries.get("rows", [])}
    except (urllib.error.URLError, ValueError) as e:
        return {"status": "error", "error": str(e)[:200]}


def collect(root, state, to=None, frm=None, crawl=True):
    rng = week(to, frm)
    prompts = state.get("measurement", {}).get("prompts") or []
    health = src_health(state, root, crawl)
    launch = health.get("launch", {})
    before = previous_scan(root, rng[1]) if launch.get("status") == "ok" else None
    if before:
        seen = {f["message"] for g in before["groups"].values() for f in g["findings"]}
        launch["new_since_last_week"] = [f"{name}: {f['message']}" for name, g in launch["groups"].items()
                                         for f in g["findings"] if f["level"] == "error" and f["message"] not in seen]
    return {
        "client": state.get("client"), "from": rng[0], "to": rng[1], "previous": {"from": rng[2], "to": rng[3]},
        "generated": datetime.datetime.now().astimezone().isoformat(timespec="minutes"),
        "baseline": state.get("measurement", {}).get("baseline", {}),
        "sources": {
            "wordpress": src_wordpress(state, rng),
            "health": health,
            "ga4": src_ga4(rng),
            "search_console": src_search_console(rng),
            "ai_search": {"status": "for the agent", "prompts": prompts},
        },
    }


# ── report draft ──────────────────────────────────────────────────────────────────
def change(now, before):
    if before in (None, 0):
        return "new" if now else "–"
    pct = (now - before) / before * 100
    return f"{'+' if pct >= 0 else ''}{pct:.0f}%"


def top(d, n=5):
    return list(d.items())[:n] if isinstance(d, dict) else []


def draft(data):
    s = data["sources"]
    lines = [
        f"# {data['client']} website: week of {data['from']} to {data['to']}",
        "",
        f"*Draft from `asf report` on {data['generated'][:10]}. Status: **draft, review before sending.** Data: `docs/reports/data/{data['to']}.json`*",
        "",
        "## The three things",
        "1. **What happened:** [one sentence, with the number]",
        "2. **Why we think so:** [the cause visible in the data, or \"unclear\"]",
        "3. **What we'll do this week:** [one action, an owner and a day]",
        "",
        "## Numbers",
        "| Metric | This week | Previous week | Change |",
        "|---|---|---|---|",
    ]
    wp = s["wordpress"]
    if wp.get("status") == "ok":
        cur, prev = wp["data"]["leads"], wp["data"]["previous"]["leads"]
        for label, key in (("Enquiries (brief form)", "brief"), ("Newsletter sign-ups", "newsletter"), ("All leads", "total")):
            lines.append(f"| {label} | {cur[key]} | {prev[key]} | {change(cur[key], prev[key])} |")
    else:
        lines.append(f"| Leads | not collected | | {wp.get('how') or wp.get('error', '')} |")
    ga = s["ga4"]
    if ga.get("status") == "ok":
        t, p = ga["traffic"]["this"], ga["traffic"]["previous"]
        lines.append(f"| Sessions | {t.get('sessions', 0):.0f} | {p.get('sessions', 0):.0f} | {change(t.get('sessions', 0), p.get('sessions'))} |")
        lines.append(f"| Users | {t.get('totalUsers', 0):.0f} | {p.get('totalUsers', 0):.0f} | {change(t.get('totalUsers', 0), p.get('totalUsers'))} |")
        lines.append(f"| Engagement rate | {t.get('engagementRate', 0) * 100:.0f}% | {p.get('engagementRate', 0) * 100:.0f}% | |")
        for ev in EVENTS:
            a, b = ga["events"]["this"].get(ev, 0), ga["events"]["previous"].get(ev, 0)
            lines.append(f"| `{ev}` events | {a:.0f} | {b:.0f} | {change(a, b)} |")
    else:
        lines.append(f"| Traffic (GA4) | not collected | | {ga.get('how') or ga.get('error', '')} |")
    base = data.get("baseline") or {}
    if base:
        lines += ["", "**Against the goal:** " + ", ".join(f"{k} = {v}" for k, v in base.items())]
    if wp.get("status") == "ok":
        cur = wp["data"]["leads"]
        for title, key in (("What enquiries asked for", "by_need"), ("Pages that produced leads", "by_page"), ("Where leads came from", "by_source")):
            rows = top(cur[key])
            lines += ["", f"### {title}"]
            lines += ["| | Leads |", "|---|---|"] + [f"| {k} | {v} |" for k, v in rows] if rows else ["None this week."]
    sc = s["search_console"]
    lines += ["", "## Search"]
    if sc.get("status") == "ok":
        t, p = sc["this"], sc["previous"]
        lines.append(f"Clicks {t.get('clicks', 0):.0f} ({change(t.get('clicks', 0), p.get('clicks'))}), impressions {t.get('impressions', 0):.0f}, average position {t.get('position', 0):.1f}.")
        lines += ["", "| Query | Clicks | Impressions | Position |", "|---|---|---|---|"]
        lines += [f"| {r['keys'][0]} | {r.get('clicks', 0):.0f} | {r.get('impressions', 0):.0f} | {r.get('position', 0):.1f} |" for r in sc["top_queries"]]
    else:
        lines.append(f"Not collected: {sc.get('how') or sc.get('error', '')}")
    ai = s["ai_search"]
    lines += ["", "## AI search (tracked prompts)"]
    if ai["prompts"]:
        lines += ["| Prompt | Cited? | Where / by which assistant |", "|---|---|---|"]
        lines += [f"| {p} | [not checked yet] | |" for p in ai["prompts"]]
    else:
        lines.append("No tracked prompts yet: `bin/asf set measurement.prompts '[\"prompt one\", \"prompt two\"]'`.")
    h = s["health"]
    lines += ["", "## Site health"]
    if h.get("status") == "ok" or "home_status" in h:
        crawl = h.get("crawl", {})
        lines.append(f"Home page: HTTP {h.get('home_status')} in {h.get('home_ms', '?')} ms. Crawl: {crawl.get('summary', 'not run')}.")
        ls = h.get("launch", {})
        if ls.get("status") == "ok":
            lines += ["", "| Check | Errors | Warnings | First issue |", "|---|---|---|---|"]
            for name, g in ls["groups"].items():
                first = next((f["message"] for f in g["findings"] if f["level"] == "error"), None) or next((f["message"] for f in g["findings"]), "–")
                lines.append(f"| {name.capitalize()} | {g['errors']} | {g['warnings']} | {first.replace('|', '/')[:110]} |")
            facts = ls.get("facts", {})
            bits = []
            if "cert_days" in facts:
                bits.append(f"certificate valid for {facts['cert_days']} more days")
            if "home_kb" in facts:
                bits.append(f"home page {facts['home_kb']:,} KB in {facts.get('home_requests', '?')} requests")
            inside = facts.get("inside", {}).get("updates", {})
            if inside:
                n = len(inside.get("plugins", [])) + len(inside.get("themes", [])) + (1 if inside.get("wordpress") else 0)
                bits.append(f"{n} update(s) waiting" if n else "WordPress, plugins and themes up to date")
            if facts.get("lighthouse"):
                bits.append("Lighthouse " + "; ".join(f"{p} " + "/".join(str(v) for v in sc.values()) for p, sc in facts["lighthouse"].items()) + " (perf/a11y/best practices/SEO)")
            if facts.get("core_web_vitals_overall"):
                bits.append(f"Core Web Vitals (real users): {facts['core_web_vitals_overall']}")
            if bits:
                text = "; ".join(bits)
                lines += ["", text[:1].upper() + text[1:] + "."]
            new = ls.get("new_since_last_week")
            if new:
                lines += ["", "**New since last week:**"] + [f"- {m}" for m in new[:8]]
            elif new is not None:
                lines += ["", "No new errors since last week's scan."]
        elif ls:
            lines.append(f"Launch scan: {ls.get('status')} ({ls.get('why') or ls.get('error', '')}).")
    else:
        lines.append(f"Couldn't reach {h.get('url')}: {h.get('error', '')}")
    lines += ["", "## Coming up", "- [this month's improvement proposal, if any, with size and price]", ""]
    return "\n".join(lines)


def run(root, state, to=None, frm=None, crawl=True, force=False):
    data = collect(root, state, to, frm, crawl)
    reports = root / "docs/reports"
    (reports / "data").mkdir(parents=True, exist_ok=True)
    data_path = reports / "data" / f"{data['to']}.json"
    data_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path = reports / f"{data['to']}.md"
    wrote_md = force or not md_path.exists()
    if wrote_md:
        md_path.write_text(draft(data), encoding="utf-8")
    return data, data_path, md_path, wrote_md
