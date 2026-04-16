# claude-vault · Claude 对话知识库

**让每一次和 Claude Code 的对话，都变成你永久的知识资产。**

[English](#english) | 中文

---

## 你是不是也有这样的经历？

花了三个小时和 Claude Code 搞定一个问题。过程中问了十几个问题，踩了几个坑，最后终于跑通了。

然后你关掉窗口。

第二周遇到类似的问题，完全想不起来当时怎么解决的。再开一个窗口，再问一遍，再踩一遍坑。

或者——你刚开始 vibe coding，每天都在学新东西：什么是 MCP、launchd 怎么配、GitHub PR 怎么推、skill 怎么安装。这些知识散落在几十个对话窗口里，没有地方积累，也没有地方复习。

**claude-vault 就是为这个问题造的。**

---

## 适合谁用

边实践边学 vibe coding、希望每天都有实际内容积累的人。

你不需要懂技术——装好之后，关窗口就行，剩下的它来做。

---

## 它做什么

每天早上9点，它自动扫描你昨天所有的 Claude Code 对话，判断哪些值得记录，然后帮你整理成结构化笔记，写进你的 Obsidian（或任何 Markdown 编辑器）。

你什么都不用做。关窗口就行。

---

## 装完之后，你的 Obsidian 长这样

```
📂 CC-Knowledge/
│
├── 📂 session-recaps/          ← 每次对话的复盘
│   ├── 2026-04-16 AI日报自动化搭建.md
│   ├── 2026-04-15 Helio官网内容改版.md
│   └── 2026-04-13 微信导出流程探索.md
│
├── 📂 concept-library/         ← 工具和概念，一个概念一个页面，越用越厚
│   ├── Whisper.md              (OpenAI 语音识别)
│   ├── MCP.md                  (Model Context Protocol)
│   ├── launchd.md              (macOS 定时任务)
│   └── Notion API.md
│
├── 📂 methodology/             ← 跨项目可复用的方法论
│   └── 内容改版方法论.md
│
├── 📂 engineering-insights/    ← 技术发现、踩坑记录
│   ├── GitHub API 文件操作.md
│   └── 脚本开发注意事项.md
│
├── 📂 mistake-log/             ← 错题本：犯过的错，下次别再犯
│   └── mistake-log.md          (🔧 操作失误 / 🧭 方向失误 / 💬 沟通失误 / 🤖 AI理解错误)
│
├── 📂 projects/                ← 每个项目的概览
│   ├── Helio/
│   └── yori学易学/
│
├── 📂 open-source-library/     ← 发现的好用开源项目
│   └── README.md               (索引表)
│
├── 📂 qa-handbook/             ← 问过的问题和解答，按类别归档
│   ├── claude-code-ops.md      (Claude Code 操作类)
│   ├── git-github.md           (Git & GitHub)
│   └── general.md              (通用概念)
│
├── 📂 weekly-digest/           ← 每周总结
│
└── 📂 _system/                 ← 系统文件（Claude 每次先读这里）
    ├── index.md                (总目录，所有文件的索引)
    ├── log.md                  (操作日志，append-only)
    └── SCHEMA.md               (工作手册，约定规则)
```

这套结构的核心设计来自 [Karpathy 的 LLM Wiki 思路](https://x.com/karpathy)：**同一个概念只有一个页面，永远更新而不是新建，知识像雪球一样越滚越大。**

这个思路具体体现在两个地方：`concept-library/` 里每个工具只有一个页面（用得越多就越厚）；`/o` 指令在写入前会先查 index，有就更新，没有才新建——永远不产生重复页面。

---

## 两种工作方式

**`/o` — 手动存，3秒钟**

对话快结束的时候，觉得这次内容值得留下来，发一条 `/o`。Claude 会读这段对话，提炼要点，自动写进你的 Obsidian：

- 今天做了什么
- 用了什么思路和方法
- ✅ 做得好的地方
- ⚠️ 下次可以改进的地方
- 💡 可复用的方法论（2-4条）
- 🔧 技术发现和踩坑
- 🙋 问过的问题和解答

**自动归档 — 每天早上9点跑，你不用管**

它会判断哪些对话值得记录（过滤掉打招呼、极短的、没有实质内容的），然后帮你整理好。

---

## 安装

**前置条件：** macOS、Python 3.9+、Node.js、Claude Code、Anthropic API key（[申请地址](https://console.anthropic.com)）

```bash
git clone https://github.com/YoriHan/claude-vault ~/.claude/skills/claude-vault
cd ~/.claude/skills/claude-vault
./setup
```

回答三个问题：

```
你的笔记用什么语言？(e.g. English, 中文, Español, 日本語)
→ 中文

笔记库放在哪里？[~/Documents/CC-Knowledge]
→ （直接回车用默认路径）

Anthropic API key (sk-ant-...):
→ sk-ant-...
```

安装脚本会自动：
- 创建完整的目录结构
- 配置 MCP，让 Claude 能读写你的笔记
- 如果不是英文，调用 API 把所有模板翻译成你选的语言
- 注册 launchd 定时任务，每天9点自动运行

**安装完之后：重启一次 Claude Code**，让 MCP 生效。

---

## 常用命令

```bash
# 看昨晚跑了什么
tail -f ~/.cc-knowledge/ingest.log

# 预览会生成什么，不真的写文件
python3 ~/.cc-knowledge/daily_ingest.py --dry-run

# 强制重新处理某个对话（传 UUID）
python3 ~/.cc-knowledge/daily_ingest.py --force <uuid>

# 重新处理所有对话
python3 ~/.cc-knowledge/daily_ingest.py --all
```

---

## 自动归档怎么判断"值不值得记录"

两阶段 API 调用：

**第一阶段（claude-sonnet-4-6）：** 值不值得记？过滤掉打招呼、不足4条用户消息、没有实质内容的对话。

**第二阶段（claude-sonnet-4-6 + claude-haiku）：** 生成对话复盘 + 提取Q&A，写进你的笔记库。

用 `--force` 可以强制处理任何对话。

---

## 修改配置

不需要重新安装，直接编辑 `~/.cc-knowledge/config.json`：

```json
{
  "vault_path": "/Users/你的用户名/Documents/CC-Knowledge",
  "language": "中文",
  "api_key": "sk-ant-..."
}
```

---

## 卸载

```bash
# 停止定时任务
launchctl unload ~/Library/LaunchAgents/com.user.cc-knowledge.plist
rm ~/Library/LaunchAgents/com.user.cc-knowledge.plist

# 删除配置和状态文件
rm -rf ~/.cc-knowledge

# 手动编辑 ~/.claude.json，删除 "cc-knowledge" 那一段

# 如果也想删笔记库（慎重）
rm -rf ~/Documents/CC-Knowledge
```

---

## 平台支持

v1 仅支持 macOS（定时任务用 launchd）。`/o` 命令在任何平台都可以用，只有自动归档是 macOS 专属。Linux/Windows 支持计划中。

---

<a name="english"></a>

## English

**Turn every Claude Code conversation into permanent knowledge — automatically.**

Every time you close a Claude Code window, the insights, Q&As, and lessons from that session disappear. claude-vault captures everything, organizes it into a structured vault, and makes it searchable in Obsidian or any Markdown editor.

**Two ways it works:**

- **`/o` command** — type it at the end of any conversation. Claude extracts what matters and files it: what was done, methodology, principles, engineering insights, Q&As.
- **Auto-ingest** — runs at 9am daily, scans your conversation history, decides what's worth keeping, writes it while you sleep.

**Install:**

```bash
git clone https://github.com/YoriHan/claude-vault ~/.claude/skills/claude-vault
cd ~/.claude/skills/claude-vault
./setup
```

Three questions: language, vault path, API key. Done.

**Requirements:** macOS, Python 3.9+, Node.js, Claude Code, [Anthropic API key](https://console.anthropic.com)

The vault structure is built around [Karpathy's LLM Wiki pattern](https://x.com/karpathy): one page per concept, always update rather than create, knowledge compounds over time. This shapes two concrete behaviors: `concept-library/` has exactly one file per tool (it grows richer with each use), and the `/o` command always checks the index before writing — updating existing pages instead of creating duplicates.
