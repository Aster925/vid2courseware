# Editorial rules — how the LLM should author the output

The scripts only extract raw material. These are the conventions for the LLM step
that turns that material into the final study courseware. Adapt to your exam/subject.

脚本只做提取；这一步由 LLM 把原料写成最终课件。以下是编辑约定。

## Universal rules

1. **Organize by subject structure, not by source video.** Group content under the
   exam's sections / skills, not "video 1, video 2…". A section reference is far
   more useful than a per-video dump.
2. **Classify by real content, not by filename.** Filenames mislead — verify from
   the transcript / on-screen text what a video actually covers.
3. **Surface overlap ≠ content overlap.** Don't blindly dedup similar-sounding
   videos; the repeated bits are usually catchphrases. Merge genuinely same-topic
   content; only drop true re-recordings (flagged by high n-gram Jaccard).
4. **Preserve sample answers / source texts verbatim.** Only light filler cleanup
   (um, uh, repeated false starts). Don't paraphrase the material itself.
5. **Strip channel promotion** (like/subscribe/links); keep an attribution credit.
6. **Prefer the cleaner source.** When on-screen document text and audio disagree,
   trust the on-screen text (keyframe OCR) for written material.

## Per-lesson courseware (local_video recipe)

A lesson folder typically contains `课件.md` (courseware) + `概要.md` (summary) +
a shortcut to the video + key screenshots.

- **Restore the document** primarily from keyframes; use the transcript for the
  spoken explanation and emphasis.
- **Merge matching PDFs** (relationship is many-to-many): unify the messy layout,
  and **keep original images for picture-based questions**.
- **Annotate for learning**: grammar, key vocabulary, exam tips — at the depth the
  user asked for (lean → rich).
- Keep bilingual material side by side (source language + the learner's language).

## Consolidated guide (youtube_subs recipe), batched

When the corpus exceeds one context window, merge across sessions:

- Carry the **growing guide** forward, not the raw transcripts.
- Each session: `editorial-rules + current guide + next transcript batch → updated guide`.
- Keep batches to ~60% of the working token budget for headroom.

### Safe incremental writing

When appending large Markdown blocks via shell heredocs, use a **unique delimiter
per block** that can't appear in the content (`GUIDE_EOF`, `SECTION_EOF`). A stray
delimiter leaking into a file is the classic bug. Verify after each write:

```bash
grep -n '^## ' output/guide.md   # expected section headers present?
tail -n 20 output/guide.md       # last block landed correctly?
```
