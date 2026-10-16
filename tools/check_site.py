#!/usr/bin/env python3
"""Check the built site before it goes live.

  python3 tools/check_site.py            checks docs/
  python3 tools/check_site.py DIR        checks another build folder

Errors (exit code 1): a page missing its title, description, canonical link,
share image or single <h1>; structured data that isn't valid JSON; an internal
link or image that points at a missing file; a broken sitemap or feed.
Warnings: titles or descriptions outside the lengths search results display,
and duplicate titles or descriptions.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

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
    for w in warns:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"Checked {len(pages)} pages: {len(errors)} errors, {len(warns)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
