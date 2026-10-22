# Uptick writing guide

Every explainer answers three questions for someone who just saw a topic trending:
**What happened? Why is everyone talking about it? What happens next?**

## Voice

- Plain, clear, neutral. Short sentences. Explain it the way a well-informed friend would.
- No hype or clickbait ("you won't believe", "shocking", "everything you need to know").
- American English and AP style: "Oct. 16", "Sept. 30, 2027", "3.7%", "$4.33 a gallon", "12:20 a.m. ET".
- Never write as if you witnessed something. Attribute: "according to", "X said", "Reuters reports".

## Shape of an explainer (600 to 1,000 words)

```
## What happened            the news in 2-3 short paragraphs, most important fact first
## <context sections>       pick what fits: Why it matters / The backstory / How we got here /
                            The numbers (use a table for 4+ figures) / Who says what
## What happens next        or "What to watch"
## Quick answers            2-3 H3 questions people actually search, each answered in 1-3 sentences
```

Add something the sources don't spell out: a timeline, a comparison, simple arithmetic
("about $67 more a month"), or a plain explanation of a technical term. That's the value.

## Sports roundup shape (500 to 1,200 words)

Daily roundups (`AUTOPILOT.md` step 6b) cover every final game in one league on one date. Same voice,
sourcing and originality rules as explainers.

```
## <League> scores for <Mon. D>     the 1-2 results that mattered most, in 2 short paragraphs
## All final scores                 a table of every game: winner, score, loser, one-line note
                                    (top scorer, streak, overtime); combined posts use one table per league
## <2-3 short game sections>        the biggest games: how it was decided and why it matters, 80-150 words each
## What it means                    standings, streaks, playoff or table picture, with simple arithmetic
                                    ("three games back with 10 to play"); this is the added value
## What's next                      the next day's notable games with times in ET
```

- **Title:** `"NBA Scores, Oct. 21: <Headline Result in a Few Words>"`, the league and date first,
  then the headline result, 45-65 characters.
- **Slug:** `<league>-scores-<mon>-<d>-<yyyy>`, like `nba-scores-oct-21-2026`. The combined post uses
  `sports-scores-<mon>-<d>-<yyyy>-other-results`.
- **Description:** name the league, the date and the top results, 120-160 characters.
- Keep game notes factual. No odds, spreads, picks, fantasy advice or injury speculation.

## Front matter template

Copy this to `content/posts/YYYY-MM-DD-<slug>.md` (date = today in UTC):

```yaml
---
title: "Keyword First: The Specific News in 45-65 Characters"
slug: keyword-first-short-slug
description: "120-160 characters. Says what happened and what the reader gets. Includes the searched keyword."
dek: "One or two sentences that add the 'so what'. Don't repeat the description."
category: World          # World, US, Politics, Business, Tech, Sports, Health, Entertainment, Science or Culture
tags: [3-6, specific, tags]
published: 2026-10-16T13:05:00Z
updated: 2026-10-16T13:05:00Z
trend_score: 75          # 0-100 from the autopilot scoring (higher = leads the homepage)
signal: "Google Trends, U.S."   # only if it really appeared there; otherwise delete this line
why_trending: "One sentence: the event that made it trend."
key_points:
  - "3-4 complete facts, each with a number, date or name."
  - "..."
  - "..."
sources:
  - title: "Exact headline of the source"
    publisher: Reuters
    url: "https://..."
    date: 2026-10-16
---
```

## Headlines, descriptions, slugs (SEO)

- **Title:** lead with the words people type: "DV Lottery 2027: ...", "TSMC Earnings: ...", "September CPI: ...".
  45-65 characters, specific, with the key fact or number. No question titles unless that's how people search.
- **Description:** 120-160 characters, includes the keyword, says what the reader will learn.
- **Slug:** 3-7 lowercase words with hyphens, keyword first. Add the month/year only when needed to be unique.
- Put the keyword in the first paragraph and in at least one H2. Never stuff keywords.
- **Internal links:** when an older Uptick explainer is related, link it once with a root-relative link like
  `[our explainer on the Strait of Hormuz](/strait-of-hormuz-ship-attacks-explained/)`.

## Sourcing

- At least **3 sources**, from at least **2 different publishers**. Prefer wire services (AP, Reuters, AFP),
  major outlets, and primary sources: agency releases, court documents, company filings, official data.
- Every fact in the post must be in your research notes from this run. Never fill gaps from memory about
  current events. Stable background (geography, history, how something works) is fine.
- Link sources inline at first use and list every source you relied on in `sources:`.
- If only one outlet reports a claim, say so ("according to The Guardian") or leave it out.

## Originality (non-negotiable)

- Write from your notes, not from an article on screen. Your own structure, order and sentences.
- Never mirror another article's headings or sequence, and never "spin" (reword sentence by sentence).
- Quotes are rare: under 15 words, at most one per source, only when the exact wording matters,
  in quotation marks with attribution.
- Run `python3 tools/originality.py <post> work/research/<slug>.txt` and rewrite anything it flags.
- Images: never use outside photos. The build draws original artwork for every post.

## Sensitive topics

- **Deaths, disasters, attacks:** facts only, respectful, no graphic detail, no speculation about causes or
  motives. Don't name victims unless officials have released names and major outlets report them.
  Never name minors.
- **Crime and courts:** "accused", "charged", "alleged" until there's a conviction. Note when someone denies it.
- **Health:** cite official health agencies and end with:
  `*This article is general information, not medical advice. Talk to a health care provider about your situation.*`
- **Money and law:** facts and official guidance, no personal advice.
- **Politics:** neutral. Lay out each side's position fairly, attributed. No opinions.
- **Real people:** no invented quotes, no gossip about private lives, nothing about private individuals.
- **Never publish:** sexual content, hate or harassment, rumors, betting picks, or instructions that could
  help someone cause harm.
- **Ad-safe writing (AdSense):** no gore or graphic descriptions of violence, injury or death; no promoting
  weapons, drugs, tobacco, alcohol sales, gambling or supplements (explaining news about them is fine); no
  health claims that go against scientific consensus; no claims that undermine elections or deny that a
  tragedy happened; never mention ads, never ask readers to click, support or visit anything. Full rules are
  in `ADSENSE_POLICY.md`.

## Updating instead of duplicating

When a story already has an Uptick post from the past 14 days and something important changes, update that post:
edit the facts, add the new sources, keep the slug, and set `updated:` to now. If the news changes the headline,
change the `title`. Add a dated note to `corrections:` only for errors, not for normal news updates.
