from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


MEDIA_EXTENSIONS = {".mp4", ".m4a", ".webm", ".mkv", ".mov"}


@dataclass(frozen=True)
class DownloadResult:
    file: Path
    probe: dict | None


def detect_site(url: str) -> str:
    lowered = url.lower()
    if "youtube.com/" in lowered or "youtu.be/" in lowered:
        return "youtube"
    if "bilibili.com/" in lowered or "b23.tv/" in lowered:
        return "bilibili"
    return "generic"


def find_node() -> str | None:
    return shutil.which("node")


def youtube_format_selector(height: int) -> str:
    return (
        f"bestvideo[height={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height={height}]+bestaudio/"
        f"best[height={height}]/"
        f"best[height<={height}]"
    )


def bilibili_format_selector(height: int) -> str:
    # Vertical Bilibili clips report as width=1080,height=1920.
    return (
        f"bestvideo[vcodec^=avc1][height={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[vcodec^=avc1][width={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[width={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"best[height<={height}]/"
        "best"
    )


def format_selector(site: str, height: int) -> str:
    if site == "youtube":
        return youtube_format_selector(height)
    if site == "bilibili":
        return bilibili_format_selector(height)
    return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"


def output_template(output_dir: Path, height: int) -> str:
    return str(output_dir / f"%(title).180B [%(id)s] {height}p.%(ext)s")


def build_ytdlp_command(
    url: str,
    *,
    output_dir: Path = Path("downloads"),
    height: int = 1080,
    site: str = "auto",
    explicit_format: str | None = None,
    cookies_from_browser: str | None = None,
    cookies: Path | None = None,
    list_formats: bool = False,
    node_path: str | None = None,
) -> list[str]:
    if cookies and cookies_from_browser:
        raise ValueError("Use either --cookies or --cookies-from-browser, not both.")

    resolved_site = detect_site(url) if site == "auto" else site
    command = [sys.executable, "-m", "yt_dlp", "--no-playlist"]

    if resolved_site == "youtube":
        node = node_path or find_node()
        if node:
            command.extend(["--js-runtimes", f"node:{node}"])
        command.extend(["--extractor-args", "youtube:player_client=mweb,web"])

    if cookies_from_browser:
        command.extend(["--cookies-from-browser", cookies_from_browser])
    if cookies:
        command.extend(["--cookies", str(cookies)])

    if list_formats:
        command.extend(["-F", url])
        return command

    output_dir.mkdir(parents=True, exist_ok=True)
    command.extend(["--merge-output-format", "mp4"])
    command.extend(["-f", explicit_format or format_selector(resolved_site, height)])
    command.extend(["-o", output_template(output_dir, height)])
    command.append(url)
    return command


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def newest_media_file(output_dir: Path, started_at: float) -> Path | None:
    if not output_dir.exists():
        return None
    candidates = [
        path
        for path in output_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in MEDIA_EXTENSIONS
        and path.stat().st_mtime >= started_at
        and not path.name.endswith(".part")
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def probe_media(path: Path) -> dict:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe was not found. Install ffmpeg or use --no-verify.")

    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_entries",
            "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def download(
    url: str,
    *,
    output_dir: Path,
    height: int,
    site: str,
    explicit_format: str | None,
    cookies_from_browser: str | None,
    cookies: Path | None,
    node_path: str | None,
    verify: bool,
    print_command: bool,
) -> DownloadResult:
    started_at = time.time() - 1
    command = build_ytdlp_command(
        url,
        output_dir=output_dir,
        height=height,
        site=site,
        explicit_format=explicit_format,
        cookies_from_browser=cookies_from_browser,
        cookies=cookies,
        node_path=node_path,
    )

    if print_command:
        print(" ".join(command))
    run(command)

    media_file = newest_media_file(output_dir, started_at)
    if not media_file:
        raise RuntimeError(f"Download finished, but no media file was found in {output_dir}.")

    probe = probe_media(media_file) if verify else None
    return DownloadResult(file=media_file, probe=probe)


def youtube_pot_status() -> tuple[bool, str]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:4416/ping", timeout=2) as response:
            body = response.read().decode("utf-8", errors="replace")
        return True, body
    except (OSError, urllib.error.URLError) as exc:
        return False, str(exc)


def doctor() -> dict[str, object]:
    pot_ok, pot_detail = youtube_pot_status()
    return {
        "python": sys.executable,
        "yt_dlp": "installed in this environment",
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "node": find_node(),
        "youtube_pot_provider": {"ok": pot_ok, "detail": pot_detail},
    }
