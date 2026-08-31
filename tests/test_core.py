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
    youtube_format_selector,
)


class CoreTest(unittest.TestCase):
    def test_detect_site(self) -> None:
        self.assertEqual(detect_site("https://youtu.be/abc"), "youtube")
        self.assertEqual(detect_site("https://www.youtube.com/watch?v=abc"), "youtube")
        self.assertEqual(detect_site("https://www.bilibili.com/video/BV123"), "bilibili")
        self.assertEqual(detect_site("https://example.com/video"), "generic")

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
