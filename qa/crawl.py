#!/usr/bin/env python3
"""Crawl a running site and check every page the way a launch reviewer would.

    python3 crawl.py http://acme.test [--config config.json] [--strict] [--max 150]

Finds pages from the WordPress sitemap (falls back to following links from the home page), then:
  errors    non-200 pages · zero or several <h1> · no <title> · no meta description (indexable pages) ·
            JSON-LD that doesn't parse · broken internal links and images · forbidden (white-label)
            terms anywhere in the HTML, including meta and schema · missing /robots.txt or /llms.txt
  warnings  title over 60 chars · description over 160 · no canonical · [CONFIRM] chips (errors with --strict)

Standard library only. Exit code 1 when there are errors.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

HERE = Path(__file__).resolve().parent
UA = "ASF-QA/1.0 (+agentic-site-framework)"


def fetch(url, method="GET"):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", "replace") if method == "GET" else ""
            return r.status, r.geturl(), r.headers.get("Content-Type", ""), body
    except urllib.error.HTTPError as e:
        return e.code, url, e.headers.get("Content-Type", ""), e.read().decode("utf-8", "replace") if method == "GET" else ""
    except Exception as e:  # connection refused, DNS, timeout
        return 0, url, "", str(e)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1 = 0
        self.title = ""
        self.meta = {}
        self.canonical = ""
        self.jsonld = []
        self.links, self.images = set(), set()
        self._in_title = self._in_ld = False
        self._buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "meta" and (a.get("name") or a.get("property")):
            self.meta[(a.get("name") or a.get("property")).lower()] = a.get("content") or ""
        elif tag == "link" and "canonical" in (a.get("rel") or "").split():
            self.canonical = a.get("href") or ""
        elif tag == "script" and (a.get("type") or "") == "application/ld+json":
            self._in_ld, self._buf = True, []
        elif tag == "a" and a.get("href"):
            self.links.add(a["href"])
        elif tag in ("img", "source"):
            for src in filter(None, [a.get("src")] + [s.strip().split(" ")[0] for s in (a.get("srcset") or "").split(",") if s.strip()]):
                self.images.add(src)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_ld:
            self._in_ld = False
            self.jsonld.append("".join(self._buf))

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_ld:
            self._buf.append(data)


def same_site(url, base):
    return urlparse(url).netloc in ("", urlparse(base).netloc)


def discover(base, limit):
    urls = []
    status, _, _, body = fetch(urljoin(base, "/wp-sitemap.xml"))
    if status == 200 and "<sitemap" in body:
        for sub in re.findall(r"<loc>(.*?)</loc>", body):
            _, _, _, sbody = fetch(sub)
            urls += re.findall(r"<loc>(.*?)</loc>", sbody)
    if not urls:  # no sitemap: follow links from the home page, one level deep
        status, _, _, body = fetch(base)
        p = Page()
        p.feed(body)
        urls = [base] + sorted({urldefrag(urljoin(base, h))[0] for h in p.links if same_site(urljoin(base, h), base)})
    seen, out = set(), []
    for u in [base.rstrip("/") + "/"] + urls:
        if u not in seen and same_site(u, base):
            seen.add(u)
            out.append(u)
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base", help="site root, e.g. http://acme.test")
    ap.add_argument("--config", help="QA config (default: config.json next to this script)")
    ap.add_argument("--strict", action="store_true", help="treat [CONFIRM] chips as errors (launch week)")
    ap.add_argument("--max", type=int, help="maximum pages to crawl")
    args = ap.parse_args()
    cfg = json.loads((Path(args.config) if args.config else HERE / "config.json").read_text())
    base = args.base.rstrip("/") + "/"

    status, _, _, err = fetch(base)
    if status != 200:
        sys.exit(f"Can't reach {base} (status {status}) {err[:200]}")

    pages = discover(base, args.max or cfg.get("crawl_max_pages", 150))
    problems = {}  # url → (errors, warnings)
    refs = {}      # internal link/image → first page that used it

    for url in pages:
        errors, warnings = [], []
        status, final, ctype, body = fetch(url)
        if status != 200:
            errors.append(f"HTTP {status}")
            problems[url] = (errors, warnings)
            continue
        if "html" not in ctype:
            continue
        p = Page()
        p.feed(body)
        noindex = "noindex" in p.meta.get("robots", "")
        if p.h1 != 1:
            errors.append(f"{p.h1} <h1> tags (want 1)")
        title = re.sub(r"\s+", " ", p.title).strip()
        if not title:
            errors.append("no <title>")
        elif len(title) > 60:
            warnings.append(f"title is {len(title)} chars: “{title}”")
        desc = p.meta.get("description", "")
        if not desc and not noindex:
            errors.append("no meta description")
        elif len(desc) > 160:
            warnings.append(f"meta description is {len(desc)} chars")
        if not p.canonical and not noindex:
            warnings.append("no canonical link")
        for block in p.jsonld:
            try:
                json.loads(block)
            except json.JSONDecodeError as e:
                errors.append(f"JSON-LD doesn't parse ({e.msg})")
        low = body.lower()
        for term in cfg["forbidden"]:
            if term.lower() in low:
                errors.append(f"forbidden term in HTML: '{term}'")
        confirms = body.count("hm-confirm")
        if confirms:
            (errors if args.strict else warnings).append(f"{confirms} [CONFIRM] chip(s)")
        for ref in p.links | p.images:
            absu = urldefrag(urljoin(final, ref))[0]
            if absu.startswith("http") and same_site(absu, base) and "/wp-admin" not in absu and "/wp-json" not in absu:
                refs.setdefault(absu, url)
        if errors or warnings:
            problems[url] = (errors, warnings)

    # Every internal link and image, once.
    for ref, page in sorted(refs.items()):
        if ref in pages:
            continue
        status = fetch(ref, "HEAD")[0]
        if status in (405, 501):
            status = fetch(ref)[0]
        if status >= 400 or status == 0:
            problems.setdefault(page, ([], []))[0].append(f"broken link/image ({status}): {ref}")

    for path in ("robots.txt", "llms.txt"):
        status, _, _, body = fetch(urljoin(base, path))
        if status == 404 and path == "robots.txt" and "user-agent" in body.lower():
            problems.setdefault(urljoin(base, path), ([], []))[1].append(
                "served with HTTP 404 (Laravel Valet does this locally); confirm it returns 200 on staging")
        elif status != 200 or not body.strip():
            problems.setdefault(urljoin(base, path), ([], []))[0].append(f"/{path} missing (HTTP {status})")
        elif path == "llms.txt":
            for term in cfg["forbidden"]:
                if term.lower() in body.lower():
                    problems.setdefault(urljoin(base, path), ([], []))[0].append(f"forbidden term: '{term}'")

    total_e = total_w = 0
    for url, (errors, warnings) in problems.items():
        total_e += len(errors)
        total_w += len(warnings)
        print(f"\n{url}")
        for e in errors:
            print(f"  ✗ {e}")
        for w in warnings:
            print(f"  · {w}")
    print(f"\n{len(pages)} pages · {len(refs)} internal links/images checked · {total_e} error(s) · {total_w} warning(s)")
    sys.exit(1 if total_e else 0)


if __name__ == "__main__":
    main()
