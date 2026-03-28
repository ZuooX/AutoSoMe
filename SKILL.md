---
name: auto-so-me
description: >-
  Product GTM & personal IP marketing agent for Xiaohongshu and WeChat MP. Two modes:
  product-gtm reads product project files to generate promotional copy;
  personal-log reads personal journals to generate authentic personal IP content.
  Both modes generate cover images and publish to Xiaohongshu / WeChat Official Account.
  Use when the user wants to promote a product, build personal IP, generate social
  media content, write Xiaohongshu / WeChat posts, or publish to social platforms.
---

# AutoSoMe — 产品 GTM & 个人 IP 营销 Agent

两种内容模式：**产品推广**（product-gtm）读取产品项目文件生成推广文案；**个人日志**（personal-log）读取个人日志生成真实感个人 IP 内容。两种模式共享封面图生成与多平台半自动发布能力（小红书 + 微信公众号）。

## 模式识别

| 用户意图关键词 | 模式 | 说明 |
|--------------|------|------|
| 推广、产品、GTM、分析产品 | `product-gtm` | 默认模式 |
| 基于这篇文章/素材/经验推广、用这篇稿子生成文案 | `product-gtm` + 内容稿件 | v0.3 新增，指定外部素材文件 |
| 个人日志、日记、个人 IP、成长记录、游玩 | `personal-log` | v0.2 新增 |
| 发布、发到小红书 | 取决于当前上下文 | 平台 `xhs`，检查 mode |
| 发到公众号、生成公众号文案、微信公众号 | 取决于当前上下文 | 平台 `mp`，检查 mode |
| 也发到公众号、跨平台 | 取决于当前上下文 | 跨平台搬运（用已有帖子 prepare -p mp） |

---

## 模式一：product-gtm（产品推广）

### 快速指令

| 用户输入 | 执行流程 |
|---------|---------|
| 「帮我推广这个项目」「分析一下这个产品」 | F1 → F2 → F3 → F4 |
| 「生成 N 篇小红书文案」 | 检查 F1 → F2 → F3-XHS → F4 |
| 「生成 N 篇公众号文案」 | 检查 F1 → F2 → F3-MP → F4 |
| 「基于这篇文章推广」+ 文件路径 | 检查 F1 → F2(稿件模式) → F3 → F4 |
| 「用这篇经验稿生成 3 篇公众号」+ 路径 | 检查 F1 → F2(稿件模式) → F3-MP → F4 |
| 「换个角度再来几篇」 | F2 → F3 → F4（复用 profile） |
| 「发布第 N 篇」「发到小红书」 | F5（xhs） |
| 「发到公众号」「把这几篇也发公众号」 | F5（mp，跨平台 prepare） |
| 「之前生成过哪些」 | F6 |
| 「语气轻松一点」「标题改一下」 | F3 局部修改 |

### 工作流程

#### 第一步：确认产品项目与素材来源

当用户提及推广或生成文案时：

1. 确认目标产品的项目路径（当前工作区 or 用户指定路径）
2. 识别**素材来源类型**：

| 素材来源 | 识别方式 | F1 行为 | F2 行为 |
|---------|---------|---------|---------|
| **产品项目**（默认） | 「帮我推广这个项目」 | 扫描项目文件生成 product-profile.md | 从产品特性选标准角度 |
| **内容稿件** | 用户提供了具体文件路径 + 「基于/用这篇」 | 确保 product-profile.md 存在，读取稿件 | 从稿件内容提炼角度 |
| **混合** | 「推广这个项目，参考这篇经验」 | 扫描项目 + 读取稿件 | 综合两者规划角度 |

3. 检查 `<项目根>/.auto-so-me/product-profile.md` 是否存在
   - **不存在** → 执行 F1 产品理解
   - **已存在** → 读取并询问是否需要更新，然后跳到 F2

#### 第二步：F1 产品理解

读取 [prompts/product-understanding.md](prompts/product-understanding.md)，按其中的指令执行：
1. 扫描项目文件
2. 生成产品理解报告
3. 用户确认或修正
4. 锁定并写入 `<项目根>/.auto-so-me/product-profile.md`

> 当素材来源是「内容稿件」时，product-profile.md 仍然需要（提供产品上下文），但如果已存在则无需重新生成。

#### 第三步：F2 内容策略 + F3 文案生成

读取 [prompts/content-strategy.md](prompts/content-strategy.md)，规划内容角度并输出策略大纲。

**F2 根据素材来源有两种模式**：

- **标准模式**（无稿件）：从 product-profile.md 出发，在 6 种标准角度中选取
- **稿件模式**（有外部稿件）：读取稿件内容，从中提炼角度。稿件中自带的角度建议优先采用，也可映射到标准角度体系。稿件路径记录到策略大纲中。

用户确认后，根据目标平台选择对应的文案 Prompt：

- **小红书（默认）**：读取 [prompts/xiaohongshu-copywriting.md](prompts/xiaohongshu-copywriting.md)，输出到 `xhs-output/`
- **微信公众号**：读取 [prompts/wechat-mp-copywriting.md](prompts/wechat-mp-copywriting.md)，输出到 `mp-output/`

如果用户未指定平台，默认生成小红书文案。用户可以说「也出一版公众号的」来额外生成。

> **稿件模式下的文案生成**：F3 应同时参考 product-profile.md（产品上下文）和稿件原文（具体内容素材）。文案的事实和细节应忠于稿件原文，不可凭空编造。

**小红书文案**写入 `<项目根>/.auto-so-me/campaigns/<batch>/xhs-output/<post-name>/content.md`：

```yaml
---
title: "标题"
tags:
  - 标签1
  - 标签2
source_file: ""              # 可选，稿件模式时记录素材来源路径
---

正文内容
```

**公众号文案**写入 `<项目根>/.auto-so-me/campaigns/<batch>/mp-output/<post-name>/content.md`：

```yaml
---
platform: mp
title: "标题"
digest: "摘要文字，120字以内"
author: ""
tags:
  - 标签1
  - 标签2
source_file: ""              # 可选，稿件模式时记录素材来源路径
---

正文内容（Markdown 格式，含小标题）
```

#### 第四步：F4 封面图生成

读取 [prompts/cover-image.md](prompts/cover-image.md)，为每篇文案生成封面图。
封面图保存为同目录下的 `cover.png`。

#### 第五步：F5 发布

三种发布方式，按推荐程度排列：

**方式一：`prepare` 命令 + 手动发布**（最安全，零风险）

```bash
# 小红书：准备单篇（标题复制到剪贴板 + 终端输出完整内容）
python -m autosome prepare --post "<项目根>/.auto-so-me/campaigns/<batch>/xhs-output/<post-name>"

# 小红书：准备时复制正文（含标签）到剪贴板
python -m autosome prepare --post "<path>" --copy-body

# 微信公众号：准备单篇
python -m autosome prepare -p mp --post "<项目根>/.auto-so-me/campaigns/<batch>/mp-output/<post-name>"

# 微信公众号：跨平台搬运（将小红书帖子适配为公众号格式）
python -m autosome prepare -p mp --post "<xhs帖子目录>" --copy-body
```

用户在对应平台手动粘贴内容发布。

**方式二：Chrome DevTools MCP 浏览器自动化**（推荐，安全可控）

通过 Chrome DevTools MCP 操控用户的**真实 Chrome 浏览器**，在用户已登录的会话中自动填写表单。
与 Playwright 方案不同，这种方式使用用户真实的浏览器环境，平台无法区分自动化与手动操作。

- **小红书发布**：读取 [prompts/browser-publish-xhs.md](prompts/browser-publish-xhs.md)，按其中的步骤使用 MCP 工具操作浏览器
- **公众号发布**：读取 [prompts/browser-publish-mp.md](prompts/browser-publish-mp.md)，按其中的步骤使用 MCP 工具操作浏览器

关键规则：
- 发布前**必须截图**让用户确认内容
- 用户**未明确说「发布」**前禁止点击发布按钮
- 公众号默认**保存为草稿**，用户手机预览后再群发

**方式二（进阶）：`publish -p mp` CDP 自动化**（推荐用于公众号，代码已固化）

直接通过 Playwright CDP 连接已登录的 Chrome，自动填写标题/正文/摘要/封面图并保存为草稿。

前提：Chrome 需以调试模式启动（一次性操作，登录状态持久化）：
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=9222 \
    --user-data-dir=~/.chrome-debug-profile
# 首次在弹出的 Chrome 中登录 https://mp.weixin.qq.com
```

发布命令：
```bash
# 公众号单篇（CDP 自动填写 + 保存草稿）
python -m autosome publish -p mp --post "<项目根>/.auto-so-me/campaigns/<batch>/mp-output/<post-name>" \
    --project "<项目根>"

# 指定自定义 CDP 端口
python -m autosome publish -p mp --post "<path>" --cdp-port 9223
```

**方式三：Playwright 浏览器自动化**（legacy，仅 xhs，有账号检测风险）

```bash
python -m autosome publish -p xhs --post "<path>"
```

> 此方式使用独立浏览器实例，平台可能检测到自动化操作。推荐优先使用方式一或方式二。

#### 第六步：F6 历史追踪

每次生成文案后，通过 CLI 写入历史记录。发布成功后自动更新状态。
新批次生成前读取该文件，避免角度重复。

```bash
# 添加历史记录（文案生成后由 Agent 调用）
python -m autosome add-entry --project "<项目根>" \
  --product "PM Agent" \
  --id "2026-03-22-batch-1-post-1" \
  --batch "2026-03-22-batch-1" \
  --angle "pain-point" \
  --title "标题" \
  --tags "#AI工具,#产品经理" \
  --file "campaigns/2026-03-22-batch-1/xhs-output/post-1-pain-point/content.md"

# 查看历史记录
python -m autosome history --project "<项目根>" --angles

# 标记为已发布
python -m autosome mark-published --project "<项目根>" --id "2026-03-22-batch-1-post-1"

# 查看已用/可用角度
python -m autosome used-angles --project "<项目根>"
```

---

## 模式二：personal-log（个人日志 / 个人 IP）

### 快速指令

| 用户输入 | 执行流程 |
|---------|---------|
| 「个人日志模式，Obsidian 库在 ~/WorkspaceOB」 | 切换 personal-log + F1 |
| 「用这篇日志生成小红书：03-个人与成长/xxx.md」 | 检查 F1 → F2(指定文件) → F3-XHS → F4 → F5 |
| 「用这篇日志生成公众号文章」 | 检查 F1 → F2(指定文件) → F3-MP → F4 → F5 |
| 「从 03-个人与成长/ 选素材，出 2 篇」 | 检查 F1 → F2(指定目录) → F3 → F4 → F5 |
| 「1 篇成长 1 篇游玩」 | F2 指定子场景 |
| 「脱敏表没问题，可以发第 1 篇」 | F5 通过 → F6 |
| 「也发一版到公众号」 | F5 通过 → F6（mp，跨平台 prepare） |
| 「别再用上个月那篇素材了」 | F7 排除 → 重新 F2 |
| 「之前发过哪些」 | F7 查看历史 |

### 素材指定方式

用户可灵活指定素材来源（三种方式可组合），**Agent 不得自行扩大读取范围**：

| 方式 | 示例 | 适用场景 |
|------|------|---------|
| **指定文件** | "用这篇：`03-个人与成长/26年3月个人日志.md`" | 最精确、最安全，适合单次加工 |
| **指定目录** | "从 `03-个人与成长/能力圈与商业探索/` 选素材" | 某一类主题批量选题 |
| **库根 + 排除** | "Obsidian 库整体扫描，排除 `04-财务管理`" | 初次建档或大范围选题 |

### 工作流程

#### 第一步：确认路径与叙事档案

当用户提及个人日志、个人 IP 或日记时：

1. 确认 `personal_output_root`（个人内容输出根目录）
   - **未指定 → 必须追问**，禁止默认写入当前 Cursor 工作区的产品项目
   - 检查 `<personal_output_root>/config.local.md` 是否已有持久化配置，有则复用
2. 确认**素材来源**（具体文件、目录、或 Obsidian 库 + 排除规则）
   - 用户未明确开放的目录/文件，**不得主动读取**
3. 检查 `<personal_output_root>/personal-profile.md` 是否存在
   - **不存在** → 执行 F1
   - **已存在** → 读取并询问是否需要更新

#### 第二步：F1 个人日志库理解

读取 [prompts/personal-log-understanding.md](prompts/personal-log-understanding.md)，按其中的指令执行：
1. 按用户指定的素材范围读取 Markdown 文件
2. 生成「人物与叙事摘要」
3. 用户确认或修正（人设关键词、内容边界）
4. 锁定并写入 `<personal_output_root>/personal-profile.md`
5. 持久化路径配置到 `<personal_output_root>/config.local.md`

#### 第三步：F2 多场景归类与选题 + F3 真实感文案

读取 [prompts/personal-log-strategy.md](prompts/personal-log-strategy.md)，归类日志子场景并输出选题大纲。
用户确认后，根据目标平台选择对应的文案 Prompt：

- **小红书（默认）**：读取 [prompts/personal-log-copywriting.md](prompts/personal-log-copywriting.md)，输出到 `xhs-output/`
- **微信公众号**：读取 [prompts/personal-log-mp-copywriting.md](prompts/personal-log-mp-copywriting.md)，输出到 `mp-output/`

**小红书文案**写入 `<personal_output_root>/campaigns/<batch>/xhs-output/<post-name>/content.md`：

```yaml
---
mode: personal-log
sub_scenes:
  - growth
source_date_range: "2026-03-15 ~ 2026-03-21"
title: "标题"
tags:
  - 标签1
  - 标签2
status: draft
desensitization_confirmed: false
---

正文内容
```

**公众号文案**写入 `<personal_output_root>/campaigns/<batch>/mp-output/<post-name>/content.md`：

```yaml
---
platform: mp
mode: personal-log
sub_scenes:
  - growth
source_date_range: "2026-03-15 ~ 2026-03-21"
title: "标题"
digest: "摘要文字，120字以内"
author: ""
tags:
  - 标签1
  - 标签2
status: draft
desensitization_confirmed: false
---

正文内容（Markdown 格式，含小标题）
```

#### 第四步：F4 封面图生成

读取 [prompts/cover-image.md](prompts/cover-image.md)（使用 personal-log 子场景风格映射），为每篇文案生成封面图。

#### 第五步：F5 脱敏与可发布性闸门（必经）

读取 [prompts/desensitization-gate.md](prompts/desensitization-gate.md)，逐篇输出脱敏检查表。

**关键规则**：
- 用户未明确确认「可以发布」前，**禁止触发浏览器发布**
- 确认后将 content.md 的 `desensitization_confirmed` 更新为 `true`，`status` 更新为 `publish_ready`

#### 第六步：F6 发布（复用 product-gtm）

仅当 `desensitization_confirmed: true` 时可执行。

三种发布方式（同 product-gtm，但必须先通过脱敏闸门）：

**方式一：`prepare` + 手动发布**（最安全）

```bash
# 小红书
python -m autosome prepare --post "<personal_output_root>/campaigns/<batch>/xhs-output/<post-name>" --copy-body

# 微信公众号
python -m autosome prepare -p mp --post "<personal_output_root>/campaigns/<batch>/mp-output/<post-name>" --copy-body

# 跨平台搬运
python -m autosome prepare -p mp --post "<personal_output_root>/campaigns/<batch>/xhs-output/<post-name>" --copy-body
```

**方式二：Chrome DevTools MCP 浏览器自动化**（推荐，安全可控）

操控用户的真实 Chrome 浏览器，平台无法区分自动化与手动操作。

- **小红书**：读取 [prompts/browser-publish-xhs.md](prompts/browser-publish-xhs.md)
- **公众号**：读取 [prompts/browser-publish-mp.md](prompts/browser-publish-mp.md)

**方式三：Playwright 自动化**（legacy，有账号检测风险）

```bash
python -m autosome publish -p xhs --post "<path>"
```

#### 第七步：F7 个人向历史追踪

发布成功后写入 `<personal_output_root>/history-personal.json`。
新批次规划时读取历史，避免短期内重复消费同一素材或故事线。

```bash
# 查看个人向历史
python -m autosome history --project "<personal_output_root>" --mode personal

# 标记已发布
python -m autosome mark-published --project "<personal_output_root>" --id "<entry-id>"
```

---

## 示例输出

- 产品理解报告示例：[examples/sample-product-profile.md](examples/sample-product-profile.md)
- 小红书文案示例：[examples/sample-post.md](examples/sample-post.md)

## 文件结构

### product-gtm（产品推广 — 写入产品项目）

```
<产品项目根>/
└── .auto-so-me/
    ├── product-profile.md          # F1 产品理解报告
    ├── history.json                # F6 历史追踪
    └── campaigns/
        └── <YYYY-MM-DD>-batch-N/
            ├── xhs-output/         # 小红书文案
            │   ├── post-1-<angle>/
            │   │   ├── content.md
            │   │   └── cover.png
            │   └── post-2-<angle>/
            │       ├── content.md
            │       └── cover.png
            └── mp-output/          # 微信公众号文案（可选）
                ├── post-1-<angle>/
                │   ├── content.md
                │   └── cover.png
                └── post-2-<angle>/
                    ├── content.md
                    └── cover.png
```

### personal-log（个人日志 — 写入独立输出目录）

```
<personal_output_root>/
├── config.local.md                 # 路径配置
├── personal-profile.md             # F1 叙事摘要
├── history-personal.json           # F7 个人向历史
└── campaigns/
    └── <YYYY-MM-DD>-batch-N/
        ├── strategy.md
        ├── desensitization-checklist.md
        ├── xhs-output/             # 小红书文案
        │   ├── post-1-<sub_scene>/
        │   │   ├── content.md
        │   │   └── cover.png
        │   └── post-2-<sub_scene>/
        │       ├── content.md
        │       └── cover.png
        └── mp-output/              # 微信公众号文案（可选）
            ├── post-1-<sub_scene>/
            │   ├── content.md
            │   └── cover.png
            └── post-2-<sub_scene>/
                ├── content.md
                └── cover.png
```
