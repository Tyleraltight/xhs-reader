---
name: xhs-reader
description: |
  读取小红书（Xiaohongshu）笔记内容。自动识别笔记类型（纯文字、图文、视频）并分配最佳抓取流程：纯文字走网页解析，图文自动下载图片并调用 Vision 看图，视频通过 yt-dlp 结合 ffmpeg 抽帧分析，且在完成后自动清理视频文件避免磁盘占用。
  触发词：小红书、读取小红书、小红书视频、小红书图文、小红书链接等。
---

# 小红书内容读取技能 (xhs-reader)

一键读取小红书笔记，自动识别文字、图文、视频内容并执行相应提取管道。

## 三条自动化流程

1. **纯文字笔记**：`curl` 抓取 HTML 提取 `__INITIAL_STATE__`，极速响应（<3秒）
2. **图文笔记**：下载多张高清配图，结合 Vision 模型逐张解析
3. **视频笔记**：`yt-dlp` 下载 → `ffmpeg` 均匀抽帧 → Vision 模型看关键帧 → **自动删除临时视频**

## 命令行用法

```bash
# 自动检测模式
python xhs_fetch.py "https://www.xiaohongshu.com/discovery/item/xxxxx"

# JSON 格式输出
python xhs_fetch.py "<链接>" --json

# 视频模式强制指定抽帧数
python xhs_fetch.py "<链接>" --mode video --frames 5
```

## Cookie 配置

对于公开笔记无需 Cookie。如需抓取特定需登录内容：

```bash
python xhs_fetch.py "<链接>" --cookies /path/to/cookies.txt
```
