# Architecture & design notes

## The premise: an LLM can't watch video or hear audio

Everything here follows from one fact. A language model only consumes **text and
images** — it can't ingest an `.mp4`. So the whole job is two moves:

1. **Extract** — convert video / audio / PDF into text and screenshots a model can read.
2. **Understand & rewrite** — the model reasons over that material and authors the result.

## The core principle: cheap tools for bulk, the LLM for judgment

> Anything a cheap deterministic tool can do, don't pay an LLM to do.
> Tools handle **volume** (batch, free, parallel, on your own GPU/CPU).
> The model handles **quality** (classify, correct, distill, write).

Transcribing 270 h of audio by "having a model listen" is impossible and costly;
local Whisper turns it into text almost for free. Conversely, "which two videos
are the same lesson re-recorded? which exam section is this?" can't be done by a
script — only the model can. Split the work along that line and both cost and
quality fall into place.

核心原则：便宜的确定性工具做"量"，大模型只做"判断与创作"。分工分对了，成本和效果都对了。

## The pipeline (layers + artifacts on disk)

```
sources (video / PDF)
        │
   ┌────▼─────────────────────────────────────────────┐
   │ EXTRACTION  (cheap, automated, parallel)          │
   │  manifest   head+tail fingerprint dedup           │
   │  transcribe faster-whisper, per-segment language  │
   │  frames     ffmpeg + perceptual-hash keyframes    │
   │  pdf        PyMuPDF text + images                 │
   └────┬─────────────────────────────────────────────┘
        │  intermediate artifacts: manifest.json, transcripts/, frames/, pdf_extract/
   ┌────▼─────────────────────────────────────────────┐
   │ INTELLIGENCE  (the LLM — not replaceable)         │
   │  classify · order · semantic-dedup · match PDFs   │
   │  restore courseware · annotate · write the guide  │
   └────┬─────────────────────────────────────────────┘
        │
   outputs (per-lesson folders / consolidated study guide)
```

Every step writes its result to disk. That **decoupling** is deliberate: any step
can be re-run, inspected, or swapped without touching the others.

## Techniques worth knowing

- **Two kinds of hashing, opposite goals.**
  - *Cryptographic* (SHA-1) for "byte-identical copy?" — one changed byte ⇒ totally
    different digest. We hash only `size + first 4MB + last 4MB` to avoid reading
    whole multi-GB files; collisions are negligible.
  - *Perceptual* (average-hash + Hamming distance) for "does this frame look the
    same?" — similar images ⇒ similar digest. Used to drop near-duplicate keyframes.
- **Byte-dedup ≠ content-dedup.** Re-recordings of one lesson are byte-different;
  find them later with **n-gram Jaccard** on the transcripts (`core/analyze.py`).
- **Whisper basics.** Encoder-decoder Transformer over a mel-spectrogram; the
  decoder generates text token-by-token like an LM (so it can *hallucinate*).
  faster-whisper (CTranslate2 backend) + float16 makes large models run on a
  consumer GPU at tens of × realtime.
- **Mixed-language audio.** Whisper picks one language per call by default; set
  `multilingual=True` for per-segment detection, then split by script.
- **Speed vs quality.** A distilled model (`large-v3-turbo`, ~50×) is fine when a
  later LLM pass cleans the text; reserve the slower full model for cases without
  that safety net.
- **Hallucination loops.** `vad_filter` (skip silence), `condition_on_previous_text=False`,
  and `no_repeat_ngram_size=3` curb the "stuck repeating" failure mode.
- **Scrolling text + perceptual hash.** Hashing the whole frame misses slow
  scrolls (static UI dominates); crop to the content region first.

## Engineering principles

- **Idempotent / resumable** — each output written once; re-runs skip finished work.
  A 6-hour batch that dies can just be restarted.
- **Pilot before full run** — validate quality and parameters on 3–5 samples
  before spending hours on the whole corpus.
- **Parallelize across resources** — run PDF/CPU work while the GPU transcribes.
- **Investigate the data first** — most design choices here were forced by a small
  experiment (counting files, transcribing one sample, viewing a few frames).
  For automation over unknown data, cheap reconnaissance beats writing code blind.
