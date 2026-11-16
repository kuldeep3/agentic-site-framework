# AI-search (AEO) and SEO checklist

Buyers now ask ChatGPT, Perplexity, Gemini and Google AI Overviews, "who's a good agency for X?". These engines cite sources that are **consistent, specific and easy to quote**. Everything below ships in the starter; this list is how you check it.

## 1. One entity, described once
- `inc/entity.php` (the plugin's facts file) holds the name, legal name, alternate names, tagline, description, contacts, founders, socials, `knows_about`, area served and plain-language facts.
- Organization schema, llms.txt, the footer and the About page all read from it. **Change a fact once.**
- The description is 1–2 sentences an engine can quote verbatim: category + defining difference + proof.

## 2. Answer-first content
- Every service and industry page opens with an `hm-answer` paragraph (40–60 words: what it is, who it's for, what changes). Its first sentence contains the page's primary query.
- About page: a factual "About us" block (who, where, since when, what, for whom).
- FAQs are real buyer questions in the buyer's words. Each answer's first sentence stands on its own.

## 3. Structured data (generated, `inc/schema.php`)
- Organization (+ logo, sameAs, founders, knowsAbout, areaServed), WebSite, WebPage, BreadcrumbList
- Service on service pages
- FAQPage, generated automatically from any `hm-faq` details block
- Article on posts and case studies
- Validate with Google's Rich Results Test before launch.

## 4. Crawl access
- `/llms.txt`: generated live, listing entity facts, key pages with one-line descriptions, and case studies.
- `robots.txt`: allows the AI crawlers by name (GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-SearchBot, PerplexityBot, Google-Extended, Applebot-Extended, Bingbot) and disallows `/wp-admin/`. Letting AI crawlers in is a client decision; record it in `decisions.md`. Leads are private posts, so they're never public URLs.
- XML sitemap (WordPress core, or the SEO plugin if one is active).

## 5. Classic SEO
- One H1 per page. SEO title ≤ 60 characters, meta description ≤ 155 and written as an answer.
- Canonical URLs. A 301 map from every old URL (from the Stage 1 inventory). No 404 guessing, which hijacks unknown URLs to the wrong page.
- Internal links: every service page links to its case studies, the next service in the journey, and /start/.
- Images: descriptive alt text, served at the right size, lazy-loaded below the fold.
- If Rank Math or Yoast is active, the plugin's SEO output steps aside so there's never a duplicate title or meta tag.

## 6. Tracking prompts (Stage 5)
Pick 5 prompts the ICP would ask an AI assistant ("best WooCommerce agency for subscription brands", "who can fix a slow WooCommerce store"). Record weekly whether the client is cited, and by which engine. That's the AEO line in the weekly report.
