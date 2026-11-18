# 02 Information architecture

*Last updated [date]*

## 1. Sitemap
| URL | Page | Recipe | ICP segment | Primary query | Sections |
|---|---|---|---|---|---|
| / | Home | home | all | [brand + category] | 8 |
| /services/ | Services hub | — | all | | |
| /services/[x]/ | [Service] | service | | | ≤ 7 |
| /industries/[x]/ | [Industry] | industry | | | ≤ 6 |
| /work/ | Case studies | archive | | | |
| /about/ | About | about | | | ≤ 6 |
| /approach/ | Approach | approach | | | 4 |
| /start/ | Ways to start | start | | | 4 |
| /contact/ | Contact | contact | | | 3 |
| /thank-you/ | Thank you (noindex) | thank-you | | | 1 |

## 2. One idea, one home
Every idea that could appear on more than one page, and the single page that owns it. Every other page links to it.

| Idea | Home page | Other pages do… |
|---|---|---|
| Process / how we work | /approach/ | Home: 4 one-line steps + link. Others: link only. |
| Pricing and offers | /start/ | Service pages: one "Starting at" fact + link |
| Team and people | /about/ | Home: faces strip. Contact: who answers. |
| Testimonial: [name] | [one page] | — |

## 3. Navigation
- **Header:** [items] + primary CTA "[label]"
- **Mega menu:** [columns], featured case: [case]
- **Footer:** [columns]

All of it lives in `inc/navigation.php` (theme). It's one PHP array.

## 4. Redirect map (old → new, 301)
| Old URL | New URL | Reason |
|---|---|---|
| | | |

It lives in the plugin's `inc/redirects.php`: exact rows in `hm_redirect_map()`, 410s in `hm_gone_paths()`. When hundreds of thin URLs share one new home (old archives, custom post types, winner or gallery stubs), write one row per prefix (`/press-release/{slug}/ → /news/`); they go in `hm_redirect_prefixes()`, and prefixes with no new home in `hm_gone_prefixes()`. Rules only fire on a 404, so they never shadow a real page.

## 5. Content types
- **Pages:** `content/pages/*.html`
- **Case studies** (CPT `case_study`, with service and industry taxonomies): `content/work/*.html`
- **Posts:** `content/posts/posts.json`
