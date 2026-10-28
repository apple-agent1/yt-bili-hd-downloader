from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import (
    DEFAULT_SUBTITLE_LANGUAGES,
    build_ytdlp_command,
    doctor,
    download,
    export_subtitles,
)


DEFAULT_OUTPUT_ROOT = Path.home() / "Downloads" / "hd-video-downloads"
SITE_CHOICES = ["auto", "youtube", "bilibili", "douyin", "xiaohongshu", "generic"]


def add_auth_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--cookies-from-browser",
        metavar="BROWSER",
        help="Pass browser cookies to yt-dlp, for example: chrome.",
    )
    parser.add_argument(
        "--cookies",
        type=Path,
        help="Path to a Netscape-format cookies file.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hd-video-download",
        description="Download HD single videos and subtitles from supported platforms.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser("download", help="Download and verify a video.")
    download_parser.add_argument("url")
    download_parser.add_argument("--height", type=int, default=1080)
    download_parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help=f"Output root; a platform folder is added. Default: {DEFAULT_OUTPUT_ROOT}.",
    )
    download_parser.add_argument(
        "--site",
        choices=SITE_CHOICES,
        default="auto",
    )
    download_parser.add_argument(
        "--format",
        dest="explicit_format",
        help="Use an explicit yt-dlp format selector or format IDs.",
    )
    download_parser.add_argument("--node", help="Node.js path for YouTube JS challenges.")
    download_parser.add_argument("--no-verify", action="store_true", help="Skip ffprobe.")
    download_parser.add_argument(
        "--subtitles",
        action="store_true",
        help="Also export available subtitles as SRT and TXT.",
    )
    download_parser.add_argument(
        "--sub-langs",
        default=DEFAULT_SUBTITLE_LANGUAGES,
        help="yt-dlp subtitle language selector.",
    )
    download_parser.add_argument("--no-open", action="store_true", help="Do not open Finder.")
    download_parser.add_argument("--print-command", action="store_true")
    add_auth_args(download_parser)

    formats_parser = subparsers.add_parser("formats", help="List available formats.")
    formats_parser.add_argument("url")
    formats_parser.add_argument(
        "--site",
        choices=SITE_CHOICES,
        default="auto",
    )
    formats_parser.add_argument("--node", help="Node.js path for YouTube JS challenges.")
    add_auth_args(formats_parser)

    subtitles_parser = subparsers.add_parser(
        "subtitles", help="Export available subtitles as SRT and TXT without video."
    )
    subtitles_parser.add_argument("url")
    subtitles_parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help=f"Output root; a platform folder is added. Default: {DEFAULT_OUTPUT_ROOT}.",
    )
    subtitles_parser.add_argument("--site", choices=SITE_CHOICES, default="auto")
    subtitles_parser.add_argument("--node", help="Node.js path for YouTube JS challenges.")
    subtitles_parser.add_argument(
        "--sub-langs",
        default=DEFAULT_SUBTITLE_LANGUAGES,
        help="yt-dlp subtitle language selector.",
    )
    subtitles_parser.add_argument("--no-open", action="store_true", help="Do not open Finder.")
    add_auth_args(subtitles_parser)

    doctor_parser = subparsers.add_parser("doctor", help="Check local dependencies.")
    doctor_parser.add_argument("--json", action="store_true")

    return parser


def print_probe_summary(probe: dict) -> None:
    print("Probe:")
    for stream in probe.get("streams", []):
        fields = [
            f"index={stream.get('index')}",
            f"type={stream.get('codec_type')}",
            f"codec={stream.get('codec_name')}",
        ]
        if stream.get("width") and stream.get("height"):
            fields.append(f"size={stream['width']}x{stream['height']}")
        if stream.get("r_frame_rate"):
            fields.append(f"fps={stream['r_frame_rate']}")
        print("  " + " ".join(fields))

    fmt = probe.get("format", {})
    if fmt:
        print(f"  duration={fmt.get('duration')} size={fmt.get('size')}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "formats":
        command = build_ytdlp_command(
            args.url,
            site=args.site,
            cookies_from_browser=args.cookies_from_browser,
            cookies=args.cookies,
            list_formats=True,
            node_path=args.node,
        )
        from .core import run

        run(command)
        return 0

    if args.command == "doctor":
        result = doctor()
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            for key, value in result.items():
                print(f"{key}: {value}")
        return 0

    if args.command == "subtitles":
        result = export_subtitles(
            args.url,
            output_root=args.output_dir,
            site=args.site,
            cookies_from_browser=args.cookies_from_browser,
            cookies=args.cookies,
            node_path=args.node,
            subtitle_languages=args.sub_langs,
            open_folder=not args.no_open,
        )
        for path in result.subtitles:
            print(f"Subtitle: {path}")
        for path in result.text_subtitles:
            print(f"Text: {path}")
        return 0

    if args.command == "download":
        result = download(
            args.url,
            output_root=args.output_dir,
            height=args.height,
            site=args.site,
            explicit_format=args.explicit_format,
            cookies_from_browser=args.cookies_from_browser,
            cookies=args.cookies,
            node_path=args.node,
            verify=not args.no_verify,
            print_command=args.print_command,
            subtitles=args.subtitles,
            subtitle_languages=args.sub_langs,
            open_folder=not args.no_open,
        )
        print(f"Downloaded: {result.file}")
        if result.probe:
            print_probe_summary(result.probe)
        for path in result.subtitles:
            print(f"Subtitle: {path}")
        for path in result.text_subtitles:
            print(f"Text: {path}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
