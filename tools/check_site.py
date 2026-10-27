#!/usr/bin/env python3
"""Check the built site before it goes live.

  python3 tools/check_site.py            checks docs/
  python3 tools/check_site.py DIR        checks another build folder

Errors (exit code 1): a page missing its title, description, canonical link,
share image or single <h1>; structured data that isn't valid JSON; an internal
link or image that points at a missing file; a broken sitemap or feed.
Warnings: titles or descriptions outside the lengths search results display,
and duplicate titles or descriptions.

AdSense compliance (see ADSENSE_POLICY.md): with `adsense_client` set in site.yaml,
missing trust pages, a missing contact address, a github.io address, a missing
ads.txt, unlabeled ad slots, or click-begging wording are errors. Thin content
(few posts, few sources, short posts) is always reported as a warning.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

import yaml

ROOT = Path(__file__).resolve().parent.parent


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.in_title = "", False
        self.meta, self.links, self.refs, self.h1 = {}, [], [], 0
        self.jsonld, self.in_jsonld, self.buf = [], False, []
        self.imgs_without_alt = 0
        self.lang = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            if a.get("rel") == "canonical":
                self.meta["canonical"] = a.get("href", "")
            elif a.get("href"):
                self.refs.append(a["href"])
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag in ("img", "script") and a.get("src"):
            self.refs.append(a["src"])
            if tag == "img" and "alt" not in a:
                self.imgs_without_alt += 1
        elif tag == "h1":
            self.h1 += 1
        if tag == "script" and a.get("type") == "application/ld+json":
            self.in_jsonld, self.buf = True, []

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.in_jsonld:
            self.jsonld.append("".join(self.buf))
            self.in_jsonld = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_jsonld:
            self.buf.append(data)


def resolve(base_dir: Path, site: Path, href: str):
    parts = urlsplit(href)
    if parts.scheme or href.startswith(("//", "#", "mailto:", "tel:")):
        return None
    path = unquote(parts.path)
    if not path:
        return None
    target = (site / path.lstrip("/")) if path.startswith("/") else (base_dir / path)
    target = target.resolve()
    if path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target


# ---------------------------------------------------------------- AdSense compliance

REQUIRED_PAGES = ["about", "contact", "privacy", "terms", "editorial-standards"]
CLICK_BEGGING = [
    "click our ads", "click the ads", "click on the ads", "click an ad", "click the ad ", "support us by clicking",
    "visit these links", "visit our sponsors", "click here to help", "help us by clicking",
]
MIN_POSTS, MIN_SOURCES, MIN_WORDS = 30, 3, 500


def front_matter(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    _, fm, body = text.split("---", 2)
    return yaml.safe_load(fm) or {}, body


def adsense_checks(site: Path, errors: list, warns: list):
    cfg = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8")) or {}
    ads_on = bool(cfg.get("adsense_client"))
    report = errors if ads_on else warns
    prefix = "AdSense" if ads_on else "before applying to AdSense"

    for slug in REQUIRED_PAGES:
        if not (site / slug / "index.html").exists():
            report.append(f"{prefix}: required page /{slug}/ is missing")
    if not str(cfg.get("contact_email") or "").strip():
        report.append(f"{prefix}: contact_email is empty in site.yaml, so the Contact page has no way to reach you")
    if not str(cfg.get("publisher_name") or "").strip():
        warns.append("site.yaml publisher_name is empty; say who runs the site (a person or business name)")
    host = urlsplit(str(cfg.get("base_url", ""))).netloc
    if host.endswith("github.io"):
        report.append(f"{prefix}: base_url is a github.io address; use your own domain (ads.txt must sit at the domain root)")
    if not str(cfg.get("custom_domain") or "").strip() and not host.endswith("github.io"):
        warns.append("custom_domain is empty; GitHub Pages needs it to keep a CNAME for your own domain")
    if ads_on and not (site / "ads.txt").exists():
        errors.append("AdSense: ads.txt was not written")
    if ads_on:
        home = site / "index.html"
        if home.exists() and "pagead2.googlesyndication.com" not in home.read_text(encoding="utf-8"):
            errors.append("AdSense: the homepage is missing the AdSense code that site review looks for")
        for rel in ("404.html", "search/index.html", "contact/index.html", "privacy/index.html", "terms/index.html"):
            f = site / rel
            if f.exists() and "pagead2.googlesyndication.com" in f.read_text(encoding="utf-8"):
                errors.append(f"AdSense: {rel} has ad code, but it's a screen without publisher content")

    # content depth (advisory, always a warning)
    posts = sorted((ROOT / "content" / "posts").glob("*.md"))
    if len(posts) < MIN_POSTS:
        warns.append(f"only {len(posts)} explainers published; aim for {MIN_POSTS}+ before applying (rule of thumb, not an official number)")
    for f in posts:
        meta, body = front_matter(f)
        words = len(re.findall(r"\b\w+\b", body))
        if len(meta.get("sources") or []) < MIN_SOURCES:
            warns.append(f"{f.name}: fewer than {MIN_SOURCES} sources")
        if words < MIN_WORDS:
            warns.append(f"{f.name}: only {words} words (aim for {MIN_WORDS}+)")

    # wording that asks people to click ads, in any content file
    for f in sorted((ROOT / "content").rglob("*.md")):
        low = f.read_text(encoding="utf-8").lower()
        for phrase in CLICK_BEGGING:
            if phrase in low:
                errors.append(f"{f.relative_to(ROOT).as_posix()}: wording that urges ad clicks ('{phrase.strip()}') breaks AdSense policy")

    # every ad unit must be labeled and sit inside an .adslot block
    for f in sorted(site.rglob("*.html")):
        html = f.read_text(encoding="utf-8")
        units = len(re.findall(r"<ins[^>]*adsbygoogle", html))
        if not units:
            continue
        rel = f.relative_to(site).as_posix()
        slots = re.findall(r'<aside class="adslot"[^>]*>(.*?)</aside>', html, flags=re.S)
        labeled = [x for x in slots if 'class="adslot__label">Advertisement<' in x and "adsbygoogle" in x]
        if len(labeled) != units:
            errors.append(f"{rel}: {units} ad unit(s) but {len(labeled)} labeled 'Advertisement' slot(s)")
        if rel.startswith(("search/", "category/", "tag/", "page/")) or rel in ("index.html", "404.html"):
            errors.append(f"{rel}: ads on a listing, search or error page break the 'no ads without publisher content' rule")


def main():
    site = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "docs"
    errors, warns = [], []
    titles, descs = defaultdict(list), defaultdict(list)
    pages = sorted(site.rglob("*.html"))
    if not pages:
        sys.exit(f"check: no HTML in {site}; run tools/build.py first")
    for f in pages:
        rel = f.relative_to(site).as_posix()
        p = Page()
        p.feed(f.read_text(encoding="utf-8"))
        robots = p.meta.get("robots", "")
        indexable = "noindex" not in robots
        if not p.title.strip():
            errors.append(f"{rel}: missing <title>")
        if not p.meta.get("description"):
            errors.append(f"{rel}: missing meta description")
        if not p.meta.get("canonical", "").startswith("http"):
            errors.append(f"{rel}: canonical link missing or not absolute")
        if not p.meta.get("og:image", "").startswith("http"):
            errors.append(f"{rel}: og:image missing or not absolute")
        if p.h1 != 1:
            errors.append(f"{rel}: has {p.h1} <h1> elements (needs exactly 1)")
        if p.imgs_without_alt:
            errors.append(f"{rel}: {p.imgs_without_alt} image(s) without alt text")
        for block in p.jsonld:
            try:
                json.loads(block)
            except ValueError as e:
                errors.append(f"{rel}: structured data is not valid JSON ({e})")
        if indexable and rel != "404.html":
            t, d = p.title.strip(), p.meta.get("description", "")
            if len(t) > 70:
                warns.append(f"{rel}: title is {len(t)} characters")
            if not 70 <= len(d) <= 170:
                warns.append(f"{rel}: description is {len(d)} characters")
            titles[t].append(rel)
            descs[d].append(rel)
        if rel == "404.html":
            continue
        for href in p.links + p.refs:
            target = resolve(f.parent, site, href)
            if target and not target.exists():
                errors.append(f"{rel}: broken link {href}")
    for t, where in titles.items():
        if len(where) > 1:
            warns.append(f"duplicate title on {', '.join(where)}")
    for d, where in descs.items():
        if len(where) > 1:
            warns.append(f"duplicate description on {', '.join(where)}")
    for name in ("sitemap.xml", "news-sitemap.xml", "feed.xml"):
        path = site / name
        if not path.exists():
            errors.append(f"{name} is missing")
            continue
        try:
            ET.parse(path)
        except ET.ParseError as e:
            errors.append(f"{name} is not valid XML ({e})")
    if not (site / "robots.txt").exists():
        errors.append("robots.txt is missing")
    adsense_checks(site, errors, warns)
    for w in warns:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"Checked {len(pages)} pages: {len(errors)} errors, {len(warns)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
