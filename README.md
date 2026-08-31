# yt-bili-hd-downloader

A small Python CLI for downloading HD single videos from YouTube and Bilibili
with `yt-dlp`, then validating the merged media with `ffprobe`.

Use it only for videos you own, videos you are allowed to download, or videos
whose license permits downloading. You are responsible for following each
platform's terms and local law.

## Features

- YouTube and Bilibili single-video downloads.
- Height-based HD format selection, including vertical Bilibili 1080p.
- Optional browser cookies through `yt-dlp` flags.
- YouTube PO Token provider support through `bgutil-ytdlp-pot-provider`.
- MP4 merge output and post-download `ffprobe` verification.
- No cookies, tokens, or downloaded media are stored in the repository.

## Requirements

- Python 3.10+
- `ffmpeg` and `ffprobe`
- Node.js for YouTube JavaScript challenge solving
- Docker, optional but recommended for YouTube 720p/1080p DASH formats

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

## Quick Start

Check local tools:

```bash
yt-bili-hd doctor
```

List formats:

```bash
yt-bili-hd formats "https://www.youtube.com/watch?v=VIDEO_ID"
yt-bili-hd formats "https://www.bilibili.com/video/BVxxxx/" --cookies-from-browser chrome
```

Download 1080p:

```bash
yt-bili-hd download "https://www.youtube.com/watch?v=VIDEO_ID" --height 1080 --cookies-from-browser chrome
yt-bili-hd download "https://www.bilibili.com/video/BVxxxx/" --height 1080 --cookies-from-browser chrome
```

Downloads go to `downloads/` by default.

## YouTube PO Token Provider

Some YouTube HD formats require a GVS PO Token. Start the provider before
downloading if YouTube only lists storyboards or 360p formats.

If you use a local proxy on port `7897`:

```bash
PROXY_PORT=7897 scripts/start-youtube-pot-provider.sh
```

Without a proxy:

```bash
scripts/start-youtube-pot-provider.sh --no-proxy
```

Verify it:

```bash
curl -fsS http://127.0.0.1:4416/ping
```

## Format Selection

The default selector prefers exact HD video plus audio:

- YouTube: exact requested height first, then lower heights.
- Bilibili: exact requested height first, then exact requested width. This
  handles vertical clips such as `1080x1920` for `--height 1080`.

If you need a specific format ID, bypass the selector:

```bash
yt-bili-hd download "URL" --format "136+140"
yt-bili-hd download "URL" --format "30080+30280"
```

## Cookies

Many HD formats require an authenticated account. Prefer browser cookies only
when needed:

```bash
yt-bili-hd download "URL" --cookies-from-browser chrome
```

You can also pass a manually exported cookies file:

```bash
yt-bili-hd download "URL" --cookies ./cookies.txt
```

Do not commit cookie files. `.gitignore` excludes common cookie filenames.

## Development

```bash
python -m unittest
python -m compileall src tests
```
