#!/usr/bin/env python3
"""Second half of new-site.sh: rename, reset and scaffold a copy of the base build for a new client.

Run by new-site.sh; not meant to be run on its own. Every step is plain file work, so it's easy
to read and change. The base (`base/`) is a design-neutral wireframe whose identifiers are
`asfbase` / `ASF Base`; this script renames them for the client and adds the skeleton pages,
docs, framework and agents.
"""
import argparse
import datetime
import json
import re
import shutil
import struct
import sys
import zlib
from pathlib import Path

TEXT = {".php", ".js", ".json", ".css", ".html", ".sh", ".md", ".txt", ".xml", ".gitignore", ""}

SRC_THEME, SRC_PLUGIN, SRC_NAME = "asfbase", "asfbase-core", "ASF Base"


def leftover_patterns(fw):
    """The base's own identifiers, plus any private names in starter/private-leak-patterns.txt.

    That file is git-ignored: list one regex per line for names that must never reach a client
    site (other clients, partners, internal tools). It's how a team keeps its client list out
    of a public framework.
    """
    patterns = [r"asfbase", r"ASF Base"]
    private = fw / "starter/private-leak-patterns.txt"
    if private.exists():
        patterns += [ln.strip() for ln in private.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.I)


def replacements(a):
    theme = a.slug.replace("-", "")
    pairs = [
        (SRC_NAME, a.name),
        (f"{SRC_PLUGIN}", f"{a.slug}-core"),
        (f"{SRC_THEME}/v1", f"{a.slug}/v1"),
        (f"{SRC_THEME}.test", f"{a.slug}.test"),
        (f"Sites/{SRC_THEME}", f"Sites/{a.slug}"),
        (SRC_THEME.upper(), theme.upper()),
        (SRC_THEME, theme),
    ]
    return pairs, theme


def text_files(root):
    for p in root.rglob("*"):
        if p.is_file() and (p.suffix in TEXT or p.name == ".gitignore") and "/wordpress/" not in p.as_posix():
            yield p


def png(path, w, h, top, bottom):
    """A plain vertical-gradient PNG (no dependencies). Placeholders only: replace before launch."""
    rows = []
    for y in range(h):
        t = y / max(1, h - 1)
        c = bytes(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        rows.append(b"\x00" + c * w)
    raw = zlib.compress(b"".join(rows), 9)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", raw) + chunk(b"IEND", b""))


def reset_client_files(t, a, fw, ref):
    theme = t / f"wp-content/themes/{SRC_THEME}"
    plugin = t / f"wp-content/plugins/{SRC_PLUGIN}"
    skel = fw / "starter/skeleton"
    # Agency sites use the skeleton root; other kinds have their own facts, navigation and pages.
    kind = skel / a.kind if a.kind != "agency" else skel

    # Client facts and navigation → templates.
    shutil.copy(kind / "entity.php", plugin / "inc/entity.php")
    shutil.copy(kind / "navigation.php", theme / "inc/navigation.php")

    # Redirect map → empty (Stage 2 builds it from the audit).
    rp = plugin / "inc/redirects.php"
    s = rp.read_text()
    s = re.sub(r"function hm_redirect_map\(\): array \{.*?\n\}\n",
               "function hm_redirect_map(): array {\n\treturn array(\n\t\t// '/old-url/' => '/new-url/',  (from docs/02-information-architecture.md §4)\n\t);\n}\n",
               s, count=1, flags=re.S)
    s = re.sub(r"function hm_gone_paths\(\): array \{.*?\n\}\n",
               "function hm_gone_paths(): array {\n\treturn array();\n}\n", s, count=1, flags=re.S)
    rp.write_text(s)

    # Archive intros in block templates are client copy.
    for tpl in (theme / "templates").glob("*.html"):
        s = tpl.read_text()
        s2 = re.sub(r'<p class="hm-lead hm-mt-l">[^<]*</p>',
                    '<p class="hm-lead hm-mt-l"><mark class="hm-confirm">[CONFIRM: one-line intro for this archive]</mark></p>', s)
        if a.kind == "product-brand":
            s2 = s2.replace('<p class="hm-label">Work</p>', '<p class="hm-label">Builds</p>')
        if s2 != s:
            tpl.write_text(s2)

    # Design: the base is a wireframe; the client's design layer starts empty (stage 3 writes it).
    shutil.copy(skel / "brand-unbranded.css", theme / "assets/css/brand.css")

    # Content: skeleton pages, no media but a placeholder hero.
    shutil.copytree(kind / "content", t / "content")
    png(t / "content/media/replace-hero.png", 1600, 1200, (228, 228, 231), (161, 161, 170))
    png(plugin / "assets/og-default.png", 1200, 630, (24, 24, 27), (11, 11, 12))
    png(plugin / "assets/logo.png", 512, 512, (63, 63, 70), (24, 24, 27))

    # Project docs: templates to fill, plus the reference's generic authoring and deployment docs.
    docs = t / "docs"
    (docs / "briefs").mkdir(parents=True, exist_ok=True)
    (docs / "briefs/.gitkeep").write_text("")
    tmpl = fw / "templates"
    for src, dst in [("goal-document.md", "00-goal.md"), ("truth-file.md", "truth.md"), ("strategy.md", "01-strategy.md"),
                     ("ia.md", "02-information-architecture.md"), ("content-checklist.md", "06-content-checklist.md"),
                     ("decisions.md", "decisions.md")]:
        shutil.copy(tmpl / src, docs / dst)
    (docs / "03-seo-aeo.md").write_text(
        "# 03 SEO and AI search\n\nFollow `framework/patterns/aeo.md`. Record here:\n\n"
        "- **Primary query per page** (from the IA)\n- **5 tracked AI-search prompts** (for the weekly report)\n"
        "- **Measurement:** every `data-cta`, form step and booking event, and where it's reported\n"
        "- **Decisions:** AI crawlers allowed or not, SEO plugin, 301 map owner\n")
    (docs / "04-design-system.md").write_text(
        "# 04 Design system\n\n*Written in stage 3 from the client's raw data. Until then the site runs on the wireframe base.*\n\n"
        "## 1. Design brief (from `truth.md`, never from another client)\n| | |\n|---|---|\n| Geography | |\n| Buyer and what they judge on | |\n"
        "| Category codes (what competitors look like) | |\n| Price position | |\n| Colours and textures in their own world (logo, products, photos, place) | |\n\n"
        "## 2. Three directions compared\n| Direction | Verdict |\n|---|---|\n| A | |\n| B | |\n| C | |\n\n"
        "## 3. The chosen design\nPalette (with contrast) · type · shape · layout and section rhythm · one motif · imagery · motion.\n"
        "It lives in `assets/css/brand.css` and `theme.json`; see `framework/patterns/design-system.md` §9.\n")
    for name in ("05-content-authoring.md", "07-deployment.md"):
        s = (ref / "docs" / name).read_text()
        if name.startswith("05"):
            s = re.sub(r"## 3\. Service taxonomy.*?(?=\n---\n)",
                       ("## 3. Product-line taxonomy (builds)\n\nCase studies are customer builds; their `services:` term is the product line and `industry:` is the vehicle type.\n\n| Term name (use in `services:`) | Slug (use in work-grid `service`) | Product line page |\n|---|---|---|\n| Example line | `example-line` | /products/example-line/ |\n"
                        if a.kind == "product-brand" else
                        "## 3. Service taxonomy (case studies)\n\n| Term name (use in `services:`) | Slug (use in work-grid `service`) | Service page |\n|---|---|---|\n| Example service | `example-service` | /services/example-service/ |\n"),
                       s, count=1, flags=re.S)
        (docs / name).write_text(s)

    # The framework itself (without the starter and the reference example) and the subagents.
    shutil.copytree(fw, docs / "framework", ignore=shutil.ignore_patterns("starter", "base", "examples", ".git", "__pycache__", ".DS_Store"))
    agents = t / ".claude/agents"
    agents.mkdir(parents=True, exist_ok=True)
    for f in (fw / "agents").glob("*.md"):
        shutil.copy(f, agents / f.name)

    # Orchestrator: project state (asf.json), the bin/asf command and the /asf Claude Code command.
    (t / "bin").mkdir(exist_ok=True)
    (t / "bin/asf").write_text('#!/usr/bin/env bash\n# The Agentic Site Framework orchestrator for this project (see docs/framework/orchestrator/README.md).\nexec python3 "$(cd "$(dirname "$0")/.." && pwd)/docs/framework/orchestrator/asf.py" "$@"\n')
    (t / "bin/asf").chmod(0o755)
    commands = t / ".claude/commands"
    commands.mkdir(parents=True, exist_ok=True)
    shutil.copy(fw / "orchestrator/claude-command.md", commands / "asf.md")
    state = {
        "framework": "Agentic Site Framework", "client": a.name, "kind": a.kind, "site_url": f"http://{a.slug}.test",
        "rest_namespace": f"{a.slug}/v1",
        "created": datetime.datetime.now().astimezone().isoformat(timespec="minutes"), "stage": "truth",
        "gates": {}, "skips": {}, "deploy": {}, "measurement": {}, "log": [],
    }
    (t / "asf.json").write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")

    # Project README and CLAUDE.md.
    theme_slug = a.slug.replace("-", "")
    for name in ("README.md", "CLAUDE.md"):
        s = (skel / name).read_text()
        s = s.replace("__NAME__", a.name).replace("__SLUG__", a.slug).replace("__THEME__", theme_slug).replace("__PLUGIN__", f"{a.slug}-core")
        (t / name).write_text(s)


def main():
    ap = argparse.ArgumentParser()
    for k in ("target", "reference", "framework", "slug", "name", "short", "mark"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--kind", default="agency", choices=["agency", "product-brand"])
    a = ap.parse_args()
    t, fw, ref = Path(a.target), Path(a.framework), Path(a.reference)

    reset_client_files(t, a, fw, ref)

    # Placeholders in the skeleton files.
    for p in [*t.joinpath("content").rglob("*.html"), t / f"wp-content/plugins/{SRC_PLUGIN}/inc/entity.php"]:
        s = p.read_text().replace("__NAME__", a.name).replace("__SHORT__", a.short).replace("__MARK__", a.mark)
        p.write_text(s)

    # Rename the base's identifiers everywhere except the framework copy.
    pairs, theme = replacements(a)
    for p in text_files(t):
        if "/docs/framework/" in p.as_posix():
            continue
        s = p.read_text(encoding="utf-8")
        s2 = s
        for old, new in pairs:
            s2 = s2.replace(old, new)
        if s2 != s:
            p.write_text(s2, encoding="utf-8")

    (t / f"wp-content/plugins/{SRC_PLUGIN}/{SRC_PLUGIN}.php").rename(t / f"wp-content/plugins/{SRC_PLUGIN}" / f"{a.slug}-core.php")
    (t / f"wp-content/plugins/{SRC_PLUGIN}").rename(t / "wp-content/plugins" / f"{a.slug}-core")
    (t / f"wp-content/themes/{SRC_THEME}").rename(t / "wp-content/themes" / theme)

    # Nothing from the base's names, or from the private list, may survive outside docs/framework.
    leftovers = leftover_patterns(fw)
    leaks = []
    for p in text_files(t):
        if "/docs/framework/" in p.as_posix():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if leftovers.search(line):
                leaks.append(f"  {p.relative_to(t)}:{i}: {line.strip()[:120]}")
    if leaks:
        print("✗ Names that must not reach a client site were left in it (fix the starter, then rerun):")
        print("\n".join(leaks[:40]))
        sys.exit(1)
    print(f"  {a.kind} site: theme {theme}, plugin {a.slug}-core, REST {a.slug}/v1, skeleton pages, docs and agents in place")


if __name__ == "__main__":
    main()
