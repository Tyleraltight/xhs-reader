---
name: xhs-reader
description: "Use when reading Xiaohongshu (小红书) links. Auto-detects content type (text/image/video) and runs the right pipeline. Text→web_extract, Image→download+vision, Video→yt-dlp+ffmpeg+vision+cleanup."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [xiaohongshu, 小红书, social-media, video, image, scraper]
    related_skills: []
---

# 小红书内容读取 (xhs-reader)

一键读取小红书笔记，自动检测内容类型并执行对应流程。

## 三条流程

### 流程 1：纯文字笔记
```
web_extract(url) → 解析文本 → 输出摘要
```
最快，3 秒完成。

### 流程 2：图文笔记
```
web_extract(url) → 解析文本 + 下载图片 → vision_analyze 逐张看图 → 输出完整内容
```
需要看图片才能理解的帖子（美食、穿搭、旅行照等）。

### 浺程 3：视频笔记
```
web_extract(url) → 解析文本
yt-dlp 下载视频 → ffmpeg 按时长均匀抽帧 → vision_analyze 看帧 → ⚠️ 删除临时视频 → 输出完整内容
```
视频下载后必须清理，避免磁盘堆积。

## 使用方法

### 方式 A：脚本（推荐批量处理）
```bash
# 自动检测类型
python ~/hermes/scripts/xhs_fetch.py "<url>" --json

# 指定模式
python ~/hermes/scripts/xhs_fetch.py "<url>" --mode video --frames 5

# 批量（多条 URL 并行）
python ~/hermes/scripts/xhs_fetch.py "<url1>" --json &
python ~/hermes/scripts/xhs_fetch.py "<url2>" --json &
wait
```

### 方式 B：手动调用（适合单条）

**纯文字：**
```
web_extract(urls=[url]) → 我直接整理输出
```

**图文：**
```
1. web_extract(urls=[url]) → 拿文字 + 图片 URL
2. vision_analyze(image_url, question="这张图在展示什么") → 逐张分析
3. 整合输出
```

**视频：**
```
1. terminal: yt-dlp -o /tmp/xhs_video.mp4 "<url>"
2. terminal: ffmpeg -i /tmp/xhs_video.mp4 -vf "fps=1" /tmp/frame_%03d.jpg
3. vision_analyze(frame_N.jpg, "这一帧在展示什么") → 看关键帧
4. terminal: rm /tmp/xhs_video.mp4  ← 必须清理！
5. 整合输出
```

## 脚本参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--mode` | auto / text / image / video | auto（自动检测）|
| `--frames` | 视频抽帧数 | 5 |
| `--outdir` | 输出目录 | ~/generated/xhs |
| `--cookies` | Cookie 文件路径 | 无 |
| `--json` | JSON 格式输出 | 否 |

## 内容类型检测规则

- `note.type == 'video'` 或有 `video_url` → **视频**
- 有 `imageList` → **图文**
- 都没有 → **纯文字**

## 视频抽帧策略

- 获取视频总时长（ffprobe）
- 按 `时长 / 帧数` 计算间隔，均匀抽帧
- 最小间隔 0.5 秒（防止过密）
- 默认抽 5 帧（短视频可减到 3，长视频可增到 10）

## Cookie 配置

小红书公开内容不需要 Cookie。如果遇到需要登录的内容：
1. 导出 Chrome Cookie 到 Netscape 格式文件
2. 用 `--cookies /path/to/cookies.txt` 传入脚本

已有 Cookie 保存在 `~/.hermes/cookies/xiaohongshu.json`（JSON 格式），
需转换为 Netscape 格式才能给 yt-dlp/curl 用。

## Common Pitfalls

1. **视频下载后忘记删除** → 脚本已内置自动清理，手动流程务必 `rm` 临时视频
2. **yt-dlp 提取失败** → 脚本会 fallback 到从 __INITIAL_STATE__ 直接拿 video URL
3. **xsec_token 过期** → 分享链接带的 token 有时效，过期后需重新获取
4. **抽帧太多导致 vision 分析慢** → 建议 3-5 帧，够用就行

## Verification

- [ ] 文字笔记能正确提取标题、正文、标签
- [ ] 图片笔记能下载图片并通过 vision 看到内容
- [ ] 视频笔记能抽帧并通过 vision 理解视频内容
- [ ] 视频文件在抽帧后被正确删除
- [ ] 临时文件不堆积在 /tmp 或 outdir
