#!/usr/bin/env python3
"""Launch readiness: security, performance, accessibility and launch settings, checked from outside.

    python3 launch.py https://staging.acme.com --env staging
    python3 launch.py https://acme.com --env production --only security,launch
    python3 launch.py http://acme.test --only accessibility
    python3 launch.py https://staging.acme.com --only lighthouse   (sends page URLs to Google PageSpeed Insights)

Groups (default: security, performance, accessibility, launch; lighthouse only when asked for):
  security       HTTPS and the http→https redirect, certificate expiry, HSTS and the other security
                 headers, mixed content, exposed files (.git, .env, backups, debug.log, the project's own
                 docs), directory listing, version leaks, login-name leaks (/?author=1, the users API),
                 XML-RPC, PHP errors printed on pages. With an Application Password it also reads the
                 site's private health endpoint: pending updates, error display, admin accounts.
  performance    response time, compression, page weight and requests, image weight, dimensions and
                 lazy-loading, render-blocking scripts, cache lifetimes, web fonts.
  accessibility  page language, image alt text, link, button and iframe names, form labels, heading
                 order, main landmark, skip link, zoom not blocked, positive tabindex, duplicate ids.
                 Colour contrast needs a browser: qa/contrast.js.
  launch         search-engine visibility right for the environment, robots.txt, sitemap, real 404s,
                 favicon, social image, a privacy policy link, no local or staging URLs in the pages,
                 the enquiry endpoint registered, a lead email address and mail delivery.
  lighthouse     Lighthouse scores (mobile) and real-user Core Web Vitals from Google PageSpeed
                 Insights. Public URLs only; set PSI_API_KEY for a higher rate limit.

Environments: `local` (http, *.test, localhost) skips server checks, which belong to the host;
`staging` expects search engines to be discouraged; `production` expects the site indexable.
Detected from the host name unless --env is given.

Credentials (optional) come from the environment only: ASF_WP_USER and ASF_WP_APP_PASSWORD.
Standard library only. Exit code 1 when there are errors. `--json FILE` writes the results.
"""
import argparse
import base64
import concurrent.futures as cf
import datetime
import gzip
import json
import os
import re
import socket
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
UA = "ASF-launch/1.0 (+agentic-site-framework)"
GROUPS = ["security", "performance", "accessibility", "launch"]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
DEFAULTS = {
    "pages": 5,                    # pages sampled for performance (home first)
    "page_weight_kb": [1500, 3000],
    "requests": [60, 100],
    "html_kb": 250,
    "image_kb": [250, 600],
    "ttfb_ms": [800, 1800],
    "cache_min_days": 7,
    "cert_days": [21, 7],
    "max_fonts": 4,
    "lighthouse_min": 90,
    "lighthouse_paths": [],        # extra paths for Lighthouse besides the home page
    "privacy_words": ["privacy", "datenschutz", "confidentialit", "privacidad", "privacy-policy"],
}


# ── HTTP ────────────────────────────────────────────────────────────────────────────────
class Resp:
    def __init__(self, status=0, url="", headers=None, body=b"", ms=0.0, error="", encoding=""):
        self.status, self.url, self.body, self.ms, self.error, self.encoding = status, url, body, ms, error, encoding
        self.headers = headers or {}
        self.wire = len(body)  # bytes on the wire (before decompression)

    def h(self, name):
        return self.headers.get(name.lower(), "")

    @property
    def text(self):
        return self.body.decode("utf-8", "replace")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Http:
    def __init__(self, insecure=False, auth=None):
        self.ctx = ssl._create_unverified_context() if insecure else ssl.create_default_context()
        https = urllib.request.HTTPSHandler(context=self.ctx)
        self.follow = urllib.request.build_opener(https)
        self.stay = urllib.request.build_opener(https, _NoRedirect())
        self.auth = auth
        self.cache = {}

    def get(self, url, *, redirects=True, method="GET", max_bytes=None, encodings="gzip, deflate", auth=False, cache=True):
        key = (url, redirects, method, max_bytes, encodings, auth)
        if cache and key in self.cache:
            return self.cache[key]
        headers = {"User-Agent": UA, "Accept": "*/*"}
        if encodings:
            headers["Accept-Encoding"] = encodings
        if auth and self.auth:
            headers["Authorization"] = "Basic " + base64.b64encode(self.auth.encode()).decode()
        req = urllib.request.Request(url, method=method, headers=headers)
        opener = self.follow if redirects else self.stay
        t = time.time()
        try:
            r = opener.open(req, timeout=25)
            ms = (time.time() - t) * 1000
            raw = r.read(max_bytes) if max_bytes else r.read()
            out = Resp(r.status, r.geturl(), {k.lower(): ", ".join(r.headers.get_all(k)) for k in r.headers.keys()}, raw, ms)
            r.close()
        except urllib.error.HTTPError as e:
            ms = (time.time() - t) * 1000
            try:
                raw = e.read(max_bytes) if max_bytes else e.read()
            except Exception:
                raw = b""
            out = Resp(e.code, url, {k.lower(): ", ".join(e.headers.get_all(k)) for k in e.headers.keys()} if e.headers else {}, raw, ms)
        except Exception as e:  # DNS, refused, TLS, timeout
            out = Resp(0, url, {}, b"", (time.time() - t) * 1000, error=str(e)[:200])
        enc = out.h("content-encoding").lower()
        out.encoding = enc
        try:
            if enc == "gzip":
                out.body = gzip.decompress(out.body)
            elif enc == "deflate":
                out.body = zlib.decompress(out.body)
        except (OSError, zlib.error, EOFError):
            pass  # a partial read (max_bytes) of a compressed body; size is still right
        if cache:
            self.cache[key] = out
        return out


# ── HTML parsing ────────────────────────────────────────────────────────────────────────
class Doc(HTMLParser):
    """One pass over a page, collecting what every group needs."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []                      # open elements: dicts
        self.lang = None
        self.title = ""
        self.meta = {}
        self.links = []                      # <link> attrs
        self.scripts = []                    # (attrs, in_head)
        self.images = []                     # (attrs, index, in_main)
        self.iframes = []
        self.anchors = []                    # (attrs, text, has_img_alt)
        self.buttons = []                    # (attrs, text)
        self.controls = []                   # (tag, attrs, labelled_by_wrapper)
        self.label_for = set()
        self.headings = []                   # (level, text)
        self.ids = {}
        self.mains = 0
        self.tabindex = []
        self.media = []                      # video/audio attrs
        self.resources = []                  # every src/href that loads something
        self.forms = []
        self._title = False

    # helpers
    def _hidden(self):
        return any(e["hidden"] for e in self.stack)

    def _within(self, tag):
        return next((e for e in reversed(self.stack) if e["tag"] == tag), None)

    def handle_starttag(self, tag, attrs):
        a = {k: (v if v is not None else "") for k, v in attrs}
        hidden = a.get("aria-hidden") == "true" or "hidden" in a
        if a.get("id"):
            self.ids[a["id"]] = self.ids.get(a["id"], 0) + 1
        if a.get("tabindex", "").strip().lstrip("+").isdigit() and int(a["tabindex"]) > 0:
            self.tabindex.append(a)
        in_head = self._within("head") is not None or not any(e["tag"] == "body" for e in self.stack)
        if tag == "html":
            self.lang = a.get("lang", "")
        elif tag == "title":
            self._title = True
        elif tag == "meta" and (a.get("name") or a.get("property")):
            self.meta[(a.get("name") or a.get("property")).lower()] = a.get("content", "")
        elif tag == "link":
            self.links.append(a)
            rel = a.get("rel", "").lower().split()
            if a.get("href") and ("stylesheet" in rel or ("preload" in rel and a.get("as") in ("font", "image", "style", "script"))):
                self.resources.append(a["href"])
        elif tag == "script" and a.get("src"):
            self.scripts.append((a, in_head))
            self.resources.append(a["src"])
        elif tag == "img":
            self.images.append((a, len(self.images), self._within("main") is not None, hidden or self._hidden()))
            if a.get("src"):
                self.resources.append(a["src"])
            for e in self.stack:
                if e["tag"] in ("a", "button"):
                    e["img_alt"] = (e.get("img_alt", "") + " " + a.get("alt", "")).strip()
        elif tag == "iframe":
            self.iframes.append(a)
        elif tag in ("video", "audio"):
            self.media.append(a)
        elif tag == "main" or a.get("role") == "main":
            self.mains += 1
        elif tag == "label" and a.get("for"):
            self.label_for.add(a["for"])
        elif tag == "form":
            self.forms.append(a)
        if tag in ("input", "select", "textarea"):
            if not (a.get("type", "").lower() in ("hidden", "submit", "button", "reset", "image") or hidden or self._hidden()):
                self.controls.append((tag, a, self._within("label") is not None))
        if tag not in VOID:
            self.stack.append({"tag": tag, "attrs": a, "text": [], "hidden": hidden})

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "title":
            self._title = False
        if tag in VOID:
            return
        # pop to the matching open element (tolerates sloppy markup)
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                el = self.stack[i]
                del self.stack[i:]
                self._close(el)
                return

    def _close(self, el):
        text = re.sub(r"\s+", " ", "".join(el["text"])).strip()
        tag, a = el["tag"], el["attrs"]
        if el["hidden"] or self._hidden():
            return
        if tag == "a" and "href" in a:
            self.anchors.append((a, text, el.get("img_alt", "")))
        elif tag == "button" or (tag == "a" and a.get("role") == "button"):
            self.buttons.append((a, text + " " + el.get("img_alt", "")))
        elif re.fullmatch(r"h[1-6]", tag):
            self.headings.append((int(tag[1]), text))

    def handle_data(self, data):
        if self._title:
            self.title += data
        for e in self.stack:
            if e["tag"] in ("a", "button", "label", "h1", "h2", "h3", "h4", "h5", "h6"):
                e["text"].append(data)


def parse(html):
    d = Doc()
    try:
        d.feed(html)
        d.close()
    except Exception:  # never let one odd page stop the run
        pass
    return d


# ── results ─────────────────────────────────────────────────────────────────────────────
class Report:
    def __init__(self):
        self.groups = {}
        self.facts = {}

    def g(self, group):
        return self.groups.setdefault(group, {"errors": 0, "warnings": 0, "passed": 0, "findings": []})

    def add(self, group, level, message, fix="", where=""):
        grp = self.g(group)
        if level == "pass":
            grp["passed"] += 1
            return
        if level in ("error", "warning"):
            grp[level + "s"] += 1
        grp["findings"].append({"level": level, "message": message, "fix": fix, "where": where})

    def ok(self, group, condition, level, message, fix="", where=""):
        self.add(group, "pass" if condition else level, message, fix, where)


def short(url, base):
    return url.replace(base.rstrip("/"), "") or "/"


def host_of(url):
    return urllib.parse.urlparse(url).hostname or ""


def detect_env(url):
    host = host_of(url)
    if host in ("localhost", "127.0.0.1", "::1") or host.endswith((".test", ".local", ".localhost")):
        return "local"
    first = host.split(".")[0]
    if re.search(r"(^|-)(staging|stage|stg|dev|test|qa|uat|preview|sandbox)(-|\d|$)", first):
        return "staging"
    return "production"


def sitemap_urls(http, base):
    r = http.get(urllib.parse.urljoin(base, "/wp-sitemap.xml"))
    if r.status != 200 or "<sitemap" not in r.text:
        return []
    groups = []
    for sub in re.findall(r"<loc>(.*?)</loc>", r.text):
        if "-users-" in sub:
            continue
        groups.append(re.findall(r"<loc>(.*?)</loc>", http.get(sub.strip()).text))
    return groups


def sample_pages(http, base, groups, n):
    """Home first, then the first page of each content type, then the rest in turn."""
    out = [base]
    i = 0
    while len(out) < n and any(i < len(g) for g in groups):
        for g in groups:
            if i < len(g) and g[i] not in out and len(out) < n:
                out.append(g[i])
        i += 1
    return out


def wp_json(http, base, path):
    r = http.get(urllib.parse.urljoin(base, "/wp-json" + path), auth=True, cache=False)
    try:
        return r.status, json.loads(r.text)
    except ValueError:
        return r.status, None


# ── security ────────────────────────────────────────────────────────────────────────────
def cert_days(host, port=443):
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=15) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as s:
            cert = s.getpeercert()
    end = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=datetime.timezone.utc)
    return (end - datetime.datetime.now(datetime.timezone.utc)).days


DEPLOY_FIX = "Delete it from the server; deploy wp-content (and WordPress), never the project folder."
EXPOSED = [
    # path, signature regex on the first 4 KB, level, what it is, fix
    (".git/HEAD", r"^(ref: |[0-9a-f]{40})", "error", "the git repository (source and history)", DEPLOY_FIX),
    (".git/config", r"\[core\]", "error", "the git repository config", DEPLOY_FIX),
    (".env", r"(?m)^[A-Z][A-Z0-9_]+=", "error", "an environment file (usually passwords and keys)", DEPLOY_FIX),
    ("wp-config.php.bak", r"DB_PASSWORD|define\s*\(", "error", "a copy of wp-config.php (database password)", "Delete it, then change the database password."),
    ("wp-config.php.old", r"DB_PASSWORD|define\s*\(", "error", "a copy of wp-config.php (database password)", "Delete it, then change the database password."),
    ("wp-config.php.save", r"DB_PASSWORD|define\s*\(", "error", "a copy of wp-config.php (database password)", "Delete it, then change the database password."),
    ("wp-config.php~", r"DB_PASSWORD|define\s*\(", "error", "a copy of wp-config.php (database password)", "Delete it, then change the database password."),
    ("wp-config.txt", r"DB_PASSWORD|define\s*\(", "error", "a copy of wp-config.php (database password)", "Delete it, then change the database password."),
    ("wp-content/debug.log", r"PHP (Warning|Notice|Fatal|Deprecated|Parse)|^\[\d", "error", "the debug log (paths, errors, sometimes data)",
     "Turn WP_DEBUG_LOG off (or log to a path outside the web root), then delete the file."),
    ("backup.zip", r"^PK", "error", "a site backup", "Delete it; keep backups off the web root (the host's backups or offsite storage)."),
    ("backup.sql", r"CREATE TABLE|INSERT INTO", "error", "a database dump", "Delete it; keep backups off the web root."),
    ("db.sql", r"CREATE TABLE|INSERT INTO", "error", "a database dump", "Delete it; keep backups off the web root."),
    ("dump.sql", r"CREATE TABLE|INSERT INTO", "error", "a database dump", "Delete it; keep backups off the web root."),
    ("phpinfo.php", r"phpinfo\(\)|PHP Version", "error", "phpinfo() (server configuration)", "Delete it."),
    ("info.php", r"phpinfo\(\)|PHP Version", "error", "phpinfo() (server configuration)", "Delete it."),
    ("asf.json", r"\"stage\"\s*:", "error", "the project's state file (asf.json)", DEPLOY_FIX),
    ("CLAUDE.md", r"^#", "error", "the project's working notes (CLAUDE.md)", DEPLOY_FIX),
    ("docs/truth.md", r"^#", "error", "the client's truth file (private claims and notes)", DEPLOY_FIX),
    ("docs/00-goal.md", r"^#", "error", "the client's goal document", DEPLOY_FIX),
    ("content/pages/home.html", r"<!-- wp:", "warning", "the content source files", DEPLOY_FIX),
    ("readme.html", r"WordPress", "warning", "WordPress's readme (shows the version)", "Delete it after each core update, or block it at the server."),
]


def check_security(ctx, rep):
    G, http, base, env, home = "security", ctx["http"], ctx["base"], ctx["env"], ctx["home"]
    host = host_of(base)
    https = base.startswith("https://")
    hs = home.h

    if env == "local":
        rep.add(G, "note", "HTTPS, certificate, HSTS and server headers are checked on staging and production, not on a local site.")
    else:
        rep.ok(G, https, "error", "The site is served over plain http.", "Install a certificate (most hosts do it free) and use https:// URLs in WordPress → Settings → General.")
        if https:
            r = http.get(f"http://{host}/", redirects=False, cache=False)
            loc = r.h("location")
            if r.status in (301, 308) and loc.startswith("https://"):
                rep.add(G, "pass", "")
            elif r.status in (302, 307) and loc.startswith("https://"):
                rep.add(G, "warning", f"http:// redirects to https:// with a temporary {r.status}.", "Make it a permanent 301 at the host or CDN.")
            elif r.status == 0:
                rep.add(G, "note", f"Couldn't reach http://{host}/ to check the redirect ({r.error[:80]}).")
            else:
                rep.add(G, "error", f"http://{host}/ doesn't redirect to https:// (HTTP {r.status}).", "Force HTTPS at the host or CDN (a 301 for every URL).")
            try:
                days = cert_days(host)
                ctx["facts"]["cert_days"] = days
                warn, err = ctx["cfg"]["cert_days"]
                if days < err:
                    rep.add(G, "error", f"The TLS certificate expires in {days} days.", "Renew it now, and check auto-renewal at the host.")
                elif days < warn:
                    rep.add(G, "warning", f"The TLS certificate expires in {days} days.", "Check that auto-renewal is on.")
                else:
                    rep.add(G, "pass", "")
            except Exception as e:
                rep.add(G, "error", f"The TLS certificate doesn't verify: {str(e)[:120]}", "Fix the certificate chain at the host.")
            sts = hs("strict-transport-security")
            m = re.search(r"max-age=(\d+)", sts)
            if not sts:
                rep.add(G, "error" if env == "production" else "warning", "No Strict-Transport-Security (HSTS) header.",
                        "The base plugin sends it over HTTPS (inc/hardening.php); if it's missing, the host or a cache is stripping headers.")
            elif not m or int(m.group(1)) < 15552000:
                rep.add(G, "warning", f"HSTS max-age is short ({sts}).", "Use at least 6 months: max-age=15552000.")
            else:
                rep.add(G, "pass", "")
        server = hs("server")
        if re.search(r"/\d", server):
            rep.add(G, "warning", f"The Server header shows a version: \"{server}\".", "Hide it at the host (server_tokens off / ServerTokens Prod).")
        if hs("x-powered-by"):
            rep.add(G, "warning", f"X-Powered-By shows \"{hs('x-powered-by')}\".", "Set expose_php = Off, or ask the host.")

    rep.ok(G, hs("x-content-type-options").lower() == "nosniff", "error", "No X-Content-Type-Options: nosniff header.",
           "inc/hardening.php sends it; check ASF_SECURITY_HEADERS isn't false and nothing strips headers.")
    csp = hs("content-security-policy")
    rep.ok(G, hs("x-frame-options").upper() in ("DENY", "SAMEORIGIN") or "frame-ancestors" in csp, "error",
           "Pages can be framed by other sites (no X-Frame-Options or CSP frame-ancestors): clickjacking.", "inc/hardening.php sends X-Frame-Options: SAMEORIGIN.")
    rep.ok(G, bool(hs("referrer-policy")), "warning", "No Referrer-Policy header.", "inc/hardening.php sends strict-origin-when-cross-origin.")
    rep.ok(G, bool(hs("permissions-policy")), "warning", "No Permissions-Policy header.", "inc/hardening.php sends one that turns off camera, microphone and location.")
    if not (csp or hs("content-security-policy-report-only")):
        rep.add(G, "warning", "No Content-Security-Policy.",
                "Write one for this site's own sources (analytics, tag manager, embeds), try it with ASF_CSP_REPORT_ONLY, then enforce it with ASF_CSP.")
    else:
        rep.add(G, "pass", "")

    # Mixed content: anything loaded over http on an https page.
    if https:
        mixed = sorted({u for u in ctx["docs"][base].resources if u.startswith("http://")})
        rep.ok(G, not mixed, "error", f"{len(mixed)} file(s) load over http on an https page, e.g. {mixed[0] if mixed else ''}.",
               "Use https:// (or relative) URLs; search the content for http:// and update it.")

    # Exposed files, fetched in parallel, first 4 KB only.
    def probe(item):
        path, sig = item[0], item[1]
        r = http.get(urllib.parse.urljoin(base, "/" + path), redirects=False, max_bytes=4096, encodings="", cache=False)
        body = r.body[:4096].decode("utf-8", "replace")
        looks_html = "<html" in body.lower()[:600] and not path.endswith(".html")
        return item, (r.status == 200 and re.search(sig, body) and not looks_html)

    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        for (path, _, level, what, fix), exposed in pool.map(probe, EXPOSED):
            rep.ok(G, not exposed, level, f"/{path} is public: {what}.", fix, where=f"/{path}")
    r = http.get(urllib.parse.urljoin(base, "/wp-content/uploads/"), max_bytes=4096, cache=False)
    rep.ok(G, not (r.status == 200 and "index of" in r.text.lower()), "error", "/wp-content/uploads/ lists its files.",
           "Turn off directory listing at the host (Options -Indexes, or autoindex off).")

    # Version leaks.
    leaks = []
    d = ctx["docs"][base]
    if "wordpress" in d.meta.get("generator", "").lower():
        leaks.append("the generator tag")
    core = [u for u in d.resources if "/wp-includes/css/" in u and re.search(r"[?&]ver=\d+\.\d+(\.\d+)?(&|$)", u)]
    if core:
        leaks.append("core asset URLs (?ver=)")
    feed = http.get(urllib.parse.urljoin(base, "/feed/"), max_bytes=4096, cache=False)
    if re.search(r"<generator>[^<]*wordpress\.org/\?v=\d", feed.text):
        leaks.append("the RSS feed")
    rep.ok(G, not leaks, "warning", "The WordPress version is visible in " + ", ".join(leaks) + ".", "inc/hardening.php hides it; check the plugin is active.")

    # Login names.
    r = http.get(urllib.parse.urljoin(base, "/?author=1"), redirects=False, cache=False)
    leaked = (r.status in (301, 302, 307, 308) and "/author/" in r.h("location")) or (r.status == 200 and re.search(r'<body[^>]*class="[^"]*\bauthor-', r.text))
    rep.ok(G, not leaked, "error", "/?author=1 reveals a login name (" + (r.h("location") or "author archive") + ").",
           "inc/hardening.php turns author archives into 404s for visitors (unless ASF_AUTHOR_ARCHIVES is true).")
    r = http.get(urllib.parse.urljoin(base, "/wp-json/wp/v2/users"), cache=False)
    rep.ok(G, not (r.status == 200 and '"slug"' in r.text), "error", "/wp-json/wp/v2/users lists users and their login slugs to anyone.",
           "inc/hardening.php closes it to visitors; a security plugin can too.")
    r = http.get(urllib.parse.urljoin(base, "/wp-sitemap-users-1.xml"), cache=False)
    rep.ok(G, not (r.status == 200 and "<loc>" in r.text), "warning", "The users sitemap lists author pages.", "inc/hardening.php removes it.")
    r = http.get(urllib.parse.urljoin(base, "/xmlrpc.php"), cache=False)
    rep.ok(G, "XML-RPC server accepts POST requests only" not in r.text, "warning", "XML-RPC is on (/xmlrpc.php): a common target for password guessing.",
           "inc/hardening.php turns it off unless ASF_ALLOW_XMLRPC is true (Jetpack and the mobile app need it).")

    # PHP errors printed into pages.
    errs = [u for u, doc in ctx["pages_html"].items() if re.search(r"<b>(Warning|Notice|Deprecated|Fatal error|Parse error)</b>:", doc)]
    rep.ok(G, not errs, "error", f"PHP errors are printed on {len(errs)} page(s), e.g. {short(errs[0], base) if errs else ''}.",
           "Set WP_DEBUG_DISPLAY to false on staging and production, then fix the error.")

    # Inside the site (needs an Application Password).
    hl = ctx.get("health")
    if hl is None:
        if not ctx.get("health_tried"):
            rep.add(G, "note", "Inside checks not run (pending updates, error display, admin accounts): set ASF_WP_USER and ASF_WP_APP_PASSWORD.")
        return
    up = hl.get("updates", {})
    if up.get("wordpress"):
        rep.add(G, "warning", f"WordPress {up['wordpress']} is available (running {hl['versions']['wordpress']}).", "Update on staging, test, then production.")
    stale = [f"{p['name']} {p['from']}→{p['to']}" for p in up.get("plugins", []) + up.get("themes", [])]
    rep.ok(G, not stale, "warning", f"{len(stale)} plugin/theme update(s) waiting: " + ", ".join(stale[:5]) + ("…" if len(stale) > 5 else "") + ".",
           "Update them (they often fix security holes); turn on auto-updates for minor releases.")
    if not up.get("checked"):
        rep.add(G, "note", "WordPress hasn't checked for updates yet (open Dashboard → Updates once).")
    s = hl.get("settings", {})
    rep.ok(G, not s.get("errors_shown"), "error", "PHP errors are set to show on screen (WP_DEBUG with WP_DEBUG_DISPLAY).", "In wp-config.php: define( 'WP_DEBUG_DISPLAY', false );")
    rep.ok(G, s.get("file_editor_off"), "warning", "The theme/plugin file editor is on.", "Leave DISALLOW_FILE_EDIT to the base plugin (true), or set it in wp-config.php.")
    rep.ok(G, not s.get("anyone_can_register"), "warning", "Anyone can register an account (Settings → General → Membership).", "Turn it off unless the site needs sign-ups.")
    u = hl.get("users", {})
    rep.ok(G, not u.get("login_admin"), "error", "An administrator logs in as \"admin\": the first name every password-guessing bot tries.",
           "Create a new admin with a personal login, move the content to it, delete \"admin\".")
    rep.ok(G, u.get("administrators", 0) <= 3, "warning", f"{u.get('administrators')} administrator accounts.", "Keep admin to the people who need it; editors can publish.")
    if env != "local":
        rep.ok(G, s.get("https"), "error", "WordPress's own address (Settings → General) isn't https.", "Set both addresses to https://.")


# ── performance ─────────────────────────────────────────────────────────────────────────
def kind_of(url, ctype):
    path = urllib.parse.urlparse(url).path.lower()
    if "font" in ctype or path.endswith((".woff2", ".woff", ".ttf", ".otf")):
        return "font"
    if ctype.startswith("image/") or path.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg")):
        return "image"
    if "css" in ctype or path.endswith(".css"):
        return "css"
    if "javascript" in ctype or path.endswith((".js", ".mjs")):
        return "js"
    return "other"


def check_performance(ctx, rep):
    G, http, base, env, cfg = "performance", ctx["http"], ctx["base"], ctx["env"], ctx["cfg"]
    pages = ctx["sample"]
    local = env == "local"
    if local:
        rep.add(G, "note", "Response time, compression and caching depend on the host: checked on staging and production. Page weight, images and scripts are checked here.")
    else:
        times = [http.get(base, cache=False).ms for _ in range(3)]
        ttfb = statistics.median(times)
        ctx["facts"]["home_ms"] = round(ttfb)
        warn, err = cfg["ttfb_ms"]
        if ttfb >= err:
            rep.add(G, "error", f"The home page takes {ttfb:.0f} ms to respond.", "Turn on page caching at the host; look for slow plugins (Query Monitor).")
        elif ttfb >= warn:
            rep.add(G, "warning", f"The home page takes {ttfb:.0f} ms to respond (aim for under {warn} ms).", "Page caching at the host usually fixes this.")
        else:
            rep.add(G, "pass", "")

    # Fetch every resource once, in parallel.
    urls = sorted({urllib.parse.urljoin(p, ref) for p in pages for ref in ctx["docs"][p].resources})
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        res = dict(zip(urls, pool.map(lambda u: http.get(u), urls)))
    # Web fonts: @font-face in the site's own CSS files and in the page itself (theme.json fonts print inline).
    fonts, no_display = set(), set()
    sources = [(u, r.text) for u, r in res.items() if kind_of(u, r.h("content-type")) == "css" and host_of(u) == host_of(base)]
    sources.append((base, ctx["pages_html"].get(base, "")))
    for u, text in sources:
        for m in re.finditer(r"@font-face\s*{[^}]*}", text):
            block = m.group(0)
            if "font-display" not in block:
                no_display.add(short(u, base))
            for f in re.findall(r"url\(['\"]?([^'\")]+\.woff2?)['\"]?\)", block):
                fonts.add(urllib.parse.urljoin(u, f))
    rep.ok(G, not no_display, "warning", f"Web fonts without font-display (text stays invisible while they load), in {', '.join(sorted(no_display))}.",
           "Add font-display: swap to each @font-face (theme.json: \"fontDisplay\": \"swap\").")
    for f in sorted(fonts - set(res)):
        res[f] = http.get(f)

    static_short = []
    uncompressed = []
    for u, r in res.items():
        k = kind_of(u, r.h("content-type"))
        if host_of(u) != host_of(base) or r.status != 200:
            continue
        cc = r.h("cache-control")
        m = re.search(r"max-age=(\d+)", cc)
        if k in ("css", "js", "image", "font") and not (m and int(m.group(1)) >= cfg["cache_min_days"] * 86400) and not r.h("expires"):
            static_short.append(short(u, base))
        if k in ("css", "js") and not r.encoding and r.wire > 2048:
            uncompressed.append(short(u, base))

    if not local:
        home = ctx["home"]
        enc = home.encoding
        if not enc:
            enc = http.get(base, encodings="br", cache=False).h("content-encoding")
        rep.ok(G, bool(enc), "error", "HTML isn't compressed (no gzip or Brotli).", "Turn on compression at the host or CDN.")
        rep.ok(G, not uncompressed, "warning", f"{len(uncompressed)} CSS/JS file(s) aren't compressed, e.g. {uncompressed[0] if uncompressed else ''}.", "Turn on gzip/Brotli for text files at the host.")
        rep.ok(G, not static_short, "warning", f"{len(static_short)} static file(s) are cached for under {cfg['cache_min_days']} days, e.g. {static_short[0] if static_short else ''}.",
               "Set a long Cache-Control max-age on CSS, JS, images and fonts (WordPress adds ?ver= to bust caches).")

    big, no_dims, lazy_lcp, eager, legacy, blocking = [], [], [], [], [], set()
    for p in pages:
        d = ctx["docs"][p]
        html = ctx["pages_resp"][p]
        weight = html.wire
        reqs = 1
        loaded = {urllib.parse.urljoin(p, ref) for ref in d.resources} | fonts
        for u in loaded:
            r = res.get(u)
            if r and r.status == 200:
                weight += r.wire
                reqs += 1
        kb = weight / 1024
        if p == base:
            ctx["facts"].update(home_kb=round(kb), home_requests=reqs)
        warn, err = cfg["page_weight_kb"]
        where = short(p, base)
        if kb >= err:
            rep.add(G, "error", f"{where} weighs {kb:,.0f} KB (budget {warn:,} KB).", "Compress and resize images first; then drop unused scripts.", where)
        elif kb >= warn:
            rep.add(G, "warning", f"{where} weighs {kb:,.0f} KB (budget {warn:,} KB).", "Compress and resize images first.", where)
        else:
            rep.add(G, "pass", "")
        rw, re_ = cfg["requests"]
        if reqs >= rw:
            rep.add(G, "error" if reqs >= re_ else "warning", f"{where} makes {reqs} requests.", "Combine or drop scripts and styles; lazy-load images.", where)
        if html.wire / 1024 > cfg["html_kb"]:
            rep.add(G, "warning", f"{where}: the HTML alone is {html.wire / 1024:,.0f} KB.", "Look for inlined images (data: URIs) or huge inline styles.", where)
        for a, in_head in d.scripts:
            if in_head and not ({"async", "defer"} & set(a)) and a.get("type") != "module":
                blocking.add(short(urllib.parse.urljoin(p, a["src"]), base))
        first_main = next(((a, i) for a, i, in_main, hid in d.images if in_main and not hid), None)
        for a, i, in_main, hid in d.images:
            src = a.get("src", "")
            if not src or src.startswith("data:"):
                continue
            absu = urllib.parse.urljoin(p, src)
            r = res.get(absu)
            if r and r.status == 200:
                kbi = r.wire / 1024
                if kbi >= cfg["image_kb"][0]:
                    big.append((kbi, short(absu, base), where))
                if kbi > 100 and urllib.parse.urlparse(absu).path.lower().endswith((".jpg", ".jpeg", ".png")):
                    legacy.append(short(absu, base))
            if not (a.get("width") and a.get("height")) and not absu.lower().endswith(".svg"):
                no_dims.append((short(absu, base), where))
            if first_main and i == first_main[1] and a.get("loading") == "lazy":
                lazy_lcp.append(where)
            if i >= 3 and in_main and a.get("loading") != "lazy":
                eager.append(where)
        for f in d.iframes:
            if re.search(r"youtube\.com|vimeo\.com|google\.com/maps", f.get("src", "")) and f.get("loading") != "lazy":
                rep.add(G, "warning", f"{where}: an embed loads straight away ({f.get('src', '')[:60]}).", "Add loading=\"lazy\" or show a thumbnail that loads the player on click.", where)

    for kbi, u, where in sorted(set(big), reverse=True)[:8]:
        rep.add(G, "error" if kbi >= cfg["image_kb"][1] else "warning", f"Image {u} is {kbi:,.0f} KB (on {where}).", "Resize to the size it's shown at and compress (WebP/AVIF, quality 75–80).", where)
    if not big:
        rep.add(G, "pass", "")
    legacy = sorted(set(legacy))
    rep.ok(G, not legacy, "warning", f"{len(legacy)} large JPEG/PNG image(s) could be WebP or AVIF, e.g. {legacy[0] if legacy else ''}.", "Convert them (smaller at the same quality).")
    no_dims_u = sorted({u for u, _ in no_dims})
    rep.ok(G, not no_dims_u, "warning", f"{len(no_dims_u)} image(s) have no width/height, so the page jumps as they load (CLS), e.g. {no_dims_u[0] if no_dims_u else ''}.",
           "Give every <img> width and height attributes (the block editor does when the image comes from the media library).")
    rep.ok(G, not lazy_lcp, "warning", f"The first image in the content is lazy-loaded on {', '.join(sorted(set(lazy_lcp))[:3])}: it's usually the largest paint.",
           "Remove loading=\"lazy\" from the first image; add fetchpriority=\"high\".")
    rep.ok(G, not eager, "warning", f"Images below the first few aren't lazy-loaded on {', '.join(sorted(set(eager))[:3])}.", "Add loading=\"lazy\" to images below the fold.")
    rep.ok(G, not blocking, "warning", f"{len(blocking)} script(s) in <head> block rendering, e.g. {sorted(blocking)[0] if blocking else ''}.",
           "Load them with defer (wp_enqueue_script(..., ['strategy' => 'defer'])) or in the footer.")
    rep.ok(G, len(fonts) <= cfg["max_fonts"], "warning", f"{len(fonts)} web font files load.", f"Keep to {cfg['max_fonts']} or fewer: fewer weights, or a variable font.")
    third = sorted({host_of(urllib.parse.urljoin(base, r)) for r in ctx["docs"][base].resources} - {host_of(base), ""})
    if third:
        ctx["facts"]["third_party_hosts"] = third
        rep.add(G, "note", "Third-party hosts on the home page: " + ", ".join(third) + ".")


# ── accessibility ───────────────────────────────────────────────────────────────────────
GENERIC = {"click here", "here", "read more", "more", "learn more", "link", "this", "details", "find out more", "continue"}


A11Y_KINDS = ["lang", "zoom", "main", "skip", "alt", "link-name", "link-text", "button-name", "label", "iframe-title",
             "heading-order", "heading-empty", "duplicate-id", "tabindex", "autoplay"]


def check_accessibility(ctx, rep):
    G, base = "accessibility", ctx["base"]
    issues = {}  # kind → {level, message, fix, pages, examples}

    def hit(kind, level, message, fix, page, example=""):
        i = issues.setdefault(kind, {"level": level, "message": message, "fix": fix, "pages": set(), "examples": []})
        i["pages"].add(short(page, base))
        if example and example not in i["examples"]:
            i["examples"].append(example)

    for page in ctx["all_pages"]:
        d = ctx["docs"].get(page)
        if d is None:
            continue
        if not (d.lang or "").strip():
            hit("lang", "error", "No page language (<html lang>)", "WordPress sets it from Settings → General → Site Language; check the theme prints language_attributes().", page)
        vp = d.meta.get("viewport", "").replace(" ", "").lower()
        if "user-scalable=no" in vp or re.search(r"maximum-scale=(0|1)(\.0*)?(,|$)", vp):
            hit("zoom", "error", "Zooming is blocked (viewport user-scalable=no or maximum-scale=1)", "Remove those from the viewport meta tag.", page)
        if d.mains != 1:
            hit("main", "warning", "Not exactly one <main> landmark", "Wrap the page content in one <main> (a Group block with the main tag).", page, f"{d.mains} found")
        if not any(a.get("href", "").startswith("#") and re.search(r"skip|main|content", (t + a.get("class", "")).lower()) for a, t, _ in d.anchors[:5]):
            hit("skip", "warning", "No skip link to the main content", "Add <a class=\"skip-link\" href=\"#main\">Skip to content</a> as the first link.", page)
        for a, _, _, hidden in d.images:
            if "alt" not in a and not hidden and a.get("role") not in ("presentation", "none"):
                hit("alt", "error", "Images without alt text", "Add alt text that says what the image shows, or alt=\"\" if it's decorative.", page, a.get("src", "")[-60:])
        for a, text, img_alt in d.anchors:
            name = (text or img_alt or a.get("aria-label", "") or a.get("title", "")).strip() or ("[labelledby]" if a.get("aria-labelledby") else "")
            if not name:
                hit("link-name", "error", "Links with no text or label", "Add visible text, or aria-label for icon links.", page, f"href=\"{a.get('href', '')[:60]}\"")
            elif name.lower().strip(" .…→›»") in GENERIC and not a.get("aria-label"):
                hit("link-text", "warning", "Vague link text", "Say where the link goes (\"Read the case study\"), or add an aria-label.", page, f"\"{name}\"")
        for a, text in d.buttons:
            if not (text.strip() or a.get("aria-label") or a.get("aria-labelledby") or a.get("title")):
                hit("button-name", "error", "Buttons with no text or label", "Add text, or aria-label for icon buttons.", page, f"class=\"{a.get('class', '')[:40]}\"")
        for tag, a, wrapped in d.controls:
            if not (wrapped or a.get("id", "") in d.label_for or a.get("aria-label") or a.get("aria-labelledby") or a.get("title")):
                hit("label", "error", "Form fields without a label", "Add a <label for=\"…\"> (a placeholder isn't a label).", page, f"<{tag} name=\"{a.get('name', '')}\">")
        for f in d.iframes:
            if not (f.get("title") or f.get("aria-label")):
                hit("iframe-title", "error", "Embedded frames without a title", "Add title=\"…\" describing the embed.", page, f.get("src", "")[:60])
        prev = None
        for level, text in d.headings:
            if prev and level > prev + 1:
                hit("heading-order", "warning", "Heading levels skip", "Use the next level down; style it with a class if it should look smaller.", page, f"h{prev} → h{level} \"{text[:30]}\"")
            prev = level
        if any(not t for _, t in d.headings):
            hit("heading-empty", "warning", "Empty headings", "Remove them or give them text.", page)
        dupes = [i for i, n in d.ids.items() if n > 1]
        if dupes:
            hit("duplicate-id", "warning", "Duplicate ids on a page", "Every id on a page must be unique (labels and anchors break otherwise).", page, ", ".join(sorted(dupes)[:3]))
        if d.tabindex:
            hit("tabindex", "warning", "Positive tabindex changes the keyboard order", "Use tabindex=\"0\" or none; order elements in the HTML instead.", page)
        for m in d.media:
            if "autoplay" in m and "muted" not in m:
                hit("autoplay", "error", "Video or audio plays sound automatically", "Add muted, or remove autoplay.", page)

    n = len(ctx["all_pages"])
    for kind, i in sorted(issues.items(), key=lambda kv: (kv[1]["level"] != "error", -len(kv[1]["pages"]))):
        pages = sorted(i["pages"])
        where = "every page" if len(pages) == n and n > 1 else (f"{len(pages)} pages, e.g. {pages[0]}" if len(pages) > 1 else pages[0])
        eg = f"; e.g. {', '.join(i['examples'][:2])}" if i["examples"] else ""
        rep.add(G, i["level"], f"{i['message']} ({where}{eg}).", i["fix"], where)
    rep.g(G)["passed"] += len(A11Y_KINDS) - len(issues)
    rep.add(G, "note", f"{n} page(s) checked. Colour contrast and keyboard focus need a browser: run qa/contrast.js and a keyboard-only pass.")


# ── launch settings ─────────────────────────────────────────────────────────────────────
def check_launch(ctx, rep):
    G, http, base, env, cfg = "launch", ctx["http"], ctx["base"], ctx["env"], ctx["cfg"]
    d, home = ctx["docs"][base], ctx["home"]
    robots_meta = (d.meta.get("robots", "") + " " + home.h("x-robots-tag")).lower()
    noindex = "noindex" in robots_meta
    robots = http.get(urllib.parse.urljoin(base, "/robots.txt"))
    blocked = bool(re.search(r"(?im)^user-agent:\s*\*\s*$(?:\n(?!user-agent).*)*?\ndisallow:\s*/\s*$", robots.text))
    hl = ctx.get("health") or {}
    allowed = hl.get("settings", {}).get("search_engines_allowed")

    if env == "production":
        rep.ok(G, not noindex, "error", "The home page says noindex: search engines will drop the site.",
               "Settings → Reading → untick \"Discourage search engines\" (and check the SEO plugin).")
        rep.ok(G, not blocked, "error", "robots.txt blocks every crawler (Disallow: /).", "Untick \"Discourage search engines\", or fix the physical robots.txt.")
        if allowed is False:
            rep.add(G, "error", "WordPress is set to discourage search engines.", "Settings → Reading → untick it.")
    elif env == "staging":
        rep.ok(G, noindex or blocked or allowed is False, "warning", "Staging is open to search engines: it can be indexed as a duplicate of the live site.",
               "Settings → Reading → tick \"Discourage search engines\" on staging (and protect it with a password if you can).")
    rep.ok(G, robots.status == 200 or (robots.status == 404 and "user-agent" in robots.text.lower()), "error", f"/robots.txt is missing (HTTP {robots.status}).", "WordPress serves one; check nothing at the host blocks it.")
    sm = http.get(urllib.parse.urljoin(base, "/wp-sitemap.xml"))
    rep.ok(G, sm.status == 200 and "<sitemap" in sm.text, "error", "No XML sitemap at /wp-sitemap.xml.", "WordPress builds one unless an SEO plugin replaces it; point robots.txt at whichever exists.")
    if env == "production":
        rep.ok(G, "sitemap:" in robots.text.lower(), "warning", "robots.txt doesn't point to the sitemap.", "WordPress adds it automatically when search engines are allowed.")

    probe = urllib.parse.urljoin(base, f"/asf-launch-check-{int(time.time())}/")
    r = http.get(probe, cache=False)
    rep.ok(G, r.status == 404, "error", f"A page that doesn't exist returns HTTP {r.status} instead of 404 (a soft 404).", "Check the host or a plugin isn't redirecting missing pages to the home page.")

    rep.ok(G, any("icon" in l.get("rel", "").lower() for l in d.links), "warning", "No favicon.", "Appearance → Editor → Site Icon (or Settings → General).")
    og = d.meta.get("og:image", "")
    if not og:
        rep.add(G, "warning", "The home page has no og:image (the picture shown when the link is shared).", "Set a 1200×630 social image (inc/seo.php reads it from the entity file).")
    else:
        r = http.get(urllib.parse.urljoin(base, og), method="GET", max_bytes=1024, encodings="", cache=False)
        rep.ok(G, r.status == 200, "error", f"The og:image doesn't load (HTTP {r.status}): {og}", "Fix the image URL.")
    rep.ok(G, bool(d.meta.get("description")), "warning", "The home page has no meta description.", "Write one (≤ 155 characters) in the page's SEO fields.")

    words = cfg["privacy_words"]
    priv = any(any(w in (a.get("href", "") + " " + t).lower() for w in words) for a, t, _ in d.anchors)
    rep.ok(G, priv, "error" if env == "production" else "warning", "No link to a privacy policy from the home page.",
           "Forms collect personal data: publish a privacy policy and link it in the footer.")

    # Local (or, on production, staging) addresses left in the pages.
    local_refs = {}
    pats = [r"https?://[a-z0-9.-]+\.(test|local|localhost)(:\d+)?/", r"https?://(localhost|127\.0\.0\.1)(:\d+)?/"]
    hosts = ctx.get("env_hosts", {})
    for role in ("local", "staging") if env == "production" else ("local",):
        if hosts.get(role) and hosts[role] != host_of(base):
            pats.append(r"https?://" + re.escape(hosts[role]) + r"[:/]")
    if env != "local":
        for page, html in ctx["pages_html"].items():
            for p in pats:
                for m in re.finditer(p, html, re.I):
                    if host_of(m.group(0)) != host_of(base):  # the site's own address is fine
                        local_refs.setdefault(m.group(0), short(page, base))
                        break
        rep.ok(G, not local_refs, "error", "Pages link to another environment's address: " + ", ".join(f"{u} (on {pg})" for u, pg in list(local_refs.items())[:3]),
               "Search-replace the old URL in the database (wp search-replace), then clear caches.")

    ns = ctx.get("rest_namespace")
    if ns:
        idx = http.get(urllib.parse.urljoin(base, "/wp-json/"))
        try:
            routes = json.loads(idx.text).get("routes", {})
            rep.ok(G, f"/{ns}/leads" in routes, "error", f"The enquiry endpoint /wp-json/{ns}/leads isn't registered: forms will fail.",
                   "Activate the site's core plugin; check permalinks aren't plain.")
        except ValueError:
            rep.add(G, "error", f"/wp-json/ doesn't return the REST index (HTTP {idx.status}): forms will fail.", "Check permalinks and that nothing blocks the REST API for visitors.")
    if hl:
        em = hl.get("email", {})
        rep.ok(G, em.get("lead_email") == "set", "error", "No lead email address: enquiries won't reach anyone.", "Set lead_email in the core plugin's inc/entity.php.")
        if not em.get("smtp_plugin"):
            rep.add(G, "warning" if env != "local" else "note", "No SMTP plugin found: lead emails go through PHP mail() and often land in spam.",
                    "Install an SMTP plugin with the client's mail service (or confirm the host relays mail), then send a test enquiry.")
        failed = em.get("last_failed")
        if failed:
            rep.add(G, "error", f"The last email failed to send ({failed.get('at', '')[:10]}, {failed.get('count')} failure(s)): {failed.get('error', '')}",
                    "Fix mail delivery, then send a test enquiry; check the lead list for enquiries that weren't emailed.")
        else:
            rep.add(G, "pass", "")
        sample = hl.get("content", {}).get("sample_content")
        rep.ok(G, not sample, "warning", "WordPress's sample content is still published: " + ", ".join(sample or []) + ".", "Delete \"Hello world!\" and \"Sample Page\".")
        rep.ok(G, not hl.get("settings", {}).get("comments_open"), "warning", "New posts allow comments by default (a spam magnet on a marketing site).",
               "Settings → Discussion → untick \"Allow people to submit comments on new posts\".")


# ── Lighthouse (PageSpeed Insights) ─────────────────────────────────────────────────────
def check_lighthouse(ctx, rep):
    G, base, cfg = "lighthouse", ctx["base"], ctx["cfg"]
    # Never send a local or private address to Google, whatever --env says.
    host = host_of(base)
    private = detect_env(base) == "local" or re.match(r"^(10|127|192\.168|172\.(1[6-9]|2\d|3[01]))\.", host)
    if ctx["env"] == "local" or private:
        rep.add(G, "error", f"Lighthouse via PageSpeed Insights needs a public URL ({host} isn't one).",
                "Run it against a public staging URL, or run Lighthouse in Chrome DevTools and record the scores with `bin/asf skip G4 lighthouse --reason \"…\"`.")
        return
    key = os.environ.get("PSI_API_KEY")
    paths = [base] + [urllib.parse.urljoin(base, p) for p in cfg["lighthouse_paths"]]
    if len(paths) == 1:
        paths += [u for u in ctx["sample"][1:3]]
    cats = ["performance", "accessibility", "best-practices", "seo"]
    scores = {}

    def run(url):
        q = [("url", url), ("strategy", "mobile")] + [("category", c) for c in cats] + ([("key", key)] if key else [])
        api = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urllib.parse.urlencode(q)
        try:
            with urllib.request.urlopen(urllib.request.Request(api, headers={"User-Agent": UA}), timeout=120) as r:
                return url, json.loads(r.read().decode("utf-8")), ""
        except urllib.error.HTTPError as e:
            return url, None, f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:160]}"
        except Exception as e:
            return url, None, str(e)[:160]

    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(run, paths))
    for url, data, err in results:
        where = short(url, base)
        if not data:
            rep.add(G, "error", f"PageSpeed Insights couldn't test {where}: {err}", "Is the URL public (no password, not blocked)? Set PSI_API_KEY if you hit the rate limit.", where)
            continue
        lh = data.get("lighthouseResult", {}).get("categories", {})
        page_scores = {c: round((lh.get(c, {}).get("score") or 0) * 100) for c in cats}
        scores[where] = page_scores
        for c, s in page_scores.items():
            rep.ok(G, s >= cfg["lighthouse_min"], "error" if s < cfg["lighthouse_min"] - 20 else "warning",
                   f"{where}: Lighthouse {c} {s} (target {cfg['lighthouse_min']}).", "Open the PageSpeed Insights report for this URL; fix the top opportunities.", where)
        field = data.get("loadingExperience", {})
        if field.get("metrics") and url == base:
            m = field["metrics"]
            ctx["facts"]["core_web_vitals"] = {k: m[k].get("percentile") for k in m if "percentile" in m[k]}
            ctx["facts"]["core_web_vitals_overall"] = field.get("overall_category")
            if field.get("overall_category") == "SLOW":
                rep.add(G, "error", "Real users get a poor experience (Core Web Vitals: SLOW).", "See the field data in PageSpeed Insights: LCP, INP and CLS.")
    ctx["facts"]["lighthouse"] = scores


# ── main ────────────────────────────────────────────────────────────────────────────────
def load_cfg(path):
    cfg = dict(DEFAULTS)
    p = Path(path) if path else HERE / "config.json"
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        cfg.update(data.get("launch", {}))
        cfg["crawl_max_pages"] = data.get("crawl_max_pages", 150)
    return cfg


def find_state():
    for d in (Path.cwd(), *Path.cwd().parents):
        if (d / "asf.json").exists():
            try:
                return json.loads((d / "asf.json").read_text(encoding="utf-8"))
            except ValueError:
                return {}
    return {}


def run(base, env=None, only=None, cfg_path=None, namespace=None, insecure=False, quiet=False):
    base = base.rstrip("/") + "/"
    env = env or detect_env(base)
    cfg = load_cfg(cfg_path)
    state = find_state()
    namespace = namespace or state.get("rest_namespace") or ""
    user, pw = os.environ.get("ASF_WP_USER"), os.environ.get("ASF_WP_APP_PASSWORD")
    http = Http(insecure=insecure or env == "local", auth=f"{user}:{pw}" if user and pw else None)
    groups = only or GROUPS
    rep = Report()
    home = http.get(base)
    if home.status != 200:
        raise SystemExit(f"Can't load {base} (HTTP {home.status}) {home.error}")
    dep = state.get("deploy", {})
    ctx = {"http": http, "base": base, "env": env, "cfg": cfg, "home": home, "facts": rep.facts, "rest_namespace": namespace,
           "env_hosts": {k: host_of(v) for k, v in (("local", state.get("site_url")), ("staging", dep.get("staging_url")), ("production", dep.get("production_url"))) if v}}
    sm = sitemap_urls(http, base)
    ctx["sample"] = sample_pages(http, base, sm, cfg["pages"])
    every = [base] + [u for g in sm for u in g if u.rstrip("/") != base.rstrip("/")]
    ctx["all_pages"] = list(dict.fromkeys(every))[: cfg["crawl_max_pages"]] if "accessibility" in groups else ctx["sample"]
    wanted = list(dict.fromkeys(ctx["sample"] + ctx["all_pages"]))
    with cf.ThreadPoolExecutor(max_workers=6) as pool:
        resps = dict(zip(wanted, pool.map(lambda u: http.get(u), wanted)))
    ctx["pages_resp"] = {u: r for u, r in resps.items() if r.status == 200}
    ctx["pages_html"] = {u: r.text for u, r in ctx["pages_resp"].items() if "html" in r.h("content-type")}
    ctx["docs"] = {u: parse(t) for u, t in ctx["pages_html"].items()}
    ctx["sample"] = [u for u in ctx["sample"] if u in ctx["docs"]]
    ctx["all_pages"] = [u for u in ctx["all_pages"] if u in ctx["docs"]]
    if http.auth and namespace:
        status, data = wp_json(http, base, f"/{namespace}/health")
        ctx["health"] = data if status == 200 and isinstance(data, dict) else None
        ctx["health_tried"] = True
        if ctx["health"] is None:
            rep.add(groups[0], "warning", f"Couldn't read /wp-json/{namespace}/health (HTTP {status}) with the Application Password.",
                    "Check ASF_WP_USER / ASF_WP_APP_PASSWORD, that the user is an administrator, and that the core plugin is up to date.")
        else:
            rep.facts["inside"] = {"versions": ctx["health"].get("versions"), "updates": ctx["health"].get("updates")}
    for g in groups:
        {"security": check_security, "performance": check_performance, "accessibility": check_accessibility,
         "launch": check_launch, "lighthouse": check_lighthouse}[g](ctx, rep)
    return {"url": base, "env": env, "generated": datetime.datetime.now().astimezone().isoformat(timespec="minutes"),
            "groups": rep.groups, "facts": rep.facts}


def print_report(result):
    marks = {"error": "✗", "warning": "·", "note": "–"}
    for name, g in result["groups"].items():
        print(f"\n{name.upper()}  {g['errors']} error(s) · {g['warnings']} warning(s) · {g['passed']} passed")
        for f in sorted(g["findings"], key=lambda f: ["error", "warning", "note"].index(f["level"])):
            print(f"  {marks[f['level']]} {f['message']}")
            if f["fix"] and f["level"] != "note":
                print(f"      → {f['fix']}")
    facts = {k: v for k, v in result["facts"].items() if k != "inside"}
    if facts:
        print("\nFacts: " + " · ".join(f"{k}={v}" for k, v in facts.items()))
    e = sum(g["errors"] for g in result["groups"].values())
    w = sum(g["warnings"] for g in result["groups"].values())
    names = "+".join(result["groups"])
    print(f"\n{names} on {result['url']} ({result['env']}): {e} error(s) · {w} warning(s)")
    return e


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", help="site root, e.g. https://staging.acme.com")
    ap.add_argument("--env", choices=["local", "staging", "production"], help="default: detected from the host name")
    ap.add_argument("--only", help="comma-separated groups: security,performance,accessibility,launch,lighthouse")
    ap.add_argument("--config", help="QA config (default: config.json next to this script)")
    ap.add_argument("--rest-namespace", help="the core plugin's REST namespace (default: from asf.json)")
    ap.add_argument("--insecure", action="store_true", help="don't verify TLS (self-signed local certificates)")
    ap.add_argument("--json", help="also write the results as JSON to this file (- for stdout only)")
    a = ap.parse_args()
    if not a.url or a.url.startswith("{"):
        sys.exit("No URL: set it first (e.g. `bin/asf set deploy.staging_url https://…`).")
    only = [g.strip() for g in a.only.split(",")] if a.only else None
    bad = [g for g in only or [] if g not in GROUPS + ["lighthouse"]]
    if bad:
        sys.exit(f"Unknown group(s): {', '.join(bad)}")
    result = run(a.url, a.env, only, a.config, a.rest_namespace, a.insecure)
    if a.json == "-":
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1 if any(g["errors"] for g in result["groups"].values()) else 0)
    if a.json:
        Path(a.json).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sys.exit(1 if print_report(result) else 0)


if __name__ == "__main__":
    main()
