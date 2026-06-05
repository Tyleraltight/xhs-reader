#!/usr/bin/env python3
"""
小红书内容抓取工具
支持三种模式：纯文字 / 图片帖子 / 视频帖子

用法:
    python xhs_fetch.py <url> [--mode auto|text|image|video] [--frames 5] [--outdir ./output]
"""

import subprocess, sys, os, json, re, shutil, tempfile, argparse
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

# ---------- 配置 ----------
DEFAULT_FRAMES = 5          # 视频默认抽帧数
DEFAULT_OUTDIR = Path(os.path.expanduser("~/generated/xhs"))
COOKIE_FILE = None           # 如果有 cookie 文件可以传入
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def log(msg):
    print(f"[xhs] {msg}", file=sys.stderr)


def extract_note_id(url: str) -> str:
    """从 URL 提取笔记 ID"""
    # /discovery/item/<id> 或 /explore/<id>
    m = re.search(r'/(?:discovery/item|explore)/([a-f0-9]+)', url)
    if m:
        return m.group(1)
    # 尝试从 URL path 最后一段提取
    path = urlparse(url).path
    parts = path.strip('/').split('/')
    if parts and re.match(r'^[a-f0-9]{24}$', parts[-1]):
        return parts[-1]
    return ""


def build_full_url(url: str) -> str:
    """确保 URL 带 xsec_token"""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if 'xsec_token' not in qs:
        return url
    return unquote(url)


def fetch_page_text(url: str) -> str:
    """用 curl 抓取页面 HTML"""
    cookie_args = []
    if COOKIE_FILE and os.path.exists(COOKIE_FILE):
        cookie_args = ["-b", COOKIE_FILE]

    result = subprocess.run(
        ["curl", "-sL", "--max-time", "15",
         "-H", f"User-Agent: {USER_AGENT}",
         "-H", "Accept: text/html",
         "-H", "Referer: https://www.xiaohongshu.com/"]
        + cookie_args + [build_full_url(url)],
        capture_output=True, text=True, timeout=20
    )
    return result.stdout


def parse_initial_state(html: str) -> dict:
    """从 __INITIAL_STATE__ 提取笔记数据"""
    m = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*;?\s*</script>', html, re.DOTALL)
    if not m:
        return {}
    raw = m.group(1).replace('undefined', 'null')
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def extract_note_info(state: dict) -> dict:
    """从 initial state 提取笔记信息"""
    note_map = state.get('note', {}).get('noteDetailMap', {})
    for note_id, note_data in note_map.items():
        n = note_data.get('note', {})
        info = {
            'id': note_id,
            'title': n.get('title', ''),
            'desc': n.get('desc', ''),
            'type': n.get('type', ''),  # 'normal' (图文) or 'video'
            'user': n.get('user', {}).get('nickname', ''),
            'likes': n.get('interactInfo', {}).get('likedCount', ''),
            'comments': n.get('interactInfo', {}).get('commentCount', ''),
            'tags': [t.get('name', '') for t in n.get('tagList', [])],
            'images': [],
            'video_url': None,
        }

        # 提取图片 URL
        image_list = n.get('imageList', [])
        for img in image_list:
            # 优先拿最大尺寸
            urls = img.get('urlDefault', '') or img.get('url', '')
            if urls:
                info['images'].append(urls)

        # 提取视频 URL
        video = n.get('video', {})
        media = video.get('media', {})
        stream = media.get('stream', {})
        # 尝试各种视频 URL 路径
        for quality in ['h264', 'h265', 'av1']:
            videos = stream.get(quality, [])
            if videos:
                best = max(videos, key=lambda v: v.get('videoBitrate', 0))
                info['video_url'] = best.get('masterUrl', '')
                if info['video_url']:
                    break
        # fallback
        if not info['video_url']:
            info['video_url'] = video.get('consumer', {}).get('originVideoKey', '')

        return info
    return {}


def detect_content_type(info: dict) -> str:
    """检测内容类型: text / image / video"""
    if info.get('type') == 'video' or info.get('video_url'):
        return 'video'
    if info.get('images'):
        return 'image'
    return 'text'


# ---------- 三种抓取模式 ----------

def fetch_text(info: dict) -> dict:
    """模式1: 纯文字"""
    return {
        'mode': 'text',
        'title': info['title'],
        'author': info['user'],
        'content': info['desc'],
        'tags': info['tags'],
        'likes': info['likes'],
        'comments': info['comments'],
    }


def fetch_images(info: dict, outdir: Path) -> dict:
    """模式2: 图片帖子 — 下载图片"""
    outdir.mkdir(parents=True, exist_ok=True)
    img_paths = []
    for i, url in enumerate(info['images'][:9]):  # 最多9张
        path = outdir / f"image_{i+1:03d}.jpg"
        subprocess.run(
            ["curl", "-sL", "--max-time", "10", "-o", str(path), url],
            capture_output=True, timeout=15
        )
        if path.exists() and path.stat().st_size > 0:
            img_paths.append(str(path))
            log(f"  下载图片 {i+1}: {path.name}")

    return {
        'mode': 'image',
        'title': info['title'],
        'author': info['user'],
        'content': info['desc'],
        'tags': info['tags'],
        'likes': info['likes'],
        'comments': info['comments'],
        'image_paths': img_paths,
        'image_count': len(img_paths),
    }


def fetch_video(info: dict, outdir: Path, num_frames: int = DEFAULT_FRAMES) -> dict:
    """模式3: 视频帖子 — 下载→抽帧→分析→删除视频"""
    outdir.mkdir(parents=True, exist_ok=True)
    video_path = outdir / "temp_video.mp4"
    frames_dir = outdir / "frames"
    frames_dir.mkdir(exist_ok=True)

    # 1. 下载视频
    video_url = info.get('video_url', '')
    if not video_url:
        # fallback: 用 yt-dlp
        log("  视频 URL 未找到，尝试 yt-dlp...")
        ytdlp_cmd = ["yt-dlp", "-o", str(video_path), "--no-check-certificates"]
        if COOKIE_FILE and os.path.exists(COOKIE_FILE):
            ytdlp_cmd += ["--cookies", COOKIE_FILE]
        ytdlp_cmd.append(f"https://www.xiaohongshu.com/explore/{info['id']}")
        subprocess.run(ytdlp_cmd, capture_output=True, timeout=60)
    else:
        log(f"  下载视频...")
        subprocess.run(
            ["curl", "-sL", "--max-time", "30", "-o", str(video_path), video_url],
            capture_output=True, timeout=35
        )

    if not video_path.exists() or video_path.stat().st_size == 0:
        return {'mode': 'video', 'error': '视频下载失败', **fetch_text(info)}

    # 2. 获取视频时长，计算抽帧间隔
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(video_path)],
        capture_output=True, text=True, timeout=10
    )
    try:
        duration = float(json.loads(probe.stdout)['format']['duration'])
    except:
        duration = 10.0

    interval = max(duration / num_frames, 0.5)
    log(f"  视频 {duration:.1f}s，每 {interval:.1f}s 抽一帧，共 {num_frames} 帧")

    # 3. 抽帧
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path),
         "-vf", f"fps=1/{interval}",
         str(frames_dir / "frame_%03d.jpg")],
        capture_output=True, timeout=30
    )

    frame_paths = sorted(frames_dir.glob("frame_*.jpg"))
    frame_paths = [str(f) for f in frame_paths[:num_frames]]
    log(f"  抽取 {len(frame_paths)} 帧")

    # 4. 删除视频文件
    if video_path.exists():
        video_path.unlink()
        log(f"  已删除临时视频")
    if frames_dir.exists() and not list(frames_dir.glob("frame_*.jpg")):
        frames_dir.rmdir()

    return {
        'mode': 'video',
        'title': info['title'],
        'author': info['user'],
        'content': info['desc'],
        'tags': info['tags'],
        'likes': info['likes'],
        'comments': info['comments'],
        'duration': f"{duration:.1f}s",
        'frame_paths': frame_paths,
        'frame_count': len(frame_paths),
    }


# ---------- 主流程 ----------

def main():
    parser = argparse.ArgumentParser(description='小红书内容抓取')
    parser.add_argument('url', help='小红书笔记 URL')
    parser.add_argument('--mode', choices=['auto', 'text', 'image', 'video'],
                        default='auto', help='抓取模式 (默认 auto)')
    parser.add_argument('--frames', type=int, default=DEFAULT_FRAMES,
                        help=f'视频抽帧数 (默认 {DEFAULT_FRAMES})')
    parser.add_argument('--outdir', type=str, default=str(DEFAULT_OUTDIR),
                        help=f'输出目录 (默认 {DEFAULT_OUTDIR})')
    parser.add_argument('--cookies', type=str, default=None,
                        help='Cookie 文件路径 (Netscape 格式)')
    parser.add_argument('--json', action='store_true',
                        help='输出 JSON 格式')

    args = parser.parse_args()

    global COOKIE_FILE
    if args.cookies:
        COOKIE_FILE = args.cookies

    outdir = Path(args.outdir)
    note_id = extract_note_id(args.url)
    if not note_id:
        log(f"无法从 URL 提取笔记 ID: {args.url}")
        sys.exit(1)

    log(f"笔记 ID: {note_id}")

    # 抓取页面
    log("抓取页面 HTML...")
    html = fetch_page_text(args.url)
    if not html:
        log("页面抓取失败")
        sys.exit(1)

    # 解析数据
    state = parse_initial_state(html)
    if not state:
        log("无法解析 __INITIAL_STATE__")
        sys.exit(1)

    info = extract_note_info(state)
    if not info:
        log("未找到笔记数据")
        sys.exit(1)

    # 检测内容类型
    content_type = detect_content_type(info)
    mode = args.mode if args.mode != 'auto' else content_type
    log(f"内容类型: {content_type} → 使用模式: {mode}")

    # 执行抓取
    if mode == 'text':
        result = fetch_text(info)
    elif mode == 'image':
        result = fetch_images(info, outdir / note_id)
    elif mode == 'video':
        result = fetch_video(info, outdir / note_id, args.frames)
    else:
        result = fetch_text(info)

    # 输出
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"\n📌 {result.get('title', '无标题')}")
        print(f"👤 {result.get('author', '未知')}")
        print(f"❤️ {result.get('likes', 0)}  💬 {result.get('comments', 0)}")
        print(f"\n📝 {result.get('content', '')}")
        if result.get('tags'):
            print(f"\n🏷️ {' '.join('#' + t for t in result['tags'])}")
        if result.get('mode') == 'image':
            print(f"\n🖼️ {result.get('image_count', 0)} 张图片已下载:")
            for p in result.get('image_paths', []):
                print(f"  → {p}")
        if result.get('mode') == 'video':
            print(f"\n🎬 视频 {result.get('duration', '?')}，{result.get('frame_count', 0)} 帧已抽取:")
            for p in result.get('frame_paths', []):
                print(f"  → {p}")


if __name__ == '__main__':
    main()
