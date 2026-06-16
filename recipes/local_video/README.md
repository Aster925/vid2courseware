# Recipe: local video files → per-lesson courseware folders

When the source is a pile of **local recordings** (no captions), you transcribe
them yourself. This recipe was built for a year of recorded French-exam
(TEF Canada) live classes: ~114 videos, ~270 hours, mixed French + Chinese,
with the courseware shown on screen as a document.

本地录课（无字幕）→ 自己转写。本 recipe 针对一整年的法语考试直播课：中法混合、课件以
文档形式显示在屏幕上。

## Flow

```
1. core/manifest        scan + de-dup (byte-identical copies) → manifest.json
2. core/transcribe      faster-whisper (multilingual) → transcripts/*.txt
3. core/extract_frames  on-screen slides → frames/<key>/*.jpg  (perceptual dedup)
4. core/pdf_extract     existing PDFs → pdf_extract/*.md (+ images)   [optional]
5. core/analyze         find genuine re-recordings (high Jaccard) to drop
6. LLM authoring        per lesson: fuse transcript + keyframes (OCR) + PDF
                        → 课件.md (courseware) + 概要.md (summary) + video shortcut
```

## Steps

```bash
cp config.example.yaml config.yaml      # then edit: sources, output_dir, model...

python -m core.manifest                 # inventory + dedup
python -m core.transcribe --all --split-by-script
python -m core.extract_frames --seq 6   # keyframes for a given lesson
python -m core.pdf_extract --inspect    # check your PDFs are text (not scanned)
python -m core.pdf_extract              # then extract them
python -m core.analyze                  # flag re-recordings (Jaccard > 25%)
```

## Step 6 — the LLM does the authoring

The scripts only *extract*. Turning the raw material into a clean lesson is the
LLM's job, per lesson:

- **Classify by real content**, not filename (filenames lie — a file named
  "listening" may actually be a speaking task).
- **Restore the courseware** primarily from the **keyframes** (on-screen document
  text is cleaner than audio); use the transcript for the spoken explanation.
- **Merge any matching PDF** (one video may span several PDFs and vice-versa),
  unify its messy layout, and **keep original images for picture-based questions**.
- Add learning annotations (grammar / vocabulary / exam tips).

See [../../docs/editorial-rules.md](../../docs/editorial-rules.md).

## Hardware

faster-whisper `large-v3-turbo` on an NVIDIA RTX 4070 SUPER ran at ~40–50× realtime
(270 h of audio in ~6 h). On CPU, use a smaller model + `compute_type: int8`.
