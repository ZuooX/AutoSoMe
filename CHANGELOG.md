# CHANGELOG — 需求偏差记录

> 仅记录实现与需求稿的偏差，不是 git commit log。
> 需求稿位于 PM Agent 工作区 `GenerateUI/projects/auto-so-me/sprints/`。

---

## 2026-03-25

### 变更
- **涉及功能**：F4 配图生成 — 从单封面升级为多图 carousel
- **需求稿原设计**：每篇文案仅生成 1 张封面图（cover.png）
- **实际实现**：基于小红书平台数据调研，将配图策略升级为 carousel 模式（≥ 4 张，干货类 6-9 张）；`cover-image.md` 改名为配图生成指令，支持逐张生成风格统一的图组；`xiaohongshu-copywriting.md` 新增配图策略章节和 carousel frontmatter 字段；`content-strategy.md` 新增配图数量指引和角度→图片类型映射
- **原因**：小红书 < 3 张图会被判定"内容单薄"限流，≥ 6 张是爆款门槛；首图决定 80% 流量

### 新增
- **涉及功能**：F5 发布 — 公众号 CDP 自动化代码固化
- **需求稿原设计**：公众号发布仅有 prepare 手动方式
- **实际实现**：`WechatMPPublisher` 类基于 Playwright CDP 实现完整公众号填写流程（标题/正文/摘要/封面图/保存草稿）；`publish -p mp` 命令新增 `--cdp-port` 参数，自动检测 CDP 端口可用性；`check_cdp_available()` 工具函数供 CLI 使用
- **原因**：手动调试确认了编辑器 DOM 结构（ProseMirror、`#js_description`、`.tool_bar__fold-btn` 等），可稳定复用；CDP 连接真实 Chrome 无账号风险

---

## 2026-03-24

### 新增
- **涉及功能**：F2 内容策略 — 内容稿件素材来源
- **需求稿原设计**：product-gtm 仅支持扫描产品项目文件作为素材来源
- **实际实现**：新增「内容稿件」素材模式，用户可提供外部文档（如使用经验、技术文章）作为 F2 策略和 F3 文案的内容来源；F2 从稿件中提炼角度（而非仅用 6 种标准角度）；frontmatter 新增 `source_file` 可选字段追踪素材来源
- **原因**：实际推广中，除了产品本身的功能特性，用户的个人使用经验也是重要素材来源

### 变更
- **涉及功能**：F5 发布 — 浏览器自动化方案迁移
- **需求稿原设计**：Playwright 独立浏览器实例自动化
- **实际实现**：引入 Chrome DevTools MCP（Google 官方开源）作为推荐浏览器自动化方案，操控用户真实 Chrome 浏览器；Playwright 方案降级为 legacy
- **原因**：Playwright 独立实例易被平台检测为自动化；Chrome DevTools MCP 操控真实 Chrome，与手动操作无异，安全性大幅提升

### 新增
- **涉及功能**：F5 发布 — Chrome DevTools MCP 发布指令
- **需求稿原设计**：无此方案
- **实际实现**：新增 `prompts/browser-publish-xhs.md` 和 `prompts/browser-publish-mp.md`，指导 Agent 通过 MCP 工具完成小红书和公众号的浏览器自动化发布
- **原因**：Chrome DevTools MCP 作为 MCP Server 运行，Agent 通过 Prompt 指令调用其工具完成发布

### 新增
- **涉及功能**：多平台发布 — 微信公众号支持
- **需求稿原设计**：README 标注"计划中"，无具体需求稿
- **实际实现**：新增公众号专属文案 Prompt（product-gtm + personal-log 各一份）、`prepare -p mp` 命令、`mp-output/` 输出目录、跨平台搬运支持（将 xhs 帖子适配为公众号格式）
- **原因**：用户需求驱动，第一期以 prepare 手动发布为主降低实现风险

---

## 2026-03-23

### 新增
- **涉及功能**：文档 — `dashboard.html` 可视化项目大盘
- **需求稿原设计**：无此产物
- **实际实现**：新增 dashboard.html，以暗色单页形式可视化展示双模式架构、功能大盘、工作流程（Mermaid）、CLI 操作手册、角度/子场景体系、项目结构
- **原因**：README 纯文本不够直观，可视化大盘便于快速理解全貌和查阅 CLI 命令

### 新增
- **涉及功能**：工程 — 开发变更记录规范
- **需求稿原设计**：无此机制
- **实际实现**：新增 `.cursor/rules/changelog.mdc`（alwaysApply）+ `CHANGELOG.md`，要求 Agent 在实现偏离需求稿时自动追加记录
- **原因**：Vibe-coding 过程中容易偏离需求稿且无记录，需要结构化追踪

### 变更
- **涉及功能**：文档 — README.md
- **需求稿原设计**：v0.1 README 仅覆盖 product-gtm 单模式
- **实际实现**：重写 README，覆盖 v0.2 双模式（product-gtm + personal-log），新增模式概览表、personal-log 快速指令、prepare 命令推荐、子场景体系、双模式生成内容目录结构、完整 8 个 prompt 文件的项目结构
- **原因**：代码已实现 v0.2 但 README 停留在 v0.1，文档与实现严重脱节
