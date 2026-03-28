import asyncio
import os

import click

from autosome.config import load_config
from autosome.parser import find_posts, parse_post


@click.group()
@click.option("--config", "config_path", default=None, help="配置文件路径")
@click.pass_context
def cli(ctx, config_path):
    """AutoSoMe - 产品 GTM & 个人 IP 营销 Agent（CLI 发布工具）"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config_path)


@cli.command()
@click.option(
    "--platform", "-p", type=click.Choice(["xhs", "mp"]), required=True, help="平台名称"
)
@click.pass_context
def login(ctx, platform):
    """[legacy] Playwright 登录（推荐改用 Chrome DevTools MCP，复用已登录的 Chrome 浏览器）"""
    config = ctx.obj["config"]

    if platform == "xhs":
        from autosome.platforms.xiaohongshu import XiaohongshuPublisher

        browser_data = config["platforms"]["xhs"]["browser_data_dir"]

        async def _run():
            async with XiaohongshuPublisher(browser_data_dir=browser_data) as pub:
                await pub.login()

        asyncio.run(_run())

    elif platform == "mp":
        click.echo("\n[TODO] 微信公众号浏览器自动化登录尚未实现")
        click.echo("请直接在浏览器中访问 https://mp.weixin.qq.com 手动登录\n")


@cli.command()
@click.option(
    "--platform", "-p", type=click.Choice(["xhs", "mp"]), required=True, help="平台名称"
)
@click.option("--output", "-o", default=".", help="调试文件保存目录（截图 + HTML）")
@click.option("--image", "test_image", default=None, type=click.Path(), help="测试图片路径，上传后查看完整表单")
@click.pass_context
def inspect(ctx, platform, output, test_image):
    """[legacy] Playwright 调试：打开发布页面，截图并分析页面元素结构"""
    config = ctx.obj["config"]

    if platform == "xhs":
        from autosome.platforms.xiaohongshu import XiaohongshuPublisher

        browser_data = config["platforms"]["xhs"]["browser_data_dir"]

        async def _run():
            async with XiaohongshuPublisher(browser_data_dir=browser_data) as pub:
                await pub.inspect(output_dir=output, test_image=test_image)

        asyncio.run(_run())

    elif platform == "mp":
        click.echo("\n[TODO] 微信公众号页面调试尚未实现")
        click.echo("请使用 prepare -p mp 命令生成内容后手动发布\n")


@cli.command()
@click.option("--platform", "-p", type=click.Choice(["xhs", "mp"]), default="xhs", help="目标平台（默认小红书）")
@click.option("--post", "post_path", type=click.Path(exists=True), help="单篇帖子目录")
@click.option("--dir", "post_dir", type=click.Path(exists=True), help="批量帖子目录")
@click.option("--index", "post_index", type=int, default=None, help="指定输出第几篇（1-based）")
@click.option("--copy-body", "copy_body", is_flag=True, help="将正文复制到剪贴板（默认复制标题）")
def prepare(platform, post_path, post_dir, post_index, copy_body):
    """准备发布内容：格式化输出到终端 + 复制到剪贴板，用户手动粘贴发布（推荐方式）"""
    from autosome.platforms import copy_to_clipboard

    if not post_path and not post_dir:
        raise click.UsageError("请指定 --post（单篇帖子目录）或 --dir（批量帖子目录）")

    post_dirs = []
    if post_path:
        post_dirs.append(post_path)
    elif post_dir:
        post_dirs = find_posts(post_dir)
        if not post_dirs:
            click.echo(f"目录下未找到帖子（缺少 content.md）: {post_dir}")
            return

    all_posts = []
    for d in post_dirs:
        try:
            all_posts.append(parse_post(d))
        except Exception as e:
            click.echo(f"[跳过] 解析失败 {d}: {e}")

    if not all_posts:
        click.echo("没有可准备的帖子")
        return

    if post_index is not None:
        if post_index < 1 or post_index > len(all_posts):
            click.echo(f"序号超出范围，共 {len(all_posts)} 篇")
            return
        all_posts = [all_posts[post_index - 1]]

    if platform == "mp":
        _prepare_mp(all_posts, copy_body, copy_to_clipboard)
    else:
        _prepare_xhs(all_posts, copy_body, copy_to_clipboard)


@cli.command()
@click.option(
    "--platform", "-p", type=click.Choice(["xhs", "mp"]), required=True, help="平台名称"
)
@click.option("--post", "post_path", type=click.Path(exists=True), help="单篇帖子目录")
@click.option("--dir", "post_dir", type=click.Path(exists=True), help="批量帖子目录")
@click.option("--auto", "auto_publish", is_flag=True, help="自动点击发布（不等待手动确认）")
@click.option("--dry-run", is_flag=True, help="仅解析和预览内容，不打开浏览器")
@click.option("--cdp-port", "cdp_port", default=9222, type=int, help="Chrome CDP 调试端口（mp 平台，默认 9222）")
@click.option("--project", "project_root", default=None, type=click.Path(), help="产品项目根目录（用于更新 history.json）")
@click.pass_context
def publish(ctx, platform, post_path, post_dir, auto_publish, dry_run, cdp_port, project_root):
    """自动发布：mp 平台通过 CDP 连接已登录的 Chrome；xhs 使用 Playwright（legacy）"""
    if platform == "xhs" and not dry_run:
        click.echo("\n⚠️  小红书使用 Playwright 独立浏览器实例，平台可检测自动化操作")
        click.echo("   推荐改用 Chrome DevTools MCP 方案（操控真实 Chrome，无检测风险）")
        click.echo("   或使用 `python -m autosome prepare` 命令生成内容后手动发布\n")

    if not post_path and not post_dir:
        raise click.UsageError("请指定 --post（单篇帖子目录）或 --dir（批量帖子目录）")

    post_dirs = []
    if post_path:
        post_dirs.append(post_path)
    elif post_dir:
        post_dirs = find_posts(post_dir)
        if not post_dirs:
            click.echo(f"目录下未找到帖子（缺少 content.md）: {post_dir}")
            return

    all_posts = []
    for d in post_dirs:
        try:
            post_data = parse_post(d)
            all_posts.append(post_data)
        except Exception as e:
            click.echo(f"[跳过] 解析失败 {d}: {e}")

    if not all_posts:
        click.echo("没有可发布的帖子")
        return

    blocked = []
    publishable = []
    for post_data in all_posts:
        if post_data.get("mode") == "personal-log" and not post_data.get("desensitization_confirmed"):
            blocked.append(post_data)
        else:
            publishable.append(post_data)

    if blocked:
        click.echo(f"\n⚠️  {len(blocked)} 篇 personal-log 帖子未通过脱敏确认，已跳过：")
        for bp in blocked:
            click.echo(f"  - {bp['title'] or '(无标题)'} [{bp.get('post_dir', '')}]")
        click.echo("请先在 content.md 中将 desensitization_confirmed 设为 true\n")

    if not publishable:
        click.echo("没有可发布的帖子")
        return

    click.echo(f"\n共 {len(publishable)} 篇帖子待发布:\n")
    for i, post_data in enumerate(publishable, 1):
        _print_post_summary(i, len(publishable), post_data)

    if dry_run:
        click.echo("[预览模式] 不执行发布")
        return

    if platform == "xhs":
        _publish_xhs(ctx.obj["config"], publishable, auto_publish, project_root)
    elif platform == "mp":
        _publish_mp_cdp(publishable, cdp_port, project_root)

    click.echo("\n全部完成!")


@cli.command("history")
@click.option("--project", "project_root", default=".", type=click.Path(exists=True), help="项目根目录（product-gtm）或个人输出根目录（personal-log）")
@click.option("--mode", type=click.Choice(["product-gtm", "personal"]), default="product-gtm", help="内容模式")
@click.option("--status", "status_filter", type=click.Choice(["draft", "reviewed", "publish_ready", "published"]), default=None, help="按状态过滤")
@click.option("--angles", is_flag=True, help="显示已用/可用角度或子场景统计")
def history_cmd(project_root, mode, status_filter, angles):
    """查看历史生成/发布记录"""
    from autosome.tracker import list_entries

    tracker_mode = "personal-log" if mode == "personal" else "product-gtm"
    entries = list_entries(project_root, status_filter=status_filter, mode=tracker_mode)

    if not entries:
        click.echo("暂无历史记录")
        if angles:
            if tracker_mode == "personal-log":
                _print_sub_scene_stats(project_root)
            else:
                _print_angle_stats(project_root)
        return

    if tracker_mode == "personal-log":
        click.echo(f"\n{'序号':<4} {'状态':<14} {'子场景':<16} {'标题':<28} {'素材范围'}")
        click.echo("-" * 90)
        for i, e in enumerate(entries, 1):
            status_icon = {
                "draft": "📝", "reviewed": "✅",
                "publish_ready": "🔓", "published": "🚀",
            }.get(e.get("status", ""), "  ")
            scenes = ",".join(e.get("sub_scenes", []))
            src_range = e.get("source_date_range", "")[:21]
            click.echo(
                f"{i:<4} {status_icon} {e.get('status', ''):<12} "
                f"{scenes:<16} "
                f"{(e.get('title', '') or '')[:26]:<28} "
                f"{src_range}"
            )
    else:
        click.echo(f"\n{'序号':<4} {'状态':<10} {'角度':<14} {'标题':<30} {'日期'}")
        click.echo("-" * 80)
        for i, e in enumerate(entries, 1):
            status_icon = {"draft": "📝", "reviewed": "✅", "published": "🚀"}.get(
                e.get("status", ""), "  "
            )
            date_str = (e.get("created_at") or "")[:10]
            click.echo(
                f"{i:<4} {status_icon} {e.get('status', ''):<8} "
                f"{e.get('angle', ''):<14} "
                f"{(e.get('title', '') or '')[:28]:<30} "
                f"{date_str}"
            )

    click.echo(f"\n共 {len(entries)} 条记录")

    if angles:
        if tracker_mode == "personal-log":
            _print_sub_scene_stats(project_root)
        else:
            _print_angle_stats(project_root)


@cli.command("mark-published")
@click.option("--project", "project_root", default=".", type=click.Path(exists=True), help="项目根目录")
@click.option("--mode", type=click.Choice(["product-gtm", "personal"]), default="product-gtm", help="内容模式")
@click.option("--id", "entry_id", required=True, help="条目 ID（如 2026-03-22-batch-1-post-1）")
def mark_published_cmd(project_root, mode, entry_id):
    """标记某条记录为已发布"""
    from autosome.tracker import mark_published

    tracker_mode = "personal-log" if mode == "personal" else "product-gtm"
    if mark_published(project_root, entry_id, mode=tracker_mode):
        click.echo(f"已标记为已发布: {entry_id}")
    else:
        click.echo(f"未找到条目: {entry_id}")


@cli.command("add-entry")
@click.option("--project", "project_root", default=".", type=click.Path(exists=True), help="项目根目录")
@click.option("--mode", type=click.Choice(["product-gtm", "personal"]), default="product-gtm", help="内容模式")
@click.option("--product", default="", help="产品名称（product-gtm 模式）")
@click.option("--id", "entry_id", required=True, help="条目 ID")
@click.option("--batch", required=True, help="批次名（如 2026-03-22-batch-1）")
@click.option("--angle", default="", help="内容角度（product-gtm 模式）")
@click.option("--sub-scenes", "sub_scenes", default="", help="子场景标签（逗号分隔，personal 模式）")
@click.option("--source-range", "source_date_range", default="", help="素材日期范围（personal 模式）")
@click.option("--title", required=True, help="标题")
@click.option("--tags", default="", help="标签（逗号分隔）")
@click.option("--file", "file_path", required=True, help="文案文件相对路径")
def add_entry_cmd(project_root, mode, product, entry_id, batch, angle, sub_scenes, source_date_range, title, tags, file_path):
    """新增一条历史记录（供 Agent 调用）"""
    from autosome.tracker import add_entry, load_history, save_history

    tracker_mode = "personal-log" if mode == "personal" else "product-gtm"

    if tracker_mode == "product-gtm" and product:
        hist = load_history(project_root, mode=tracker_mode)
        hist["product"] = product
        save_history(project_root, hist, mode=tracker_mode)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    entry = {
        "id": entry_id,
        "batch": batch,
        "title": title,
        "tags": tag_list,
        "file": file_path,
    }

    if tracker_mode == "personal-log":
        scene_list = [s.strip() for s in sub_scenes.split(",") if s.strip()] if sub_scenes else []
        entry["sub_scenes"] = scene_list
        entry["source_date_range"] = source_date_range
    else:
        entry["angle"] = angle

    add_entry(project_root, entry, mode=tracker_mode)
    click.echo(f"已添加记录: {entry_id}")


@cli.command("used-angles")
@click.option("--project", "project_root", default=".", type=click.Path(exists=True), help="产品项目根目录")
@click.option("--recent", "recent_batches", default=2, type=int, help="查看最近 N 个批次的角度")
def used_angles_cmd(project_root, recent_batches):
    """查看已用/可用角度（供 Agent 调用）"""
    _print_angle_stats(project_root, recent_batches)


# ------------------------------------------------------------------
# 内部辅助函数
# ------------------------------------------------------------------


def _prepare_xhs(all_posts: list[dict], copy_body: bool, copy_fn):
    """小红书 prepare 流程：格式化输出 + 剪贴板。"""
    for i, post_data in enumerate(all_posts, 1):
        _print_prepare_xhs(i, len(all_posts), post_data)

    last = all_posts[-1] if len(all_posts) == 1 else all_posts[0]
    if copy_body:
        body_with_tags = last["body"]
        if last.get("tags"):
            body_with_tags += "\n\n" + " ".join(f"#{t}" for t in last["tags"])
        if copy_fn(body_with_tags):
            click.echo("✅ 正文（含标签）已复制到剪贴板")
        else:
            click.echo("⚠️ 无法复制到剪贴板，请手动复制上方内容")
    else:
        if copy_fn(last.get("title", "")):
            click.echo("✅ 标题已复制到剪贴板（加 --copy-body 可复制正文）")
        else:
            click.echo("⚠️ 无法复制到剪贴板，请手动复制上方内容")

    click.echo("\n📱 请打开小红书 App → 点击「+」发布 → 粘贴内容 → 上传图片 → 发布")
    if last.get("images"):
        click.echo(f"📷 图片路径（共 {len(last['images'])} 张）：")
        for img in last["images"]:
            click.echo(f"   {img}")


def _prepare_mp(all_posts: list[dict], copy_body: bool, copy_fn):
    """微信公众号 prepare 流程：格式化输出 + 剪贴板。"""
    from autosome.platforms.wechat_mp import format_for_mp, print_prepare_output

    for i, post_data in enumerate(all_posts, 1):
        print_prepare_output(i, len(all_posts), post_data)

    last = all_posts[-1] if len(all_posts) == 1 else all_posts[0]
    mp_data = format_for_mp(last)
    if copy_body:
        if copy_fn(mp_data["body"]):
            click.echo("✅ 正文已复制到剪贴板")
        else:
            click.echo("⚠️ 无法复制到剪贴板，请手动复制上方内容")
    else:
        if copy_fn(mp_data["title"]):
            click.echo("✅ 标题已复制到剪贴板（加 --copy-body 可复制正文）")
        else:
            click.echo("⚠️ 无法复制到剪贴板，请手动复制上方内容")

    click.echo("\n🖥️  请打开微信公众号后台 → 新建图文 → 粘贴内容 → 上传封面图 → 发布")
    if mp_data.get("cover"):
        click.echo(f"🖼️  封面图路径: {mp_data['cover']}")


def _print_prepare_xhs(index: int, total: int, post_data: dict):
    """格式化输出单篇帖子内容，供用户手动复制到小红书 App。"""
    title = post_data.get("title", "")
    body = post_data.get("body", "")
    tags = post_data.get("tags", [])
    images = post_data.get("images", [])

    click.echo(f"\n{'='*60}")
    if total > 1:
        click.echo(f"📝 第 {index}/{total} 篇")
    click.echo(f"{'='*60}")

    click.echo(f"\n📌 标题:\n{title}")
    click.echo(f"\n📄 正文:\n{body}")

    if tags:
        click.echo(f"\n🏷️  标签:\n{' '.join(f'#{t}' for t in tags)}")

    if images:
        click.echo(f"\n📷 图片（{len(images)} 张）:")
        for img in images:
            click.echo(f"   {os.path.abspath(img)}")

    click.echo(f"\n{'='*60}\n")


def _print_post_summary(index: int, total: int, post_data: dict):
    mode = post_data.get("mode", "product-gtm")
    mode_label = "个人日志" if mode == "personal-log" else "产品推广"
    click.echo(f"--- [{index}/{total}] [{mode_label}] {post_data['title'] or '(无标题)'} ---")
    body_preview = post_data["body"][:80]
    if len(post_data["body"]) > 80:
        body_preview += "..."
    click.echo(f"  正文: {body_preview}")
    click.echo(f"  图片: {len(post_data['images'])} 张")
    if post_data["tags"]:
        click.echo(f"  标签: {', '.join(post_data['tags'])}")
    if mode == "personal-log":
        scenes = post_data.get("sub_scenes", [])
        if scenes:
            click.echo(f"  子场景: {', '.join(scenes)}")
        desens = "✅ 已确认" if post_data.get("desensitization_confirmed") else "❌ 未确认"
        click.echo(f"  脱敏状态: {desens}")
    click.echo()


def _print_angle_stats(project_root: str, recent_batches: int = 2):
    from autosome.tracker import ALL_ANGLES, get_available_angles, get_used_angles

    used = get_used_angles(project_root, recent_batches)
    available = get_available_angles(project_root, recent_batches)

    click.echo(f"\n--- 角度统计（最近 {recent_batches} 个批次）---")
    for angle in ALL_ANGLES:
        mark = "✅ 已用" if angle in used else "⬜ 可用"
        click.echo(f"  {mark}  {angle}")
    click.echo(f"\n已用 {len(used)} / 共 {len(ALL_ANGLES)} 个角度，剩余 {len(available)} 个可用")


def _print_sub_scene_stats(project_root: str, recent_batches: int = 2):
    from autosome.tracker import ALL_SUB_SCENES, get_used_source_ranges, get_used_sub_scenes

    used_scenes = get_used_sub_scenes(project_root, recent_batches)
    used_ranges = get_used_source_ranges(project_root, recent_batches + 1)

    click.echo(f"\n--- 子场景统计（最近 {recent_batches} 个批次）---")
    for scene in ALL_SUB_SCENES:
        mark = "✅ 已用" if scene in used_scenes else "⬜ 可用"
        click.echo(f"  {mark}  {scene}")
    click.echo(f"\n已用 {len(used_scenes)} / 共 {len(ALL_SUB_SCENES)} 个子场景")

    if used_ranges:
        click.echo("\n--- 近期已用素材日期范围 ---")
        for r in sorted(used_ranges):
            click.echo(f"  📅 {r}")


def _publish_xhs(config: dict, all_posts: list[dict], auto_publish: bool, project_root: str | None = None):
    import random

    from autosome.platforms.xiaohongshu import XiaohongshuPublisher

    browser_data = config["platforms"]["xhs"]["browser_data_dir"]

    async def _run():
        async with XiaohongshuPublisher(browser_data_dir=browser_data) as pub:
            for i, post_data in enumerate(all_posts, 1):
                click.echo(f"\n{'='*50}")
                click.echo(f"[{i}/{len(all_posts)}] 发布: {post_data['title']}")
                click.echo(f"{'='*50}")

                success = await pub.publish(post_data, auto_publish=auto_publish)

                if success and project_root:
                    _try_mark_published(project_root, post_data)

                if i < len(all_posts):
                    wait = random.randint(180, 480)
                    click.echo(
                        f"\n[安全间隔] 下一篇将在 {wait // 60} 分 {wait % 60} 秒后发布..."
                    )
                    await asyncio.sleep(wait)

    asyncio.run(_run())


def _publish_mp_cdp(all_posts: list[dict], cdp_port: int, project_root: str | None = None):
    """通过 CDP 连接已登录的 Chrome，自动发布微信公众号文章（保存为草稿）。"""
    from autosome.platforms.wechat_mp import WechatMPPublisher, check_cdp_available

    if not check_cdp_available(cdp_port):
        click.echo(f"\n❌ Chrome CDP 端口 {cdp_port} 未响应，请先启动 Chrome 调试模式：")
        click.echo("   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\")
        click.echo(f"       --remote-debugging-port={cdp_port} \\")
        click.echo("       --user-data-dir=~/.chrome-debug-profile")
        click.echo("\n   启动后在 Chrome 中登录 https://mp.weixin.qq.com，再重试。\n")
        return

    publisher = WechatMPPublisher(cdp_port=cdp_port)

    for i, post_data in enumerate(all_posts, 1):
        click.echo(f"\n{'='*50}")
        click.echo(f"[{i}/{len(all_posts)}] 发布: {post_data['title']}")
        click.echo(f"{'='*50}")

        result = publisher.publish(post_data, save_draft=True)

        if result["success"]:
            click.echo(f"  ✅ {result['message']}")
            if result.get("screenshot"):
                click.echo(f"  📸 截图: {result['screenshot']}")
            if project_root:
                _try_mark_published(project_root, post_data)
        else:
            click.echo(f"  ❌ 发布失败: {result['message']}")


def _try_mark_published(project_root: str, post_data: dict):
    """尝试在对应 history 文件中将帖子标记为已发布。"""
    from autosome.tracker import find_entry_by_file, mark_published

    post_dir = post_data.get("post_dir", "")
    if not post_dir:
        return

    mode = post_data.get("mode", "product-gtm")
    entry = find_entry_by_file(project_root, post_dir, mode=mode)
    if entry:
        mark_published(project_root, entry["id"], mode=mode)
        click.echo(f"  [历史] 已标记为已发布: {entry['id']}")
