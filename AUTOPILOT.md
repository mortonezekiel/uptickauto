# Uptick autopilot runbook

This file is what each scheduled run follows. The scheduled task attaches this repository,
clones it, and then works through every step below. Read `WRITING_GUIDE.md` and `ADSENSE_POLICY.md`
before writing. The site is working toward Google AdSense approval, so every post must stay inside those policies.

**The goal of every run:** publish a small number of genuinely useful explainers about what the
world is searching for right now. Quality beats volume. Publishing nothing is better than
publishing something thin, unverified or copied.

## 1. Get ready

1. Work from the repository root. Run `git pull --rebase` first.
2. The site needs only Python with `markdown`, `jinja2`, `PyYAML` and `Pillow`, which come with the
   workspace. Don't try to install anything.
3. **Daily cap.** Count what's already published today (UTC):
   `grep -l "^published: $(date -u +%F)" content/posts/*.md | wc -l`
   The site publishes at most **6 new explainers per day**, spread over the day's runs. If today's count plus
   what you plan would pass 6, publish fewer or nothing. Updates to existing posts don't count toward the cap.
4. Check what's already covered in the last 14 days:
   `grep -h "^title:\|^published:" content/posts/*.md | paste - - | sort -k4 | tail -40`

## 2. Find what's trending

Use WebFetch and WebSearch (the shell can't reach most websites). Gather signals from:

- **Google Trends daily feeds** for several countries, listed in the task prompt
  (`https://trends.google.com/trending/rss?geo=US`, `GB`, `IN`, `CA`, `AU`). Ask WebFetch for every item
  with its approximate traffic and attached news headlines.
- **Top news:** WebSearch for today's date with words like "news", "breaking", "announces", "ruling".
- **Sports:** if the sports data tool is available, check scores for leagues in season.

Build a candidate list of 8 to 15 topics: topic, where it's trending, rough traffic, likely category.

## 3. Choose

Give each candidate a `trend_score` from 0 to 100:

- **Interest (up to 50):** traffic, number of countries or feeds where it appears, prominence in top news.
- **Explainability (up to 25):** is there real context to add (why, backstory, what's next)?
- **Verifiability (up to 25):** can you get 3+ solid sources right now?

Skip a topic when:
- it was covered in the last 7 days and nothing important changed (if something did change, update that
  post instead; see step 6);
- only one outlet is reporting it, or it's a rumor;
- it's a breaking tragedy less than about 6 hours old with conflicting reports;
- it's about a private individual, or gossip, or explicit, or a betting tip;
- it would need graphic detail, speculation about causes, or naming minors or private people to explain;
- it's too local or too small to matter to a wide audience.

Pick the **top 2** (a maximum of 3 if several are huge), but only topics with a `trend_score` of **60 or
more**. Some runs will honestly have only one strong topic, or none. That's fine.
Spread categories: usually no more than one post per category in a run, and skip a topic when a post on
the same story already went out earlier today unless something important changed.

## 4. Research each pick

1. Find at least 3 sources from at least 2 publishers (wires, major outlets, official documents).
2. WebFetch each one. Ask for the facts: who, what, when, where, numbers, what happens next, and any
   short quote that really matters.
3. Save everything you read, including search-result snippets, to `work/research/<slug>.txt`.
   (`work/` is never committed.)
4. If you can't get 3 sources, drop the topic and take the next one.

## 5. Write

Create `content/posts/YYYY-MM-DD-<slug>.md` using the template and rules in `WRITING_GUIDE.md`.
Set `published` and `updated` to the current UTC time, like `2026-10-16T13:05:00Z`. Every fact must be
in your research notes from this run.

## 6. Update instead of duplicating

If a topic already has a post from the last 14 days and there's a real development, edit that post:
update the facts, add the new sources, keep the slug, set `updated:` to now. An update counts toward the
run's limit.

## 7. Check (all must pass)

1. Copy check for every new or edited post:
   `python3 tools/originality.py content/posts/<file>.md work/research/<slug>.txt`
   If it fails, rewrite the flagged passages in your own words and run it again.
2. Fact check: reread each post against your notes. Every number, date, name and claim must match a source.
3. Build: `python3 tools/build.py` (fix anything it reports as an error; read the warnings).
4. Site check: `python3 tools/check_site.py` must report 0 errors. Read every warning; a new warning about
   sources, word count or wording caused by your post means fix the post.
5. AdSense gate: walk through section 7 of `ADSENSE_POLICY.md` for each new or edited post. If any item
   fails and can't be fixed in this run, don't publish that post.

## 8. Publish

```
git add -A
git commit -m "Publish: <short titles>"
git push
```

If the push is rejected because the remote moved, run `git pull --rebase` and push again.
Never force-push.

## 9. Report

Finish with a short summary for the owner: the titles you published or updated with their live links,
and the strongest topics you skipped and why. If you published nothing, say why. Mention any
`check_site.py` warning that still stands, and if the site is still short of 30 explainers, say how many
remain before the AdSense application.

---

## The scheduled task's prompt

The scheduled task sends this prompt each time (OWNER/REPO is filled in when the task is created):

> Run the Uptick autopilot. Attach the GitHub repository OWNER/REPO with push access, clone it, read
> AUTOPILOT.md and WRITING_GUIDE.md, and follow AUTOPILOT.md exactly. Trend feeds to check:
> https://trends.google.com/trending/rss?geo=US https://trends.google.com/trending/rss?geo=GB
> https://trends.google.com/trending/rss?geo=IN https://trends.google.com/trending/rss?geo=CA
> https://trends.google.com/trending/rss?geo=AU
