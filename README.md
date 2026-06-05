# 🍜 xhs-reader

小红书内容抓取工具 — 自动识别文字/图文/视频，一键读取。

## 🚀 快速开始

```bash
# 安装依赖
pip install yt-dlp

# 确保 ffmpeg 已安装
ffmpeg -version

# 运行
python xhs_fetch.py "https://www.xiaohongshu.com/discovery/item/xxxxx"
```

## 📋 三条流程

| 类型 | 自动流程 | 说明 |
|------|---------|------|
| 📝 纯文字 | curl 抓取 HTML → 解析 `__INITIAL_STATE__` | 最快，3秒完成 |
| 🖼️ 图文 | 下载图片 → 可配合 vision 模型看图 | 美食、穿搭、旅行照等 |
| 🎬 视频 | yt-dlp 下载 → ffmpeg 抽帧 → 可配合 vision 看帧 → **自动删除视频** | 避免磁盘堆积 |

## 🛠️ 使用方法

### 基础用法
```bash
# 自动检测内容类型
python xhs_fetch.py "<小红书链接>"

# JSON 格式输出
python xhs_fetch.py "<小红书链接>" --json
```

### 指定模式
```bash
# 强制按视频模式处理
python xhs_fetch.py "<链接>" --mode video --frames 5

# 强制按图文模式处理
python xhs_fetch.py "<链接>" --mode image
```

### 批量处理
```bash
# 并行处理多条链接
python xhs_fetch.py "<url1>" --json > out1.json &
python xhs_fetch.py "<url2>" --json > out2.json &
wait
```

## 📦 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 小红书笔记 URL | 必填 |
| `--mode` | auto / text / image / video | auto |
| `--frames` | 视频抽帧数 | 5 |
| `--outdir` | 输出目录 | ~/generated/xhs |
| `--cookies` | Cookie 文件路径 | 无 |
| `--json` | JSON 格式输出 | 否 |

## 🔑 Cookie 配置

公开内容不需要 Cookie。如需访问需要登录的内容：

1. 从浏览器导出 Cookie（Netscape 格式）
2. 传入 `--cookies /path/to/cookies.txt`

## ⚙️ 依赖

- Python 3.8+
- `yt-dlp`（视频下载）
- `ffmpeg` / `ffprobe`（视频抽帧）
- `curl`（HTML 抓取）

## 📁 项目结构

```
xhs-reader/
├── xhs_fetch.py    # 核心脚本
├── SKILL.md        # Hermes Agent Skill 定义
└── README.md
```

## 📄 License

MIT
