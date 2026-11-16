# Prompt 07: Design direction and review

**Stage:** 3 System · **Run by:** the orchestrator, with a human designer reviewing

## A. Direction
```text
Propose the design direction for [CLIENT]'s site. You're a senior brand designer with 20 years
at top studios, designing for [CLIENT]'s buyers in [geography].

Read the raw data first: docs/truth.md (who they are, their arc, voice, products, people),
docs/references.md (the competitor teardown, including their real colours from CSS),
content/media/ (open every photo), the client's logo at [path], and
docs/framework/patterns/design-system.md.

Design brief (fill it from that data before proposing anything; ask if any line is unknown):
- Geography: [where they sell]
- Buyer: [who decides, and what they judge on]
- Category codes: [what competitors look like, from the teardown]
- Price position: [premium / mid-market / budget]
- Their own world: [logo, products, packaging, photos, place, founders' words]
Never start from the base wireframe, a template, or another client's design.

Show three directions side by side, scored against the brief, and recommend one. Each direction:
1. The visual idea in one sentence: the one move that is theirs, tied to something true in the
   raw data (e.g. textures from the client's own culture photography; a car care brand's
   water beading turned into its accent colour).
2. Palette: roles (text, dark surfaces, accent on light, accent on dark, one rich moment, soft
   ground) with contrast ratios. Flat colour: no gradients.
3. Type: a display face + a UI face (free, self-hostable), with width, weight, tracking and case.
4. Layout and section rhythm: grid, density, how sections alternate, how the hero is composed.
5. Shape and one motif: corners, borders, buttons and labels, and the single recurring device.
6. Imagery: which verified images carry the hero and the cards, and what replaces missing
   photos (typographic covers, product shots).
7. What makes it unlike the competitors in the teardown, and unlike other clients' sites.
Then build ONLY the home hero and two sections in the design layer (assets/css/brand.css +
theme.json), and stop for review.
```

## B. Review (run before the client sees anything, and again at G3)
```text
Review the page at [URL] at 1440px and 375px wide as a skeptical creative director.
Screenshot both widths. Go through docs/framework/patterns/design-system.md §4 (anti-"AI look")
item by item: pass or fail, with the element at fault. Then check the calm-hero rule (§5)
and the layout frame (§6) by running docs/framework/qa/responsive.js.
Finally, answer honestly: would this look at home next to the reference sites in docs/references.md?
If not, name the three changes that would close the gap most.
```
