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
3. **Daily cap.** Count what's already published today (UTC), explainers and sports roundups separately:
   `grep -L "^format: roundup" $(grep -l "^published: $(date -u +%F)" content/posts/*.md) 2>/dev/null | wc -l`  (explainers)
   `grep -l "^format: roundup" $(grep -l "^published: $(date -u +%F)" content/posts/*.md) 2>/dev/null | wc -l`  (roundups)
   The site publishes at most **6 new explainers per day**, spread over the day's runs. If today's count plus
   what you plan would pass 6, publish fewer or nothing. Updates to existing posts don't count toward the cap.
   Daily sports roundups (step 6b) have their own cap of **8 per day** and don't count toward the 6.
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

## 6b. Daily sports roundups

Every run also covers each completed game in the leagues below with **one roundup per league per game
date**, not one post per game. A separate post for every game would be the thin, mass-produced content that
`ADSENSE_POLICY.md` section 5 warns against. Roundups follow the "Sports roundup" shape in `WRITING_GUIDE.md`.

**Leagues** (only when in season and games were played):
- U.S. majors: NFL, NBA, MLB (including the postseason), NHL.
- Soccer: Premier League, Champions League, Europa League, La Liga, Serie A, Bundesliga, Ligue 1, MLS.
- Cricket: men's international matches (Tests, ODIs, T20Is) between full-member nations.
- College and others: FBS college football (Top 25 games plus every other FBS final in the table), men's
  college basketball (Top 25 games plus every other Division I final in the table, once the season starts),
  WTA and ATP tour-level main-draw singles results, Formula 1 race results.

**Which games each run covers:**
1. Find the game dates whose games are **all final** and that have no roundup yet. Check with
   `grep -l "^format: roundup" content/posts/*.md | xargs grep -h "^roundup_league:\|^game_date:" | paste - -`.
   The morning run (about 9 a.m. ET) usually covers the previous day's North American games plus anything
   that finished overnight; the evening run (about 6 p.m. ET) usually covers European soccer, cricket and
   tennis that finished earlier that day. Never publish a roundup with a game still in progress or postponed
   without saying so.
2. Use the date the games were played in the league's home time zone (ET for North American leagues), not
   the UTC date.
3. A league with **3 or more** games on that date gets its own roundup. Leagues with 1 or 2 games, tennis
   and F1 go into one combined "Sports scores, <date>: other results" roundup for that date.
4. If more than 8 roundups would publish today, keep the highest-interest leagues and fold the rest into
   the combined roundup. Never skip a league's results just to stay under the cap.
5. If a game already has its own Uptick explainer (for example a trending upset), still list its score in
   the roundup and link the explainer instead of retelling it.

**Research:** at least 3 sources from at least 2 publishers per roundup. Use the league's official
scoreboard or results page as the primary source (NBA.com, MLB.com, NHL.com, NFL.com, Premier League,
UEFA, ESPNcricinfo, WTA/ATP, Formula1.com, NCAA.com), plus wire or major-outlet recaps (AP, Reuters, ESPN,
BBC Sport, Sky Sports). Every final score must appear in at least one source you fetched this run, and the
games you write up in detail need two. Save the notes to `work/research/<slug>.txt` as in step 4.

**Front matter for roundups:** use the normal template with `category: Sports` and add three extra lines:
`format: roundup`, `roundup_league: NBA` (or `Other` for the combined post) and `game_date: 2026-10-21`.
Set `trend_score` to **50** so trending explainers keep the top of the homepage, and leave out `signal:`
unless the roundup's main game really appeared in a trend feed.

**Never** include betting odds, point spreads, picks, fantasy advice or injury speculation. Report only
injuries that a team or league has announced.

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
and the strongest topics you skipped and why. List the sports roundups separately (league, game date, link),
and say which completed game dates are still waiting for a roundup and why. If you published nothing, say why. Mention any
`check_site.py` warning that still stands, and if the site is still short of 30 explainers, say how many
remain before the AdSense application.

---

## The scheduled task's prompt

The scheduled task sends this prompt each time (OWNER/REPO is filled in when the task is created):

> Run the Uptick autopilot. Attach the GitHub repository OWNER/REPO with push access, clone it, read
> AUTOPILOT.md and WRITING_GUIDE.md, and follow AUTOPILOT.md exactly, including the daily sports roundups
> in step 6b. Trend feeds to check:
> https://trends.google.com/trending/rss?geo=US https://trends.google.com/trending/rss?geo=GB
> https://trends.google.com/trending/rss?geo=IN https://trends.google.com/trending/rss?geo=CA
> https://trends.google.com/trending/rss?geo=AU
