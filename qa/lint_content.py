#!/usr/bin/env python3
"""Lint seed content (WordPress block markup with front matter) before it reaches the editor.

    python3 lint_content.py <content-dir> [--config config.json] [--strict] [--list-confirm]

Checks every content/pages/*.html and content/work/*.html:
  errors    unbalanced or misnamed block comments · invalid block JSON · className missing from the
            block's wrapper tag (the editor's "unexpected content") · missing title/slug ·
            SEO title / description too long · more than one <h1> · too many top-level sections ·
            missing {{media:…}} files · forbidden (white-label) terms
  warnings  missing description · [CONFIRM] chips, in the page or its front matter (errors with
            --strict) · leftover skeleton names such as "Example service" (errors with --strict) ·
            buzzwords · the contrast phrase used more than once · text or quotes repeated across pages
  theme     [CONFIRM] chips left in the theme's templates and parts (warnings; errors with --strict)

Standard library only. Exit code 1 when there are errors.
"""
import argparse
import fnmatch
import html
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRONT = re.compile(r"\A\s*<!--(.*?)-->\s*", re.S)
BLOCK = re.compile(r"<!--\s+(/?)wp:([a-z][a-z0-9-]*(?:/[a-z][a-z0-9-]*)?)(\s+(\{.*?\}))?\s+(/?)-->", re.S)
MEDIA = re.compile(r"\{\{media(?:-[a-z_]+)?:([^}]+)\}\}")
CONFIRM = re.compile(r"\[CONFIRM[^\]]*\]")
FIRST_TAG = re.compile(r"\s*<([a-z0-9]+)\b([^>]*)>", re.I)
TEXT_UNITS = re.compile(r"<(p|h[1-6]|li|blockquote|summary)\b[^>]*>(.*?)</\1>", re.S | re.I)
NO_WRAPPER = {"core/list-item", "core/html", "core/shortcode", "core/freeform", "core/more", "core/nextpage"}


def load_config(path):
    cfg = json.loads((Path(path) if path else HERE / "config.json").read_text())
    return cfg


def parse_front(raw):
    meta, body = {}, raw
    m = FRONT.match(raw)
    if m:
        for line in m.group(1).splitlines():
            kv = re.match(r"^\s*([a-z_]+)\s*:\s*(.*)$", line)
            if kv:
                meta[kv.group(1)] = kv.group(2).strip()
        body = raw[m.end():]
    return meta, body, (raw[: m.end()].count("\n") if m else 0)


def visible_text(fragment):
    fragment = re.sub(r"<!--.*?-->", " ", fragment, flags=re.S)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


def classes_of(attrs):
    m = re.search(r'class="([^"]*)"', attrs)
    return set(m.group(1).split()) if m else set()


def lint_file(path, cfg, media_dir, strict):
    errors, warnings = [], []
    raw = path.read_text(encoding="utf-8")
    meta, body, offset = parse_front(raw)

    def line_of(pos):
        return offset + body.count("\n", 0, pos) + 1

    # Front matter
    for key in ("title", "slug"):
        if not meta.get(key):
            errors.append(f"front matter: missing '{key}'")
    # A chip in front matter would go live as the page title or the search snippet. Its length is
    # judged once it's replaced, not while it's a placeholder.
    front_chips = [f"{k}: {c}" for k, v in meta.items() for c in CONFIRM.findall(v)]
    if front_chips:
        (errors if strict else warnings).append(f"{len(front_chips)} [CONFIRM] chip(s) in front matter ({', '.join(sorted({c.split(':')[0] for c in front_chips}))})")
    if meta.get("seo_title") and not CONFIRM.search(meta["seo_title"]) and len(meta["seo_title"]) > cfg["seo_title_max"]:
        errors.append(f"seo_title is {len(meta['seo_title'])} chars (max {cfg['seo_title_max']})")
    if not meta.get("description"):
        warnings.append("front matter: no description (the SEO fallback will be used)")
    elif not CONFIRM.search(meta["description"]) and len(meta["description"]) > cfg["description_max"]:
        errors.append(f"description is {len(meta['description'])} chars (max {cfg['description_max']})")
    leftovers = sorted({n for n in cfg.get("skeleton_names", []) if n in raw})
    if leftovers:
        (errors if strict else warnings).append("skeleton placeholder left: " + ", ".join(f"'{n}'" for n in leftovers))

    # Block structure
    stack, top_sections = [], 0
    for m in BLOCK.finditer(body):
        closing, name, attrs_json, self_closing = m.group(1), m.group(2), m.group(4), m.group(5)
        full = name if "/" in name else f"core/{name}"
        ln = line_of(m.start())
        attrs = {}
        if attrs_json:
            try:
                attrs = json.loads(attrs_json)
            except json.JSONDecodeError as exc:
                errors.append(f"line {ln}: invalid JSON in wp:{name} ({exc.msg})")
        if closing:
            if not stack:
                errors.append(f"line {ln}: closing /wp:{name} with no open block")
            elif stack[-1][0] != full:
                errors.append(f"line {ln}: /wp:{name} closes wp:{stack[-1][0].removeprefix('core/')} opened on line {stack[-1][1]}")
                stack.pop()
            else:
                stack.pop()
            continue
        if not stack and full == "core/group" and attrs.get("tagName") == "section":
            top_sections += 1
        if not self_closing:
            stack.append((full, ln))
            # The wrapper element must carry the block's className, or the editor flags the block.
            if full.startswith("core/") and full not in NO_WRAPPER:
                tag = FIRST_TAG.match(body, m.end())
                missing = set(str(attrs.get("className", "")).split()) - (classes_of(tag.group(2)) if tag else set())
                if missing:
                    errors.append(f"line {ln}: wp:{name} className {sorted(missing)} not on its wrapper tag")
                if full == "core/group" and tag and tag.group(1).lower() != attrs.get("tagName", "div"):
                    errors.append(f"line {ln}: wp:group tagName '{attrs.get('tagName', 'div')}' but wrapper is <{tag.group(1)}>")
    for full, ln in stack:
        errors.append(f"line {ln}: wp:{full.removeprefix('core/')} is never closed")

    if top_sections > cfg["max_sections"]:
        errors.append(f"{top_sections} top-level sections (max {cfg['max_sections']}): one idea, one home")
    h1s = len(re.findall(r"<h1\b", body, re.I))
    if h1s > 1:
        errors.append(f"{h1s} <h1> tags (one per page)")

    # Media
    for ref in MEDIA.findall(body):
        if not (media_dir / ref.strip()).exists():
            errors.append(f"media not found: content/media/{ref.strip()}")

    # Words
    text = visible_text(body)
    everything = (" ".join(meta.values()) + " " + text)
    low = everything.lower()
    for term in cfg["forbidden"]:
        if term.lower() in low:
            errors.append(f"forbidden term: '{term}'")
    for word in cfg["buzzwords"]:
        if re.search(rf"\b{re.escape(word.lower())}", low):
            warnings.append(f"buzzword: '{word}'")
    contrast = cfg.get("contrast_phrase")
    if contrast:
        n = low.count(contrast.lower())
        if n > 1:
            warnings.append(f"'{contrast}' appears {n} times (use the contrast once per page)")
    confirms = CONFIRM.findall(body)
    front = raw[: len(raw) - len(body)]
    if confirms:
        (errors if strict else warnings).append(f"{len(confirms)} [CONFIRM] chip(s)")

    units = []
    for m in TEXT_UNITS.finditer(body):
        tag, inner = m.group(1).lower(), visible_text(m.group(2))
        units.append((tag, inner))
    return errors, warnings, units, CONFIRM.findall(front) + confirms, top_sections, len(text.split())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("content", help="path to the content/ folder")
    ap.add_argument("--config", help="QA config (default: config.json next to this script)")
    ap.add_argument("--strict", action="store_true", help="treat [CONFIRM] chips as errors (launch week)")
    ap.add_argument("--list-confirm", action="store_true", help="print every [CONFIRM] chip and exit")
    args = ap.parse_args()

    cfg = load_config(args.config)
    root = Path(args.content)

    # Design: every client needs its own brand layer (stage 3); never the placeholder or the reference look.
    brand_notes = []
    themes = list((root.parent / "wp-content/themes").glob("*/assets/css/main.css"))
    for main_css in themes:
        brand = main_css.with_name("brand.css")
        if not brand.exists():
            brand_notes.append(f"{brand.relative_to(root.parent)} is missing: the site has no design layer")
        elif "ASF:UNBRANDED" in brand.read_text(encoding="utf-8"):
            brand_notes.append(f"{brand.relative_to(root.parent)} is still the unbranded placeholder (stage 3 replaces it)")
    files = sorted([*root.glob("pages/*.html"), *root.glob("work/*.html")])
    if not files:
        sys.exit(f"No pages found under {root}/pages or {root}/work")

    seen = defaultdict(set)  # normalised text → files
    total_e = total_w = 0
    report = []
    for f in files:
        rel = f.relative_to(root).as_posix()
        errors, warnings, units, confirms, sections, words = lint_file(f, cfg, root / "media", args.strict)
        if args.list_confirm:
            for c in confirms:
                print(f"{rel}: {c}")
            continue
        if not any(fnmatch.fnmatch(f.name, pat) for pat in cfg["ignore_files"]):
            # Short labels ("Who this is for.") repeat by design; sentences and quotes shouldn't.
            for tag, text in units:
                min_len = cfg["dupe_min_chars"] if tag in ("p", "li", "blockquote") else 30
                if len(text) >= min_len and tag != "summary":
                    seen[("quote" if tag == "blockquote" else "text", text.lower())].add(rel)
        report.append((rel, errors, warnings, sections, words))
    theme_dir = root.parent / "wp-content/themes"
    templates = [t for t in sorted(theme_dir.glob("*/*/*.html")) if t.parent.name in ("templates", "parts")]
    if args.list_confirm:
        for tpl in templates:
            for c in CONFIRM.findall(tpl.read_text(encoding="utf-8")):
                print(f"{tpl.relative_to(root.parent).as_posix()}: {c}")
        return

    for rel, errors, warnings, sections, words in report:
        total_e += len(errors)
        total_w += len(warnings)
        if errors or warnings:
            print(f"\n{rel}  ({sections} sections, {words} words)")
            for e in errors:
                print(f"  ✗ {e}")
            for w in warnings:
                print(f"  · {w}")

    repeats = [(kind, text, sorted(where)) for (kind, text), where in seen.items() if len(where) > 1]
    if repeats:
        print("\nRepeated across pages (one idea, one home; quotes belong to one page):")
        for kind, text, where in sorted(repeats, key=lambda r: (r[0] != "quote", r[2])):
            total_w += 1
            label = "quote" if kind == "quote" else "text "
            print(f"  · {label} “{text[:80]}{'…' if len(text) > 80 else ''}”\n          {', '.join(where)}")
    # Chips in theme templates and parts (archive intros, the 404) render on live pages too.
    theme_chips = [(t.relative_to(root.parent).as_posix(), n) for t in templates if (n := len(CONFIRM.findall(t.read_text(encoding="utf-8"))))]
    if theme_chips:
        print("\nTheme templates (edit them in the theme, or in Appearance → Editor):")
        for rel, n in theme_chips:
            print(f"  {'✗' if args.strict else '·'} {rel}: {n} [CONFIRM] chip(s)")
            if args.strict:
                total_e += 1
            else:
                total_w += 1
    if brand_notes:
        print("\nDesign:")
        for note in brand_notes:
            print(f"  {'✗' if args.strict else '·'} {note}")
            if args.strict:
                total_e += 1
            else:
                total_w += 1
    print(f"\n{len(report)} files · {total_e} error(s) · {total_w} warning(s)")
    sys.exit(1 if total_e else 0)


if __name__ == "__main__":
    main()
