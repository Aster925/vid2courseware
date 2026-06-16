# -*- coding: utf-8 -*-
"""
Speech-to-text with faster-whisper.

Transcribes the unique videos listed in manifest.json (or any folder of media).
Handles mixed-language audio via Whisper's `multilingual` per-segment language
detection, and (optionally) splits the output by script so you get a clean
single-language file per language present.

用 faster-whisper 转写。支持混合语言（逐段检测），可按文字系统拆分出单语种文本。

Outputs per video: <stem>.json, <stem>.srt, <stem>.txt
(and <stem>.<script>.txt when --split-by-script and multiple scripts appear).

Usage:
    python -m core.transcribe --all              # everything in manifest
    python -m core.transcribe --seq 1 7 12       # selected manifest rows
    python -m core.transcribe --input path.mp4   # a single file, no manifest
"""
import os
import sys
import json
import time
import argparse

sys.stdout.reconfigure(encoding="utf-8")
from core.cfg import load_config, add_cuda_dlls

add_cuda_dlls()


def fmt_ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")


def script_of(text):
    """Coarse script tag for a segment: cjk / latin / other."""
    for c in text:
        if "一" <= c <= "鿿":
            return "cjk"
    return "latin" if any(c.isalpha() for c in text) else "other"


def safe(name):
    return "".join(c if c.isalnum() or c in "._-()" else "_" for c in name)[:80]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seq", nargs="*", type=int)
    ap.add_argument("--input", help="single media file (bypass manifest)")
    ap.add_argument("--model")
    ap.add_argument("--split-by-script", action="store_true",
                    help="also write one .txt per script (e.g. .cjk.txt / .latin.txt)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    tcfg = cfg.get("transcribe", {})
    out_dir = cfg.get("output_dir", "./output")
    model_name = args.model or tcfg.get("model", "large-v3-turbo")
    device = tcfg.get("device", "cuda")
    compute = tcfg.get("compute_type", "float16")
    multilingual = bool(tcfg.get("multilingual", True))
    beam = int(tcfg.get("beam_size", 5))

    # build target list
    if args.input:
        targets = [{"seq": 0, "path": args.input, "filename": os.path.basename(args.input)}]
    else:
        with open(os.path.join(out_dir, "manifest.json"), encoding="utf-8") as f:
            rows = [r for r in json.load(f) if r.get("canonical") and r.get("seq")]
        by_seq = {r["seq"]: r for r in rows}
        if args.all:
            targets = sorted(rows, key=lambda x: x["seq"])
        elif args.seq:
            targets = [by_seq[s] for s in args.seq if s in by_seq]
        else:
            sys.exit("Pass --all, --seq N..., or --input FILE")

    tdir = os.path.join(out_dir, "transcripts")
    os.makedirs(tdir, exist_ok=True)

    from faster_whisper import WhisperModel
    print(f"loading {model_name} ({device}/{compute}) ...")
    model = WhisperModel(model_name, device=device, compute_type=compute)

    for r in targets:
        seq, path, fn = r.get("seq", 0), r["path"], r["filename"]
        stem = (f"{seq:03d}_" if seq else "") + safe(os.path.splitext(fn)[0])
        jpath = os.path.join(tdir, stem + ".json")
        if os.path.exists(jpath):
            print(f"[skip] {stem}")
            continue
        if not os.path.exists(path):
            print(f"[miss] {path}")
            continue
        print(f"[{seq:03d}] {fn} ...", flush=True)
        t0 = time.time()
        segments, info = model.transcribe(
            path, language=None if multilingual else tcfg.get("language"),
            multilingual=multilingual, beam_size=beam, vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            condition_on_previous_text=False,   # cut hallucination loops
            no_repeat_ngram_size=3,
        )
        segs, by_script, srt = [], {}, []
        for i, s in enumerate(segments, 1):
            txt = s.text.strip()
            sc = script_of(txt)
            segs.append({"start": round(s.start, 2), "end": round(s.end, 2), "script": sc, "text": txt})
            by_script.setdefault(sc, []).append(txt)
            srt.append(f"{i}\n{fmt_ts(s.start)} --> {fmt_ts(s.end)}\n{txt}\n")
            if i % 200 == 0:
                print(f"    ...{i} segs, {s.end/60:.0f}min", flush=True)

        meta = {"seq": seq, "filename": fn, "duration_sec": round(info.duration, 1),
                "n_segments": len(segs), "segments": segs}
        with open(jpath, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        with open(os.path.join(tdir, stem + ".txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(s["text"] for s in segs))
        with open(os.path.join(tdir, stem + ".srt"), "w", encoding="utf-8") as f:
            f.write("\n".join(srt))
        if args.split_by_script and len(by_script) > 1:
            for sc, lines in by_script.items():
                with open(os.path.join(tdir, f"{stem}.{sc}.txt"), "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
        el = time.time() - t0
        print(f"    done: {info.duration/60:.1f}min, {len(segs)} segs, "
              f"{el/60:.1f}min wall, {info.duration/el:.1f}x", flush=True)


if __name__ == "__main__":
    main()
