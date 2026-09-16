# TextOps Skills — Hebrew & English transcription for Claude Code

AI-agent skills by [TextOps](https://agents.text-ops-subs.com/en) for working with audio and video inside Claude Code (and other agents).

The main skill, **`transcription-speech-to-text-hebrew`**, transcribes Hebrew and English audio/video with speaker diarization in about **1 minute of processing per hour of recording**. Give it a local file, a Google Drive link, a YouTube video or playlist, or a Facebook / Instagram / X (Twitter) link, and get a transcript back as `.txt` and `.json` — then ask the agent for a summary, meeting minutes, show notes, a quiz or a lesson plan without leaving your workflow.

- **Website (English):** https://agents.text-ops-subs.com/en
- **אתר (עברית):** https://agents.text-ops-subs.com/
- **Pricing:** https://agents.text-ops-subs.com/pricing — 200 free minutes for new users, no credit card

## Install

```bash
npx skills add https://github.com/textops/textops-skills --skill transcription-speech-to-text-hebrew -g -y
```

Then create a free API key at https://agents.text-ops-subs.com/en and save it in `textops_settings.json` inside the skill folder (or set the `TEXTOPS_API_KEY` environment variable). Open a new Claude Code session and ask it to transcribe something.

## Skills in this repo

| Skill | What it does |
|---|---|
| [`transcription-speech-to-text-hebrew`](transcription-speech-to-text-hebrew/) | Hebrew & English transcription via the TextOps API: local files, Google Drive, YouTube (incl. playlists), Facebook, Instagram, X. Speaker diarization (up to 5 speakers), word-level timestamps, balance check. |
| [`hebrew-tech-lecture-summary`](hebrew-tech-lecture-summary/) | Summarize lectures, meetings, articles or transcripts into structured Hebrew Markdown. |
| [`media-files-conversion-ffmpeg`](media-files-conversion-ffmpeg/) | FFmpeg conversion, extraction, trimming, resizing and compression in natural language. |
| [`media-fixing-and-repair`](media-fixing-and-repair/) | Diagnose and repair broken or out-of-sync media files with FFmpeg/FFprobe. |

## Why TextOps for Hebrew

General-purpose speech-to-text models are trained mostly on English and degrade noticeably on Hebrew. TextOps is optimized for Hebrew (including spoken, informal Hebrew) with full English support, and is built to run inside an agent: the transcript stays out of the model's context unless you ask for it, so it is cheap in tokens and you can keep working while it runs in the background.

## Typical use cases

| Use case | Ask the agent for |
|---|---|
| Training & lectures | Summary, slides, quiz questions, lesson plan |
| Podcasts | Show notes, social-media quotes, SEO description |
| Meetings & sprints | Minutes, action items, decisions |

## Data & privacy

Audio/video is uploaded to TextOps servers for transcription and deleted automatically after one day. Details are in [`transcription-speech-to-text-hebrew/SKILL.md`](transcription-speech-to-text-hebrew/SKILL.md) and on the website ([Privacy Policy](https://agents.text-ops-subs.com/privacy-policy.html), [Terms](https://agents.text-ops-subs.com/terms-of-service.html)).

## License

MIT
