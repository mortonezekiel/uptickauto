#!/usr/bin/env python3
"""Build the Uptick site.

  python3 tools/build.py                   live site -> docs/
  python3 tools/build.py --preview DIR     preview copy (explicit index.html links, for previews)
  python3 tools/build.py --now 2026-10-16T05:00:00Z   build as if it were this time

Reads site.yaml, content/posts/*.md and content/pages/*.md; writes HTML pages,
sitemap.xml, news-sitemap.xml, feed.xml and robots.txt. Post images are drawn
once into media/<slug>/ and reused on later builds.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import sys
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape as xesc

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import art  # noqa: E402

try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("America/New_York")
except Exception:  # pragma: no cover
    LOCAL_TZ = dt.timezone(dt.timedelta(hours=-4), "ET")

UTC = dt.timezone.utc
RESERVED = {"assets", "media", "category", "tag", "page", "about", "editorial-standards", "privacy", "404", "feed.xml"}
FONTS_HREF = ("https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500"
              "&family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..600"
              "&family=Schibsted+Grotesk:wght@500..900&display=swap")
MONTHS = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WARNINGS: list[str] = []


def die(msg: str):
    sys.exit(f"build: {msg}")


def warn(msg: str):
    WARNINGS.append(msg)


def slugify(text: str, sep: str = "-") -> str:
    text = str(text).lower().replace("&", " and ").replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", sep, text).strip(sep)


# ---------------------------------------------------------------- dates

def to_utc(value, field: str, src: str) -> dt.datetime:
    if isinstance(value, dt.datetime):
        d = value
    elif isinstance(value, dt.date):
        d = dt.datetime(value.year, value.month, value.day, 12)
    elif isinstance(value, str):
        try:
            d = dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            die(f"{src}: '{field}' must look like 2026-10-16T04:20:00Z")
    else:
        die(f"{src}: '{field}' is missing or is not a date")
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    return d.astimezone(UTC)


def local(d):
    if isinstance(d, dt.datetime):
        return d.astimezone(LOCAL_TZ)
    return d


def ap_date(d) -> str:
    d = local(d)
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def ap_time(d) -> str:
    d = local(d)
    hour = d.hour % 12 or 12
    ampm = "a.m." if d.hour < 12 else "p.m."
    return f"{hour}:{d.minute:02d} {ampm} ET"


def iso(d) -> str:
    if isinstance(d, dt.datetime):
        return d.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return d.isoformat()


# ---------------------------------------------------------------- content

def read_doc(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        die(f"{path.name}: needs front matter between --- lines")
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        die(f"{path.name}: front matter is not valid YAML ({e})")
    return meta, m.group(2)


def render_markdown(body: str):
    md = markdown.Markdown(
        extensions=["extra", "sane_lists", "smarty", "toc"],
        extension_configs={"toc": {"slugify": slugify}},
        output_format="html",
    )
    html = md.convert(body)
    toc = [(t["id"], t["name"]) for t in md.toc_tokens if t.get("level") == 2]
    html = html.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    return html, toc


def smart(text: str) -> str:
    """Curly quotes and apostrophes for text that skips Markdown (front matter)."""
    text = re.sub(r'(^|[\s(\[{\u2014-])"', "\\1\u201c", str(text))
    text = text.replace('"', "\u201d")
    text = re.sub(r"(^|[\s(\[{\u2014-])'", "\\1\u2018", text)
    return text.replace("'", "\u2019")


def count_words(html: str) -> int:
    return len(re.findall(r"[A-Za-z0-9’']+", re.sub(r"<[^>]+>", " ", html)))


def load_config():
    cfg = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
    for key in ("name", "tagline", "description", "base_url", "categories"):
        if not cfg.get(key):
            die(f"site.yaml: '{key}' is required")
    cfg["base_url"] = str(cfg["base_url"]).rstrip("/")
    for c in cfg["categories"]:
        c.setdefault("slug", slugify(c["name"]))
    if "example" in cfg["base_url"]:
        warn("site.yaml base_url is still a placeholder; canonical links and the sitemap point at it")
    return cfg


def load_posts(cfg, now: dt.datetime, include_future: bool = False):
    cats = {c["name"].lower(): c for c in cfg["categories"]}
    posts, seen = [], set()
    for path in sorted((ROOT / "content" / "posts").glob("*.md")):
        meta, body = read_doc(path)
        src = path.name
        for field in ("title", "slug", "description", "category", "published"):
            if not meta.get(field):
                die(f"{src}: missing '{field}'")
        if meta.get("draft"):
            continue
        slug = str(meta["slug"])
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            die(f"{src}: slug must be lowercase words joined by hyphens")
        if slug in RESERVED or slug in seen:
            die(f"{src}: slug '{slug}' is reserved or already used by another post")
        seen.add(slug)
        cat = cats.get(str(meta["category"]).lower())
        if not cat:
            die(f"{src}: unknown category '{meta['category']}'. Use one listed in site.yaml")
        published = to_utc(meta["published"], "published", src)
        updated = max(to_utc(meta.get("updated") or meta["published"], "updated", src), published)
        if published > now and not include_future:
            continue
        html, toc = render_markdown(body)
        words = count_words(html)
        title, desc = smart(meta["title"]), smart(meta["description"])
        if len(title) > 70:
            warn(f"{src}: title is {len(title)} characters; search results show about 60")
        if not 110 <= len(desc) <= 165:
            warn(f"{src}: description is {len(desc)} characters; aim for 120-160")
        sources = meta.get("sources") or []
        if len([s for s in sources if s.get("url")]) < 2:
            warn(f"{src}: fewer than 2 linked sources")
        posts.append({
            "slug": slug, "title": title, "description": desc,
            "dek": smart(meta.get("dek") or desc), "category": cat,
            "tags": [str(t) for t in (meta.get("tags") or [])],
            "published": published, "updated": updated,
            "why": smart(meta.get("why_trending") or ""), "signal": str(meta.get("signal") or ""),
            "key_points": [smart(k) for k in (meta.get("key_points") or [])],
            "sources": sources, "corrections": meta.get("corrections") or [],
            "trend_score": float(meta.get("trend_score", 50)), "featured": bool(meta.get("featured")),
            "html": html, "toc": toc, "words": words, "minutes": max(1, math.ceil(words / 200)),
            "path": f"{slug}/",
        })
    posts.sort(key=lambda p: p["published"], reverse=True)
    return posts


def load_pages():
    pages = []
    for path in sorted((ROOT / "content" / "pages").glob("*.md")):
        meta, body = read_doc(path)
        html, _ = render_markdown(body)
        pages.append({
            "slug": meta.get("slug") or path.stem, "title": meta["title"],
            "description": meta.get("description", ""), "dek": meta.get("dek", ""),
            "nav_label": meta.get("nav_label") or meta["title"], "order": meta.get("order", 50),
            "html": html, "path": f"{meta.get('slug') or path.stem}/",
        })
    pages.sort(key=lambda p: p["order"])
    return pages


# ---------------------------------------------------------------- media

def ensure_media(cfg, posts):
    for p in posts:
        folder = ROOT / "media" / p["slug"]
        key = f'{art.ART_VERSION}|{p["title"]}|{p["category"]["name"]}|{p["category"]["color"]}|{cfg["name"]}'
        stamp = hashlib.sha256(key.encode()).hexdigest()[:16]
        marker = folder / ".stamp"
        if marker.exists() and marker.read_text().strip() == stamp and all((folder / f).exists() for f in art.FILES):
            continue
        art.make_post_media(p["slug"], p["title"], p["category"]["name"], p["category"]["color"], cfg["name"], folder)
        marker.write_text(stamp)
    brand = ROOT / "theme" / "static" / "img"
    marker = brand / ".stamp"
    stamp = f'{art.ART_VERSION}|{cfg["name"]}'
    if not marker.exists() or marker.read_text().strip() != stamp:
        art.make_brand_assets(cfg["name"], brand)
        marker.write_text(stamp)


# ---------------------------------------------------------------- linking

class Linker:
    """Relative links that work at a domain root, under a /repo/ path, or in a preview."""

    def __init__(self, base: str, mode: str):
        self.base, self.mode = base, mode

    def rel(self, target: str, cur_dir: str) -> str:
        frag = ""
        if "#" in target:
            target, frag = target.split("#", 1)
            frag = "#" + frag
        if self.mode == "absolute":
            return self.abs(target) + frag
        is_dir = target == "" or target.endswith("/")
        dest = target + ("index.html" if is_dir and self.mode == "preview" else "")
        rel = os.path.relpath(dest or ".", cur_dir or ".")
        if is_dir and self.mode != "preview":
            rel = "./" if rel == "." else rel + "/"
        return rel + frag

    def abs(self, target: str) -> str:
        return f"{self.base}/{target}"


def rewrite_internal(html: str, linker: Linker, cur_dir: str) -> str:
    return re.sub(r'href="/(?!/)([^"]*)"', lambda m: f'href="{linker.rel(m.group(1), cur_dir)}"', html)


def jsonld(obj) -> Markup:
    return Markup(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))


# ---------------------------------------------------------------- selection

def pick_home(posts, now, per_page):
    if not posts:
        return None, [], [], []
    fresh = [p for p in posts if now - p["published"] <= dt.timedelta(hours=36)] or posts[:1]
    featured = [p for p in fresh if p["featured"]]
    lead = (featured or sorted(fresh, key=lambda p: (p["trend_score"], p["published"]), reverse=True))[0]
    rest = [p for p in posts if p is not lead]
    recent = sorted([p for p in rest if now - p["published"] <= dt.timedelta(hours=72)],
                    key=lambda p: (p["trend_score"], p["published"]), reverse=True)
    rail = recent[:5]
    for p in rest:
        if len(rail) >= 5:
            break
        if p not in rail:
            rail.append(p)
    remaining = [p for p in rest if p not in rail]
    return lead, rail, remaining[:per_page], remaining[per_page:]


def related_for(post, posts, n=3):
    def score(p):
        s = 3 if p["category"] is post["category"] else 0
        s += len(set(t.lower() for t in p["tags"]) & set(t.lower() for t in post["tags"])) * 2
        s += 1 / (1 + abs((p["published"] - post["published"]).total_seconds()) / 86400)
        return s
    return sorted([p for p in posts if p is not post], key=score, reverse=True)[:n]


def chunks(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)] or [[]]


# ---------------------------------------------------------------- feeds

def sitemap_xml(urls):
    rows = "".join(f"<url><loc>{xesc(loc)}</loc><lastmod>{lastmod}</lastmod></url>\n" for loc, lastmod in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "</urlset>\n")


def news_sitemap_xml(cfg, posts, linker):
    rows = []
    for p in posts:
        rows.append(
            "<url><loc>{loc}</loc><news:news><news:publication><news:name>{name}</news:name>"
            "<news:language>en</news:language></news:publication><news:publication_date>{date}</news:publication_date>"
            "<news:title>{title}</news:title></news:news></url>\n".format(
                loc=xesc(linker.abs(p["path"])), name=xesc(cfg["name"]), date=iso(p["published"]), title=xesc(p["title"])))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n' + "".join(rows) + "</urlset>\n")


def rss_xml(cfg, posts, linker, now):
    items = []
    for p in posts[:30]:
        link = linker.abs(p["path"])
        items.append(
            f"<item><title>{xesc(p['title'])}</title><link>{xesc(link)}</link>"
            f"<guid isPermaLink=\"true\">{xesc(link)}</guid><pubDate>{format_datetime(p['published'])}</pubDate>"
            f"<category>{xesc(p['category']['name'])}</category><description>{xesc(p['description'])}</description></item>\n")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n<channel>\n'
            f"<title>{xesc(cfg['name'])}</title><link>{xesc(linker.abs(''))}</link>"
            f"<description>{xesc(cfg['description'])}</description><language>en-us</language>"
            f"<lastBuildDate>{format_datetime(now)}</lastBuildDate>"
            f"<atom:link href=\"{xesc(linker.abs('feed.xml'))}\" rel=\"self\" type=\"application/rss+xml\"/>\n"
            + "".join(items) + "</channel>\n</rss>\n")


# ---------------------------------------------------------------- build

def build(out: Path, mode: str, now: dt.datetime, include_future: bool = False):
    cfg = load_config()
    preview = mode == "preview"
    posts = load_posts(cfg, now, include_future)
    pages = load_pages()
    ensure_media(cfg, posts)

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(ROOT / "theme" / "static", out / "assets", ignore=shutil.ignore_patterns(".stamp"))
    for p in posts:
        shutil.copytree(ROOT / "media" / p["slug"], out / "media" / p["slug"], ignore=shutil.ignore_patterns(".stamp"))

    linker = Linker(cfg["base_url"], mode)
    base = cfg["base_url"]
    css_v = hashlib.sha256((ROOT / "theme/static/css/site.css").read_bytes()).hexdigest()[:10]
    js_v = hashlib.sha256((ROOT / "theme/static/js/site.js").read_bytes()).hexdigest()[:10]
    cats_used = [c for c in cfg["categories"] if any(p["category"] is c for p in posts)]
    updated_at = max([p["updated"] for p in posts], default=now)
    org_id = f"{base}/#org"
    org = {"@type": "Organization", "@id": org_id, "name": cfg["name"], "url": f"{base}/",
           "logo": {"@type": "ImageObject", "url": f"{base}/assets/img/logo-512.png", "width": 512, "height": 512}}
    default_image = linker.abs("assets/img/share-default.png")
    nav_pages = [pg for pg in pages if pg["slug"] != "404"]
    trending = pick_home(posts, now, cfg.get("posts_per_page", 12))[1]

    env = Environment(loader=FileSystemLoader(str(ROOT / "theme" / "templates")),
                      autoescape=select_autoescape(["html", "xml"]), trim_blocks=True, lstrip_blocks=True)
    today_local = local(now).date()

    def when(d):
        return ap_time(d) if local(d).date() == today_local else ap_date(d)

    common = dict(site=cfg, cats=cats_used, preview=preview, css_v=css_v, js_v=js_v, fonts_href=FONTS_HREF,
                  ap_date=ap_date, ap_time=ap_time, iso=iso, when=when, slugify=slugify, year=local(now).year,
                  nav_pages=nav_pages, updated_at=updated_at, trending=trending,
                  masthead_date=f"{DAYS[local(updated_at).weekday()]}, {ap_date(updated_at)}")
    written = []

    def render(template, out_rel, ctx, link_mode=None):
        cur_dir = os.path.dirname(out_rel)
        lk = Linker(base, link_mode) if link_mode else linker
        html = env.get_template(template).render(
            **common, **ctx, u=lambda t: lk.rel(t, cur_dir), a=linker.abs,
            bare=preview and out_rel == "index.html")
        dest = out / out_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        written.append(out_rel)

    def meta(title_tag, description, path, *, og_type="website", image=None, image_alt=None, robots=None,
             graph=None, article=None):
        return {"title_tag": title_tag, "description": description, "canonical": linker.abs(path),
                "og_type": og_type, "og_image": image or default_image,
                "og_image_alt": image_alt or f"{cfg['name']}: {cfg['tagline']}",
                "robots": robots or "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1",
                "jsonld": jsonld({"@context": "https://schema.org", "@graph": graph}) if graph else None,
                "article": article}

    # home + pagination
    per_page = cfg.get("posts_per_page", 12)
    lead, rail, grid, older = pick_home(posts, now, per_page)
    older_pages = chunks(older, per_page) if older else []
    total_pages = 1 + len(older_pages)
    home_desc = cfg["description"]
    website = {"@type": "WebSite", "@id": f"{base}/#website", "url": f"{base}/", "name": cfg["name"],
               "description": home_desc, "publisher": {"@id": org_id}, "inLanguage": "en-US"}
    render("home.html", "index.html", {
        "meta": meta(cfg["name"] if preview else f"{cfg['name']}: {cfg['tagline']}", home_desc, "", graph=[website, org]),
        "active": "home", "lead": lead, "rail": rail, "grid": grid, "page_num": 1, "total_pages": total_pages})
    for i, chunk in enumerate(older_pages, start=2):
        render("home.html", f"page/{i}/index.html", {
            "meta": meta(f"Latest explainers, page {i} | {cfg['name']}", f"More explainers from {cfg['name']}, page {i}.",
                         f"page/{i}/", robots="noindex, follow"),
            "active": "home", "lead": None, "rail": [], "grid": chunk, "page_num": i, "total_pages": total_pages})

    # posts
    for p in posts:
        path = p["path"]
        url = linker.abs(path)
        card_abs = linker.abs(f"media/{p['slug']}/card.png")
        art_abs = linker.abs(f"media/{p['slug']}/art-1600.webp")
        cat_path = f"category/{p['category']['slug']}/"
        article = {"@type": "NewsArticle", "@id": f"{url}#article", "mainEntityOfPage": url,
                   "headline": p["title"][:110], "description": p["description"], "image": [card_abs, art_abs],
                   "datePublished": iso(p["published"]), "dateModified": iso(p["updated"]),
                   "author": [{"@type": "Organization", "name": cfg.get("author_name", cfg["name"]),
                               "url": linker.abs("about/")}],
                   "publisher": {"@id": org_id}, "articleSection": p["category"]["name"], "keywords": p["tags"],
                   "wordCount": p["words"], "isAccessibleForFree": True, "inLanguage": "en-US",
                   "citation": [s["url"] for s in p["sources"] if s.get("url")]}
        crumbs = {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{base}/"},
            {"@type": "ListItem", "position": 2, "name": p["category"]["name"], "item": linker.abs(cat_path)},
            {"@type": "ListItem", "position": 3, "name": p["title"]}]}
        cur_dir = os.path.dirname(f"{path}index.html")
        render("post.html", f"{path}index.html", {
            "meta": meta(f"{p['title']} | {cfg['name']}" if len(p["title"]) <= 52 else p["title"],
                         p["description"], path, og_type="article", image=card_abs, image_alt=p["title"],
                         graph=[article, crumbs, org],
                         article={"published": iso(p["published"]), "modified": iso(p["updated"]),
                                  "section": p["category"]["name"], "tags": p["tags"]}),
            "og_title": p["title"], "active": p["category"]["slug"], "post": p,
            "body": Markup(rewrite_internal(p["html"], linker, cur_dir)),
            "related": related_for(p, posts), "side": [q for q in trending if q is not p][:5],
            "share_url": url})

    # categories
    for c in cats_used:
        items = [p for p in posts if p["category"] is c]
        path = f"category/{c['slug']}/"
        for i, chunk in enumerate(chunks(items, 24), start=1):
            page_path = path if i == 1 else f"{path}page/{i}/"
            title = f"{c['name']} news explained" + (f", page {i}" if i > 1 else "")
            coll = {"@type": "CollectionPage", "@id": linker.abs(page_path), "url": linker.abs(page_path),
                    "name": f"{c['name']} | {cfg['name']}", "description": c.get("blurb", ""),
                    "isPartOf": {"@id": f"{base}/#website"}}
            render("list.html", f"{page_path}index.html", {
                "meta": meta(f"{title} | {cfg['name']}", c.get("blurb") or f"{c['name']} explainers from {cfg['name']}.",
                             page_path, graph=[coll, org], robots=None if i == 1 else "noindex, follow"),
                "active": c["slug"], "kind": "Topic", "heading": c["name"], "blurb": c.get("blurb", ""),
                "items": chunk, "color": c["color"], "page_num": i, "total_pages": math.ceil(len(items) / 24),
                "base_path": path})

    # tags
    tags: dict[str, dict] = {}
    for p in posts:
        for t in p["tags"]:
            entry = tags.setdefault(slugify(t), {"name": t, "items": []})
            entry["items"].append(p)
    for slug, entry in tags.items():
        path = f"tag/{slug}/"
        thin = len(entry["items"]) < 3
        render("list.html", f"{path}index.html", {
            "meta": meta(f"{entry['name']}: latest explainers | {cfg['name']}",
                         f"Every {cfg['name']} explainer about {entry['name']}, newest first.", path,
                         robots="noindex, follow" if thin else None),
            "active": "", "kind": "Tag", "heading": entry["name"], "blurb": "",
            "items": entry["items"], "color": None, "page_num": 1, "total_pages": 1, "base_path": path})

    # static pages
    for pg in pages:
        if pg["slug"] == "404":
            continue
        render("page.html", f"{pg['path']}index.html", {
            "meta": meta(f"{pg['title']} | {cfg['name']}", pg["description"] or cfg["description"], pg["path"]),
            "active": "", "page": pg, "body": Markup(rewrite_internal(pg["html"], linker, pg["slug"]))})

    if not preview:
        render("404.html", "404.html", {
            "meta": meta(f"Page not found | {cfg['name']}", "This page doesn't exist. Find the latest explainers here.",
                         "404.html", robots="noindex, follow"),
            "active": "", "latest": posts[:6]}, link_mode="absolute")

    # sitemaps, feed, robots
    urls = [(linker.abs(""), iso(updated_at))]
    urls += [(linker.abs(p["path"]), iso(p["updated"])) for p in posts]
    for c in cats_used:
        latest = max(p["updated"] for p in posts if p["category"] is c)
        urls.append((linker.abs(f"category/{c['slug']}/"), iso(latest)))
    for slug, entry in tags.items():
        if len(entry["items"]) >= 3:
            urls.append((linker.abs(f"tag/{slug}/"), iso(max(p["updated"] for p in entry["items"]))))
    urls += [(linker.abs(pg["path"]), iso(updated_at)) for pg in pages if pg["slug"] != "404"]
    (out / "sitemap.xml").write_text(sitemap_xml(urls), encoding="utf-8")
    fresh = [p for p in posts if now - p["published"] <= dt.timedelta(days=2)]
    (out / "news-sitemap.xml").write_text(news_sitemap_xml(cfg, fresh, linker), encoding="utf-8")
    (out / "feed.xml").write_text(rss_xml(cfg, posts, linker, now), encoding="utf-8")
    (out / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {linker.abs('sitemap.xml')}\nSitemap: {linker.abs('news-sitemap.xml')}\n",
        encoding="utf-8")
    if not preview:
        (out / ".nojekyll").write_text("", encoding="utf-8")
        if cfg.get("custom_domain"):
            (out / "CNAME").write_text(str(cfg["custom_domain"]).strip() + "\n", encoding="utf-8")
        if cfg.get("adsense_client"):
            pub = str(cfg["adsense_client"]).replace("ca-", "")
            (out / "ads.txt").write_text(f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")

    return {"posts": len(posts), "pages": len(written), "out": str(out)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preview", metavar="DIR", help="write a preview build to DIR instead of docs/")
    ap.add_argument("--now", help="build as if the current time were this ISO timestamp")
    ap.add_argument("--future", action="store_true", help="include posts scheduled in the future")
    args = ap.parse_args()
    now = to_utc(args.now, "--now", "command line") if args.now else dt.datetime.now(UTC).replace(microsecond=0)
    out = Path(args.preview).resolve() if args.preview else ROOT / "docs"
    result = build(out, "preview" if args.preview else "site", now, args.future)
    print(f"Built {result['posts']} posts, {result['pages']} pages -> {result['out']}")
    for w in WARNINGS:
        print(f"  warning: {w}")


if __name__ == "__main__":
    main()
