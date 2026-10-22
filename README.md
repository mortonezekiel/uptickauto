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
| `ADSENSE_POLICY.md` | AdSense and Google Search rules the site and every post must follow |
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
- **Ads:** see "Getting approved for AdSense" below.

## Live visitor count

The notice "2,970 people visited Uptick in the past hour" comes from a small counter in `counter/` that runs free on
Cloudflare Workers. It counts each person once per rolling hour, without cookies, and skips bots, so the number is real.

1. Deploy it with the button in `counter/README.md` (or open
   https://deploy.workers.cloudflare.com/?url=https://github.com/mortonezekiel/uptickauto/tree/main/counter).
2. Copy the address Cloudflare shows, like `https://uptick-visitor-counter.NAME.workers.dev`, into
   `visitor_counter_url` in `site.yaml`. Rebuild and push.
3. `visitor_counter_min` (default 25) hides the notice whenever fewer people than that visited in the past hour.
   Every visit is still counted. See the live number anytime at `<counter address>/count`.

## Getting approved for AdSense

Read `ADSENSE_POLICY.md` first. In order:

1. **Your own domain.** Buy one, set `base_url` and `custom_domain` in `site.yaml`, point the domain at GitHub
   Pages, and turn on **Enforce HTTPS** in Settings > Pages. `github.io` addresses can't serve `ads.txt` at the root.
2. **Say who runs the site.** Fill in `contact_email`, `publisher_name` and `publisher_location`.
3. **Grow the archive.** Aim for 30 or more explainers over several weeks, with `check_site.py` clean.
4. **Apply** at adsense.google.com with the final address. Don't put ad code anywhere before approval,
   except the connection snippet AdSense asks for. Put the publisher ID in `adsense_client` when told to.
5. **Turn on consent.** In AdSense, open Privacy & messaging and publish the European regulations message
   (EEA, UK, Switzerland) before ads go live.
6. **After approval,** set `adsense_slot_article` to an ad unit ID for one labeled in-article ad, or use Auto
   ads. Never click your own ads. Rebuild, run `check_site.py` and push.

The checker enforces the parts it can see: required pages, contact address, labeled ad slots, no ads on
listing pages, no click-begging wording and no `github.io` address once `adsense_client` is set.

The fonts in `theme/fonts/` (Schibsted Grotesk, DM Mono) are used under the SIL Open Font License; the
license files sit next to them.
