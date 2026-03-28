import os
from pathlib import Path

import frontmatter

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


def parse_post(post_dir: str) -> dict:
    """解析一篇帖子目录，返回结构化数据。

    帖子目录结构：
        某篇帖子/
        ├── content.md          # 标题 + 正文 (YAML frontmatter)
        ├── cover.jpg           # 封面图（可选，自动排到第一张）
        ├── 01.jpg              # 图片按文件名排序
        └── 02.png
    """
    post_path = Path(post_dir)
    content_file = post_path / "content.md"

    if not content_file.exists():
        raise FileNotFoundError(f"未找到 content.md: {content_file}")

    post = frontmatter.load(str(content_file))

    title = post.metadata.get("title", "")
    tags = post.metadata.get("tags", [])
    body = post.content.strip()

    images = sorted(
        [
            str(post_path / f)
            for f in os.listdir(post_path)
            if Path(f).suffix.lower() in IMAGE_EXTENSIONS
        ]
    )

    cover_candidates = [post_path / f"cover{ext}" for ext in IMAGE_EXTENSIONS]
    for c in cover_candidates:
        if c.exists():
            cover_str = str(c)
            if cover_str in images:
                images.remove(cover_str)
            images.insert(0, cover_str)
            break

    platform = post.metadata.get("platform", "xhs")
    digest = post.metadata.get("digest", "")
    author = post.metadata.get("author", "")
    mode = post.metadata.get("mode", "product-gtm")
    sub_scenes = post.metadata.get("sub_scenes", [])
    source_date_range = post.metadata.get("source_date_range", "")
    desensitization_confirmed = post.metadata.get("desensitization_confirmed", False)
    status = post.metadata.get("status", "draft")
    source_file = post.metadata.get("source_file", "")

    return {
        "title": title,
        "body": body,
        "tags": tags,
        "images": images,
        "post_dir": str(post_path),
        "platform": platform,
        "digest": digest,
        "author": author,
        "mode": mode,
        "sub_scenes": sub_scenes,
        "source_date_range": source_date_range,
        "desensitization_confirmed": desensitization_confirmed,
        "status": status,
        "source_file": source_file,
    }


def find_posts(base_dir: str) -> list[str]:
    """查找目录下所有包含 content.md 的帖子目录。"""
    base = Path(base_dir)
    posts = []
    for item in sorted(base.iterdir()):
        if item.is_dir() and (item / "content.md").exists():
            posts.append(str(item))
    return posts
