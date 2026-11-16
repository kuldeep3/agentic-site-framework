# Prompt 03: Reference teardown

**Stage:** 1 Truth (feeds 2 and 3) · **Run by:** the Researcher subagent · **Needs:** a browser tool

## Prompt
```text
Tear down these reference sites for structure and craft, not words: [URL 1], [URL 2], [URL 3].
They're best-in-class sites for [segment]. Our client is [CLIENT]; see docs/truth.md §1.

For each site, record:
1. The home page section order, one line per section: what it says and which component it uses.
2. The hero formula: headline pattern (stakes? about-us? outcome?), supporting line, CTA wording,
   how social proof is shown.
3. Proof: where results first appear (which scroll), and the format (numbers, logos, quotes, video).
4. CTA strategy: how many CTAs, their wording, and the conversion path.
5. Pricing transparency: published prices, anchors, "starting at".
6. What makes it look expensive: type, spacing, imagery, motion, restraint. Be specific
   (e.g. "sentence-case display at ~96px, a single accent colour, real client photography full-bleed").
7. What we should NOT borrow, and why.
8. Their colours and type, read from the CSS (not guessed from screenshots): the main hex values
   and the font families. Stage 3 designs against these category codes (prompt 07).

Finish with a section "Patterns to adapt for [CLIENT]", 5–8 bullets, each tied to something
true in docs/truth.md. Never copy a line of their copy.
Write the result to docs/references.md.
```

## Expected output
`docs/references.md`.

## Check before accepting
- Every "pattern to adapt" ties back to the client's truth. A pattern that only fits the reference brand is dropped.
