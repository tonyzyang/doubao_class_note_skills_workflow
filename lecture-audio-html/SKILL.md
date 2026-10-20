---
name: lecture-audio-html
description: "把一堂课的录音（配合 PPTX 或现场照片幻灯片）端到端做成一个离线可打开的单文件 HTML「完整讲义」：前半是课堂同步（幻灯片图在上、老师口述知识点在下，含开场背景与现场问答），后半是全讲复习（思维导图、复习路径、核心结论、自测、时间脉络、核心模块、数字速记、易混点、话术、迁移清单）。中文触发如：录音转课堂笔记网页、把录音和PPT做成完整讲义、录音加幻灯片做同步加复习的HTML、课程录音整理成可复习的离线网页。本 skill 为独立版本，已内联全部所需参考文档，不依赖其他 skill；转写环节需要环境中已安装并登录 lark-cli（飞书/豆包命令行）。"
---

# 录音 → 完整讲义 HTML（课堂同步 + 全讲复习）

## Overview

把课程录音（和幻灯片）做成一个离线单文件 HTML，读起来像跟着老师上完整堂课，随后可直接全讲复习。图片全部 base64 内嵌、ECharts 内联、无任何外链。

## 核心原则（不可违背）

1. **文字 = 老师口述的知识点，不是翻译幻灯片**：写老师口头展开的本质、为什么、直觉、例子、易错；严禁复述幻灯片。
   - **判据（最高优先级，按此逐条验收）**：幻灯片上写着、但录音里没有讲过的内容，一律不写——哪怕是数字、参数、规格、清单明细、逐镜头台词；数字只来自口述，约数保留“约”。
   - **不是逐字稿原文搬运**：把口述内容总结化、条理化（本质一句 + 分点 + 要点框），但知识点不得遗漏。
   - 唯一例外：幻灯片文字被老师在录音里亲口念出/复述，可写（此时它属于口述内容）。
   - 写完每页必须回到逐字稿检索该知识点，检索不到就删；用户曾因违反此点连续五次打回。
2. **唯一画的是思维导图（ECharts tree）**；不画柱图/折线/饼图等课程图表，不画数据表；复习用文字、列表、卡片。
3. **去掉无内容页**：如「谢谢」、纯致谢、纯空白。
4. **离线单文件**：base64 图片、内联 ECharts、系统字体、无外链；内容完整、篇幅不限。
5. 现场问答逐题收录（同步区 + 复习区自测各一次），不挑不删；只写老师真正讲过的，不编造。
6. **防漏与防伪并列**：构建前必须按 `references/06-gap-check.md` 做逐段正向核对（录音按话题切分、段段有落点）；超 1 分钟的案例、故事、人物经历必须独立展开，不得只在复习区一句话带过；与 PPT 对不上的录音内容补为无图条目或补讲块，不删录音内容。

## 工作流（按序执行，先读对应 reference 再做）

**阶段一：核查录音并转写** — Read `references/01-transcription.md`。
- 先确认录音是完整一堂课；转写通过 lark-cli 妙记三步完成（上传→建妙记→`--wait-ready` 取逐字稿），已有的妙记/逐字稿直接复用。
- 执行妙记三步前，**读取 `references/lark-meeting.md` 并按其中的说明执行**（该文件已内联 lark-meeting 主文件、「生成和修改妙记」场景手册，以及 `minutes +upload`、`minutes +detail` 命令参考）；其中 Drive 上传步骤需要读取 `references/lark-drive.md` 并按其中的说明执行（已内联 lark-drive 主文件与 `drive +upload` 命令参考）。
- 通读并梳理讲课主线。

**阶段二：获取幻灯片（二选一，汇合到同一套图片）** — Read `references/02-slide-source.md`。
- 路径 A 有 PPTX：`python scripts/extract_ppt_windows.py "<deck.pptx>" --out raw`（Windows/PowerPoint；无则用 LibreOffice，见 reference）。
- 路径 B 无 PPT：引导用户分批上传现场照片（每批≤20张、逐批确认到「传完了」），再按讲课顺序重排去重。
- 两条路径都运行 `python scripts/prepare_images.py <staging> --out images` 压缩并生成 manifest；剔除「谢谢」等无内容页。

**阶段三：撰写课堂同步** — Read `references/03-sync-authoring.md`。
- 从 `assets/content_template.json` 复制为 content.json；写 opening、逐页 blocks（p/ul/note/ex）、qa；照片路径做查漏，插入无图补讲条目。
- 每条写完立刻回逐字稿检索确认讲过；幻灯片上有但录音没说的，包括数字/参数/明细，一律不写。

**阶段四：撰写全讲复习** — Read `references/04-review-authoring.md`。
- 写 review：map、paths、conclusions、quiz、timeline、modules、numbers、confuse、talks、transfer；条数照实，不限量。

**阶段五：查漏补缺（构建前必做，防"漏"）** — Read `references/06-gap-check.md`。
- 按录音**自然话题**逐段切分（不按 PPT 页），建立"段→落点"清单，逐段正向核对；超 1 分钟的独立案例/故事/人物经历必须独立展开、禁止一句话带过；人名、地名、数字段段有落点；与 PPT 对不上的录音内容补为无图条目或补讲块；再做独特关键词扫描与反向防伪核对。
- 任何知识点不能只在复习区出现、同步区缺失；现场问答须同步区与复习区均有落点。

**阶段六：构建、验证、交付** — Read `references/05-validation.md`。
- `python scripts/build_html.py content.json --out "课程·主题·完整讲义.html"`；覆盖度核对、标签平衡、无外链。
- 截图自检使用本 skill 自带的 `scripts/shot.py`（其完整使用说明见 `references/html.md`，该文件已内联 html skill 主文件）；出桌面+移动截图核对（consoleErrors=[]）。
- 用 present_files 交付单个 HTML，最终回复 ≤8 行。

## 资源索引

- `scripts/extract_ppt_windows.py`：PPTX 每页导出 PNG（Windows PowerPoint COM）。
- `scripts/prepare_images.py`：压缩图片为 images/NN.jpg、生成 manifest.json。
- `scripts/transcode_audio.py`：音频转码辅助脚本。
- `scripts/build_html.py`：由 content.json 构建单个离线 HTML（图片 base64、ECharts 内联）。
- `scripts/shot.py`：HTML 桌面/移动截图与自检脚本（来自 html skill，离线可用）。
- `assets/content_template.json`：content.json 结构模板。
- `assets/echarts.min.js`：构建器内联用，无需单独打开。
- `references/`：01 转写、02 幻灯片来源、03 同步撰写、04 复习撰写、05 验证交付、06 查漏补缺；以及内联的三个外部 skill 文档 `lark-meeting.md`、`lark-drive.md`、`html.md`。

## 边界

- 转写失败、额度不足（quota_exceeded）、文件超限：如实告知，不降级为本地 ASR，不编造逐字稿。
- 转写链路依赖 lark-cli 与飞书/豆包妙记服务；环境中没有 lark-cli 或未登录时，按 `references/lark-meeting.md` 的认证错误引导处理，无法绕过。
- 用户当次明确要保留主讲人/日期、要画其他图、或要在线版时，以用户指令为准，并在交付说明中点明偏离了默认规范。
