<!-- One change per pull request. Link the request it answers, so the board moves by itself. -->
Closes #

<!-- After launch: the change this carries (`bin/asf change new <slug> …` on this branch). Its brief and sign-offs are in docs/changes/ and docs/log/. -->
Change: `docs/changes/<slug>.md`

## What this does


## Where to look
<!-- The pages or URLs it changes. Screenshots at 375 and 1440 for anything visual. -->


## Checked
- [ ] `python3 docs/framework/qa/lint_content.py content` has no errors
- [ ] Every number, name and quote is in `docs/truth.md` as public, or shows a `[CONFIRM]` chip
- [ ] Looks right at 375, 768, 1440 and 1920 (visual changes)
- [ ] Opens in the block editor with no invalid blocks (page changes)
- [ ] One idea, one home: nothing here repeats a section that lives on another page

## Who needs to look
<!-- Tick what applies and ask that person for a review. Names are in `bin/asf team`. -->
- [ ] Designer: it changes how something looks
- [ ] Content: it changes what a page says
- [ ] Developer: it changes the theme, the plugin or how the site deploys
- [ ] QA: it changes a form, navigation or a template many pages use
