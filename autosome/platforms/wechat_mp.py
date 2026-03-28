"""微信公众号平台支持。

提供两种发布方式：
1. prepare: 格式化内容到终端 + 剪贴板，用户手动发布
2. WechatMPPublisher: 通过 CDP（Chrome DevTools Protocol）连接已登录的 Chrome
   浏览器自动填写并保存草稿，规避账号风控风险。

CDP 模式使用前提：
    Chrome 需以远程调试模式启动：
    /Applications/Google Chrome.app/Contents/MacOS/Google Chrome \\
        --remote-debugging-port=9222 \\
        --user-data-dir=~/.chrome-debug-profile
"""

import re

import click

MP_EDITOR_URL = "https://mp.weixin.qq.com"
CDP_DEFAULT_PORT = 9222


def format_for_mp(post_data: dict) -> dict:
    """将 parse_post() 输出转换为公众号适用格式。

    主要处理：
    - 正文中去掉小红书风格的 #标签 文本
    - 生成 digest（摘要），优先使用 frontmatter 中的 digest 字段
    - 保留 Markdown 结构（小标题、列表等）
    """
    title = post_data.get("title", "")
    body = post_data.get("body", "")
    digest = post_data.get("digest", "")
    author = post_data.get("author", "")
    tags = post_data.get("tags", [])
    images = post_data.get("images", [])

    cleaned_body = _strip_hashtags(body)

    if not digest:
        plain = cleaned_body.replace("#", "").replace("*", "").strip()
        digest = plain[:117] + "..." if len(plain) > 120 else plain

    return {
        "title": title,
        "digest": digest,
        "author": author,
        "body": cleaned_body,
        "tags": tags,
        "images": images,
        "cover": images[0] if images else None,
    }


def _strip_hashtags(text: str) -> str:
    """移除正文末尾的小红书风格标签行（如 #AI工具 #效率提升）。

    保留正文中嵌入的 Markdown 标题（以 # 开头后跟空格的行）。
    """
    lines = text.rstrip().split("\n")

    while lines and re.match(r"^\s*(#\S+\s*)+$", lines[-1]):
        lines.pop()

    return "\n".join(lines).rstrip()


def print_prepare_output(index: int, total: int, post_data: dict):
    """格式化输出单篇帖子内容，供用户手动复制到微信公众号后台。"""
    mp_data = format_for_mp(post_data)

    click.echo(f"\n{'='*60}")
    if total > 1:
        click.echo(f"📝 第 {index}/{total} 篇")
    click.echo(f"{'='*60}")

    click.echo(f"\n📌 标题:\n{mp_data['title']}")

    if mp_data["author"]:
        click.echo(f"\n✍️  作者: {mp_data['author']}")

    click.echo(f"\n📋 摘要:\n{mp_data['digest']}")

    click.echo(f"\n📄 正文:\n{mp_data['body']}")

    if mp_data["tags"]:
        click.echo(f"\n🏷️  标签（内容管理用）:\n{', '.join(mp_data['tags'])}")

    if mp_data["cover"]:
        click.echo(f"\n🖼️  封面图:\n   {mp_data['cover']}")

    if mp_data["images"]:
        click.echo(f"\n📷 全部图片（{len(mp_data['images'])} 张）:")
        for img in mp_data["images"]:
            click.echo(f"   {img}")

    click.echo(f"\n{'='*60}\n")


def check_cdp_available(port: int = CDP_DEFAULT_PORT) -> bool:
    """检查 Chrome CDP 调试端口是否可用。"""
    import urllib.error
    import urllib.request

    try:
        urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=2)
        return True
    except (urllib.error.URLError, OSError):
        return False


class WechatMPPublisher:
    """通过 CDP 连接已登录的 Chrome，自动发布微信公众号文章。

    使用方式：
        publisher = WechatMPPublisher(cdp_port=9222)
        result = publisher.publish(post_data, save_draft=True)

    Chrome 启动命令（首次需要）：
        /Applications/Google Chrome.app/Contents/MacOS/Google Chrome \\
            --remote-debugging-port=9222 \\
            --user-data-dir=~/.chrome-debug-profile
    """

    PROSEMIRROR_SEL = ".ProseMirror"
    TITLE_SEL = '[placeholder*="标题"]'
    DIGEST_SEL = "#js_description"
    SAVE_DRAFT_TEXT = "保存为草稿"
    SETTINGS_BTN_SEL = "a.tool_bar__fold-btn"
    CREATE_ARTICLE_TEXT = "文章"

    def __init__(self, cdp_port: int = CDP_DEFAULT_PORT):
        self.cdp_port = cdp_port

    def publish(self, post_data: dict, save_draft: bool = True) -> dict:
        """执行完整的公众号文章发布流程。

        Args:
            post_data: parse_post() 返回的帖子数据字典
            save_draft: True=保存为草稿（推荐），False=不执行发布操作（仅填写内容）

        Returns:
            dict: {"success": bool, "message": str, "screenshot": str}
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return {
                "success": False,
                "message": "未安装 Playwright，请运行：pip install playwright && playwright install chromium",
                "screenshot": None,
            }

        mp_data = format_for_mp(post_data)

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://localhost:{self.cdp_port}")
            context = browser.contexts[0]

            # 找到或打开公众号首页
            home_page = self._get_or_open_home(context)

            # 点击「文章」进入编辑器
            editor_page = self._open_editor(context, home_page)

            # 填写内容
            self._fill_title(editor_page, mp_data["title"])
            self._fill_body(editor_page, mp_data["body"])
            self._open_settings(editor_page)
            self._fill_digest(editor_page, mp_data["digest"])
            if mp_data.get("cover"):
                self._upload_cover(editor_page, mp_data["cover"])

            # 截图确认
            screenshot_path = "/tmp/mp-publish-confirm.png"
            editor_page.evaluate("window.scrollTo(0, 0)")
            editor_page.wait_for_timeout(500)
            editor_page.screenshot(path=screenshot_path)

            if save_draft:
                self._save_draft(editor_page)
                message = "草稿已保存，请在公众号后台预览后发表"
            else:
                message = "内容已填写，请在浏览器中手动检查并保存"

            return {
                "success": True,
                "message": message,
                "screenshot": screenshot_path,
            }

    def _get_or_open_home(self, context):
        """找到已打开的公众号页面，否则打开新标签。"""
        for page in context.pages:
            if "mp.weixin.qq.com" in page.url:
                page.evaluate("window.scrollTo(0, 0)")
                return page

        page = context.new_page()
        page.goto(MP_EDITOR_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        return page

    def _open_editor(self, context, home_page):
        """在首页点击「文章」按钮，等待编辑器标签打开。"""
        home_page.evaluate("window.scrollTo(0, 500)")
        home_page.wait_for_timeout(500)

        pages_before = len(context.pages)
        home_page.get_by_text(self.CREATE_ARTICLE_TEXT, exact=True).first.click()

        # 等待新标签
        for _ in range(20):
            home_page.wait_for_timeout(500)
            if len(context.pages) > pages_before:
                break

        editor_page = context.pages[-1]
        editor_page.wait_for_timeout(1500)
        return editor_page

    def _fill_title(self, page, title: str):
        """填写文章标题。"""
        title_input = page.locator(self.TITLE_SEL).first
        title_input.click()
        page.wait_for_timeout(200)
        title_input.fill(title)
        page.wait_for_timeout(300)

    def _fill_body(self, page, body: str):
        """填写正文内容（ProseMirror 富文本编辑器）。"""
        editor = page.locator(self.PROSEMIRROR_SEL)
        editor.click()
        page.wait_for_timeout(300)
        page.keyboard.insert_text(body.strip())
        page.wait_for_timeout(500)

    def _open_settings(self, page):
        """展开右侧「文章设置」面板。"""
        page.locator(self.SETTINGS_BTN_SEL).click()
        page.wait_for_timeout(1000)

    def _fill_digest(self, page, digest: str):
        """填写摘要（最多 120 字）。"""
        if not digest:
            return
        digest_trimmed = digest[:120]
        page.locator(self.DIGEST_SEL).fill(digest_trimmed)
        page.wait_for_timeout(300)

    def _upload_cover(self, page, cover_path: str):
        """上传封面图。"""
        import os

        if not os.path.exists(cover_path):
            click.echo(f"  [警告] 封面图文件不存在: {cover_path}")
            return

        file_input = page.locator('input[type="file"][accept*="image"]').first
        if file_input.count() > 0:
            file_input.set_input_files(cover_path)
            page.wait_for_timeout(3000)

    def _save_draft(self, page):
        """点击「保存为草稿」按钮。"""
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        page.locator(f'button:has-text("{self.SAVE_DRAFT_TEXT}"), a:has-text("{self.SAVE_DRAFT_TEXT}")').first.click()
        page.wait_for_timeout(2000)
