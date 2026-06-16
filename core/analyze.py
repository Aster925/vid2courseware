# -*- coding: utf-8 -*-
"""
Corpus analysis before the LLM step.

Two questions to answer before feeding transcripts to an LLM:
  1) How big is the corpus?  ->  token budget (does it exceed one context window?)
  2) How much *real* content overlaps?  ->  4-gram Jaccard between transcripts.

Key lesson (from the CELPIP build): surface overlap != content overlap.
Pairwise 4-gram Jaccard was only 0.7-2.7% there -> the shared text was just the
instructor's catchphrases, not duplicate teaching. So: merge by topic, don't
blindly dedup. High Jaccard (say >25%) instead flags genuine re-recordings.

转写喂给 LLM 前先分析：①语料多大(token 预算，是否超出上下文窗口) ②真实内容重叠多少
(4-gram Jaccard)。表层重复≠内容重复——高 Jaccard 才是"重录的同一节课"。

Usage:
    python -m core.analyze                       # uses output/transcripts/*.txt
    python -m core.analyze --dir some/folder --pair-threshold 0.25
"""
import os
import sys
import glob
import argparse
import itertools

sys.stdout.reconfigure(encoding="utf-8")
from core.cfg import load_config


def estimate_tokens(text):
    # ~1.35 tokens per whitespace word is a decent heuristic for many languages.
    return int(len(text.split()) * 1.35)


def ngrams(text, n=4):
    w = text.lower().split()
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def jaccard(a, b):
    A, B = ngrams(a), ngrams(b)
    u = A | B
    return len(A & B) / len(u) if u else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--dir", help="folder of .txt transcripts")
    ap.add_argument("--context-window", type=int, default=200000)
    ap.add_argument("--pair-threshold", type=float, default=0.25,
                    help="flag transcript pairs with Jaccard above this as likely re-recordings")
    args = ap.parse_args()

    cfg = load_config(args.config)
    out_dir = cfg.get("output_dir", "./output")
    tdir = args.dir or os.path.join(out_dir, "transcripts")
    files = sorted(glob.glob(os.path.join(tdir, "*.txt")))
    files = [f for f in files if not f.endswith((".cjk.txt", ".latin.txt", ".other.txt"))]
    if not files:
        sys.exit(f"No .txt transcripts in {tdir}")

    texts, total = {}, 0
    print(f"== token budget ({len(files)} files) ==")
    for f in files:
        txt = open(f, encoding="utf-8").read()
        texts[os.path.basename(f)] = txt
        tok = estimate_tokens(txt)
        total += tok
    print(f"corpus total ~{total:,} tokens "
          f"({'fits' if total <= args.context_window else 'EXCEEDS'} a "
          f"{args.context_window:,}-token window → "
          f"{'single pass' if total <= args.context_window else 'must batch'})")

    print(f"\n== redundancy (4-gram Jaccard, flagging > {args.pair_threshold:.0%}) ==")
    names = list(texts)
    flagged = 0
    for a, b in itertools.combinations(names, 2):
        j = jaccard(texts[a], texts[b])
        if j >= args.pair_threshold:
            print(f"  {j:5.1%}  {a}  ~=  {b}")
            flagged += 1
    print(f"{flagged} pair(s) above threshold"
          + ("" if flagged else "  → no real duplicates; merge by topic, don't dedup"))


if __name__ == "__main__":
    main()
