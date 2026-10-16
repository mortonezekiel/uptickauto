# Uptick

A blog that explains what the world is searching for. A scheduled Claude task finds trending topics,
researches each one across several sources, writes an original explainer, checks it, and publishes it.

## How it fits together

| Folder or file | What it is |
|---|---|
| `content/posts/` | One Markdown file per explainer (front matter + body) |
| `content/pages/` | About, Editorial standards, Privacy |
| `site.yaml` | Site name, live address, topics, optional Search Console / Analytics / AdSense codes |
| `theme/` | Page templates, stylesheet, script, fonts for the artwork |
| `tools/build.py` | Builds the site into `docs/` |
| `tools/check_site.py` | Checks titles, descriptions, links, structured data, sitemap and feed |
| `tools/originality.py` | Copy check: flags any 8+ word run shared with the research notes |
| `tools/art.py` | Draws the original share card and artwork for each post |
| `media/` | Generated post artwork (kept so it isn't redrawn every build) |
| `docs/` | The built website that GitHub Pages serves |
| `AUTOPILOT.md` | The step-by-step instructions each scheduled run follows |
| `WRITING_GUIDE.md` | Voice, structure, sourcing, originality and SEO rules |

## Build it yourself

```
python3 tools/build.py        # writes docs/
python3 tools/check_site.py   # should report 0 errors
```

## Going live on GitHub Pages

1. In `site.yaml`, set `base_url` to the live address (and `custom_domain` if you use your own domain).
2. Build, commit and push.
3. In the repository's **Settings > Pages**, set the source to **Deploy from a branch**, branch `main`,
   folder `/docs`.

## Getting found on Google

1. Add the site in Google Search Console (search.google.com/search-console).
2. Choose the **HTML tag** verification method, copy the code inside `content="..."` into
   `google_site_verification` in `site.yaml`, rebuild and push, then press Verify.
3. In Search Console, open **Sitemaps** and submit `sitemap.xml` and `news-sitemap.xml`.
4. Optional: do the same in Bing Webmaster Tools (it can import from Search Console).

## Changing things

- **Posting frequency:** edit the scheduled task's schedule, or the "Pick the top 2" line in `AUTOPILOT.md`.
- **Remove a post:** delete its file in `content/posts/` (and its folder in `media/`), rebuild, push.
- **Rename the blog:** change `name` in `site.yaml`; the artwork redraws itself on the next build.
- **Ads:** put your AdSense publisher ID in `adsense_client`. AdSense requires a custom domain.

The fonts in `theme/fonts/` (Schibsted Grotesk, DM Mono) are used under the SIL Open Font License; the
license files sit next to them.
