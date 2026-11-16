# Prompt 08: QA review

**Stage:** 4 Ship · **Run by:** the QA subagent (`site-qa`)

## Prompt
```text
Run the full QA for [CLIENT]'s site at [LOCAL URL]. Project root: [path].

Automated:
1. python3 docs/framework/qa/lint_content.py content --config docs/framework/qa/config.json
2. python3 docs/framework/qa/crawl.py [URL] --config docs/framework/qa/config.json
3. Responsive: in the browser, for each of home, [a service], [an industry], about, [a case study]
   and contact, at widths 375, 768, 1440 and 1920, run docs/framework/qa/responsive.js and record
   the result.
4. Editor validation: open each page in the block editor and run the snippet in
   docs/framework/stages/4-ship.md §4.2.
5. Launch readiness: python3 docs/framework/qa/launch.py [URL] (add --env staging on staging).
   Security, performance, accessibility and launch settings; set ASF_WP_USER and
   ASF_WP_APP_PASSWORD to include the site's own health (updates, admin accounts, failed emails).
6. Contrast and focus: on each key template, in each colour context, run
   docs/framework/qa/contrast.js in the browser. Then Tab through the header, the menu and the form.

Human read (as [ICP buyer], in this order: home → [service] → [case study] → start → contact):
- Repetition: the same idea, proof, quote or heading on two pages
- Flat lines: anything a competitor could say unchanged
- Claims without proof within one scroll
- Pages that feel long: count sections, and name any section that doesn't earn its place
- Dead ends: a page with no clear next step
- Visual: the anti-"AI look" checklist and the calm-hero rule

Report: one table of failures (page, check, what's wrong, suggested fix), ranked by impact on
the goal. Security errors (exposed files, leaked login names, a public debug log) rank first after
any white-label hit. Don't fix anything yourself unless told to. List what you couldn't check.
```

## Expected output
A ranked failure table. The orchestrator fixes, then reruns the automated checks.
