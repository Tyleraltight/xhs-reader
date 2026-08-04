# xhs-reader

> 链接一丢，小红书图文/视频/纯文字笔记全自动抓取与解析，自动抽帧并清理临时文件。
> Auto-detect and parse Xiaohongshu (Rednote) posts: text, images with vision analysis, and videos with automatic frame extraction and auto-cleanup.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/Tyleraltight/xhs-reader?style=flat-square)](https://github.com/Tyleraltight/xhs-reader/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Tyleraltight/xhs-reader?style=flat-square)](https://github.com/Tyleraltight/xhs-reader/network/members)
[![Last Commit](https://img.shields.io/github/last-commit/Tyleraltight/xhs-reader?style=flat-square)](https://github.com/Tyleraltight/xhs-reader/commits/main)

**[中文](#中文) | [English](#english)**

---

<a name="中文"></a>
## 中文

### 💡 核心亮点

- ⚡ **纯文字极速抓取**：轻量解析网页状态，3 秒内提取正文与标签
- 🖼️ **图文多图深度看图**：自动下载博主配图，结合 Vision 模型逐张阅读
- 🎬 **视频自动抽帧与防积压**：`yt-dlp` + `ffmpeg` 均匀抽帧分析，任务结束后自动清除临时视频
- 🔑 **无缝 Cookie 挂载**：支持传入 Netscape 格式 Cookie 解析私密/受限笔记

### 📦 一键安装

```bash
npx skills add Tyleraltight/xhs-reader
```

### 📋 前置条件

- [ ] Python 3.8+ 已安装 (`python3 --version`)
- [ ] 已安装 `yt-dlp` (`pip install yt-dlp`)
- [ ] 系统中已安装 `ffmpeg` (`ffmpeg -version`)

### 💬 自然语言使用示例

在 Agent 对话界面中输入：

- 📱 `"帮我读取这条小红书笔记：https://www.xiaohongshu.com/discovery/item/xxxx"`
- 🎬 `"分析一下这个小红书视频讲了什么教程"`
- 🖼️ `"提取这个小红书穿搭笔记里的图片和文字"`

### ❓ 常见问题 (Troubleshooting)

| 问题现象 | 可能原因 | 解决办法 |
|---------|---------|---------|
| 视频模式报错或无法下载 | `yt-dlp` 版本过旧或缺失 `ffmpeg` | 运行 `pip install -U yt-dlp` 升级，并确认 `ffmpeg` 可在命令行执行 |
| 提示链接失效或需登录 | 链接包含的时效性 `xsec_token` 已过期 | 在小红书 App 或网页端重新复制最新的分享链接 |
| 磁盘空间增长 | 异常中断导致临时视频未删除 | 运行命令清理：`rm -rf ~/generated/xhs/* /tmp/xhs_*` |

---

<a name="english"></a>
## English

### 💡 Features

- ⚡ **Fast Text Extraction**: Instant parsing under 3 seconds.
- 🖼️ **Image Post Support**: Download images and process via Vision LLM.
- 🎬 **Video Pipelines**: `yt-dlp` download → `ffmpeg` frame extraction → Auto-delete video file to save disk space.

### 📦 Installation

```bash
npx skills add Tyleraltight/xhs-reader
```
