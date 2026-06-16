"""
TextOps transcription script.
Usage:
  python transcribe.py --file <path_or_url> [--diarization true|false]
                       [--output-format json|text] [--output-path <path>]
  python transcribe.py --job-id <id> [--output-format json|text] [--output-path <path>]
"""

import argparse
import json
import os
import re
import sys
import time
import requests

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ── API config ───────────────────────────────────────────────────────────────

def _load_api_key():
    # 1. Try settings.json next to the skill folder
    settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "textops_settings.json")
    if os.path.isfile(settings_path):
        try:
            with open(settings_path, encoding="utf-8") as f:
                val = json.load(f).get("TEXTOPS_API_KEY", "")
            if val and val != "YOUR_API_KEY_HERE":
                return val
        except Exception:
            pass

    # 2. Fall back to environment variable
    val = os.environ.get("TEXTOPS_API_KEY", "")
    if val:
        return val

    # 3. Neither found — guide the user
    settings_path_display = settings_path
    print(
        "\n"
        "ERROR: TEXTOPS_API_KEY not found.\n"
        "\n"
        "Get your API key here: https://agents.text-ops-subs.com\n"
        "\n"
        "Option 1 — settings.json (easiest):\n"
        f"  Open: {settings_path_display}\n"
        '  Replace  "YOUR_API_KEY_HERE"  with your key and save.\n'
        "\n"
        "Option 2 — environment variable:\n"
        "  Windows (Command Prompt):\n"
        "    setx TEXTOPS_API_KEY your_key_here\n"
        "  Windows (PowerShell):\n"
        "    [System.Environment]::SetEnvironmentVariable('TEXTOPS_API_KEY','your_key_here','User')\n"
        "  Mac / Linux:\n"
        "    echo 'export TEXTOPS_API_KEY=your_key_here' >> ~/.zshrc && source ~/.zshrc\n",
        flush=True,
    )
    sys.exit(1)

API_KEY = _load_api_key()


def _load_settings():
    settings_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "textops_settings.json",
    )
    result = {"language": "he", "num_speakers": 1, "word_timestamps": False}
    if os.path.isfile(settings_path):
        try:
            with open(settings_path, encoding="utf-8") as f:
                data = json.load(f)
            for k in result:
                if k in data:
                    result[k] = data[k]
        except Exception:
            pass
    return result


# this is tmp, problems with google... 
GET_UPLOAD_URL        = "https://get-upload-signed-url-hjqzix372q-uc.a.run.app"
SUBMIT_MODAL_URL      = "https://us-central1-whisper-cloud-functions.cloudfunctions.net/submit_modal_job"
CHECK_JOB_URL         = "https://us-central1-whisper-cloud-functions.cloudfunctions.net/check_modal_job"
BALANCE_URL           = "https://us-central1-whisper-cloud-functions.cloudfunctions.net/get_user_balance"
PLAYLIST_ESTIMATE_URL = "https://us-central1-whisper-cloud-functions.cloudfunctions.net/get_playlist_estimate"

SECS_PER_MIN     = 0.83   # 1 min of audio ≈ 0.83s → 1h file: first check ~40s (no diarization)
DIARIZATION_MULT = 2.25   # diarization ×2.25 → 1h file: first check ~90s
POLL_INTERVAL    = 5      # seconds between polls
SMALL_FILE_MB    = 20     # threshold in MB (local files)
SMALL_DURATION_SEC = 1200 # threshold in seconds = 20 min (URL files)
MAX_FILE_MB      = 2048   # 2 GB upload limit
MAX_POLLS        = 180    # 180 × 5s = 15 min max

SOCIAL_MEDIA_HOSTNAMES = {
    "facebook.com", "www.facebook.com", "m.facebook.com", "fb.watch",
    "instagram.com", "www.instagram.com",
    "twitter.com", "www.twitter.com", "x.com", "www.x.com",
}
_SOCIAL_VIDEO_PATTERNS = [
    re.compile(r"facebook\.com/.+/videos/"),
    re.compile(r"facebook\.com/watch"),
    re.compile(r"facebook\.com/reel/"),
    re.compile(r"fb\.watch/"),
    re.compile(r"instagram\.com/(p|reel|tv)/"),
    re.compile(r"(twitter|x)\.com/\w+/status/\d+"),
]


def is_social_media_url(url):
    from urllib.parse import urlparse
    host = urlparse(url).netloc.lower()
    if host not in SOCIAL_MEDIA_HOSTNAMES:
        return False
    return any(p.search(url) for p in _SOCIAL_VIDEO_PATTERNS)


def _social_basename(url):
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    host   = parsed.netloc.lower()
    path   = parsed.path
    if "instagram" in host:
        m = re.search(r"/(p|reel|tv)/([^/]+)", path)
        return f"instagram_{m.group(1)}_{m.group(2)}" if m else "instagram"
    if "facebook" in host or "fb.watch" in host:
        m = re.search(r"/videos/(\d+)", path)
        if m:
            return f"facebook_video_{m.group(1)}"
        v = parse_qs(parsed.query).get("v", [None])[0]
        if v:
            return f"facebook_video_{v}"
        slug = re.sub(r"[^a-zA-Z0-9]", "_", path.strip("/"))
        return f"facebook_{slug[:30]}" if slug else "facebook"
    if "twitter" in host or host in ("x.com", "www.x.com"):
        m = re.search(r"/status/(\d+)", path)
        return f"tweet_{m.group(1)}" if m else "tweet"
    return "social"


_start_time = None

def log(msg):
    """Print with immediate flush so output streams in real time."""
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("utf-8", errors="replace").decode("utf-8"), flush=True)

def elapsed():
    """Seconds elapsed since script start, as integer."""
    return int(time.time() - _start_time) if _start_time else 0


# ── duration detection ───────────────────────────────────────────────────────

def _try_ffprobe(file_path):
    import subprocess
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", file_path],
        capture_output=True, text=True, timeout=10
    )
    info = json.loads(result.stdout)
    for stream in info["streams"]:
        if "duration" in stream:
            return float(stream["duration"])
    return None


def _try_moviepy(file_path):
    from moviepy.editor import VideoFileClip
    clip = VideoFileClip(file_path)
    duration = clip.duration
    clip.close()
    return float(duration) if duration else None


def get_duration_seconds(file_path):
    if file_path.startswith("http://") or file_path.startswith("https://"):
        return None
    for _, fn in [("ffprobe", _try_ffprobe), ("moviepy", _try_moviepy)]:
        try:
            result = fn(file_path)
            if result and result > 0:
                return result
        except Exception:
            pass
    return None


def calc_initial_wait(duration_sec, has_diarization):
    if duration_sec is None:
        return None
    wait = (duration_sec / 60) * SECS_PER_MIN
    if has_diarization:
        wait *= DIARIZATION_MULT
    return wait * 0.8  # start checking 20% before estimated finish


# ── upload (for local files) ─────────────────────────────────────────────────

def get_signed_urls(filename):
    log(f"[UPLOAD] Getting signed URL for: {filename}")
    res = requests.post(GET_UPLOAD_URL, json={"filename": filename},
                        headers={"textops-api-key": API_KEY})
    res.raise_for_status()
    return res.json()


def upload_file(upload_url, file_path, filename):
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    log(f"[UPLOAD] Uploading: {filename} ({size_mb:.1f} MB)...")
    with open(file_path, "rb") as f:
        res = requests.put(upload_url, data=f)
    if res.status_code == 403:
        log("ERROR: Upload 403 — signed URL may have expired, try again")
        sys.exit(1)
    res.raise_for_status()
    log(f"[UPLOAD] Complete: {filename}")


# ── submit + poll ─────────────────────────────────────────────────────────────

def submit_job(download_url, has_diarization, word_timestamps=False, is_hebrew=True):
    params = {
        "word_timestamps": word_timestamps,
        "is_hebrew": is_hebrew,
    }
    if has_diarization is False:
        params["enable_diarization"] = False
    log("[JOB] Submitting...")
    for attempt in range(1, 4):
        res = requests.post(SUBMIT_MODAL_URL,
                            json={"download_url": download_url, "params": params},
                            headers={"textops-api-key": API_KEY})
        if res.status_code == 400:
            body = res.json() if res.content else {}
            err  = body.get("error", "Bad request")
            details = body.get("details", "")
            if "not accessible" in err:
                log(f"ERROR: URL is not publicly accessible. {details}".strip())
                log("  If this is a Google Drive link, set sharing to 'Anyone with the link'.")
            elif "not a transcribable" in err:
                log("ERROR: File format is not supported for transcription.")
                log("  Supported formats: mp3/mp4/wav/m4a/ogg/flac/aac/wma/opus/webm/mkv/avi/mov/wmv/3gp/ts")
            else:
                log(f"ERROR: {err}. {details}".strip())
            sys.exit(1)
        if res.status_code >= 500:
            log(f"[JOB] Server error {res.status_code} (attempt {attempt}/3) — retrying in 5s...")
            time.sleep(5)
            continue
        res.raise_for_status()
        break
    else:
        log(f"ERROR: Server returned {res.status_code} after 3 attempts.")
        sys.exit(1)
    body = res.json()
    job_id = body["textopsJobId"]
    server_duration = body.get("duration_seconds")
    log(f"[JOB] ID: {job_id}")
    log(f"[JOB] Tip: if interrupted, resume with --job-id {job_id}")
    return job_id, server_duration


def poll_job(job_id, initial_wait, poll_interval=POLL_INTERVAL, max_polls=MAX_POLLS):
    if initial_wait is not None:
        log(f"[WAIT] First check in {initial_wait:.0f}s (estimated processing time)")
        time.sleep(initial_wait)
    else:
        log("[WAIT] Duration unknown — first check in 10s")
        time.sleep(10)

    last_progress = -1
    for attempt in range(1, max_polls + 1):
        res = requests.post(CHECK_JOB_URL,
                            json={"textopsJobId": job_id},
                            headers={"textops-api-key": API_KEY})
        res.raise_for_status()
        data = res.json()

        status   = data.get("status", "?")
        progress = data.get("progress", 0)

        if data.get("has_error"):
            log(f"ERROR: Processing failed: {data.get('user_messages') or status}")
            sys.exit(1)

        has_segments = bool(data.get("result", {}).get("segments"))
        if status == "done" or has_segments:
            log(f"[DONE] Processing complete ({elapsed()}s total)")
            return data

        # print progress only when it changes (avoid log spam)
        if progress != last_progress:
            log(f"[PROGRESS] {progress}% ({elapsed()}s elapsed)")
            last_progress = progress

        time.sleep(poll_interval)

    log(f"WARNING: Timeout after {elapsed()}s — job may still be running")
    log(f"WARNING: Resume with: python transcribe.py --job-id {job_id} ...")
    sys.exit(1)


def extract_segments(data):
    """
    API response structure can vary:
      - data["result"]["segments"]      (most common)
      - data["result"]["result"]["segments"]  (nested)
    Returns segments list and prints the actual structure if not found.
    """
    result = data.get("result", {})

    # try flat structure first
    segments = result.get("segments")
    if segments is not None:
        return segments

    # try nested structure
    inner = result.get("result", {})
    segments = inner.get("segments")
    if segments is not None:
        return segments

    # not found — print actual structure to help debug
    log("\nWARNING: No segments found in response. Actual response structure:")
    log(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
    log("\n  Tip: check the key that contains the text and open an issue with this structure")
    return []


# ── output writers ────────────────────────────────────────────────────────────

def write_json(data, output_path):
    result = data.get("result", data)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    size = os.path.getsize(output_path)
    if size < 10:
        log(f"WARNING: Empty JSON file ({size} bytes) — API response contained no content")
    return size


# ── output writer (shared by full-poll and --check-once paths) ────────────────

def save_output(data, output_path, has_diarize, output_format):
    import subprocess
    json_path = os.path.splitext(output_path)[0] + ".json"
    os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
    size = write_json(data, json_path)
    log(f"[FILE] JSON: {json_path} ({size:,} bytes)")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    txt_path = os.path.splitext(output_path)[0] + ".txt"
    result = subprocess.run(
        [sys.executable, os.path.join(script_dir, "json_to_text.py"),
         json_path, "--output", txt_path,
         "--diarization", "true" if has_diarize else "false"],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.stdout:
        log(result.stdout.strip())
    if result.returncode != 0 and result.stderr:
        log(f"WARNING: {result.stderr.strip()}")


# ── balance ───────────────────────────────────────────────────────────────────

def get_balance():
    res = requests.get(BALANCE_URL, headers={"textops-api-key": API_KEY})
    res.raise_for_status()
    seconds = res.json()["seconds_remaining"]
    minutes = seconds // 60
    log(f"[BALANCE] {seconds} seconds remaining (~{minutes} minutes)")
    return seconds


# ── playlist ──────────────────────────────────────────────────────────────────

def get_playlist_estimate(playlist_url):
    res = requests.post(PLAYLIST_ESTIMATE_URL,
                        json={"playlist_url": playlist_url},
                        headers={"textops-api-key": API_KEY})
    if res.status_code == 400:
        body = res.json() if res.content else {}
        log(f"ERROR: {body.get('error', 'Bad request')}")
        sys.exit(1)
    res.raise_for_status()
    return res.json()


def print_playlist_info(playlist_url):
    """Fetch playlist metadata and print structured info for the skill to read.
    No transcription is performed here — the skill orchestrates individual jobs."""
    log("[PLAYLIST] Fetching playlist info...")
    info = get_playlist_estimate(playlist_url)

    playlist_id = info["playlist_id"]
    count       = info["count"]
    total_sec   = info["total_seconds"]
    balance_sec = info["user_seconds_remaining"]
    has_enough  = info["has_enough_balance"]
    videos      = info["videos"]

    log(f"[PLAYLIST] id={playlist_id} count={count} total={total_sec}s balance={balance_sec}s enough={has_enough}")
    for v in videos:
        lang = v.get("language") or "null"
        acc  = v.get("accessible")
        dur  = v.get("duration_seconds", "null")
        log(f'[VIDEO] index={v["video_index"]} title="{v.get("title","")}" duration={dur}s accessible={acc} lang={lang} url={v["url"]}')

    if not has_enough:
        shortfall = total_sec - balance_sec
        log(f"ERROR: Not enough balance. Need {total_sec}s, have {balance_sec}s (short by {shortfall}s).")
        sys.exit(2)

    log(f"[PLAYLIST_FOLDER] playlist_{playlist_id}")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    _s = _load_settings()
    _ns = _s.get("num_speakers", 1)
    if _ns is None:
        _diar_default = "auto"
    elif _ns == 1:
        _diar_default = "false"
    else:
        _diar_default = "true"
    _wt_default  = "true" if _s.get("word_timestamps") else "false"
    _heb_default = "true" if _s.get("language", "he") == "he" else "false"

    parser = argparse.ArgumentParser(description="TextOps transcription")
    parser.add_argument("--balance", action="store_true",
                        help="Check remaining transcription balance and exit")
    parser.add_argument("--playlist", default=None,
                        help="YouTube playlist URL — transcribe all accessible videos into a folder")
    parser.add_argument("--file", default=None, help="Local file path or URL")
    parser.add_argument("--job-id", default=None,
                        help="Resume from existing Job ID (skip upload/submit)")
    parser.add_argument("--diarization", default=_diar_default,
                        help="Enable speaker separation: true / false / auto (default: from textops_settings.json)")
    parser.add_argument("--word-timestamps", default=_wt_default,
                        help="Word-level timestamps (slower): true/false (default: from textops_settings.json)")
    parser.add_argument("--is-hebrew", default=_heb_default,
                        help="Route to Hebrew model (true) or multilingual model (false) (default: from textops_settings.json)")
    parser.add_argument("--output-format", default="json",
                        choices=["json", "text"], help="Output format")
    parser.add_argument("--output-path", default=None,
                        help="Where to save the result (optional)")
    parser.add_argument("--submit-only", action="store_true",
                        help="Upload and submit, print Job ID + timing hints, exit immediately (no polling)")
    parser.add_argument("--check-once", action="store_true",
                        help="With --job-id: poll once. Exit 0=done (files saved), 3=still processing, 1=error")
    args = parser.parse_args()

    if args.balance:
        get_balance()
        sys.exit(0)

    if not args.file and not args.job_id and not args.playlist:
        log("ERROR: Required: --file, --job-id, --playlist, or --balance")
        sys.exit(1)

    global _start_time
    _start_time = time.time()

    _diar = args.diarization.lower()
    if _diar in ("true", "1", "yes"):
        has_diarize = True
    elif _diar in ("false", "0", "no"):
        has_diarize = False
    else:
        has_diarize = None   # auto — sends null to API → server auto-detects speakers
    has_word_ts   = args.word_timestamps.lower() in ("true", "1", "yes")
    is_hebrew     = args.is_hebrew.lower() not in ("false", "0", "no")
    output_format = args.output_format

    if args.playlist:
        print_playlist_info(args.playlist)
        sys.exit(0)

    # ── determine output path ─────────────────────────────────────────────────
    if args.output_path:
        output_path = args.output_path
    elif args.job_id:
        ext = ".json" if output_format == "json" else ".txt"
        output_path = os.path.join(os.getcwd(), f"{args.job_id}_transcript{ext}")
    elif args.file.startswith("http://") or args.file.startswith("https://"):
        output_path = None  # finalized below from URL basename
    else:
        base = os.path.splitext(os.path.basename(args.file))[0]
        ext  = ".json" if output_format == "json" else ".txt"
        output_path = os.path.join(os.getcwd(), base + "_transcript" + ext)

    # ── resume / check-once from existing job ID ─────────────────────────────
    if args.job_id:
        if args.check_once:
            # Single poll — no sleep, exit immediately with status code
            res = requests.post(CHECK_JOB_URL,
                                json={"textopsJobId": args.job_id},
                                headers={"textops-api-key": API_KEY})
            res.raise_for_status()
            data = res.json()
            if data.get("has_error"):
                log(f"ERROR: Processing failed: {data.get('user_messages') or data.get('status', '?')}")
                sys.exit(1)
            has_segments = bool(data.get("result", {}).get("segments"))
            if data.get("status") == "done" or has_segments:
                log(f"[DONE] Processing complete ({elapsed()}s total)")
                if has_diarize is None:
                    _speakers = set(s.get("speaker", "") for s in extract_segments(data) if s.get("speaker"))
                    has_diarize = len(_speakers) > 1
                save_output(data, output_path, has_diarize, output_format)
                sys.exit(0)
            progress = data.get("progress", 0)
            log(f"[STATUS] processing {progress}%")
            sys.exit(3)

        log(f"[JOB] Resuming with existing Job ID: {args.job_id}")
        data = poll_job(args.job_id, initial_wait=None)
        if has_diarize is None:
            _speakers = set(s.get("speaker", "") for s in extract_segments(data) if s.get("speaker"))
            has_diarize = len(_speakers) > 1
    else:
        file_arg = args.file
        is_url   = file_arg.startswith("http://") or file_arg.startswith("https://")

        if is_url:
            from urllib.parse import urlparse
            if is_social_media_url(file_arg):
                base = _social_basename(file_arg)
            else:
                url_basename = os.path.basename(urlparse(file_arg).path) or "audio"
                base = os.path.splitext(url_basename)[0] or "transcript"
            if not output_path:
                ext  = ".json" if output_format == "json" else ".txt"
                output_path = os.path.join(os.getcwd(), base + "_transcript" + ext)

            duration_sec = None
            download_url = file_arg
            file_size_mb = 0
        else:
            filename     = os.path.basename(file_arg)
            file_size_mb = os.path.getsize(file_arg) / (1024 * 1024)
            if file_size_mb > MAX_FILE_MB:
                log(f"ERROR: File is too large ({file_size_mb:.0f} MB). Maximum allowed size is {MAX_FILE_MB} MB (2 GB).")
                log("  Convert to a smaller format first, e.g.:")
                log("    ffmpeg -i input.mp4 -vn -ar 44100 -ac 2 -b:a 128k output.mp3")
                sys.exit(1)
            duration_sec = get_duration_seconds(file_arg)
            urls         = get_signed_urls(filename)
            upload_file(urls["upload_url"], file_arg, filename)
            download_url = urls["download_url"]

        initial_wait = calc_initial_wait(duration_sec, has_diarize)

        poll_interval = POLL_INTERVAL
        max_polls     = MAX_POLLS

        job_id, server_duration = submit_job(download_url, has_diarize, has_word_ts, is_hebrew)

        # For URLs (e.g. YouTube), local duration is unknown — use server-returned duration
        if initial_wait is None and server_duration:
            initial_wait = calc_initial_wait(server_duration, has_diarize)

        if args.submit_only:
            base_path = os.path.splitext(output_path)[0] if output_path else os.path.join(os.getcwd(), job_id + "_transcript")
            log(f"[OUTPUT] {base_path}")
            first_check  = int(initial_wait) if initial_wait else 10
            est_total    = int(initial_wait / 0.8) if initial_wait else "unknown"
            log(f"[TIMING] first_check={first_check}s poll_interval={poll_interval}s estimated_total={est_total}s")
            sys.exit(0)

        data   = poll_job(job_id, initial_wait, poll_interval, max_polls)
        if has_diarize is None:
            _speakers = set(s.get("speaker", "") for s in extract_segments(data) if s.get("speaker"))
            has_diarize = len(_speakers) > 1

    save_output(data, output_path, has_diarize, output_format)


if __name__ == "__main__":
    main()
