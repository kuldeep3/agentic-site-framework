/* Responsive + layout-frame check. Paste into the page (browser tool "javascript_tool", or DevTools console)
 * at each width: 375, 768, 1440, 1920. Returns a small report object.
 *
 *   overflowX   true if the page scrolls sideways (always a bug)
 *   wide        elements sticking out of the viewport, outermost only, ignoring intentional scrollers
 *   edge        the content edge most section children share (px from the left)
 *   offGrid     section children whose left edge isn't on that edge (the "some sections are wider" bug)
 *
 * Tune per project without editing: set window.ASF_SECTION (default ".hm-section") and
 * window.ASF_GRID_IGNORE (selectors allowed off the grid, e.g. full-bleed strips) before pasting.
 */
(() => {
  const SECTION = window.ASF_SECTION || ".hm-section";
  const IGNORE = window.ASF_GRID_IGNORE || "[data-grid-ignore], .alignfull, .hm-marquee > *, .hm-creatives, script, style";
  const vw = document.documentElement.clientWidth;
  const label = (el) => {
    const cls = [...el.classList].filter((c) => !c.startsWith("wp-block-") && !c.startsWith("is-layout")).slice(0, 3).join(".");
    const text = (el.innerText || "").trim().replace(/\s+/g, " ").slice(0, 40);
    return `${el.tagName.toLowerCase()}${cls ? "." + cls : ""}${text ? ` “${text}”` : ""}`;
  };
  const clipped = (el) => {
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      if (/(auto|scroll|hidden|clip)/.test(getComputedStyle(p).overflowX)) return true;
    }
    return false;
  };
  const visible = (el) => {
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return s.display !== "none" && s.visibility !== "hidden" && r.width > 0 && r.height > 0;
  };

  // 1. Anything poking out of the viewport (outermost offender only).
  const flagged = new Set();
  const wide = [];
  for (const el of document.body.querySelectorAll("*")) {
    if (!visible(el) || clipped(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.right <= vw + 1 && r.left >= -1) continue;
    if (el.parentElement && flagged.has(el.parentElement)) { flagged.add(el); continue; }
    flagged.add(el);
    wide.push(`${label(el)} spans ${Math.round(r.left)}→${Math.round(r.right)}px`);
  }

  // 2. One content edge: direct children of every section should share a left edge.
  const lefts = [];
  for (const section of document.querySelectorAll(SECTION)) {
    for (const child of section.children) {
      if (child.matches(IGNORE) || !visible(child)) continue;
      const pos = getComputedStyle(child).position;
      if (pos === "absolute" || pos === "fixed") continue;
      lefts.push({ el: child, section, left: Math.round(child.getBoundingClientRect().left) });
    }
  }
  const counts = {};
  lefts.forEach((l) => (counts[l.left] = (counts[l.left] || 0) + 1));
  const edge = Number(Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? 0);
  const offGrid = lefts
    .filter((l) => Math.abs(l.left - edge) > 2)
    .map((l) => `${label(l.el)} at ${l.left}px in section.${[...l.section.classList].filter((c) => !c.startsWith("wp-block-") && c !== "alignfull").join(".")}`);

  return {
    url: location.pathname,
    width: window.innerWidth,
    overflowX: document.documentElement.scrollWidth > vw + 1,
    edge,
    checked: lefts.length,
    wide: wide.slice(0, 15),
    offGrid: offGrid.slice(0, 15),
    pass: document.documentElement.scrollWidth <= vw + 1 && wide.length === 0 && offGrid.length === 0,
  };
})();
