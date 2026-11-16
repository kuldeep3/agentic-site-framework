# Principles

Fourteen rules. Each one comes from something that went wrong, or was pushed back on, while building real client sites with this framework (a US marketing agency and a UK car care brand, anonymised here). The "why" is the part to remember.

### 1. Ground the story in the client's truth, not in agency clichés
Write from the client's own words, their clients' words and their real business arc, all collected in the truth file.
**Why:** on the first project, polished but generic headlines ("one team, no hand-offs") were rejected: *"these options don't define the business."* The winning line came from the client's own engagement notes, which showed how clients arrived, what they bought next and why they stayed.

### 2. Proof before pitch
Results and the client's own customers' words come before the list of services.
**Why:** a busy owner trusts numbers and peers more than adjectives. It's the structure of the best agency sites (Omniscient, for example).

### 3. Lead with the reader's stake
Hero and service headlines speak to *you* (the reader's cost or goal), then one line says who we are and what we do.
**Why:** a clever line about the agency itself read well internally and failed with buyers. A line about the reader's stake, followed by one plain sentence about who we are, landed in three seconds.

### 4. One idea, one home. ≤ 8 sections per page.
If a section exists elsewhere (process, team, pricing), link to it. Never repeat it.
**Why:** the first build repeated a "process steps" block on 9 pages and the client called the pages too long. Cutting duplicates made every page sharper.

### 5. A calm hero
One message, one real image, one primary CTA, social proof in one line. No collages, stat badges or spinning widgets.
**Why:** a photo + dashboard + phone + badge composition was called cluttered. A single strong image won.

### 6. Real imagery, verified per client
Only show a client's work on that client's pages, after you've looked at it. Never use stock. When there's no photo, use a designed typographic cover.
**Why:** on the first project, one mockup filed under the flagship client actually showed another client's work, and one "results" image was a stock photo. Filenames lie.

### 7. Never ship the "AI look"
Banned by default: cream/beige backgrounds with serif-italic accents, monospace "eyebrow" labels, fake terminal or "readout" panels, grain overlays, and the endless eyebrow → H2 → three-card rhythm.
**Why:** the first design was rejected as *"looks like Claude design… made by AI."* See `patterns/design-system.md` for what replaced it.

### 8. Every client gets its own design, from their raw data
The base is a wireframe. Stage 3 builds the look (palette, type, layout, section rhythm, components, motif) from the client's own material: logo, products, photos, place, buyers, competitors. Never a re-skin of another client.
**Why:** a second client came out of the starter wearing the first client's design with new colours, and was rightly rejected: *"every design should be different, based on the raw data from the client."*

### 9. One layout frame, verified at four widths
Every section's content aligns to the same grid edge. Panels, header and footer share one max width. Check 375 / 768 / 1440 / 1920.
**Why:** "some sections are quite wide but some are not." Inline labels and centred narrow headings drifted off the grid on wide screens. `qa/responsive.js` catches it.

### 10. Every number has a source, or a visible `[CONFIRM]` chip
Unverified facts get a yellow chip on the page, never silence. Internal or confidential numbers stay off the site until the owner signs off.
**Why:** the strongest proof on the first project (a client's revenue growth) was private client data. It went into the checklist, not onto the page.

### 11. Confidentiality and white-label are absolute
Never name the delivery partner, the offshore team, internal rates or other clients' private data. Name the agency's clients only with their permission.
**Why:** for agency partners, being invisible *is* the product.

### 12. AI-search ready from day one
Answer-first summaries, real FAQs → FAQPage schema, one entity facts file feeding schema + llms.txt + footer, crawlers allowed.
**Why:** buyers now ask ChatGPT and Perplexity first. Being cited is a growth channel.

### 13. Content is code, rebuildable with one command
Pages are stored as block markup in files, seeded by a script; client facts live in one file; nothing client-specific is hard-coded in the theme.
**Why:** it lets AI writers work in parallel on files, lets QA run on files, and lets the next person rebuild the whole site from zero in about 2 minutes.

### 14. Measure from day one; the weekly report is the service
Analytics events ship with the build. A report goes out every week, asked for or not.
**Why:** it's how the engagement stays recurring ("the report is the service").
