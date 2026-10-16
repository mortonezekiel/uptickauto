#!/usr/bin/env python3
"""Copy check: does a draft reuse wording from its sources?

  python3 tools/originality.py content/posts/2026-10-16-my-post.md work/research/my-post.txt [more files or folders]

Compares the draft's article text (front matter and link URLs removed) against
every source text given. Any run of 8 or more consecutive words that also
appears in a source is flagged, unless it sits inside quotation marks
(a short attributed quote is allowed) or is mostly figures (a run needs at
least 6 non-numeric words to count). Exit code 1 means rewrite the flagged
passages; 0 means the draft passed.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORD = re.compile(r"[a-z0-9]+(?:['’][a-z]+)?")


def article_text(raw: str) -> str:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
    front, body = (m.group(1), m.group(2)) if m else ("", raw)
    # include the reader-facing front matter fields too
    keep = []
    for line in front.splitlines():
        line = line.strip()
        if re.match(r"^(dek|why_trending|description):", line):
            keep.append(line.split(":", 1)[1])
        elif line.startswith("- ") and not re.search(r"https?://", line):
            keep.append(line[2:])
    text = "\n".join(keep) + "\n" + body
    text = re.sub(r"\]\([^)]*\)", "]", text)          # drop link targets
    text = re.sub(r"https?://\S+", " ", text)
    return text


def strip_quotes(text: str) -> str:
    return re.sub(r"[\"“][^\"”\n]{0,200}[\"”]", " ‖ ", text)


def tokens(text: str) -> list[str]:
    return WORD.findall(text.lower().replace("’", "'"))


def load_sources(paths: list[str]) -> list[str]:
    texts = []
    for p in paths:
        path = Path(p)
        files = sorted(path.rglob("*")) if path.is_dir() else [path]
        for f in files:
            if f.is_file():
                texts.append(f.read_text(encoding="utf-8", errors="ignore"))
    return texts


def check(draft: str, sources: list[str], n: int):
    src_grams = set()
    for s in sources:
        t = tokens(s)
        src_grams.update(tuple(t[i:i + n]) for i in range(len(t) - n + 1))
    hits = []
    for segment in strip_quotes(draft).split("‖"):
        t = tokens(segment)
        i = 0
        while i <= len(t) - n:
            if tuple(t[i:i + n]) in src_grams:
                j = i + n
                while j < len(t) and tuple(t[j - n + 1:j + 1]) in src_grams:
                    j += 1
                run = t[i:j]
                # Figures are facts, not wording: a run counts only if it has 6+ real words.
                if sum(1 for w in run if not w.isdigit()) >= 6:
                    hits.append(" ".join(run))
                i = j
            else:
                i += 1
    total = max(1, len(tokens(draft)) - n + 1)
    return hits, total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft")
    ap.add_argument("sources", nargs="+", help="source text files or folders")
    ap.add_argument("-n", type=int, default=8, help="flag shared runs of this many words (default 8)")
    args = ap.parse_args()
    draft = article_text(Path(args.draft).read_text(encoding="utf-8"))
    sources = load_sources(args.sources)
    if not sources:
        sys.exit("originality: no source text found; save your research notes first")
    hits, total = check(draft, sources, args.n)
    name = Path(args.draft).name
    if hits:
        print(f"FAIL {name}: {len(hits)} passage(s) share {args.n}+ words with a source. Rewrite them:")
        for h in hits:
            print(f"  - {h}")
        sys.exit(1)
    print(f"PASS {name}: no run of {args.n}+ words matches the {len(sources)} source file(s)")


if __name__ == "__main__":
    main()
