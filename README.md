# 高清视频下载 / HD Video Download

A small Python CLI and Codex Skill for downloading single HD videos from
YouTube, Bilibili, Douyin, and Xiaohongshu with `yt-dlp`.

Use it only for videos you own, videos you are allowed to download, or videos
whose license permits downloading. You are responsible for following each
platform's terms and local law.

## Features

- YouTube, Bilibili, Douyin, and Xiaohongshu URL detection.
- Douyin search/profile URLs with `modal_id` are converted to direct video URLs.
- Height-based format selection, including vertical Bilibili 1080p.
- Optional Chrome or Netscape cookie authentication.
- Available platform subtitles exported as SRT and plain TXT.
- Verified media output with `ffprobe`.
- One output folder per platform under `~/Downloads/hd-video-downloads/`.
- Finder opens automatically after a successful download on macOS.
- No cookies, tokens, subtitles, or downloaded media are stored in Git.

Subtitle export uses subtitle tracks exposed by the platform. It does not
silently transcribe audio when a video has no subtitle track.

When used as a Codex Skill, an optional Feishu Minutes transcription fallback
may be used only if the connector is installed and the user authorizes upload.

## Requirements

- Python 3.10+
- `ffmpeg` and `ffprobe`
- Node.js for YouTube JavaScript challenge solving
- Docker, optional but recommended for protected YouTube HD formats

On macOS with Homebrew:

```bash
brew install ffmpeg node
```

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

The new command is `hd-video-download`. The old `yt-bili-hd` command remains
as a compatibility alias.

## Download

```bash
hd-video-download doctor
hd-video-download formats "VIDEO_URL" --cookies-from-browser chrome
hd-video-download download "VIDEO_URL" --height 1080 --cookies-from-browser chrome
```

Download video and export available subtitles as SRT and TXT:

```bash
hd-video-download download "VIDEO_URL" --height 1080 \
  --cookies-from-browser chrome --subtitles
```

Export subtitles without downloading the video:

```bash
hd-video-download subtitles "VIDEO_URL" --cookies-from-browser chrome
```

Use `--no-open` when Finder should not open. Use `-o DIR` to change the output
root; the CLI still creates a `youtube`, `bilibili`, `douyin`,
`xiaohongshu`, or `generic` subfolder.

## Authentication

Many HD formats require a logged-in account. Read Chrome cookies only with the
account owner's permission:

```bash
hd-video-download download "VIDEO_URL" --cookies-from-browser chrome
```

Alternatively, pass a Netscape-format cookie file:

```bash
hd-video-download download "VIDEO_URL" --cookies ./cookies.txt
```

Never commit cookie files. The repository ignores common cookie filenames.

## YouTube PO Token Provider

Some YouTube HD formats require a GVS PO Token. Start the provider if YouTube
only lists storyboards or low-resolution formats:

```bash
PROXY_PORT=7897 scripts/start-youtube-pot-provider.sh
```

Without a proxy:

```bash
scripts/start-youtube-pot-provider.sh --no-proxy
```

## Codex Skill

The reusable Skill is in `.agents/skills/hd-video-download`. Its display name
is **高清视频下载**. The Skill wrapper creates an isolated environment under
`~/.cache/hd-video-download/` and invokes this project's CLI.

For a personal installation, link or copy that folder to:

```text
~/.agents/skills/hd-video-download
```

Refresh the Skills page or restart Codex after installation.

## Development

```bash
python -m unittest
python -m compileall src tests
```
