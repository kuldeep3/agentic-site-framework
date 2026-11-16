# 07 — Deployment: staging → production

*Last updated 2026-10-29*

The live site runs WordPress with the **Enfold** theme, **Rank Math** and **Gravity Forms**. This build replaces the theme and adds one plugin. It does not need a new host.

## 1. Staging (do this first)
1. Clone production to a staging site (host snapshot or migration plugin). Turn on "Discourage search engines". `robots.php` respects that setting.
2. Upload `wp-content/themes/asfbase/` and `wp-content/plugins/asfbase-core/`. Activate the plugin, then the theme.
3. Import content. Either:
   - **Seed** (fast, staging only): copy `bin/` and `content/` to the server and run `wp eval-file bin/seed.php content`. It upserts by slug, so existing pages with the same slug are overwritten.
   - **Manual:** open each `content/pages/*.html`, switch the editor to Code view, and paste the markup.
4. Settings → Reading: front page = **Home**, posts page = **Insights**. Permalinks: `/%postname%/`.
5. Rank Math: the seed also writes `rank_math_title` and `rank_math_description`. Confirm titles in Rank Math → Titles & Meta and turn **off** Rank Math's FAQ schema, because `asfbase-core` builds FAQPage from content.
6. Redirects: import `hm_redirect_map()` (`asfbase-core/inc/redirects.php`) into Rank Math → Redirections, then add `define( 'HM_PHP_REDIRECTS', false );` to `wp-config.php`.
7. Forms: the native brief form works as-is (leads go to WP → Leads and email). If ASF Base prefers Gravity Forms, swap the `hm/brief-form` block on Contact and Growth Audit. Keep the three-step structure and the budget/timeline questions.
8. Email deliverability: install an SMTP plugin (for example WP Mail SMTP) so lead emails don't land in spam.
9. Analytics: add GTM or GA4 (Site Kit or a header snippet). `site.js` already pushes `cta_click`, `book_call_open`, `phone_click`, `lead_submit`, `newsletter_signup` and `offer_view` to `dataLayer`. Keep the existing **Meta pixel** (ID on the live site) for ads.

## 2. QA before go-live
- [ ] Everything in `06-content-checklist.md` signed off; no `[CONFIRM]` chips left (`grep -r hm-confirm`)
- [ ] Every old URL in the redirect map returns 301 (spot-check 10)
- [ ] `/smsoptin/`, `/sms-terms-conditions/`, `/sms-privacy-policy/` and `/terms/` resolve (SMS carrier compliance)
- [ ] Test a brief end to end: thank-you page, lead in WP, email received
- [ ] Rich Results Test on Home, one service page and one case study (Organization, Service, FAQPage, Article)
- [ ] `/llms.txt` and `/robots.txt` load on production
- [ ] Lighthouse mobile ≥ 90 on Home and one service page; check LCP on the hero image
- [ ] Check at 375, 768, 1440 and 1920 (alignment and overflow)

## 3. Go-live
1. Back up production. Switch the theme, activate the plugin, import content (same as staging).
2. Flush permalinks (Settings → Permalinks → Save).
3. Search Console + Bing Webmaster: submit the sitemap and request indexing for Home and the 7 service pages.
4. Watch the 404 log for a week (Rank Math → 404 Monitor) and add redirects for anything missed.

## 4. After launch (first 90 days)
- Weekly: leads, booked calls, AI-referred sessions (GA4 segment, see `03-seo-aeo.md` §5)
- Publish 2 cluster articles a month (`03-seo-aeo.md` §4)
- Replace placeholders with a real team photo shoot and hi-res imagery of the flagship client
