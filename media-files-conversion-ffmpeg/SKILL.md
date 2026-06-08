---
name: media-files-conversion-ffmpeg
description: FFmpeg operations in natural language with best practices built-in. Use when working with audio/video files for conversion, extraction, trimming, resizing, or compression. Automatically applies smart defaults (stream copy for video when possible, efficient presets, CPU-only encoding).
license: MIT
compatibility: "Designed for Claude Code. Requires FFmpeg installed on the system. Python 3.7+ required for the helper script."
metadata:
  version: "1.0.14"
  author: "TextOps"
  tags: "ffmpeg, video, audio, conversion, trimming, compression, resizing, media"
---

# FFmpeg Skill

Natural language FFmpeg operations with opinionated best practices for speed, reliability, and quality.

## Core Principles

1. **Stream copy by default** - When converting video containers, use `-c copy` to avoid re-encoding (10x faster, no quality loss)
2. **CPU-only encoding** - No GPU encoders (more reliable, hardware-agnostic)
3. **Fast presets** - Default to `fast` preset for x264/x265 (good balance of speed/quality)
4. **Context-aware audio** - Ask about transcription when converting to MP3 (Whisper prefers 16kHz mono)

## Common Operations

### Audio Extraction

When extracting audio from video:

```bash
# Standard audio extraction (AAC/MP3)
ffmpeg -i input.mp4 -vn -acodec copy output.aac

# For transcription (Whisper-optimized)
ffmpeg -i input.mp4 -vn -ar 16000 -ac 1 -c:a libmp3lame -b:a 64k output.mp3
```

**Always ask**: "Is this for transcription?" before choosing the format.

### Video Conversion

When converting video containers (e.g., MKV → MP4):

```bash
# Fast conversion (stream copy - no re-encoding)
ffmpeg -i input.mkv -c copy output.mp4
```

If stream copy fails (incompatible codecs), fall back to re-encoding:

```bash
# Fallback: re-encode with fast preset
ffmpeg -i input.mkv -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k output.mp4
```

### Trimming

When trimming video (preserving quality):

```bash
# Fast trim (stream copy)
ffmpeg -ss 00:01:30 -to 00:02:45 -i input.mp4 -c copy output.mp4

# Accurate trim (re-encode if needed)
ffmpeg -i input.mp4 -ss 00:01:30 -to 00:02:45 -c:v libx264 -preset fast -crf 23 -c:a copy output.mp4
```

### Resizing

When resizing video:

```bash
# Resize to 720p (maintains aspect ratio)
ffmpeg -i input.mp4 -vf scale=-2:720 -c:v libx264 -preset fast -crf 23 -c:a copy output.mp4

# Resize to specific width (maintains aspect ratio)
ffmpeg -i input.mp4 -vf scale=1280:-2 -c:v libx264 -preset fast -crf 23 -c:a copy output.mp4
```

### Compression

**For WhatsApp/Telegram:**

```bash
# Aggressive compression (under 50MB target)
ffmpeg -i input.mp4 -vf scale=-2:480 -c:v libx264 -preset fast -crf 28 -b:a 64k -ac 1 output.mp4
```

**General compression:**

```bash
# Balanced compression
ffmpeg -i input.mp4 -c:v libx264 -preset fast -crf 28 -c:a aac -b:a 96k output.mp4
```

## Decision Tree

### Audio Conversion

1. **Ask**: "What's the purpose?" (listening, transcription, archival)
2. **For transcription**: Use 16kHz mono MP3
3. **For listening**: Use AAC or high-quality MP3
4. **For archival**: Use FLAC or original codec with stream copy

### Video Conversion

1. **Check**: Is this just a container change? (e.g., MKV → MP4)
   - YES → Use stream copy
   - NO → Continue
2. **Check**: Does the user want quality preservation or compression?
   - Preservation → Use CRF 18-23
   - Compression → Use CRF 26-30
3. **Check**: Is speed critical?
   - YES → Use `veryfast` preset
   - NO → Use `fast` preset

## Helper Script

Use `scripts/ffmpeg_helper.py` for common operations:

```bash
# Extract audio (auto-detects purpose)
python3 scripts/ffmpeg_helper.py extract-audio input.mp4 --ask-purpose

# Convert video (smart defaults)
python3 scripts/ffmpeg_helper.py convert input.mkv output.mp4

# Trim video (fast mode by default)
python3 scripts/ffmpeg_helper.py trim input.mp4 output.mp4 --start 00:01:30 --end 00:02:45

# Resize video
python3 scripts/ffmpeg_helper.py resize input.mp4 output.mp4 --height 720

# Compress for messaging
python3 scripts/ffmpeg_helper.py compress input.mp4 output.mp4 --target whatsapp
```

## Presets Reference

See `references/presets.md` for detailed preset explanations and use cases.

## Error Handling

When stream copy fails:
1. Inform the user: "Stream copy failed (incompatible codecs). Re-encoding with fast preset..."
2. Retry with re-encoding
3. Show the command used for transparency

When output is too large:
1. Suggest compression options
2. Offer CRF adjustment (higher = smaller file)
3. Offer resolution downscaling
