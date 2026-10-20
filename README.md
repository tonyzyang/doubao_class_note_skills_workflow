# 课程录音 → 完整讲义 HTML（lecture-audio-html）

把一堂课的**录音**（配合 **PPTX** 或现场拍摄的**幻灯片照片**）端到端做成一个**离线可打开的单文件 HTML「完整讲义」**。不需要手工整理，也不依赖任何其他 skill——所有外部参考文档都已内联在本 skill 中。

## 这个 skill 能做什么

产出的 HTML 分为两大部分：

1. **课堂同步**：幻灯片图在上、老师口述的知识点在下，完整还原课堂顺序；包含开场背景、逐页讲解和现场问答。
   - 正文只写老师**口头展开**的内容（概念本质、为什么、直觉推导、课上例子、易错点），**不翻译幻灯片**；幻灯片上有但录音里没讲过的内容一律不写。
2. **全讲复习**：思维导图（ECharts 树图）、复习路径（5/20/45 分钟 + 迁移）、核心结论、自测题（含现场问答）、时间脉络、核心模块、数字速记、易混点、可直接复述的话术、迁移清单。

整个文件**图片 base64 内嵌、ECharts 内联、无任何外链**，双击即可在浏览器打开，方便离线复习和分享。

## 使用示例

直接用自然语言提出需求即可，例如：

> 这是我今天《高级计量经济学》第 3 讲的录音（约 2 小时），PPT 也一起发给你，帮我做成一份可以复习的完整讲义网页。

或者只有现场照片、没有 PPT：

> 这是上课录音，幻灯片我是用手机拍的，一会儿分批发给你，帮我做成课堂笔记网页。

skill 会自动完成：录音核查与转写 → 幻灯片导出/照片整理 → 课堂同步撰写 → 全讲复习撰写 → 查漏补缺 → 构建并自检 HTML，最终交付单个 `.html` 文件。

## 环境要求

- **Python 3**（用于图片处理和 HTML 构建）。
- **转写环节需要 lark-cli**：录音转写通过飞书/豆包「妙记」完成（上传 → 创建妙记 → 等待并拉取逐字稿）。环境中需已安装并登录 `lark-cli`；没有 lark-cli 时无法完成转写，skill 会按提示引导，**不会**降级为本地 ASR（Whisper 等）。
- 有 PPTX 时：Windows + PowerPoint 可直接导出每页图片；其他环境会改用 LibreOffice。
- 页面截图自检（`scripts/shot.py`）首选 Playwright，未安装时会自动降级到系统 Chrome/Edge/Chromium；自检失败不影响交付。

## 安装方法

**Claude Code 用户**：把整个 `lecture-audio-html/` 文件夹复制到 `~/.claude/skills/` 目录下即可：

```bash
# 假设已克隆本仓库
cp -r lecture-audio-html ~/.claude/skills/
```

安装后目录结构如下：

```text
~/.claude/skills/lecture-audio-html/
├── SKILL.md            # 主文件（完整工作流）
├── references/         # 各阶段说明 + 已内联的外部 skill 文档
├── scripts/            # PPT 导出、图片处理、HTML 构建、截图自检脚本
└── assets/             # 内容模板与 ECharts
```

**其他支持 Agent Skills 的客户端**：将 `lecture-audio-html/` 文件夹放入该客户端对应的 skills 目录，流程相同。

## 仓库地址

<https://github.com/tonyzyang/doubao_class_note_skills_workflow>

如果这个 skill 帮你节省了整理笔记的时间，**觉得有用请点个 Star ⭐**，也欢迎提 Issue 和 PR。

---

## English Introduction

**lecture-audio-html** turns a course recording (together with a PPTX deck or photos of slides) into a single, offline, self-contained HTML handout. The first half follows the lecture in real time — slides on top, the instructor's spoken points (not slide text) below, including opening context and live Q&A. The second half is a full review kit: an ECharts mind map, 5/20/45-minute review paths, key conclusions, self-test questions, a timeline, core modules, key numbers, confusing points, ready-to-recall talk tracks, and a transfer checklist. Images are embedded as base64 and ECharts is inlined, so the file opens in any browser with no external links. Claude Code users can install it by copying the `lecture-audio-html/` folder into `~/.claude/skills/`. If you find it useful, please leave a Star ⭐.
