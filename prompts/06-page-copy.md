# Prompt 06: Page copy as block markup

**Stage:** 3 System · **Run by:** Writer subagents (`site-copywriter`), one per page family, in parallel

## Prompt (one per family)
```text
Write these pages for [CLIENT] as WordPress block markup files: [list of briefs, e.g.
docs/briefs/services-*.md].

Read first:
- docs/01-strategy.md: §3 (message stack) and §7 (voice)
- docs/truth.md: claims register and voice bank
- docs/05-content-authoring.md: the file format, front matter and component vocabulary.
  Use ONLY these components and copy their markup patterns exactly.
- content/pages/home.html: a finished page to match for markup style
- docs/framework/patterns/messaging.md

For each brief, write content/pages/<slug-with-dashes>.html:
- Front matter: title, slug, seo_title (≤ 60), description (≤ 155, written as an answer), order.
- Exactly the sections in the brief, in order, ≤ 8 top-level sections.
- The hero headline speaks to the reader's stake. One "Most agencies… We…" contrast per page.
- Service and industry pages: an hm-answer paragraph (40–60 words, primary query in sentence one)
  and an hm-fit block (4 good fit / 4 not a fit).
- Every number comes from the claims register with status public. Anything else is wrapped as
  <mark class="hm-confirm">[CONFIRM: what to check]</mark>.
- Images only from the brief's verified list, via {{media:file}} placeholders.
- Don't add a closing CTA section: the footer CTA closes every page.

Self-check before you finish: run `python3 docs/framework/qa/lint_content.py content` and fix every
error in your files. Report the warnings you left and why.
```

## After all Writers finish (orchestrator)
Read every page in order as one buyer: home → services → a case study → start → contact. Remove repeated lines, repeated proof and repeated headings across families. Then run `lint_content.py` again: its duplicate check catches what you miss.
