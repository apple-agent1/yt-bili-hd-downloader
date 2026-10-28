from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yt_bili_hd_downloader.core import (  # noqa: E402
    bilibili_format_selector,
    build_ytdlp_command,
    detect_site,
    newest_media_file,
    normalize_url,
    platform_output_dir,
    srt_to_txt,
    youtube_format_selector,
)


class CoreTest(unittest.TestCase):
    def test_detect_site(self) -> None:
        self.assertEqual(detect_site("https://youtu.be/abc"), "youtube")
        self.assertEqual(detect_site("https://www.youtube.com/watch?v=abc"), "youtube")
        self.assertEqual(detect_site("https://www.bilibili.com/video/BV123"), "bilibili")
        self.assertEqual(detect_site("https://www.douyin.com/video/123"), "douyin")
        self.assertEqual(
            detect_site("https://www.xiaohongshu.com/explore/abc"), "xiaohongshu"
        )
        self.assertEqual(detect_site("https://example.com/video"), "generic")

    def test_normalize_douyin_modal_url(self) -> None:
        url = "https://www.douyin.com/search/example?modal_id=7691214267206405391&type=general"
        self.assertEqual(
            normalize_url(url, "douyin"),
            "https://www.douyin.com/video/7691214267206405391",
        )

    def test_platform_output_dir(self) -> None:
        self.assertEqual(
            platform_output_dir(Path("~/Downloads/videos"), "bilibili"),
            Path.home() / "Downloads" / "videos" / "bilibili",
        )

    def test_youtube_selector_prefers_exact_height(self) -> None:
        selector = youtube_format_selector(720)
        self.assertIn("bestvideo[height=720][ext=mp4]+bestaudio[ext=m4a]", selector)
        self.assertIn("best[height<=720]", selector)

    def test_bilibili_selector_handles_vertical_1080p(self) -> None:
        selector = bilibili_format_selector(1080)
        self.assertIn("width=1080", selector)
        self.assertIn("height=1080", selector)
        self.assertIn("vcodec^=avc1", selector)

    def test_command_does_not_use_cookies_by_default(self) -> None:
        command = build_ytdlp_command("https://www.bilibili.com/video/BV123/")
        self.assertNotIn("--cookies-from-browser", command)
        self.assertNotIn("--cookies", command)

    def test_command_accepts_browser_cookies(self) -> None:
        command = build_ytdlp_command(
            "https://www.bilibili.com/video/BV123/",
            cookies_from_browser="chrome",
        )
        self.assertIn("--cookies-from-browser", command)
        self.assertIn("chrome", command)

    def test_subtitle_command_writes_srt_without_media(self) -> None:
        command = build_ytdlp_command(
            "https://www.youtube.com/watch?v=abc",
            write_subtitles=True,
            skip_download=True,
        )
        self.assertIn("--write-subs", command)
        self.assertIn("--write-auto-subs", command)
        self.assertIn("--convert-subs", command)
        self.assertIn("--skip-download", command)
        self.assertNotIn("--no-overwrites", command)

    def test_srt_to_txt_removes_timing_and_duplicate_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subtitle = Path(tmp) / "example.srt"
            subtitle.write_text(
                "1\n00:00:00,000 --> 00:00:01,000\n你好\n\n"
                "2\n00:00:01,000 --> 00:00:02,000\n你好\n世界\n",
                encoding="utf-8",
            )
            text_file = srt_to_txt(subtitle)
            self.assertEqual(text_file.read_text(encoding="utf-8"), "你好\n世界\n")

    def test_newest_media_file_uses_started_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            old_file = output_dir / "old.mp4"
            new_file = output_dir / "new.mp4"
            old_file.write_text("old")
            started_at = time.time()
            time.sleep(0.01)
            new_file.write_text("new")
            self.assertEqual(newest_media_file(output_dir, started_at), new_file)


if __name__ == "__main__":
    unittest.main()
