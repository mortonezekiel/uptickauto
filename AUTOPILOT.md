# Uptick autopilot runbook

This file is what each scheduled run follows. The scheduled task attaches this repository,
clones it, and then works through every step below. Read `WRITING_GUIDE.md` and `ADSENSE_POLICY.md`
before writing. The site is working toward Google AdSense approval, so every post must stay inside those policies.

**The goal of every run:** publish a small number of genuinely useful explainers about what the
world is searching for right now. Quality beats volume. Publishing nothing is better than
publishing something thin, unverified or copied.

## 0. The owner reviews every post before it goes live (since 2026-10-28)

Google's AdSense rules say: "Don't place ads on automatically generated content without manual review or
curation." So a run never publishes anything by itself:

- Every new explainer is saved as a **draft**: put `draft: true` in its front matter. Drafts are committed and
  pushed like any post, but the build leaves them off the site.
- **Never add `reviewed:` yourself.** Only the owner's approval in a conversation adds it (see below). Ads
  appear only on the homepage and on explainers that have `reviewed:`.
- If **6 or more drafts** are already waiting (`grep -l "^draft: true" content/posts/*.md | wc -l`), write no
  new ones this run; remind the owner in the report instead.
- Updating a live post (step 6): make the edit, then **delete its `reviewed:` line** so ads come off until the
  owner reads it again, and list it in the report.

### Approving drafts (only when the owner says so in a conversation)

The owner replies with something like "approve all", "approve 1 and 3", "skip 2" or a change request.

1. Each approved draft: delete the `draft: true` line, add `reviewed: YYYY-MM-DD` (today, New York time), and
   set `published:` and `updated:` to the current UTC time.
2. Each skipped draft: delete its file in `content/posts/` and its folder in `media/` if there is one.
3. A change request: make the change, show the owner, and publish only once they approve.
4. Live posts the owner says they've read: add `reviewed: YYYY-MM-DD` with the day they read them.
5. Run `python3 tools/build.py` and `python3 tools/check_site.py` (0 errors), then commit
   "Publish (owner-approved): <titles>" and push.

## 1. Get ready

1. Work from the repository root. Run `git pull --rebase` first.
2. The site needs only Python with `markdown`, `jinja2`, `PyYAML` and `Pillow`, which come with the
   workspace. Don't try to install anything.
3. **Daily cap.** Count what's already published today (UTC), explainers and sports roundups separately:
   `grep -L "^format: roundup" $(grep -l "^published: $(date -u +%F)" content/posts/*.md) 2>/dev/null | wc -l`  (explainers)
   `grep -l "^format: roundup" $(grep -l "^published: $(date -u +%F)" content/posts/*.md) 2>/dev/null | wc -l`  (roundups)
   **While Google AdSense reviews the site (since 2026-10-27), runs write at most 3 new explainer drafts per
   day**, spread over the day's runs. If today's count plus what you plan would pass 3, publish fewer or nothing.
   Updates to existing posts don't count toward the cap. Daily sports roundups (step 6b) are **paused**: publish
   none until the owner turns them back on.
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
Add `draft: true` so it waits for the owner's review (step 0).

## 6. Update instead of duplicating

If a topic already has a post from the last 14 days and there's a real development, edit that post:
update the facts, add the new sources, keep the slug, set `updated:` to now. An update counts toward the
run's limit.
Then delete its `reviewed:` line so ads come off until the owner reads it again (step 0).

## 6b. Daily sports roundups

**Paused since 2026-10-27 while Google AdSense reviews the site. Don't publish new roundups or add scores to
existing ones until the owner turns this step back on.** The existing roundups are hidden from the site by
`hide_roundups: true` in `site.yaml` (nothing is deleted). The rules below are kept for when it resumes.

**Resuming, only when the owner says so.** The owner wants the site fully caught up on the day roundups return:

1. Set `hide_roundups: false` in `site.yaml` so the hidden roundups come back.
2. Backfill the same day, before anything new: publish a roundup for every league and game date missed during
   the pause, oldest first, following the rules below. Start each league the day after its last roundup:
   NBA, NHL and the combined "other results" after Oct. 26; NFL, Premier League and La Liga after Oct. 25;
   Bundesliga, Serie A, MLS and college football after Oct. 24; cricket after Oct. 27; Champions League after
   Oct. 21; Europa League after Oct. 22 (all 2026). Cover every final game through yesterday. The 8-a-day cap
   doesn't apply to the backfill; if one run can't finish it, the next runs that day continue until it's done.
3. Delete this paused note and the cap note in step 1, then carry on with the normal daily routine.

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
git commit -m "Drafts for owner review: <short titles>"
git push
```

If the push is rejected because the remote moved, run `git pull --rebase` and push again.
Never force-push.

## 9. Report

Finish with a short message for the owner. Number each new draft with its title and a review link,
`https://github.com/mortonezekiel/uptickauto/blob/main/content/posts/<file>.md`, and list any live post you
updated with its link on upticktrends.com. Then tell them how to answer: reply in Claude with "approve all",
"approve 1 and 3", "skip 2" or what to change. Mention any older drafts still waiting, the strongest topics you
skipped and why, and any `check_site.py` warning that still stands. If you wrote no drafts, say why.

---

## The scheduled task's prompt

The "Uptick autopilot" scheduled task runs at 8:59 a.m. and 5:59 p.m. New York time. Its prompt tells each run
to clone this repository, follow this file, write drafts only (step 0), and end with the review list (step 9).
