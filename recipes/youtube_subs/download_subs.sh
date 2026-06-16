#!/usr/bin/env bash
# Download subtitles only (no video) for a whole YouTube channel/playlist.
# Subtitles are tiny and fast — when a channel has captions, you don't need ASR.
#
# 只下字幕、不下视频。频道有字幕时，这是最省事的取材方式。
#
# Usage:  ./download_subs.sh "https://www.youtube.com/@SomeChannel/videos"  [out_dir]
set -euo pipefail

CHANNEL="${1:?pass a channel/playlist URL}"
OUT="${2:-data/raw_vtt}"
mkdir -p "$OUT"

# --write-auto-subs falls back to YouTube's auto captions when no human subs exist.
# --sub-langs: change to your language(s), e.g. "fr.*" or "zh.*".
# --restrict-filenames: spaces -> "_", strips special chars.
yt-dlp \
  --skip-download \
  --write-subs --write-auto-subs \
  --sub-langs "en.*" \
  --sub-format vtt \
  --restrict-filenames \
  --output "$OUT/%(playlist_index)03d_%(title)s____%(id)s.%(ext)s" \
  "$CHANNEL"

# Filename convention produced here:
#   0040_English_for_Emergency____hwNFG-zhFjU.en.vtt
#   └┬─┘ └────────┬───────────┘  └────┬────┘
#  index        title            11-char video id
echo "done -> $OUT"
