---
name: hd-video-download
description: Download and verify HD single videos from YouTube, Bilibili, Douyin, or Xiaohongshu; export available SRT and TXT subtitles; and open the platform output folder after success. Use when the user asks to save a supported video link, select a resolution, export subtitles, or troubleshoot a protected download.
---

# 高清视频下载

使用随附脚本调用统一下载 CLI：

```bash
scripts/download_video.sh download "VIDEO_URL" --height 1080
```

默认输出到 `~/Downloads/hd-video-downloads/<platform>/`。CLI 在下载后使用
`ffprobe` 验证媒体，并在 macOS 上自动打开对应 Finder 文件夹。

## 工作流

1. 默认处理单个视频；除非用户明确要求，不下载播放列表或主页全部内容。
2. 根据链接自动识别 YouTube、B站、抖音或小红书。抖音搜索和主页链接中的
   `modal_id` 会转换为单视频地址。
3. 用户指定清晰度时传入 `--height`；没有指定时使用 1080。
4. 只有在用户已明确授权读取浏览器登录信息后，才传入
   `--cookies-from-browser chrome`。不得复制、输出或提交 Cookie。
5. 下载成功后报告文件路径、实际分辨率和字幕路径。默认保留 CLI 自动打开
   Finder 的行为；用户明确要求不打开时传入 `--no-open`。

## 字幕

视频和字幕一起下载：

```bash
scripts/download_video.sh download "VIDEO_URL" --height 1080 --subtitles
```

只导出字幕：

```bash
scripts/download_video.sh subtitles "VIDEO_URL"
```

字幕命令导出平台提供的 SRT，并生成去除序号和时间码的 TXT。平台没有匹配
字幕时应明确说明；不要把“无字幕”误报为导出成功，也不要未经用户要求自动
调用第三方语音转写服务。

若平台没有独立字幕轨，而用户明确要求语音转写：仅在 `$lark-minutes` 可用且
用户已授权上传该媒体时，按飞书妙记流程提取逐字稿，再转换为 SRT/TXT；该能力
是可选外部集成，不是本 CLI 的默认能力。

## 验证与排障

- 运行 `scripts/download_video.sh doctor` 检查 `yt-dlp`、ffmpeg、Node 和
  YouTube PO Token 服务。
- 需要登录的高清格式使用已授权的 Chrome Cookie 后重试。
- YouTube 只显示图片或低清格式时，阅读
  [references/troubleshooting.md](references/troubleshooting.md)。
- 下载完成但未通过 `ffprobe` 验证时，不要打开文件夹或宣称成功。

只下载用户有权保存的内容，并遵守平台条款及当地法律。
