#!/usr/bin/env bash
# Encode rendered frames to MP4 (full size) and a looping GIF (half width).
# Usage: encode.sh <frames_dir> <out_basename> [fps]   → out_basename.mp4, out_basename.gif
set -euo pipefail
FRAMES="$1"; OUT="$2"; FPS="${3:-24}"
ffmpeg -loglevel error -y -framerate "$FPS" -i "$FRAMES/f%04d.png" \
  -c:v libx264 -pix_fmt yuv420p -crf 17 -movflags +faststart "$OUT.mp4"
W=$(ffprobe -v error -select_streams v -show_entries stream=width -of csv=p=0 "$OUT.mp4")
ffmpeg -loglevel error -y -framerate "$FPS" -i "$FRAMES/f%04d.png" \
  -vf "fps=20,scale=$((W / 2)):-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" \
  -loop 0 "$OUT.gif"
ffprobe -v error -show_entries stream=width,height,duration -of csv=p=0 "$OUT.mp4"
ls -la "$OUT.mp4" "$OUT.gif"
