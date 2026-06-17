# Contributing

Thanks for your interest! This project is small and modular by design — adding a
new source or extractor should be easy.

## Design principle

> **Cheap deterministic tools do the volume (batch, free, parallel). The LLM does
> the judgment (classify, correct, distill, write).**

Keep that line in mind: a contribution that pushes deterministic work into a
script (so the LLM step gets cleaner input) is exactly the right kind.

## Repo structure

- **`core/`** — source-agnostic building blocks. Each is a standalone script:
  config-driven (`config.yaml`) with `argparse` overrides, `stdout` set to UTF-8,
  and **idempotent/resumable** (re-runs skip finished work).
- **`recipes/`** — end-to-end flows for a specific source (e.g. `local_video`,
  `youtube_subs`). A recipe is mostly a README wiring `core/` modules together,
  plus any source-specific glue (like the YouTube subtitle downloader).
- **`docs/`** — design rationale and the editorial rules for the LLM step.

## How to add…

- **A new source recipe** (e.g. Bilibili, a Zoom export, burned-in subtitles):
  add `recipes/<name>/README.md` describing the flow, plus any small glue script.
  Reuse `core/` wherever possible.
- **A new core extractor**: add `core/<thing>.py` following the existing shape
  (load config via `core.cfg`, accept CLI overrides, write artifacts under
  `output_dir`, be resumable). Add a one-line mention to the README table.

## Conventions

- Python 3.9+, standard library first; add a dependency only when it earns its place.
- Keep scripts runnable as `python -m core.<name>`.
- **Never commit data.** No videos, transcripts, generated courseware, or personal
  paths. Examples must be synthetic. The `.gitignore` is your safety net — don't
  weaken it.

## Dev setup

```bash
pip install -r requirements.txt
python -m core.analyze --dir examples    # quick smoke test, no GPU needed
```

## Pull requests

Small, focused PRs are easiest to review. Describe what you changed and how you
tested it. For larger ideas, open an issue first to discuss.
