# 07 — Deployment: staging → production

This build is one theme and one plugin on WordPress. It runs on any WordPress host (managed hosting is easiest: SSL, backups, caching and staging come with it). Record what's true for this client in `docs/decisions.md`: the host, the SEO plugin (if any), the forms (the native brief form, or a forms plugin), the mail service.

Deploy `wp-content/themes/<theme>/` and `wp-content/plugins/<slug>-core/`, never the project folder: `docs/`, `content/`, `asf.json` and `CLAUDE.md` hold the client's private working notes. `launch.py` fails if they're reachable.

## 1. Staging (do this first)
1. Create the staging site at the host (or clone production, if there is one). Turn on **Settings → Reading → Discourage search engines**; protect it with a password if the host allows. `robots.php` respects the setting.
2. Upload the theme and the plugin. Activate the plugin, then the theme.
3. Import content. Either:
   - **Seed** (fast, staging only): copy `bin/` and `content/` to the server, run `wp eval-file bin/seed.php content`, then delete both folders from the server. It upserts by slug, so existing pages with the same slug are overwritten.
   - **Manual:** open each `content/pages/*.html`, switch the editor to Code view, and paste the markup.
4. Settings → Reading: the front page and posts page. Permalinks: `/%postname%/`.
5. SEO plugin (if the client uses one): the seed writes `rank_math_title` / `rank_math_description`; map them to the plugin in use, and turn off its FAQ schema, because the core plugin builds FAQPage from content.
6. Redirects: import `hm_redirect_map()` (`inc/redirects.php`) into the redirect tool in use, then add `define( 'HM_PHP_REDIRECTS', false );` to `wp-config.php`. With no redirect tool, leave the PHP redirects on.
7. Mail: install an SMTP plugin connected to the client's mail service (or confirm the host relays mail), set `lead_email` in `inc/entity.php`, and send a test enquiry. Lead emails sent through PHP `mail()` often land in spam. Failed sends are recorded and show up in `launch.py` and the weekly report.
8. Analytics: set `define( 'ASF_GA4_ID', 'G-…' );` (or `ASF_GTM_ID`) in production's wp-config; the plugin loads the tag with Google Consent Mode. Consent defaults to required: UK/EU sites need a consent banner that calls `window.asfConsent.grant()` (set `ASF_ANALYTICS_CONSENT` to `not_required` only where the law allows). `site.js` already sends `cta_click`, `book_call_open`, `phone_click`, `lead_submit`, `newsletter_signup` and `offer_view`.
9. An Application Password for the scans and the weekly report: WordPress admin → Users → Profile → Application Passwords. Store it as `ASF_WP_USER` / `ASF_WP_APP_PASSWORD` wherever the checks run, never in the repo.
10. Record it: `bin/asf set deploy.staging_url https://…`.

## 2. Hardening (on by default)
The core plugin's `inc/hardening.php` sends the security headers (nosniff, framing, referrer, permissions; HSTS over HTTPS), hides the WordPress version, turns author archives and the users API into dead ends for visitors (they leak login names), turns XML-RPC off, turns the file editor off and makes login errors vague. Switch a piece off in wp-config only when the client needs it, and write down why:

| Constant | Effect |
|---|---|
| `ASF_ALLOW_XMLRPC` true | Keep XML-RPC (Jetpack, the WordPress mobile app) |
| `ASF_AUTHOR_ARCHIVES` true | Keep `/author/…` pages |
| `ASF_SECURITY_HEADERS` false | Don't send the headers (the host's edge already does) |
| `ASF_HSTS` false | No Strict-Transport-Security |
| `ASF_CSP_REPORT_ONLY` / `ASF_CSP` | A Content-Security-Policy written for this site's sources: report-only first, then enforced |
| `DISALLOW_FILE_EDIT` false | Allow the theme/plugin file editor |

The host handles the rest. Ask them for: HTTP→HTTPS as a 301, gzip or Brotli, long cache lifetimes on static files, no directory listing, no server version headers, daily backups kept 30 days, and `readme.html` removed (or blocked).

## 3. Checks before go-live
Run from the project root (`/asf run` does this at stage 4):

```bash
python3 docs/framework/qa/launch.py https://staging.<domain> --env staging
```

```bash
python3 docs/framework/qa/launch.py https://staging.<domain> --env staging --only lighthouse
```

- [ ] `launch.py`: zero errors in security, performance, accessibility and launch settings
- [ ] Lighthouse mobile ≥ 90 on home and two inner pages (the second command; staging must be public, or run Lighthouse in Chrome DevTools)
- [ ] `contrast.js` clean in each colour context; keyboard-only pass through the menu and the form
- [ ] No `[CONFIRM]` chips left (`lint_content.py content --strict`)
- [ ] Every old URL in the redirect map returns 301 (spot-check 10)
- [ ] Legal and compliance pages the client needs resolve (privacy policy at least; any regulated or carrier-required pages)
- [ ] A test enquiry end to end: thank-you page, lead in WordPress, email in the inbox (not spam)
- [ ] Rich Results Test on home, one service page and one case study
- [ ] Responsive at 375, 768, 1440 and 1920
- [ ] Every admin: a personal login (no `admin`), a strong password, two-factor authentication
- [ ] Uptime monitoring on the production URL, alerting a named person

## 4. Go-live
1. Back up production. Switch the theme, activate the plugin, import content (same as staging).
2. Untick **Discourage search engines**. Flush permalinks (Settings → Permalinks → Save).
3. Search-replace the staging address in the database if content was copied (`wp search-replace`), then clear caches.
4. Record it: `bin/asf set deploy.production_url https://…`, then `python3 docs/framework/qa/launch.py https://<domain> --env production`. It fails if the site is still noindexed, links to staging or has no privacy link.
5. Search Console and Bing Webmaster Tools: submit the sitemap and request indexing for the home page and the main service pages.
6. Watch the 404 log for a week and add redirects for anything missed.

## 5. After launch
- Weekly: `/asf report` (leads, traffic, search, AI citations, and a rescan of the live site that lists anything new).
- Monthly: plugin and core updates on staging first, then production; one improvement proposal.
- Quarterly: review admin accounts and Application Passwords, delete unused plugins, test a backup restore.
