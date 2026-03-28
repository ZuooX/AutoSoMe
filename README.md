# AutoSoMe — 产品 GTM & 个人 IP 营销 Agent

两种内容模式：**产品推广**（product-gtm）读取产品项目文件生成推广文案；**个人日志**（personal-log）读取个人日志生成真实感个人 IP 内容。两种模式共享封面图生成与多平台半自动发布能力（小红书 + 微信公众号）。

## 架构

AutoSoMe 由两部分组成：

| 组件 | 职责 | 形态 |
|------|------|------|
| **Cursor Skill** | 产品/日志理解、内容策略、文案生成、封面图生成、脱敏审查 | SKILL.md + Prompt 文件 |
| **Python CLI** | 内容准备、历史追踪 | `autosome/` Python 包 |
| **Chrome DevTools MCP** | 浏览器自动化发布（操控真实 Chrome） | MCP Server |

```
Cursor Skill 生成内容 → 写入目录结构 → CLI prepare 输出到剪贴板手动发布（最安全）
                                       → Chrome DevTools MCP 浏览器自动化（推荐）
                                       → CLI publish Playwright 自动化（legacy）
```

## 模式概览

| 模式 | 触发关键词 | 核心流程 | 输出位置 |
|------|-----------|---------|---------|
| **product-gtm** | 推广、产品、GTM | F1 产品理解 → F2 策略 → F3 文案 → F4 封面 → F5 发布 → F6 追踪 | `<产品项目根>/.auto-so-me/` |
| **personal-log** | 个人日志、日记、个人 IP | F1 日志理解 → F2 选题 → F3 文案 → F4 封面 → F5 脱敏 → F6 发布 → F7 追踪 | `<personal_output_root>/` |

## 快速开始

### 1. 安装依赖

```bash
cd AutoSoMe
pip install -r requirements.txt
```

Chrome DevTools MCP 会在 Cursor 中自动启用（已配置在 `.cursor/mcp.json`），无需额外安装。

> Playwright（legacy）：如仍需使用旧版浏览器自动化，额外执行 `playwright install chromium`。

### 2. 部署 Cursor Skill

```bash
ln -sf "$(pwd)" ~/.cursor/skills-cursor/auto-so-me
```

部署后，在任意 Cursor 工作区中即可使用 AutoSoMe Skill。

### 3. 使用（product-gtm 模式）

在 Cursor 中对话：

| 你说 | Agent 执行 |
|------|-----------|
| 「帮我推广这个项目」 | F1 → F2 → F3 → F4 全流程 |
| 「生成 3 篇小红书文案」 | 检查 F1 → F2 → F3-XHS → F4 |
| 「生成 3 篇公众号文案」 | 检查 F1 → F2 → F3-MP → F4 |
| 「换个角度再来几篇」 | F2 → F3 → F4（复用 profile） |
| 「发布第 1 篇」 | F5 发布 |
| 「发到公众号」 | F5 公众号 prepare |
| 「之前生成过哪些」 | F6 历史查询 |
| 「语气轻松一点」「标题改一下」 | F3 局部微调 |

### 4. 使用（personal-log 模式）

| 你说 | Agent 执行 |
|------|-----------|
| 「个人日志模式，Obsidian 库在 ~/WorkspaceOB」 | 切换 personal-log + F1 |
| 「用这篇日志生成小红书：03-个人与成长/xxx.md」 | F1 → F2 → F3 → F4 → F5 脱敏 |
| 「从 03-个人与成长/ 选素材，出 2 篇」 | F1 → F2 → F3 → F4 → F5 脱敏 |
| 「脱敏表没问题，可以发第 1 篇」 | F6 发布 |
| 「之前发过哪些」 | F7 历史查询 |

### 5. 发布

三种方式，按推荐程度排列：

**方式一：`prepare` 命令 + 手动发布**（最安全，零风险）

```bash
# 小红书
python -m autosome prepare --post "<path>" --copy-body

# 微信公众号
python -m autosome prepare -p mp --post "<path>" --copy-body

# 跨平台搬运（小红书 → 公众号）
python -m autosome prepare -p mp --post "<xhs-post-dir>" --copy-body
```

**方式二：`publish -p mp` CDP 自动化**（公众号推荐，代码已固化）

> **注意**：调试 Chrome 与主 Chrome 使用独立配置目录，互不影响。但两者**不能同时从 Dock 打开**——调试 Chrome 运行时点 Dock 图标会切换到调试窗口。
> 推荐节奏：主 Chrome 用完 `Cmd+Q` → 启动调试 Chrome → 发布 → `Cmd+Q` → 从 Dock 重新打开主 Chrome。

建议先添加 shell 别名（一次性）：

```bash
echo 'alias chrome-debug="/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=$HOME/.chrome-debug-profile"' >> ~/.zshrc && source ~/.zshrc
```

首次使用：

```bash
chrome-debug
# 在弹出的 Chrome 中登录 https://mp.weixin.qq.com（仅首次需要，之后自动复用登录态）
```

然后运行：

```bash
python -m autosome publish -p mp \
    --post "<项目根>/.auto-so-me/campaigns/<batch>/mp-output/<post-name>" \
    --project "<项目根>"
```

CLI 自动检测 CDP 端口 → 连接 Chrome → 填写标题/正文/摘要/封面图 → 保存草稿。

**方式二（备选）：Chrome DevTools MCP 浏览器自动化**（在 Cursor 对话中使用）

在 Cursor 对话中告诉 Agent「帮我发布到小红书/公众号」，Agent 会：
1. 通过 Chrome DevTools MCP 操控你的**真实 Chrome 浏览器**
2. 自动填写标题、正文、上传图片
3. 截图让你确认后再点击发布

**方式三：Playwright 自动化**（legacy，有账号检测风险）

```bash
python -m autosome login -p xhs     # 首次登录
python -m autosome publish -p xhs --post "<path>"
```

> 此方式使用独立浏览器实例，平台可能检测到自动化操作。推荐优先使用方式一或方式二。

### 6. 历史追踪

```bash
# 产品推广历史
python -m autosome history --project . --angles

# 个人日志历史
python -m autosome history --project "<personal_output_root>" --mode personal --angles

# 标记已发布
python -m autosome mark-published --project . --id "<entry-id>"

# 个人日志标记已发布
python -m autosome mark-published --project "<personal_output_root>" --mode personal --id "<entry-id>"

# 查看可用角度
python -m autosome used-angles --project .
```

## 功能列表

### product-gtm（产品推广）

| 编号 | 功能 | 状态 | 实现方 |
|------|------|------|-------|
| F1 | 产品理解引擎 | ✅ 已完成 | Skill |
| F2 | 内容策略规划（6 种角度） | ✅ 已完成 | Skill |
| F3 | 小红书文案生成 | ✅ 已完成 | Skill |
| F3-MP | 公众号文案生成 | ✅ 已完成 | Skill |
| F4 | 封面图生成 | ✅ 已完成 | Skill |
| F5 | 半自动发布（prepare + 浏览器自动化） | ✅ 已完成 | CLI |
| F6 | 历史内容追踪 | ✅ 已完成 | CLI + Skill |

### personal-log（个人日志）

| 编号 | 功能 | 状态 | 实现方 |
|------|------|------|-------|
| F1 | 个人日志库理解（叙事档案） | ✅ 已完成 | Skill |
| F2 | 多场景归类与选题 | ✅ 已完成 | Skill |
| F3 | 真实感文案生成（小红书） | ✅ 已完成 | Skill |
| F3-MP | 真实感文案生成（公众号） | ✅ 已完成 | Skill |
| F4 | 封面图生成（个人风格映射） | ✅ 已完成 | Skill |
| F5 | 脱敏与可发布性闸门 | ✅ 已完成 | Skill |
| F6 | 半自动发布（复用 product-gtm） | ✅ 已完成 | CLI |
| F7 | 个人向历史追踪 | ✅ 已完成 | CLI + Skill |

## 内容角度 / 子场景体系

### product-gtm：6 种内容角度

| 角度 ID | 名称 | 内容结构 |
|---------|------|---------|
| pain-point | 痛点切入 | 痛点共鸣 → 方案 → 产品 → CTA |
| scenario | 场景展示 | 场景 → 使用 → 对比 → CTA |
| comparison | 对比测评 | 痛点 → 新方案 → 对比 → CTA |
| tutorial | 教程干货 | 步骤 → 演示 → 总结 → CTA |
| showcase | 成果展示 | 成果 → 过程 → 揭秘 → CTA |
| story | 个人故事 | 背景 → 问题 → 方案 → 成果 |

### personal-log：4 种子场景

| 子场景 | 名称 | 内容倾向 |
|--------|------|---------|
| growth | 成长 | 学习、习惯、职业思考、复盘 |
| travel | 游玩出行 | 行程体验、城市印象 |
| reflection | 日常思考 | 观点、情绪、价值观 |
| life | 其它生活 | 可分享日常 |

## 生成内容目录结构

### product-gtm（写入产品项目）

```
<产品项目根>/
└── .auto-so-me/
    ├── product-profile.md          # F1 产品理解报告
    ├── history.json                # F6 历史追踪
    └── campaigns/
        └── YYYY-MM-DD-batch-N/
            ├── strategy.md         # F2 内容策略大纲
            ├── xhs-output/         # 小红书文案
            │   ├── post-1-pain-point/
            │   │   ├── content.md
            │   │   └── cover.png
            │   └── post-2-tutorial/
            │       ├── content.md
            │       └── cover.png
            └── mp-output/          # 公众号文案（可选）
                ├── post-1-pain-point/
                │   ├── content.md
                │   └── cover.png
                └── post-2-tutorial/
                    ├── content.md
                    └── cover.png
```

### personal-log（写入独立输出目录）

```
<personal_output_root>/
├── config.local.md                 # 路径配置（Obsidian 库、排除目录等）
├── personal-profile.md             # F1 叙事档案
├── history-personal.json           # F7 个人向历史
└── campaigns/
    └── YYYY-MM-DD-batch-N/
        ├── strategy.md             # F2 选题大纲
        ├── desensitization-checklist.md  # F5 脱敏检查表
        ├── xhs-output/             # 小红书文案
        │   ├── post-1-growth/
        │   │   ├── content.md
        │   │   └── cover.png
        │   └── post-2-travel/
        │       ├── content.md
        │       └── cover.png
        └── mp-output/              # 公众号文案（可选）
            ├── post-1-growth/
            │   ├── content.md
            │   └── cover.png
            └── post-2-travel/
                ├── content.md
                └── cover.png
```

## 项目结构

```
AutoSoMe/
├── SKILL.md                           # Cursor Skill 入口（双模式）
├── prompts/                           # Prompt 指令文件
│   ├── product-understanding.md       # product-gtm F1 产品理解
│   ├── content-strategy.md            # product-gtm F2 内容策略
│   ├── xiaohongshu-copywriting.md     # product-gtm F3 小红书文案
│   ├── wechat-mp-copywriting.md       # product-gtm F3-MP 公众号文案
│   ├── personal-log-understanding.md  # personal-log F1 日志理解
│   ├── personal-log-strategy.md       # personal-log F2 选题规划
│   ├── personal-log-copywriting.md    # personal-log F3 小红书真实感文案
│   ├── personal-log-mp-copywriting.md # personal-log F3-MP 公众号真实感文案
│   ├── desensitization-gate.md        # personal-log F5 脱敏闸门
│   ├── cover-image.md                 # F4 封面图（双模式共用）
│   ├── browser-publish-xhs.md        # Chrome DevTools MCP 小红书发布指令
│   └── browser-publish-mp.md         # Chrome DevTools MCP 公众号发布指令
├── examples/                          # 示例文件
│   ├── sample-product-profile.md
│   └── sample-post.md
├── autosome/                          # Python CLI
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                         # CLI 命令定义
│   ├── config.py                      # 配置加载
│   ├── parser.py                      # content.md 解析
│   ├── tracker.py                     # 历史追踪（双模式）
│   └── platforms/
│       ├── __init__.py                # 公共工具（剪贴板等）
│       ├── xiaohongshu.py             # 小红书 Playwright 自动化（legacy）
│       └── wechat_mp.py               # 微信公众号（prepare 辅助）
├── .cursor/
│   └── mcp.json                       # Chrome DevTools MCP 配置
├── config.example.yaml
├── requirements.txt
├── pyproject.toml
├── dashboard.html                     # 可视化项目大盘
└── README.md
```

## 支持平台

| 平台 | 状态 | 发布方式 |
|------|------|---------|
| 小红书 | ✅ 已支持 | prepare 手动 / Chrome DevTools MCP 自动 / Playwright legacy |
| 微信公众号 | ✅ 已支持 | prepare 手动 / Chrome DevTools MCP 自动 |
| YouTube | 计划中 | - |

## 配置

复制 `config.example.yaml` 为 `config.yaml`，可自定义浏览器数据存储路径等。

## License

MIT
