/* Colour contrast and keyboard focus check (WCAG 2.2 AA). Paste into the page (browser tool
 * "javascript_tool", or the DevTools console) on each key template. Returns a small report object.
 *
 *   failures   visible text below 4.5:1 (or 3:1 for large text: 24px, or 18.66px bold), grouped by
 *              colour pair, with an example and how many elements use it
 *   unknown    text over an image or gradient: the script can't measure it, so check those by eye
 *   noFocus    links, buttons and fields whose CSS gives them no outline, ring or other change when
 *              focused (the browser's own ring may still show if nothing removes it: check by Tab)
 *   pass       true when there are no failures and every control has a focus style
 *
 * Run it in each colour context the design uses (light sections, dark sections, the footer, the
 * header over a dark hero). Open menus first if their links should be checked too.
 */
(() => {
  const parse = (c) => {
    const m = c.match(/rgba?\(([^)]+)\)/);
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

  // The colour actually behind an element: walk up, blending translucent backgrounds.
  const background = (el) => {
    const layers = [];
    for (let p = el; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.backgroundImage !== "none" && !/^url\(.*\.svg/.test(s.backgroundImage)) return null; // image or gradient
      const c = parse(s.backgroundColor);
      if (c && c.a > 0) { layers.push(c); if (c.a >= 1) break; }
    }
    let base = { r: 255, g: 255, b: 255, a: 1 };
    for (const c of layers.reverse()) base = blend(c, base);
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
  // :focus-visible, so copy every :focus / :focus-visible rule as a [data-asf-focus] rule (same
  // specificity, right after the original) and compare each control with and without the attribute.
  const added = [];
  const copyRules = (list, owner) => {
    for (let i = 0; i < list.length; i++) {
      const r = list[i];
      if (!(r instanceof CSSStyleRule)) { if (r.cssRules && r.insertRule) copyRules(r.cssRules, r); continue; }
      if (!/:focus(-visible)?(?![-\w])/.test(r.selectorText)) continue;
      const sel = r.selectorText.replace(/:focus-visible|:focus(?![-\w])/g, "[data-asf-focus]");
      try { owner.insertRule(`${sel}{${r.style.cssText}}`, i + 1); added.push([owner, owner.cssRules[i + 1]]); i++; } catch (e) { /* unsupported selector */ }
    }
  };
  for (const sheet of document.styleSheets) {
    try { copyRules(sheet.cssRules, sheet); } catch (e) { /* another origin's stylesheet */ }
  }
  const look = (el) => { const s = getComputedStyle(el); return [s.outlineStyle, s.outlineWidth, s.outlineColor, s.boxShadow, s.borderColor, s.backgroundColor, s.color, s.textDecorationLine].join("|"); };
  const noFocus = [];
  const controls = [...document.querySelectorAll("a[href], button, input:not([type=hidden]), select, textarea, [tabindex]:not([tabindex='-1'])")]
    .filter(visible).slice(0, 120);
  for (const el of controls) {
    const idle = look(el);
    el.setAttribute("data-asf-focus", "");
    const focused = look(el);
    el.removeAttribute("data-asf-focus");
    if (focused === idle) noFocus.push(label(el) + ` “${(el.innerText || el.value || el.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ").slice(0, 30)}”`);
  }
  for (const [owner, rule] of added.reverse()) {
    const i = [...owner.cssRules].indexOf(rule);
    if (i >= 0) owner.deleteRule(i);
  }

  const failures = [...pairs.values()].sort((a, b) => b.count - a.count);
  return {
    pass: failures.length === 0 && noFocus.length === 0,
    failures,
    unknown: [...unknown].slice(0, 15),
    noFocus: [...new Set(noFocus)].slice(0, 15),
    checked: seen.size,
  };
})();
