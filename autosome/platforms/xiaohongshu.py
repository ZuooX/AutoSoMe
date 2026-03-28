import asyncio
import os
import random
import sys
import traceback
import webbrowser

import click
from playwright.async_api import BrowserContext, Page, async_playwright

from autosome.platforms import copy_to_clipboard

XHS_CREATOR_URL = "https://creator.xiaohongshu.com"
XHS_PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish"

MOD_KEY = "Meta" if sys.platform == "darwin" else "Control"

ANTI_DETECT_INIT_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

Object.defineProperty(navigator, 'plugins', {
    get: () => [
        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
        {name: 'Native Client', filename: 'internal-nacl-plugin'},
    ],
});

Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});

window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}};

const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) =>
    parameters.name === 'notifications'
        ? Promise.resolve({state: Notification.permission})
        : originalQuery(parameters);
"""


async def _human_delay(min_sec=0.5, max_sec=1.5):
    """模拟人类操作的随机延迟。"""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


async def _human_type(page: Page, text: str):
    """模拟人类打字速度，每个字符间隔随机。"""
    for char in text:
        await page.keyboard.type(char, delay=0)
        await asyncio.sleep(random.uniform(0.02, 0.08))


def _copy_to_clipboard(text: str) -> bool:
    """向后兼容的别名，实际调用公共 copy_to_clipboard。"""
    return copy_to_clipboard(text)


def fallback_publish(post_data: dict):
    """回退方案：复制标题到剪贴板 + 格式化输出 + 打开发布页。

    当浏览器自动化失败时调用，帮助用户手动发布。
    """
    title = post_data.get("title", "")
    body = post_data.get("body", "")
    tags = post_data.get("tags", [])
    images = post_data.get("images", [])

    click.echo("\n" + "=" * 50)
    click.echo("[回退方案] 浏览器自动化失败，请手动发布")
    click.echo("=" * 50)

    if _copy_to_clipboard(title):
        click.echo("\n✅ 标题已复制到剪贴板")
    else:
        click.echo("\n⚠️ 无法复制到剪贴板，请手动复制")

    click.echo(f"\n--- 标题 ---\n{title}")
    click.echo(f"\n--- 正文 ---\n{body}")

    if tags:
        click.echo(f"\n--- 标签 ---\n{' '.join(f'#{t}' for t in tags)}")

    if images:
        click.echo(f"\n--- 图片（{len(images)} 张）---")
        for img in images:
            click.echo(f"  {img}")

    click.echo(f"\n正在打开小红书发布页...")
    webbrowser.open(XHS_PUBLISH_URL)
    click.echo("请在浏览器中手动粘贴内容并发布。")


class XiaohongshuPublisher:
    """小红书创作者平台自动化发布。

    通过 Playwright 操控浏览器，实现自动填写标题、正文、上传图片。
    使用持久化浏览器上下文保存登录状态，避免每次重新登录。
    包含反检测措施以降低被平台识别为自动化操作的风险。
    """

    def __init__(self, browser_data_dir: str, headless: bool = False):
        self.browser_data_dir = browser_data_dir
        self.headless = headless
        self._pw = None
        self._context: BrowserContext | None = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.stop()

    async def start(self):
        os.makedirs(self.browser_data_dir, exist_ok=True)
        self._pw = await async_playwright().start()
        self._context = await self._pw.chromium.launch_persistent_context(
            self.browser_data_dir,
            headless=self.headless,
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
            accept_downloads=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
            ],
            ignore_default_args=["--enable-automation"],
        )
        await self._context.add_init_script(ANTI_DETECT_INIT_SCRIPT)

    async def stop(self):
        if self._context:
            await self._context.close()
        if self._pw:
            await self._pw.stop()

    async def login(self, timeout: int = 120):
        """打开浏览器让用户手动登录，自动检测登录成功后保存状态。

        Args:
            timeout: 等待登录完成的超时时间（秒）
        """
        page = await self._context.new_page()
        await page.goto(XHS_CREATOR_URL)
        click.echo("\n浏览器已打开，请在浏览器中登录小红书创作者平台...")
        click.echo(f"（等待登录完成，最长等待 {timeout} 秒）")
        try:
            await page.wait_for_selector(
                'div.creator-tab, [class*="sidebar"] a, [class*="user-info"]',
                timeout=timeout * 1000,
            )
            click.echo("检测到登录成功，状态已保存！")
        except Exception:
            click.echo("等待超时，如已登录则状态已自动保存。")
        await page.close()

    async def inspect(self, output_dir: str = ".", test_image: str = None):
        """打开发布页面，可选上传测试图片后截图并保存页面 HTML，用于调试选择器。

        Args:
            output_dir: 截图和 HTML 文件的保存目录
            test_image: 可选，用于测试上传的图片路径，上传后可看到标题/正文输入框
        """
        page = await self._context.new_page()
        try:
            click.echo("正在打开小红书发布页面...")
            await page.goto(XHS_PUBLISH_URL)
            await page.wait_for_load_state("domcontentloaded")
            await _human_delay(2, 4)

            await _click_tab_image_text(page)

            if test_image and os.path.exists(test_image):
                click.echo(f"  上传测试图片: {test_image}")
                file_input = page.locator("input.upload-input").first
                if await file_input.count() > 0:
                    await file_input.set_input_files(test_image)
                    await _human_delay(3, 5)
                    click.echo("  图片上传完成，等待表单渲染...")
                    await _human_delay(1.5, 3)

            os.makedirs(output_dir, exist_ok=True)
            screenshot_path = os.path.join(output_dir, "xhs_publish_page.png")
            html_path = os.path.join(output_dir, "xhs_publish_page.html")

            await page.screenshot(path=screenshot_path, full_page=True)
            html = await page.content()
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)

            click.echo(f"截图已保存: {screenshot_path}")
            click.echo(f"HTML已保存: {html_path}")

            click.echo("\n--- 页面可见输入框 ---")
            inputs = await page.locator("input:visible").all()
            for i, inp in enumerate(inputs):
                try:
                    tag = await inp.evaluate("el => el.tagName")
                    placeholder = await inp.get_attribute("placeholder") or ""
                    cls = await inp.get_attribute("class") or ""
                    id_ = await inp.get_attribute("id") or ""
                    click.echo(
                        f"  [{i}] <{tag}> placeholder='{placeholder}'"
                        f" id='{id_}' class='{cls[:60]}'"
                    )
                except Exception:
                    pass

            click.echo("\n--- 页面可见 contenteditable 元素 ---")
            editors = await page.locator(
                'div[contenteditable="true"]:visible'
            ).all()
            for i, ed in enumerate(editors):
                try:
                    cls = await ed.get_attribute("class") or ""
                    id_ = await ed.get_attribute("id") or ""
                    placeholder = await ed.get_attribute("placeholder") or ""
                    click.echo(
                        f"  [{i}] <div> contenteditable id='{id_}'"
                        f" class='{cls[:60]}' placeholder='{placeholder}'"
                    )
                except Exception:
                    pass

        finally:
            await page.close()

    async def publish(self, post_data: dict, auto_publish: bool = False) -> bool:
        """发布一篇帖子到小红书。

        Args:
            post_data: 由 parser.parse_post() 返回的帖子数据
            auto_publish: True 则自动点击发布按钮，False 则等待用户手动确认

        Returns:
            True 表示发布流程正常完成，False 表示回退到手动模式
        """
        page = await self._context.new_page()
        error_occurred = False
        try:
            await page.goto(XHS_PUBLISH_URL)
            await page.wait_for_load_state("domcontentloaded")
            await _human_delay(2, 4)

            await _click_tab_image_text(page)

            images = post_data.get("images", [])
            if images:
                await self._upload_images(page, images)

            title = post_data.get("title", "")
            if title:
                await self._fill_title(page, title)

            body = post_data.get("body", "")
            tags = post_data.get("tags", [])
            if body or tags:
                await self._fill_body(page, body, tags)

            if auto_publish:
                await _human_delay(1, 3)
                await self._click_publish(page)
                click.echo("帖子已发布")
                click.echo("浏览器将保持 15 秒供确认结果，之后自动关闭...")
                await asyncio.sleep(15)
            else:
                click.echo("\n内容已自动填写，请在浏览器中检查并手动点击「发布」")
                click.echo("发布成功后回到终端按 Enter 关闭浏览器...")
                try:
                    await _wait_for_enter()
                except EOFError:
                    click.echo("（终端无法接收输入，浏览器将保持 30 秒后自动关闭）")
                    await asyncio.sleep(30)
                await asyncio.sleep(3)

            return True

        except Exception:
            error_occurred = True
            click.echo("\n[错误] 发布过程中出现异常：")
            click.echo(traceback.format_exc())

            fallback_publish(post_data)
            return False

        finally:
            if not error_occurred:
                await page.close()

    # ------------------------------------------------------------------
    # 内部方法：各表单字段操作
    # ------------------------------------------------------------------

    async def _upload_images(self, page: Page, image_paths: list[str]):
        click.echo(f"  上传 {len(image_paths)} 张图片...")

        file_input = page.locator("input.upload-input").first
        if await file_input.count() > 0:
            await file_input.set_input_files(image_paths)
        else:
            click.echo("  [警告] 未找到图片上传入口，请手动上传")
            return

        wait_sec = min(len(image_paths) * 3, 30) + random.uniform(1, 3)
        await asyncio.sleep(wait_sec)
        click.echo("  图片上传完成，等待表单渲染...")
        await _human_delay(1.5, 3)

    async def _fill_title(self, page: Page, title: str):
        click.echo(f"  填写标题: {title}")

        el = await self._find_element(
            page,
            [
                'input[placeholder="填写标题会有更多赞哦"]',
                'input[placeholder*="标题"]',
                "input.d-text",
            ],
        )

        if el:
            await el.click()
            await _human_delay(0.3, 0.8)
            await _human_type(page, title)
        else:
            click.echo("  [警告] 未找到标题输入框，请手动填写")

    async def _fill_body(self, page: Page, body: str, tags: list[str] = None):
        click.echo("  填写正文...")

        el = await self._find_element(
            page,
            [
                "div.tiptap.ProseMirror",
                "div.ProseMirror",
                'div[contenteditable="true"]',
            ],
        )

        if not el:
            click.echo("  [警告] 未找到正文编辑器，请手动填写")
            return

        await el.click()
        await _human_delay(0.3, 0.8)
        await _human_type(page, body)
        await _human_delay(0.3, 0.8)

        if tags:
            click.echo(f"  添加标签: {', '.join(tags)}")
            for tag in tags:
                await page.keyboard.press("Enter")
                await _human_delay(0.3, 0.6)

                await _human_type(page, f"#{tag}")
                await _human_delay(1.5, 2.5)

                selected = await self._try_select_topic(page, tag)
                if selected:
                    click.echo(f"    已选择话题: #{tag}")
                else:
                    await page.keyboard.press("Space")
                    click.echo(f"    未匹配话题，已作为文本插入: #{tag}")
                await _human_delay(0.5, 1.0)

    async def _click_publish(self, page: Page):
        el = await self._find_element(
            page,
            [
                'button.d-button:has-text("发布")',
                'button:has-text("发布")',
            ],
        )

        if el:
            await el.click()
            await page.wait_for_load_state("domcontentloaded")
            await _human_delay(2, 4)
        else:
            click.echo("  [警告] 未找到发布按钮，请手动发布")

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    async def _try_select_topic(self, page: Page, tag: str) -> bool:
        """尝试从话题建议弹窗中选择匹配的话题。

        依次尝试多组选择器，等待弹窗出现后点击第一个匹配项。
        """
        selectors = [
            f'div[class*="topic-item"]:has-text("{tag}")',
            f'div[class*="hash-tag"]:has-text("{tag}")',
            f'li[class*="topic"]:has-text("{tag}")',
            f'[class*="suggest"] [class*="item"]:has-text("{tag}")',
            f'[class*="mention"] [class*="item"]:has-text("{tag}")',
            f'[class*="topic"]:has-text("{tag}")',
            f'[class*="suggest"]:has-text("{tag}")',
            f'li:has-text("{tag}")',
        ]

        for attempt in range(2):
            for selector in selectors:
                try:
                    el = page.locator(selector).first
                    if await el.count() > 0 and await el.is_visible():
                        await el.scroll_into_view_if_needed()
                        await _human_delay(0.1, 0.3)
                        await el.click(force=True)
                        await _human_delay(0.3, 0.6)
                        return True
                except Exception:
                    continue

            if attempt == 0:
                await _human_delay(1.0, 1.5)

        return False

    async def _find_element(self, page: Page, selectors: list[str]):
        """按优先级依次尝试多个选择器，返回第一个可见的元素。"""
        for selector in selectors:
            try:
                el = page.locator(selector).first
                if await el.count() > 0 and await el.is_visible():
                    return el
            except Exception:
                continue
        return None


async def _click_tab_image_text(page: Page):
    """点击「上传图文」标签，确保进入图文发布模式。

    页面中存在两个「上传图文」节点，一个被移到 left:-9999px 的隐藏克隆，
    需过滤掉该克隆，点击真正可见的 .creator-tab 元素。
    """
    tabs = page.locator(
        'div.creator-tab:not([style*="-9999"])'
    ).filter(has_text="上传图文")
    count = await tabs.count()
    if count > 0:
        await tabs.first.click()
        await _human_delay(1.0, 2.0)
        click.echo("  已切换到「上传图文」标签")
    else:
        click.echo("  [提示] 未找到「上传图文」标签，跳过切换")


async def _wait_for_enter():
    """异步等待用户按 Enter。"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, input)
