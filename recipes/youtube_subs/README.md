# Recipe: YouTube channel → one consolidated study guide

When the source is a YouTube channel **with captions**, you don't need
transcription at all — just download the subtitles. This recipe was first built
to turn an English-exam (CELPIP) teaching channel of ~110 videos into a single
study guide organized by test section.

字幕齐全的 YouTube 频道，直接下字幕即可，无需转写。本 recipe 把上百个教学视频合并成
一份「按考试板块组织」的学习指南。

## Flow

```
1. download_subs.sh   yt-dlp → data/raw_vtt/*.vtt   (subtitles only, no video)
2. vtt_to_text.py     *.vtt → data/transcripts/*.txt  (clean, dedup lines)
3. core/analyze.py    token budget + 4-gram Jaccard redundancy
4. LLM consolidation  merge transcripts → ONE guide, by test section
                      (see ../../docs/editorial-rules.md)
```

## Steps

```bash
# 1) subtitles  (edit --sub-langs inside the script for your language)
./download_subs.sh "https://www.youtube.com/@SomeChannel/videos"

# 2) clean to plain text
python vtt_to_text.py data/raw_vtt data/transcripts

# 3) how big is it, and is anything really duplicated?
python -m core.analyze --dir data/transcripts
```

## 4) Consolidate with an LLM

If the corpus exceeds one context window (analyze.py will tell you), consolidate
in **batches across separate sessions**, carrying the *growing guide* forward
(not the raw transcripts):

```
Session 1:  editorial-rules + Batch 1 transcripts        → guide v1
Session 2:  editorial-rules + guide v1 + Batch 2          → guide v2
Session 3:  editorial-rules + guide v2 + Batch 3          → final guide
```

Keep each batch to ~60% of the working token budget for headroom. See
[../../docs/editorial-rules.md](../../docs/editorial-rules.md) for the merge conventions.

> **Why organize by test section, not by video?** Across a teaching channel the
> real content overlap is tiny (measured 4-gram Jaccard ~0.7–2.7%); what repeats
> is the instructor's phrasing, not the teaching. So merge by topic — a section
> reference is far more useful than a video-by-video dump.
