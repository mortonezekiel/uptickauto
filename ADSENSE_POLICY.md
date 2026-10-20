# AdSense compliance (Uptick)

Read this before every autopilot run and before every site change. It summarizes Google's AdSense Program
policies, Google Publisher Policies and Publisher Restrictions, plus Google Search's guidance on AI content,
as read on 2026-10-20. Google can change these at any time, so re-check the sources at the bottom when
something looks different. Where this file says "(not in the policy pages)", it is a practical rule of thumb,
not an official requirement.

## 1. What gets a site approved

- **Original, high-quality content you own.** AdSense eligibility asks for high-quality, original content that
  attracts an audience, and for the applicant to be 18 or older and able to access the site's HTML source.
- **Value added to anything built on other people's material.** Ads are not allowed on pages with copied or
  embedded content from others unless the page adds commentary, curation or other value.
- **Real content on every page that carries ads.** No ads on screens with little or no publisher content, on
  pages under construction, or on alert/navigation/utility pages.
- **Easy navigation.** Clear menus, working links, no dead ends, no links to content that doesn't exist.
- **A site you control.** (not in the policy pages) Use your own domain, not a free `github.io` address.
  `ads.txt` must sit at the domain root, which a project path on `github.io` cannot do.
- **Enough published work.** (not in the policy pages) Aim for 30 or more strong explainers, several weeks of
  history, and a clean `check_site.py` before applying. Thin or brand-new sites are the most common rejection.

## 2. Content that is never allowed

Illegal content; copyright infringement; hate, harassment or bullying (including denying that tragic events
happened); promoting violence, terrorism or self-harm; deceptive or misrepresentative content (hiding who
runs the site, false affiliation, "get rich quick" claims); harmful health claims that contradict scientific
consensus; claims that undermine elections or democratic participation; manipulated media about public
matters; enabling dishonest behavior (fake documents, hacking, spyware); sexually explicit content;
anything involving the sexual exploitation of children; adult themes in family-styled content.

**Uptick rules that follow:** never publish rumors, unattributed claims or speculation about causes of
tragedies; never name private individuals or minors; cite official health agencies and add the health
disclaimer; never invent quotes; never publish betting picks.

## 3. Content that gets few or no ads (restricted, not banned)

Sexual content; shocking or graphic content (gore, violence, heavy profanity); explosives; guns and gun
parts; other weapons; tobacco; recreational drugs; alcohol sales or irresponsible drinking; online
gambling; prescription drugs; unapproved supplements.

News explainers about wars, attacks, disasters and outbreaks are allowed, but write them factually, with
no graphic detail. Google may reduce ad risk around "sensitive events" and the Publisher Policies don't spell
out what that entails, so expect lower ad fill on breaking tragedies.

## 4. Behavior rules for the site and the ads

- **Never click your own ads** and never ask anyone to. Never pay for or trade clicks or views.
- **No wording that urges clicks** ("support us", "click here to help", "visit these links") and no arrows
  or graphics pointing at ads.
- **Label ads accurately**: "Advertisement" or "Sponsored links". Never "Top offers" or similar.
- **Ads must not look like content or navigation**, and content must not look like ads. Never put an ad in a
  menu, in the header, or where users expect a navigation link.
- **No ads in pop-ups, pop-unders, emails or floating boxes.** No interstitials that block reading.
- **No more ads than content** on any page. Ads must not cover content, and content must not cover ads.
- **No redirects, forced downloads, malware or changing browser settings.**
- **Don't imply Google endorses the site** or use Google logos or trademarks.
- **Paid or bought traffic** must be real people who can easily find what was promised: no click farms,
  autosurf, paid-to-click, unsolicited mass email.
- **Don't modify ad code** in a way that inflates performance.
- **Privacy and consent.** Visitors from the European Economic Area, the UK and Switzerland must give
  consent before cookies, local storage or personal data are used for ad personalization. Keep records of
  consent and let people withdraw it. Use Google's free "Privacy & messaging" consent tool in the AdSense
  dashboard (or another certified consent platform) once the account exists.

## 5. Google Search spam rules that matter for an automated blog

- **Scaled content abuse.** Publishing many pages mainly to rank, with little value for readers, is spam
  however it's made, including AI. Uptick's defense is a small number of well-researched explainers, each
  adding context the sources don't spell out. **Fewer, better posts. Never pad the volume.**
- **Scraping and "spinning".** Rewording other sites sentence by sentence is spam. Write from notes, in new
  structure.
- **Fabrication.** Fact-check everything, including titles, descriptions, structured data and image alt text.
- **Disclose how content is made.** Google recommends telling readers how automation was used. Uptick does
  this on every post and on the About and Editorial standards pages. Keep it.
- **No hidden text, cloaking, paid links without `rel="sponsored"`, or tools that promise something they
  don't deliver.**
- **Don't create extra sites to hide scale.**

## 6. What the build now enforces

`python3 tools/check_site.py` fails when `adsense_client` is set and any of these are missing: Contact,
Privacy, About, Terms and Editorial standards pages; a working contact address; `ads.txt`; an
"Advertisement" label on every ad slot; no ad slot in the header, nav or footer. It also warns when the
site has fewer than 30 explainers, when a post has fewer than 3 sources, is under 500 words, or when the
site address is still a `github.io` address.

## 7. Per-run gate (autopilot step 7)

Before publishing, each new or edited post must pass all of these:

1. 3 or more sources from 2 or more publishers, all listed in `sources:`.
2. Every number, date and name matches the saved research notes.
3. `originality.py` passes (no 8-word run copied from the notes).
4. No graphic detail, no speculation, no private individuals, no minors, no rumors.
5. Health posts cite an official agency and carry the medical disclaimer line.
6. Title, description, dek, key points and alt text are accurate and not clickbait.
7. 500 words or more, with at least one section that adds something the sources don't spell out.
8. Nothing in the post asks readers to click, support or visit anything, and nothing mentions ads.

If a post can't pass, publish nothing. A missed run is better than a risky post.

## 8. Sources

- AdSense Program policies: https://support.google.com/publisherpolicies/answer/48182
- Google Publisher Policies (content): https://support.google.com/publisherpolicies/answer/10502938
- Google Publisher Restrictions: https://support.google.com/publisherpolicies/answer/10437795
- AdSense eligibility: https://support.google.com/adsense/answer/9724
- EU user consent policy: https://www.google.com/about/company/user-consent-policy/
- Google Search spam policies: https://developers.google.com/search/docs/essentials/spam-policies
- Google Search guidance on generative AI content: https://developers.google.com/search/docs/fundamentals/using-gen-ai-content
