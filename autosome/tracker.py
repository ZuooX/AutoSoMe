"""AutoSoMe 历史内容追踪模块。

支持两种模式：
- product-gtm：管理 <项目根>/.auto-so-me/history.json
- personal-log：管理 <personal_output_root>/history-personal.json

供内容策略去重和历史查询使用。
"""

import json
import os
from datetime import datetime, timezone

HISTORY_DIR = ".auto-so-me"
HISTORY_FILE = "history.json"
PERSONAL_HISTORY_FILE = "history-personal.json"

ALL_ANGLES = [
    "pain-point",
    "scenario",
    "tutorial",
    "showcase",
    "comparison",
    "story",
]

ALL_SUB_SCENES = [
    "growth",
    "travel",
    "reflection",
    "life",
]


def _history_path(project_root: str, mode: str = "product-gtm") -> str:
    if mode == "personal-log":
        return os.path.join(project_root, PERSONAL_HISTORY_FILE)
    return os.path.join(project_root, HISTORY_DIR, HISTORY_FILE)


def load_history(project_root: str, mode: str = "product-gtm") -> dict:
    """读取历史文件，不存在则返回空结构。"""
    path = _history_path(project_root, mode)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    if mode == "personal-log":
        return {"mode": "personal-log", "entries": []}
    return {"product": "", "entries": []}


def save_history(project_root: str, history: dict, mode: str = "product-gtm"):
    """写入历史文件，自动创建目录。"""
    path = _history_path(project_root, mode)
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_entry(project_root: str, entry: dict, mode: str = "product-gtm") -> dict:
    """新增一条记录并返回完整 history。

    product-gtm: entry 至少包含 id, batch, angle, title, tags, file。
    personal-log: entry 至少包含 id, batch, sub_scenes, title, tags, file。
    自动补充 status=draft, created_at=now, published_at=None。
    """
    history = load_history(project_root, mode)
    entry.setdefault("status", "draft")
    entry.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    entry.setdefault("published_at", None)
    if mode == "personal-log":
        entry.setdefault("desensitization_confirmed", False)
        entry.setdefault("source_date_range", "")
    history["entries"].append(entry)
    save_history(project_root, history, mode)
    return history


def mark_published(project_root: str, entry_id: str, mode: str = "product-gtm") -> bool:
    """将指定条目标记为已发布，返回是否找到该条目。"""
    history = load_history(project_root, mode)
    for entry in history["entries"]:
        if entry["id"] == entry_id:
            entry["status"] = "published"
            entry["published_at"] = datetime.now(timezone.utc).isoformat()
            save_history(project_root, history, mode)
            return True
    return False


def update_status(project_root: str, entry_id: str, status: str, mode: str = "product-gtm") -> bool:
    """更新指定条目的状态（draft/reviewed/publish_ready/published）。"""
    history = load_history(project_root, mode)
    for entry in history["entries"]:
        if entry["id"] == entry_id:
            entry["status"] = status
            if status == "published":
                entry["published_at"] = datetime.now(timezone.utc).isoformat()
            save_history(project_root, history, mode)
            return True
    return False


def list_entries(project_root: str, status_filter: str = None, mode: str = "product-gtm") -> list[dict]:
    """列出条目，支持按 status 过滤。"""
    history = load_history(project_root, mode)
    entries = history.get("entries", [])
    if status_filter:
        entries = [e for e in entries if e.get("status") == status_filter]
    return entries


def get_used_angles(project_root: str, recent_batches: int = 2) -> list[str]:
    """返回最近 N 个批次已用的角度列表（供 product-gtm F2 去重）。"""
    history = load_history(project_root)
    entries = history.get("entries", [])
    if not entries:
        return []

    batches = sorted(set(e.get("batch", "") for e in entries), reverse=True)
    recent = batches[:recent_batches]
    return list(
        set(
            e.get("angle", "")
            for e in entries
            if e.get("batch", "") in recent and e.get("angle")
        )
    )


def get_available_angles(project_root: str, recent_batches: int = 2) -> list[str]:
    """返回尚未在最近 N 个批次中使用的角度。"""
    used = set(get_used_angles(project_root, recent_batches))
    return [a for a in ALL_ANGLES if a not in used]


def get_used_sub_scenes(project_root: str, recent_batches: int = 2) -> list[str]:
    """返回最近 N 个批次已用的子场景标签（供 personal-log F2 去重）。"""
    history = load_history(project_root, mode="personal-log")
    entries = history.get("entries", [])
    if not entries:
        return []

    batches = sorted(set(e.get("batch", "") for e in entries), reverse=True)
    recent = batches[:recent_batches]
    used = set()
    for e in entries:
        if e.get("batch", "") in recent:
            for scene in e.get("sub_scenes", []):
                used.add(scene)
    return list(used)


def get_used_source_ranges(project_root: str, recent_batches: int = 3) -> list[str]:
    """返回最近 N 个批次已用的素材日期范围（供 personal-log 素材去重）。"""
    history = load_history(project_root, mode="personal-log")
    entries = history.get("entries", [])
    if not entries:
        return []

    batches = sorted(set(e.get("batch", "") for e in entries), reverse=True)
    recent = batches[:recent_batches]
    return list(
        set(
            e.get("source_date_range", "")
            for e in entries
            if e.get("batch", "") in recent and e.get("source_date_range")
        )
    )


def find_entry_by_file(project_root: str, file_path: str, mode: str = "product-gtm") -> dict | None:
    """根据文件路径（相对或绝对）查找对应的 history 条目。"""
    history = load_history(project_root, mode)
    abs_root = os.path.abspath(project_root)

    base_dir = os.path.join(abs_root, HISTORY_DIR) if mode == "product-gtm" else abs_root
    if os.path.isabs(file_path):
        rel_path = os.path.relpath(file_path, base_dir)
    else:
        rel_path = file_path

    for entry in history["entries"]:
        if entry.get("file") == rel_path:
            return entry

    post_dir = file_path.rstrip("/")
    for entry in history["entries"]:
        entry_file = entry.get("file", "")
        entry_dir = os.path.dirname(entry_file)
        if post_dir.endswith(entry_dir) or entry_dir.endswith(
            os.path.basename(post_dir)
        ):
            return entry

    return None
