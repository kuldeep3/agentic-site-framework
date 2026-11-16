/* Colour contrast and keyboard focus check (WCAG 2.2 AA). Paste into the page (browser tool
 * "javascript_tool", or the DevTools console) on each key template. Returns a small report object.
 *
 *   failures   visible text below 4.5:1 (or 3:1 for large text: 24px, or 18.66px bold), grouped by
 *              colour pair, with an example and how many elements use it
 *   unknown    text over an image or gradient: the script can't measure it, so check those by eye
 *   noFocus    links, buttons and fields whose CSS gives them no outline, ring or other change when
 *              focused, on the control itself or on its parent or grandparent (:focus-within). The
 *              browser's own ring may still show if nothing removes it: check by Tab
 *   pass       true when there are no failures and every control has a focus style
 *
 * What counts as "behind" the text: the backgrounds of its ancestors (translucent ones blended), a
 * panel painted by an ancestor's absolutely positioned ::before (when it covers most of that
 * ancestor), and, when no ancestor below <body> is opaque (a fixed or sticky header over a dark
 * hero), whatever is painted under the text on screen. Text that is off screen and has no opaque
 * ancestor is measured against <body>.
 *
 * Run it in each colour context the design uses (light sections, dark sections, the footer, the
 * header over a dark hero). Open menus first if their links should be checked too. Transitions are
 * switched off while it measures, and its temporary styles are removed when it's done.
 */
(() => {
  const parse = (c) => {
    const m = c && c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[\s,/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const blend = (top, under) => ({
    r: top.r * top.a + under.r * (1 - top.a),
    g: top.g * top.a + under.g * (1 - top.a),
    b: top.b * top.a + under.b * (1 - top.a),
    a: 1,
  });
  const lum = ({ r, g, b }) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
  const hex = ({ r, g, b }) => "#" + [r, g, b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");
  const label = (el) => {
    const cls = [...el.classList].filter((c) => !c.startsWith("wp-") && !c.startsWith("is-")).slice(0, 2).join(".");
    return `${el.tagName.toLowerCase()}${cls ? "." + cls : ""}`;
  };
  const visible = (el) => {
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return s.display !== "none" && s.visibility !== "hidden" && +s.opacity > 0.1 && r.width > 1 && r.height > 1
      && !el.closest("[aria-hidden='true'], [hidden], .screen-reader-text, .hm-hp");
  };

  // Measure the end state of every style, not a transition halfway through (a focus ring that fades
  // in would otherwise read as "no change"). pointer-events: auto lets elementsFromPoint() see
  // decorative layers that opt out of clicks. Removed again at the end.
  const pause = document.createElement("style");
  pause.textContent = "*, *::before, *::after { transition: none !important; pointer-events: auto !important; }";
  document.head.appendChild(pause);
  const added = [];

  try {
    const isImage = (bgImage) => bgImage && bgImage !== "none" && !/^url\(.*\.svg/.test(bgImage); // image or gradient

    // The colours an element paints under its content, topmost first: its background, and a
    // ::before panel (absolutely positioned, covering most of the element). Small ::before marks
    // such as check-mark circles don't count. null = an image or gradient: can't measure.
    const own = (p) => {
      const s = getComputedStyle(p);
      if (isImage(s.backgroundImage)) return null;
      const out = [];
      const c = parse(s.backgroundColor);
      if (c && c.a > 0) out.push(c);
      const b = getComputedStyle(p, "::before");
      if (!/^(none|normal)$/.test(b.content) && b.position === "absolute" && b.display !== "none") {
        const w = p.offsetWidth || p.getBoundingClientRect().width;
        const h = p.offsetHeight || p.getBoundingClientRect().height;
        const covers = w > 0 && h > 0 && parseFloat(b.width) >= 0.8 * w && parseFloat(b.height) >= 0.5 * h;
        if (covers) {
          if (isImage(b.backgroundImage)) return null;
          const bc = parse(b.backgroundColor);
          // A negative z-index puts the panel under the element's own background; otherwise over it.
          if (bc && bc.a > 0) (parseInt(b.zIndex, 10) < 0 ? out.push(bc) : out.unshift(bc));
        }
      }
      return out;
    };
    // Add an element's layers to the stack; true once an opaque one is reached, null for an image.
    const stack = (layers, p) => {
      const o = own(p);
      if (!o) return null;
      for (const c of o) { layers.push(c); if (c.a >= 1) return true; }
      return false;
    };

    // The colour actually behind an element.
    const background = (el) => {
      const layers = [];
      // 1. Its ancestors, stopping before <body>.
      for (let p = el; p && p !== document.body && p !== document.documentElement; p = p.parentElement) {
        const done = stack(layers, p);
        if (done === null) return null;
        if (done) return flatten(layers);
      }
      // 2. Nothing opaque: what's painted under it on screen (a fixed or absolute header over a dark
      //    hero), at the middle of its first line.
      const box = [...el.getClientRects()].find((r) => r.width > 0 && r.height > 0);
      const x = box ? box.left + box.width / 2 : -1;
      const y = box ? box.top + box.height / 2 : -1;
      if (x >= 0 && y >= 0 && x < innerWidth && y < innerHeight) {
        const hits = document.elementsFromPoint(x, y);
        const at = hits.indexOf(el);
        for (const e of at >= 0 ? hits.slice(at + 1) : hits) { // topmost first; what's above the text doesn't count
          if (e === document.documentElement || e === document.body || e.contains(el) || el.contains(e)) continue;
          if (getComputedStyle(e).opacity === "0") continue;
          if (/^(img|picture|video|canvas|iframe|object|embed)$/.test(e.localName) || e instanceof SVGElement) return null;
          const done = stack(layers, e);
          if (done === null) return null;
          if (done) return flatten(layers);
        }
      }
      // 3. Then <body> and <html>, then white.
      for (const p of [document.body, document.documentElement]) {
        const done = stack(layers, p);
        if (done === null) return null;
        if (done) break;
      }
      return flatten(layers);
    };
    const flatten = (layers) => {
      let base = { r: 255, g: 255, b: 255, a: 1 };
      for (const c of [...layers].reverse()) base = blend(c, base);
      return base;
    };

    const pairs = new Map();
    const unknown = new Set();
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) => (n.nodeValue.trim().length > 1 ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT),
    });
    const seen = new Set();
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const el = n.parentElement;
      if (!el || seen.has(el) || /^(SCRIPT|STYLE|NOSCRIPT|OPTION)$/.test(el.tagName) || !visible(el)) continue;
      seen.add(el);
      const s = getComputedStyle(el);
      const bg = background(el);
      if (!bg) { unknown.add(label(el) + ` “${n.nodeValue.trim().slice(0, 30)}”`); continue; }
      const fgRaw = parse(s.color);
      if (!fgRaw) continue;
      const fg = blend(fgRaw, bg);
      const size = parseFloat(s.fontSize);
      const large = size >= 24 || (size >= 18.66 && +s.fontWeight >= 700);
      const need = large ? 3 : 4.5;
      const r = ratio(fg, bg);
      if (r + 0.005 >= need) continue;
      const key = `${hex(fg)} on ${hex(bg)}`;
      const entry = pairs.get(key) || { pair: key, ratio: +r.toFixed(2), need, count: 0, example: "" };
      entry.count += 1;
      entry.example ||= `${label(el)} “${n.nodeValue.trim().replace(/\s+/g, " ").slice(0, 40)}”`;
      pairs.set(key, entry);
    }

    // Focus: each control should look different when focused. Script-driven focus doesn't trigger
    // :focus-visible, so copy every :focus / :focus-visible rule as a [data-asf-focus] rule, and every
    // :focus-within rule as a [data-asf-within] rule (same specificity, right after the original).
    // Then compare each control, with its parent and grandparent (a row whose border changes while
    // the field inside it is focused), with and without the attributes.
    const copyRules = (list, owner) => {
      for (let i = 0; i < list.length; i++) {
        const r = list[i];
        if (!(r instanceof CSSStyleRule)) { if (r.cssRules && r.insertRule) copyRules(r.cssRules, r); continue; }
        if (!/:focus(-visible|-within)?(?![-\w])/.test(r.selectorText)) continue;
        const sel = r.selectorText
          .replace(/:focus-within(?![-\w])/g, "[data-asf-within]")
          .replace(/:focus-visible(?![-\w])|:focus(?![-\w])/g, "[data-asf-focus]");
        try { owner.insertRule(`${sel}{${r.style.cssText}}`, i + 1); added.push([owner, owner.cssRules[i + 1]]); i++; } catch (e) { /* unsupported selector */ }
      }
    };
    for (const sheet of document.styleSheets) {
      try { copyRules(sheet.cssRules, sheet); } catch (e) { /* another origin's stylesheet */ }
    }
    const look1 = (el) => { const s = getComputedStyle(el); return [s.outlineStyle, s.outlineWidth, s.outlineColor, s.boxShadow, s.borderColor, s.backgroundColor, s.color, s.textDecorationLine].join("|"); };
    const look = (el) => [el, el.parentElement, el.parentElement?.parentElement].filter(Boolean).map(look1).join("||");
    const noFocus = [];
    const controls = [...document.querySelectorAll("a[href], button, input:not([type=hidden]), select, textarea, [tabindex]:not([tabindex='-1'])")]
      .filter(visible).slice(0, 120);
    for (const el of controls) {
      const idle = look(el);
      const chain = [];
      for (let p = el; p; p = p.parentElement) chain.push(p); // :focus-within matches the control and every ancestor
      el.setAttribute("data-asf-focus", "");
      chain.forEach((p) => p.setAttribute("data-asf-within", ""));
      const focused = look(el);
      el.removeAttribute("data-asf-focus");
      chain.forEach((p) => p.removeAttribute("data-asf-within"));
      if (focused === idle) noFocus.push(label(el) + ` “${(el.innerText || el.value || el.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ").slice(0, 30)}”`);
    }

    const failures = [...pairs.values()].sort((a, b) => b.count - a.count);
    return {
      pass: failures.length === 0 && noFocus.length === 0,
      failures,
      unknown: [...unknown].slice(0, 15),
      noFocus: [...new Set(noFocus)].slice(0, 15),
      checked: seen.size,
    };
  } finally {
    for (const [owner, rule] of added.reverse()) {
      const i = [...owner.cssRules].indexOf(rule);
      if (i >= 0) owner.deleteRule(i);
    }
    pause.remove();
  }
})();
