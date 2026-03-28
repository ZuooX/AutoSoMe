# 浏览器自动化发布 — 小红书

通过 Chrome DevTools MCP 工具在用户的真实 Chrome 浏览器中完成小红书发布。

## 前置条件

- Chrome DevTools MCP 已配置并可用
- 用户的 Chrome 浏览器中已登录小红书创作者平台（https://creator.xiaohongshu.com）
- 帖子的 `content.md` 已生成且经用户确认

## 发布流程

### Step 1: 读取帖子数据

从 `content.md` 中提取：
- `title`：标题
- `body`：正文
- `tags`：标签列表
- 同目录下的图片文件（cover.* 排第一张）

### Step 2: 打开发布页

```
使用 navigate_page 打开 https://creator.xiaohongshu.com/publish/publish
```

等待页面加载完成。

### Step 3: 点击「上传图文」标签

页面中可能有多个 tab，需要点击「上传图文」进入图文发布模式。使用 `click` 工具点击可见的包含"上传图文"文字的 tab 元素。

### Step 4: 上传图片

使用 `upload_file` 工具，选择器为 `input.upload-input`，上传所有图片文件（cover 排第一张）。

上传后等待 3-5 秒让图片处理完成。使用 `take_screenshot` 确认图片已上传成功。

### Step 5: 填写标题

使用 `fill` 或 `click` + `type_text` 填写标题输入框。候选选择器（按优先级）：
1. `input[placeholder="填写标题会有更多赞哦"]`
2. `input[placeholder*="标题"]`
3. `input.d-text`

### Step 6: 填写正文

正文编辑器是 contenteditable 的富文本区域。候选选择器：
1. `div.tiptap.ProseMirror`
2. `div.ProseMirror`
3. `div[contenteditable="true"]`

使用 `click` 点击编辑区，然后 `type_text` 输入正文内容。

### Step 7: 添加标签

在正文编辑器中，对每个标签：
1. 按 Enter 换行
2. 输入 `#标签名`
3. 等待 1-2 秒让话题建议弹出
4. 如果看到匹配的话题建议，点击选择；否则按 Space 确认为文本

### Step 8: 截图确认

使用 `take_screenshot` 截取当前页面，展示给用户确认：
- 图片是否正确上传
- 标题是否正确
- 正文和标签是否完整

**必须等待用户明确确认「可以发布」后，才能执行下一步。**

### Step 9: 点击发布

用户确认后，点击页面上的「发布」按钮。候选选择器：
1. `button:has-text("发布")`
2. `button.d-button:has-text("发布")`

发布后等待页面跳转，使用 `take_screenshot` 确认发布成功。

## 异常处理

| 场景 | 处理方式 |
|------|---------|
| 未登录 | 截图告知用户，请用户在 Chrome 中手动登录后重试 |
| 图片上传失败 | 截图确认，提示用户手动上传 |
| 找不到输入框 | 使用 `take_screenshot` 截图分析页面状态，尝试替代选择器 |
| 发布按钮不可点击 | 截图告知用户，可能缺少必填项 |

## 安全原则

- **必须**在发布前截图让用户确认
- **禁止**在用户未确认的情况下自动点击发布
- personal-log 模式必须先通过脱敏闸门（`desensitization_confirmed: true`）
- 发布间隔建议 ≥ 3 分钟
