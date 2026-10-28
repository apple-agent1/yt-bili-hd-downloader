# Troubleshooting

## Authentication failures

B站、抖音和小红书的高清地址可能要求登录。获得用户授权后增加：

```bash
--cookies-from-browser chrome
```

若 Chrome 正在锁定 Cookie 数据库，可关闭多余窗口后重试，或使用用户提供的
Netscape 格式 Cookie 文件。不要导出或提交用户 Cookie。

## Douyin search or profile URLs

带 `modal_id` 的抖音搜索、精选或用户主页链接会自动转换为：

```text
https://www.douyin.com/video/<modal_id>
```

没有 `modal_id` 的页面不是明确的单视频链接，应请用户提供具体视频链接。

## No subtitles were exported

字幕导出仅处理平台暴露给 `yt-dlp` 的人工或自动字幕。部分抖音、小红书视频
只有画面内字幕，没有独立字幕轨，因此无法直接导出 SRT。此时应说明没有可用
字幕；语音识别属于额外流程。

## YouTube only lists images or low resolution

可能缺少 PO Token 或 JavaScript challenge 运行环境：

1. 确认 Node.js 已安装。
2. 确认当前环境使用新版 `yt-dlp[default]`。
3. 在项目根目录运行 `scripts/start-youtube-pot-provider.sh`。
4. 本地代理供 Docker 使用时，将回环地址改为 `host.docker.internal`。

检查服务：

```bash
curl -fsS http://127.0.0.1:4416/ping
```

## Verification

CLI 会在视频下载后调用 `ffprobe`。缺少 ffmpeg 时，在 macOS 上运行：

```bash
brew install ffmpeg
```
