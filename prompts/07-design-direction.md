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
Then write each direction as a preview stylesheet, assets/css/directions/a.css, b.css and c.css,
good enough for the home hero and two sections (fonts self-hosted inside each file). Check each
at /?asf_direction=a|b|c, run prompt C to put them in Figma, and stop for the client's choice.
Only the chosen direction becomes assets/css/brand.css + theme.json.
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

## C. Push the directions to Figma for review (stage 3.2a)
```text
Put the design directions for [CLIENT] in one Figma file the client and designer can comment on.
For each direction (a, b, c): open the home page and [one inner page] at /?asf_direction=<x>, at
1440px and at 375px, and capture each as a frame with the Figma connector (from the rendered
page or its code). One Figma page per direction, frames named "<Page> · <width>". Add a page
"Decision": the three home heroes side by side, with the design brief (docs/04-design-system.md §1)
and each direction's one-sentence idea as text. If the connector can't capture a page, place a
full-page screenshot instead and say so.
Then: `bin/asf set design.figma_url <file URL>`, fill §4 of docs/04-design-system.md, and give me
the link to share. Don't share it with anyone yourself.
```

## D. Bring design feedback back (stage 3.2a and G3)
```text
Read the comments on [FIGMA FILE URL] with the Figma connector. For each unresolved comment, draft
one item: the comment in the commenter's words, who wrote it, the frame it's on, and the comment
link. Show me the list; file the ones I approve with
`bin/asf intake add "<short title>" --type design --source figma --ref "<comment link>" --quote "<their words>"`.
If a comment changes the design itself (not just a question), say which rule in brand.css it
touches. When the client names a direction, record it word for word:
`bin/asf set design.direction "<letter>, chosen by <name> on <date>: <their words>"`.
```
