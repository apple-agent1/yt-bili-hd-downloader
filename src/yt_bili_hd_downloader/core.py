from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


MEDIA_EXTENSIONS = {".mp4", ".m4a", ".webm", ".mkv", ".mov"}
SUBTITLE_EXTENSIONS = {".srt"}
DEFAULT_SUBTITLE_LANGUAGES = "zh.*,zh-Hans,zh-Hant,zh,en.*"


@dataclass(frozen=True)
class DownloadResult:
    file: Path
    probe: dict | None
    subtitles: tuple[Path, ...] = ()
    text_subtitles: tuple[Path, ...] = ()


@dataclass(frozen=True)
class SubtitleResult:
    subtitles: tuple[Path, ...]
    text_subtitles: tuple[Path, ...]
    output_dir: Path


def detect_site(url: str) -> str:
    lowered = url.lower()
    if "youtube.com/" in lowered or "youtu.be/" in lowered:
        return "youtube"
    if "bilibili.com/" in lowered or "b23.tv/" in lowered:
        return "bilibili"
    if "douyin.com/" in lowered:
        return "douyin"
    if "xiaohongshu.com/" in lowered or "xhslink.com/" in lowered:
        return "xiaohongshu"
    return "generic"


def normalize_url(url: str, site: str) -> str:
    if site != "douyin":
        return url

    parsed = urllib.parse.urlparse(url)
    modal_id = urllib.parse.parse_qs(parsed.query).get("modal_id", [None])[0]
    if modal_id and modal_id.isdigit():
        return f"https://www.douyin.com/video/{modal_id}"
    return url


def platform_output_dir(output_root: Path, site: str) -> Path:
    return output_root.expanduser() / site


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
    write_subtitles: bool = False,
    subtitle_languages: str = DEFAULT_SUBTITLE_LANGUAGES,
    skip_download: bool = False,
) -> list[str]:
    if cookies and cookies_from_browser:
        raise ValueError("Use either --cookies or --cookies-from-browser, not both.")

    resolved_site = detect_site(url) if site == "auto" else site
    url = normalize_url(url, resolved_site)
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
    if not skip_download:
        command.append("--no-overwrites")
    if write_subtitles:
        command.extend(
            [
                "--write-subs",
                "--write-auto-subs",
                "--sub-langs",
                subtitle_languages,
                "--sub-format",
                "srt/best",
                "--convert-subs",
                "srt",
            ]
        )
    if skip_download:
        command.extend(["--skip-download", "--force-overwrites"])
    else:
        command.extend(["--print", "after_move:filepath"])
    command.extend(["--merge-output-format", "mp4"])
    command.extend(["-f", explicit_format or format_selector(resolved_site, height)])
    command.extend(["-o", output_template(output_dir, height)])
    command.append(url)
    return command


def run(command: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE if capture_output else None,
        text=capture_output,
    )


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


def changed_files(output_dir: Path, started_at: float, suffixes: set[str]) -> tuple[Path, ...]:
    if not output_dir.exists():
        return ()
    return tuple(
        sorted(
            (
                path
                for path in output_dir.iterdir()
                if path.is_file()
                and path.suffix.lower() in suffixes
                and path.stat().st_mtime >= started_at
            ),
            key=lambda path: path.name,
        )
    )


def srt_to_txt(path: Path) -> Path:
    timestamp = re.compile(r"^\s*\d{2}:\d{2}:\d{2}[,.]\d{3}\s+-->\s+")
    tag = re.compile(r"<[^>]+>")
    lines: list[str] = []

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.isdigit() or timestamp.match(line):
            continue
        line = tag.sub("", line).strip()
        if line and (not lines or line != lines[-1]):
            lines.append(line)

    output = path.with_suffix(".txt")
    output.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return output


def media_path_from_output(stdout: str) -> Path | None:
    for line in reversed(stdout.splitlines()):
        candidate = Path(line.strip()).expanduser()
        if candidate.suffix.lower() in MEDIA_EXTENSIONS and candidate.exists():
            return candidate
    return None


def open_output_folder(path: Path) -> bool:
    if sys.platform != "darwin" or not shutil.which("open"):
        return False
    subprocess.run(["open", str(path)], check=False)
    return True


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
    output_root: Path,
    height: int,
    site: str,
    explicit_format: str | None,
    cookies_from_browser: str | None,
    cookies: Path | None,
    node_path: str | None,
    verify: bool,
    print_command: bool,
    subtitles: bool = False,
    subtitle_languages: str = DEFAULT_SUBTITLE_LANGUAGES,
    open_folder: bool = True,
) -> DownloadResult:
    started_at = time.time() - 1
    resolved_site = detect_site(url) if site == "auto" else site
    output_dir = platform_output_dir(output_root, resolved_site)
    command = build_ytdlp_command(
        url,
        output_dir=output_dir,
        height=height,
        site=resolved_site,
        explicit_format=explicit_format,
        cookies_from_browser=cookies_from_browser,
        cookies=cookies,
        node_path=node_path,
    )

    if print_command:
        print(" ".join(command))
    completed = run(command, capture_output=True)
    media_file = media_path_from_output(completed.stdout)

    if not media_file:
        media_file = newest_media_file(output_dir, started_at)
    if not media_file:
        raise RuntimeError(f"Download finished, but no media file was found in {output_dir}.")

    probe = probe_media(media_file) if verify else None
    subtitle_result = None
    if subtitles:
        subtitle_result = export_subtitles(
            url,
            output_root=output_root,
            site=resolved_site,
            cookies_from_browser=cookies_from_browser,
            cookies=cookies,
            node_path=node_path,
            subtitle_languages=subtitle_languages,
            open_folder=False,
        )

    if open_folder:
        open_output_folder(output_dir)

    return DownloadResult(
        file=media_file,
        probe=probe,
        subtitles=subtitle_result.subtitles if subtitle_result else (),
        text_subtitles=subtitle_result.text_subtitles if subtitle_result else (),
    )


def export_subtitles(
    url: str,
    *,
    output_root: Path,
    site: str,
    cookies_from_browser: str | None,
    cookies: Path | None,
    node_path: str | None,
    subtitle_languages: str = DEFAULT_SUBTITLE_LANGUAGES,
    open_folder: bool = True,
) -> SubtitleResult:
    started_at = time.time() - 1
    resolved_site = detect_site(url) if site == "auto" else site
    output_dir = platform_output_dir(output_root, resolved_site)
    command = build_ytdlp_command(
        url,
        output_dir=output_dir,
        site=resolved_site,
        cookies_from_browser=cookies_from_browser,
        cookies=cookies,
        node_path=node_path,
        write_subtitles=True,
        subtitle_languages=subtitle_languages,
        skip_download=True,
    )
    run(command)

    subtitle_files = changed_files(output_dir, started_at, SUBTITLE_EXTENSIONS)
    if not subtitle_files:
        raise RuntimeError(
            "The platform did not provide matching subtitles. "
            "Audio transcription is not performed automatically."
        )
    text_files = tuple(srt_to_txt(path) for path in subtitle_files)

    if open_folder:
        open_output_folder(output_dir)
    return SubtitleResult(subtitle_files, text_files, output_dir)


def youtube_pot_status() -> tuple[bool, str]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:4416/ping", timeout=2) as response:
            body = response.read().decode("utf-8", errors="replace")
        return True, body
    except (OSError, urllib.error.URLError) as exc:
        return False, str(exc)


def doctor() -> dict[str, object]:
    pot_ok, pot_detail = youtube_pot_status()
    yt_dlp = importlib.util.find_spec("yt_dlp")
    return {
        "python": sys.executable,
        "yt_dlp": yt_dlp.origin if yt_dlp else None,
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
        "node": find_node(),
        "youtube_pot_provider": {"ok": pot_ok, "detail": pot_detail},
    }
