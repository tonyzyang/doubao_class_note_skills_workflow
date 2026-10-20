# 内联文档：lark-meeting（飞书视频会议 / 妙记）

本文件内联了本工作流执行妙记转写时需要读取的 lark-meeting skill 全部相关文档，按下列顺序排列，各部分均为原文：

1. 原 `lark-meeting/SKILL.md`（主文件）
2. 原 `lark-meeting/scenes/create-and-edit-minutes.md`（生成和修改妙记场景手册）
3. 原 `lark-meeting/references/lark-minutes-upload.md`（minutes +upload 命令参考）
4. 原 `lark-meeting/references/lark-minutes-detail.md`（minutes +detail 命令参考）

原文中形如 `references/lark-minutes-upload.md`、`scenes/create-and-edit-minutes.md` 的相对链接，均指向本文件内对应章节；其中指向 `lark-drive` 的链接，指向本目录的 `lark-drive.md`。

---

## 一、原 lark-meeting/SKILL.md

```markdown
---
name: lark-meeting
version: 1.0.0
description: "飞书视频会议：查询会议记录与会议产物(纪要/逐字稿/妙记)、妙记搜索/上传/下载/编辑、会议录制控制；查询进行中的会议、实时会议内容(发言/聊天/共享文档)问答(会上/会里)、发送会中聊天/表情、查询或创建会议绑定聊天，以及主持人结束会议、移出参会人、闭麦或请求开麦；基于 meeting_id、meeting_no、event_id、note_id、minute_token、vc-node-id 或妙记 URL 查询相关信息。预约会议、忙闲和会议室管理走 lark-calendar。"
metadata:
  requires:
    bins: ["lark-cli"]
  cliHelp: "lark-cli vc --help;lark-cli minutes --help;lark-cli note --help"
---

# lark-meeting

飞书视频会议业务的统一入口，支持查询会议记录、查询或创建会议群聊、实时会议互动、管理妙记、阅读智能纪要等操作。本技能负责领域关系、任务路由和跨命令编排。

本产物所有命令自动以当前登录用户身份执行，无需传入身份参数，也没有身份选择或切换的需要。遇到未认证、token 或 scope 错误时，直接根据错误响应中的提示（如 `missing_scopes`、`console_url`）引导用户在应用后台补开权限后重试。

## 领域模型与概念

```text
[会议来源]

Calendar 日程 (event_id) ──预约或关联──┐
即时会议（无 event_id）────────────────┴──► 会议 (meeting_id)

Calendar 日程 ──meeting_note────────────► Doc（用户纪要，独立于 AI 智能纪要）

[会议产物]

会议 (meeting_id)
├── 当前聊天绑定 ──► IM Chat (chat_id，可选，可能复用私聊)
├── AI 总结 ──► Note 智能纪要 (note_id)
│               ├── 智能纪要文档 ───────────► Doc (note_doc_token)
│               ├── 逐字稿
│               │   ├── normal  ──────────► Doc (verbatim_doc_token)
│               │   └── unified ──────────► note +transcript（非独立 Doc）
│               └── 共享文档 ──────────────► Doc (shared_doc_tokens)
│
└── 录制 ──► Minutes 妙记 (minute_token)
                 ├── AI 产物：Summary / Todo / Chapter / Keyword
                 ├── Transcript（文字记录，别名：「转写」「逐字稿」「文字记录」）
                 └── 原始音视频

本地音视频 ─────────────────────────────► Minutes 妙记 (minute_token)
```

| 对象 | 主标识 | 概念与关系 |
|---|---|---|
| Calendar 日程 | `event_id` | 日历上的日程，包含时间、参与人、会议室和 RSVP，可预约或关联 VC 会议；不是完整的会议记录。日程上的 `meeting_note` 是用户手工绑定的 Doc，与 AI 智能纪要无关。 |
| Meeting 会议 | `meeting_id` | 实际发生的视频会议，可以来自 Calendar，也可以是没有日程的即时会议。会议主题、时间、参会人快照和会中事件属于会议数据；Note 与 Minutes 是它可能关联的会后产物。 |
| IM Chat 会议聊天 | `chat_id` | 会议当前绑定的聊天，可能是群或复用的私聊；绑定查询与创建/复用属于 VC，消息读写属于 IM。 |
| Note 智能纪要 | `note_id` | 开启 AI 总结后形成的逻辑产物集合。`note_display_type` 决定获取逐字稿中文字记录的不同方式。 |
| Minutes 妙记 | `minute_token` | 由会议录制或本地音视频上传生成，包含总结、待办、章节、关键词、文字记录(别名：「转写」「逐字稿」「文字记录」)和原始音视频；可以关联 VC 会议，也可以独立存在。 |
| Doc 文档 | Doc token | 内容载体，不是会议标识。`note_doc_token`、`shared_doc_tokens` 和部分 `verbatim_doc_token` 指向 Doc；Doc token 不能当作 `note_id` 或 `meeting_id`。 |

### 核心标识

- `meeting_id`：会议 ID。长数字字符串，不是 9 位会议号。
- `meeting_no`：会议号。9 位纯数字；CLI 参数名为 `--meeting-number`。
- `chat_id`：IM 聊天 ID，通常以 `oc_` 开头；从会议详情或创建/复用结果取得，不能用 `meeting_id` 替代。
- `minute_token`：妙记 Token。小写字母数字串，通常取自妙记 URL `/minutes/<minute_token>`。

以上标识均按字符串原样传递，不能相互替代。

### 领域不变量

- Note 与 Minutes 分别来自 AI 总结和录制两条独立链路。一场会议可能同时有两类产物、只有其中一类，也可能都没有；不能根据 `note_id` 推断必然存在 `minute_token`，反之亦然。
- Minutes 可以由本地音视频直接生成，因此不一定关联 `meeting_id` 或 Calendar `event_id`。
- Calendar `meeting_note`、Note `note_id`、Minutes `minute_token` 和各类 Doc token 标识不同对象，不能互换、代入其他域的命令或从一者反推另一者。
- 结束会议和移出参会人都必须先确认用户的明确目标；预览使用 `--dry-run`，真实执行只有在确认后才传 `--yes`。

## 快速行动

### 根据当前状态判断是否拉取会中事件并给出引导
当最新用户信息明确显示「AI 总结」未开启且没有「关联录音」时，**不要**查询会中事件，明确告知用户并按客户端类型引导：

判断「AI 总结」是否开启、是否存在「关联录音」时，**必须以用户最新消息为准，禁止通过对话上下文推断**。

- **电脑端**：按下面「电脑端标准话术」原样整段输出，不要修改：

> 目前无法获取会议信息，原因是当前会议的 AI 总结未开启，且没有关联录音，我无法获取到会议的发言和内容。
>
> 请选择以下任一方式解决：
> 1. **开启会议「AI 总结」** — 你在会议界面中找到 AI 总结功能并开启，开启后我可以读取会议内容并为你总结。
> 2. **开启「录音转写」** — 我可以帮你发起录音转写，记录本次会议内容。
>
> 需要我帮你发起录音转写吗？

得到用户的肯定回复或开启录音的意图时，使用 `doubao-record` 技能为用户开启录音。

- **手机端**：手机端不支持会议进行中同时开启录音，**不要**建议开启录音转写，只提示开启会议「AI 总结」。手机端标准话术，原样整段输出，不要修改：

> 目前无法获取会议信息，原因是当前会议的 AI 总结未开启，且没有关联录音，我无法获取到会议的发言和内容。
>
> 请在会议界面开启会议的「AI 总结」功能。

### 查询进行中的会议或关联录音的内容

**注意**：如果会议在进行中，或用户当前处于会议侧边栏，直接用 `lark-cli vc +meeting-events` 获取会中内容，不要使用其他方式；会议有关联录音时同样用该命令获取录音内容。

```bash
# 当前用户所在会议
lark-cli vc +meeting-list-active

# 确定唯一 meeting_id 后查询会中事件
lark-cli vc +meeting-events --meeting-id <meeting_id> --page-all --format pretty
```
- `--page-all` 参数必传，一次性获取所有事件，避免分页查询。
- `--page-all` 和 `--page-token` 可同时传
- `--page-token <returned_page_token>`
- 使用 `--page-token` 拉取增量，page-token 为上一页或上一次查询结果中保存的 page_token；建议持久化保存，便于下次继续拉取新增事件

同时有多场会议时，需要先选择要查询的会议；只有一场会议时，直接查询该场会议的会议事件。返回空不代表当前用户没有在开会，只能说明没有找到该接口可发现的进行中会议。

当用户在会议中或处于会议侧边栏时，优先使用会中事件回答用户的问题。

### 判断用户是否要做会议笔记

仅当用户有明确表达记录意图（「写 / 划 / 记 / 标记 / 备忘 / 摘抄」等）时，才进入**会议笔记**场景（见场景手册「会议个人笔记」），创建并追加个人笔记文档。

- 意图不明确时先询问、要求用户给出明确指令，**不主动建文档**。
- 用户只说「总结一下」时走会议总结，不要误判为会议笔记。

## 会议场景约定

会议场景下常见的意图判定与动作约定。

### 会中共享文档

会中可能有人共享文档（通过 `vc +meeting-events` 可读到共享的 Doc token）。当用户说「总结文档 / 整理文档 / 看下文档」等时：

- **有共享文档**：默认理解为「总结会中共享的文档」，读取该 Doc 内容并总结，**不要**新建文档。
- **没有共享文档**：意图不明确，可询问用户想总结哪个文档，或按常规文档生成流程处理。

### 文档评论

用户说「总结评论 / 看下评论 / 评论有哪些」等时，默认指**会中共享文档里的评论**（与「总结文档」同源）：

- **有共享文档**：读取该 Doc 的评论，关注未解决状态的评论。
- **没有共享文档**：意图不明确，询问用户想总结哪个文档的评论。

## 场景手册

当任务目标与场景匹配时，阅读对应的场景手册，按流程执行任务。

- [查询会议及其产物](scenes/query-meeting-and-artifacts.md)：按主题、时间、参会人或 `meeting_id` / `meeting_no` / `event_id` 定位历史会议；查询参会人、录像和会议关联的智能纪要或妙记；基于会议记录总结或复盘；查询会后群聊，或已有 `meeting_id`、未说明会议状态时只读查询当前绑定。
- [查询当前用户录音列表](references/lark-recording-list.md)：没有会议标识、需要列出自己的录音或按时间筛选录音时，使用 `recording +list`；通过录音关联的产物标识继续读取妙记或纪要。
- [查询妙记及其产物](scenes/query-minutes-and-artifacts.md)：已有妙记 URL / `minute_token`，或按标题、所有者、参与者搜索妙记；读取总结、待办、章节、关键词、逐字稿，下载原始音视频，或查询关联智能纪要。
- [生成和修改妙记、管理妙记权限](scenes/create-and-edit-minutes.md)：将本地音视频生成妙记、逐字稿、总结、待办或章节；修改妙记标题、总结、待办、关键词或说话人；申请妙记权限，或查看、分配妙记协作者权限。
- [查询智能纪要及关联产物](scenes/query-note-and-artifacts.md)：已有 `note_id`、智能纪要 Docx URL/token，或需要查询纪要正文、逐字稿、妙记和共享文档等关联产物。
- [会中事件与会中互动](scenes/live-meeting-interact.md)：查询当前登录用户所在的活跃会议、查看发言/聊天/共享内容、按需读取当前会议画面；获取正在进行的会议绑定群、创建/复用会议聊天并按需转 IM，或发送文本/表情、操作倒计时；用户明确要求结束会议、移出参会人、闭麦或请求开麦时，也从这里路由到对应命令。
- [会议个人笔记](scenes/lark-meeting-personal-note.md)：仅当用户有明确表达记录意图（「写/划/记/标记/备忘/摘抄」等）时创建并追加个人笔记飞书文档；意图不明确时先询问、要求用户给出明确指令，不主动建文档；会议结束后基于完整会议内容自动整理完善。

## 命令参考

| 命令 | 用途 | 参考方式 |
|---|---|---|
| `vc +search` | 搜索历史会议 | [lark-vc-search](references/lark-vc-search.md) |
| `vc +detail` | 查询会议信息、可选 Chat 绑定及关联的 Note、Minutes 标识 | [lark-vc-detail](references/lark-vc-detail.md) |
| `vc meeting get` | 查询会议基础信息和参会人快照 | `lark-cli vc meeting get --help` |
| `recording +list` | 分页查询当前用户录音及关联产物 | [lark-recording-list](references/lark-recording-list.md) |
| `vc +recording` | 从会议定位录制及妙记 | [lark-vc-recording](references/lark-vc-recording.md) |
| `vc +meeting-recording-start` | 开始当前会议录制 | [lark-vc-recording-control](references/lark-vc-recording-control.md) |
| `vc +meeting-recording-stop` | 停止当前会议录制 | [lark-vc-recording-control](references/lark-vc-recording-control.md) |
| `vc +meeting-list-active` | 发现当前可见的进行中会议 | [lark-vc-meeting-list-active](references/lark-vc-meeting-list-active.md) |
| `vc +meeting-events` | 读取会中或关联录音事件和共享内容 | [lark-vc-meeting-events](references/lark-vc-meeting-events.md) |
| `vc +meeting-chat` | 会中创建或复用会议群聊（会议群/群组），仅需 `meeting_id` | [lark-vc-meeting-chat](references/lark-vc-meeting-chat.md) |
| `vc +meeting-message-send` | 发送会中文本消息或表情 | [lark-vc-meeting-message-send](references/lark-vc-meeting-message-send.md) |
| `vc +meeting-screenshot` | 获取视频会议截图 | [lark-vc-meeting-screenshot](references/lark-vc-meeting-screenshot.md) |
| `vc +meeting-countdown` | 设置、延长、提前结束或关闭会中倒计时 | [lark-vc-meeting-countdown](references/lark-vc-meeting-countdown.md) |
| `vc +meeting-end` | 结束整场进行中的会议 | [lark-vc-meeting-end](references/lark-vc-meeting-end.md) |
| `vc +meeting-participant-kickout` | 移出一至十个指定参会人 | [lark-vc-meeting-participant-kickout](references/lark-vc-meeting-participant-kickout.md) |
| `vc +meeting-participant-mute` | 将指定参会人闭麦 | [lark-vc-meeting-participant-audio](references/lark-vc-meeting-participant-audio.md) |
| `vc +meeting-participant-unmute` | 请求指定参会人开麦 | [lark-vc-meeting-participant-audio](references/lark-vc-meeting-participant-audio.md) |
| `vc +meeting-invite` | 邀请指定用户加入会议 | [lark-vc-meeting-invite](references/lark-vc-meeting-invite.md) |
| `minutes +search` | 搜索妙记 | [lark-minutes-search](references/lark-minutes-search.md) |
| `minutes minutes get` | 查询妙记基础信息 | `lark-cli minutes minutes get --help` |
| `minutes +detail` | 读取妙记信息和指定产物 | [lark-minutes-detail](references/lark-minutes-detail.md) |
| `minutes +download` | 下载妙记原始音视频 | [lark-minutes-download](references/lark-minutes-download.md) |
| `minutes +upload` | 从云空间音视频生成妙记 | [lark-minutes-upload](references/lark-minutes-upload.md) |
| `minutes +update` | 修改妙记标题 | [lark-minutes-update](references/lark-minutes-update.md) |
| `minutes +speaker-replace` | 替换妙记逐字稿说话人 | [lark-minutes-speaker-replace](references/lark-minutes-speaker-replace.md) |
| `minutes +summary` | 替换妙记 AI 总结 | [lark-minutes-summary](references/lark-minutes-summary.md) |
| `minutes +todo` | 增删改妙记 AI 待办 | [lark-minutes-todo](references/lark-minutes-todo.md) |
| `minutes +apply-permission` | 申请妙记查看或编辑权限 | [lark-minutes-apply-permission](references/lark-minutes-apply-permission.md) |
| `minutes +share-permission` | 将一条妙记一键分享给会议参会人 | [lark-minutes-share-permission](references/lark-minutes-share-permission.md) |
| `drive +member-list` | 查看妙记协作者及其权限 | [lark-drive-member-list](../lark-drive/references/lark-drive-member-list.md) |
| `drive +member-add` | 给指定成员分配妙记查看或编辑权限 | [lark-drive-member-add](../lark-drive/references/lark-drive-member-add.md) |
| `minutes +word-replace` | 批量替换妙记逐字稿关键词 | `lark-cli minutes +word-replace --help` |
| `note +detail` | 查询智能纪要及关联文档标识 | [lark-note-detail](references/lark-note-detail.md) |
| `note +transcript` | 获取 unified 智能纪要逐字稿 | [lark-note-transcript](references/lark-note-transcript.md) |

## 渐进加载规则

按“快速行动 → 场景手册 → 命令参考”渐进加载：

1. 用户目标符合“快速行动”的进入条件时，直接执行对应 CLI；不要预读场景手册、命令参考、`--help` 或 schema。
2. 不符合快速行动条件，或缺少关键标识、需要消歧、涉及写操作时，读取与目标匹配的一个主场景手册；主场景明确转交到下游场景时，只继续读取被引用的场景或章节，并按其中流程执行 CLI。
3. 仅当缺少具体参数、返回字段、特殊约束或异常处理方式时：有参考手册的命令读取对应文件；没有参考手册的命令运行表中列出的精确 `lark-cli ... --help`。场景或 reference 已给出精确命令时，不再调用 `--help`；仅在参数缺失、命令不识别或文档与运行结果冲突时调用。
```

---

## 二、原 lark-meeting/scenes/create-and-edit-minutes.md

```markdown
# 生成和修改妙记、管理妙记权限

生成妙记和修改妙记都是写操作，必须有用户明确意图。生成成功后保存 `minute_token`；修改前确认唯一 `minute_token` 和目标内容，提供 token 不等于授权修改。

## 从本地音视频生成妙记

标准链路是 Drive 上传 → Minutes 创建 → 按需读取产物。不要改用 ffmpeg、Whisper 或其他本地 ASR。

### 上传音视频到 Drive

确认本地媒体路径以及用户最终需要妙记链接、逐字稿、总结、待办还是章节。源文件须符合 [`minutes +upload`](../references/lark-minutes-upload.md) 的格式要求，时长不超过 6 小时，大小不超过 6 GB。

按 [`lark-drive`](../../lark-drive/SKILL.md) 的路径和写操作规则执行 `drive +upload`，取得 `file_token`。上传参数和文件限制见 [`lark-drive-upload`](../../lark-drive/references/lark-drive-upload.md)。

### 使用 file_token 创建妙记

```bash
lark-cli minutes +upload --file-token <file_token>
```

从返回的 `minute_url` 路径最后一段提取 `minute_token`，去掉 query 参数。创建参数、支持格式和异步语义见 [`lark-minutes-upload`](../references/lark-minutes-upload.md)。`minutes +upload` 成功仅表示异步创建请求已提交；报告返回的 `minute_url` 和可解析的 `minute_token`。未执行 `minutes +detail` 并确认就绪前，不得声称妙记产物已生成或可用。用户只要求发起创建或返回链接时，到此停止。

### 等待并读取妙记产物

上传后立即读取产物时必须加 `--wait-ready`：

```bash
lark-cli minutes +detail --minute-tokens <minute_token> --wait-ready --transcript
```

将 `--transcript` 替换或扩展为用户需要的 `--summary`、`--todo`、`--chapter` 或 `--keyword`。创建任务仍在处理中时，按返回状态和重试提示轮询；不要重复上传或重复创建妙记。

用户要求独立提炼或复盘时，读取 Transcript 并基于原始发言分析，不要复述现成 Summary。产物 flags 和等待行为见 [`lark-minutes-detail`](../references/lark-minutes-detail.md)。

### 从失败阶段恢复

- Drive 上传成功但 Minutes 创建失败：保留并报告 `file_token`，从创建妙记继续，不要重复上传。
- Minutes 创建成功但产物未就绪：保留 `minute_token` 并重试查询，不要重新创建妙记。
- 不得把 Drive 上传成功误报为妙记创建成功；明确报告失败发生在上传、创建还是产物生成阶段。

## 修改妙记标题

使用 `minutes +update --minute-token <token> ...`。参数见 [`lark-minutes-update`](../references/lark-minutes-update.md)。

## 替换 AI 总结

使用 `minutes +summary --minute-token <token> ...` 替换总结全文。内容格式与权限见 [`lark-minutes-summary`](../references/lark-minutes-summary.md)。

## 增删改 AI 待办

妙记 AI 待办不是飞书任务。上下文包含妙记 URL / `minute_token` 并要求修改妙记待办时，禁止改走 `lark-task`；用户同时指定了负责人（包括"负责人是我"）也不改变归属。

```bash
lark-cli minutes +todo --minute-token <token> --operation add|update|delete ...
```

- 多条新增优先使用 `--todos` 批量提交。
- 更新或删除前，先执行 `minutes +detail --minute-tokens <token> --todo`，按内容匹配取得精确 `todo_id`；不要用列表顺序代替 ID。
- 待办 ID、批量结构和部分成功语义见 [`lark-minutes-todo`](../references/lark-minutes-todo.md)。

### 指定负责人

妙记待办表示负责人的既定写法是把 `@姓名` 作为纯文本写进待办内容，不存在独立的负责人字段：

- 用户直接给出姓名时不做任何查找，原文拼成 `@姓名`。
- 用户说"负责人是我"时，先用 `lark-cli contact +get-user` 取真实姓名再拼接；取不到就不写任何 `@` 提及，不要保留字面的 `@我`。
- 姓名解析只影响追加的 `@` 文本，绝不能阻塞或取消待办创建；不要为处理负责人改走 `lark-task` 或做进一步通讯录搜索。
- 不要用"是谁创建的就归属于谁"代替真正的 `@` 文本拼接；创建者和负责人是两件不相关的事。
- 回复只陈述结果（妙记、待办内容、负责人、完成状态），不要解释接口字段限制，也不要建议改用 `lark-task` 来"明确负责人"。

完整规则和示例见 [`lark-minutes-todo`](../references/lark-minutes-todo.md) 的「负责人 / `@` 提及」。

## 批量替换逐字稿关键词

`+word-replace` 修改的是妙记「转写／逐字稿／文字记录」中的字面词条（同一产物的不同叫法）。

`--minute-token` 必须是妙记 token（例如 `obcn...`），合法输入只有两种：`minutes +search` / `vc +recording` 等接口返回的 `token` 字段，或从妙记 URL 里提取最后一段路径并去掉 query 参数后的裸 token。禁止直接传妙记标题、URL 里的 slug、会议主题或完整妙记 URL；不确定时先跑 `minutes +search` / `vc +recording` 拿到 `minute_token` 再执行替换。

```bash
lark-cli minutes +word-replace --minute-token <token> --replace-words '[{"source_word":"<old>","target_word":"<new>"}]'
```

多组替换放在同一个 JSON 数组中。具体参数运行 `lark-cli minutes +word-replace --help`。

用户给出原词和目标词后直接替换：不要为了核对写法先读取 Transcript，也不要在替换成功后回读 Transcript 验证。接口逐词返回结果，按结果回报即可。

只要有一个关键词命中就是成功：`data.message` 列出 Succeeded 和 Failed 关键词。重试时只提交 Failed 的词，不要重复提交已成功的词，否则会把新词再替换一遍。

全部关键词都没命中才是失败（`not_found`）。这是参数问题而不是权限问题；如实告知用户哪些词没命中，请用户确认精确写法、大小写和空格后再决定是否重试，不要靠读取 Transcript 自行猜词。

## 替换逐字稿说话人

1. 调用 `lark-cli api GET "/open-apis/minutes/v1/minutes/<token>/transcript/speakerlist"` 取得 `speaker_id`。
2. 按原说话人的显示名称精确匹配。存在同名候选时，结合 Transcript 展示候选并让用户确认，不要擅选。
3. 用户只提供目标姓名时，用 [`lark-contact`](../../lark-contact/SKILL.md) 解析为 `ou_` open_id。
4. 执行 `minutes +speaker-replace --from-speaker-id <speaker_id> --to-user-id <open_id>`；不要把展示名传给 `--from-speaker-id`。

完整流程和参数见 [`lark-minutes-speaker-replace`](../references/lark-minutes-speaker-replace.md)。

## 查看妙记授权列表

用户要查看妙记已授权给哪些成员，或查询某个成员当前的查看 / 编辑权限时，使用 Drive 协作者列表；这不是读取妙记内容，也不是为当前身份申请权限。先读取 [`lark-drive`](../../lark-drive/SKILL.md) 和 [`drive +member-list`](../../lark-drive/references/lark-drive-member-list.md)。

```bash
lark-cli drive +member-list --token "<minute_url>" --format json
```

完整妙记 URL 可自动推断资源类型为 `minutes`；裸 `minute_token` 必须显式传 `--type minutes`。需要核对指定成员时，按 `member_id` 精确匹配返回的 `items[]`，不要按姓名或列表顺序猜测。

## 一键分享给会议参会人

用户要求“把妙记分享给这场会的参会人”“给参会人开放妙记权限”时，使用 `minutes +share-permission`。本命令只接收 `minute_token`；分享范围、权限含义和权限校验由服务端处理，不要在 CLI 侧自行推断参会人名单。

```bash
lark-cli minutes +share-permission --minute-token <token> --format json
```

执行成功只代表服务端接受请求，不要额外承诺具体通知或事件效果。完整语义见 [`lark-minutes-share-permission`](../references/lark-minutes-share-permission.md)。

## 分配妙记权限

用户要求“把妙记分享给某人”“让某人可以查看 / 编辑”或“给某人授予权限”时，修改的是目标妙记的协作者权限，使用 `drive +member-add`；禁止使用 `minutes +apply-permission`，后者只为当前调用身份向妙记所有者申请权限。

先读取 [`lark-drive`](../../lark-drive/SKILL.md) 和 [`drive +member-add`](../../lark-drive/references/lark-drive-member-add.md)。目标成员只有展示名时，按 [`lark-contact`](../../lark-contact/SKILL.md) 将其唯一解析为对应 ID；存在多个候选时请用户选择，不得猜测。

```bash
lark-cli drive +member-add \
  --token "<minute_url>" \
  --member-id "<open_id>" \
  --member-type openid \
  --perm view \
  --yes \
  --format json
```

完整妙记 URL 可自动推断资源类型为 `minutes`；裸 `minute_token` 必须显式传 `--type minutes`。根据用户要求选择 `view` 或 `edit`；妙记不支持 `full_access`。只有妙记、目标成员和权限档位均已明确，且用户已明确要求执行授权时，才传 `--yes`。

写入后使用 `drive +member-list` 按 `member_id` 回读验证。只有返回的目标成员权限与用户要求一致时，才能声明分配完成；若目标成员已有不同权限，不要仅根据 `member-add` 回执声称权限已被覆盖或降级。

## 申请妙记权限

没有查看或编辑权限时，先说明权限事实。只有用户明确要求申请权限时才执行：

```bash
lark-cli minutes +apply-permission --minute-token <token> --perm view
```

根据用户目标选择 `view` 或 `edit`。这只是发起申请，不代表已经获得权限。权限语义见 [`lark-minutes-apply-permission`](../references/lark-minutes-apply-permission.md)。

`permission_denied` 表示对该妙记没有编辑权，不等于 OAuth scope 缺失；请所有者授权，不要误当作缺权限处理。

## ASR/AI 额度不足

`minutes +upload`、`+summary`、`+todo` 和 `+word-replace` 都可能返回 `quota_exceeded`，表示 ASR/AI 额度已耗尽。`+upload` 是额度不足以转写这个音视频，妙记根本没有创建；其余三个是该妙记生成时额度就已用尽、AI 产物未完整生成，写操作无法落库。

请用户去妙记详情页查看额度详细信息，不要重试：CLI 无法补充或提升额度，重试同样的请求不会成功。这不是权限问题，也不要误走 `+apply-permission`。

## 确认修改结果

修改前只读取目标相关字段，修改后用 `minutes +detail` 或对应读取接口回读。命令自身已逐项返回写入结果时不再回读，例如 `minutes +word-replace` 的 Succeeded / Failed 关键词。批量或多步修改逐项报告写前值、写后结果和失败原因；部分成功时不要回滚已成功项，除非命令明确承诺原子回滚。
```

---

## 三、原 lark-meeting/references/lark-minutes-upload.md

```markdown
# minutes +upload


上传音视频文件到飞书妙记并生成妙记（Minute）。

本 skill 对应 shortcut：`lark-cli minutes +upload`。

## 典型触发表达

- "把这个音视频文件转成妙记"
- "把这个音视频文件转成纪要"
- "把这个音视频文件转成逐字稿、文字稿或撰写文字"
- "把这个音视频文件转成总结、待办或章节"

## 命令示例

```bash
# 通过已上传到云空间（云盘/云存储）的 file_token 生成妙记
lark-cli minutes +upload --file-token boxcnxxxxxxxxxxxxxxxx

```

## 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--file-token <token>` | 是 | 已经上传到飞书云空间（云盘/云存储）的音视频文件的 file_token |

## 支持的格式与限制

待上传到妙记的原始音视频文件必须满足以下要求：

- 支持音频格式：`wav`、`mp3`、`m4a`、`aac`、`ogg`、`wma`、`amr`
- 支持视频格式：`avi`、`wmv`、`mov`、`mp4`、`m4v`、`mpeg`、`ogg`、`flv`
- 音视频时长不能超过 `6` 小时
- 文件大小不能超过 `6 GB`

> 说明：本 shortcut 只接收 `file_token`，不会直接读取本地文件内容，因此这些格式、时长和大小限制对应的是**原始上传文件**本身。若妙记生成失败，请先回查源文件是否满足上述要求。

## 核心约束

### 1. 必须提供 file_token

本接口不直接处理本地文件的上传，必须先使用 `drive +upload` 将文件上传到云空间（云盘/云存储）获取 `file_token`，然后再调用本接口。

### 2. 异步生成

API 会立即返回 `minute_url`，但妙记可能仍在异步生成中。`minutes +upload` 不返回处理状态，命令成功只表示异步创建请求已提交；只有后续执行 `minutes +detail` 并确认就绪，才能声称妙记产物已生成或可用。上传与后续产物获取由 [`create-and-edit-minutes`](../scenes/create-and-edit-minutes.md) 编排；上传后立即查询产物时，`minutes +detail` 必须使用 `--wait-ready`。

## 输出结果示例

```json
{
  "minute_url": "http(s)://<host>/minutes/<minute-token>",
  "minute_token": "<minute-token>"
}
```

| 字段 | 说明 |
|------|------|
| `minute_url` | 生成的妙记访问链接 |
| `minute_token` | 从 `minute_url` 提取出的妙记 Token，可直接传给 `minutes +detail --minute-tokens` |

## 常见错误与排查

| 错误现象 | 错误码 | 根本原因 | 解决方案 |
|---------|--------|---------|---------|
| `error.subtype` = `quota_exceeded` | 2091008 | ASR/AI 额度已用尽，不足以转写这个音视频，妙记未创建 | 让用户去妙记详情页查看额度详细信息；CLI 无法补充或提升额度，重试同一个 `--file-token` 不会成功 |

## 相关场景
- [生成和修改妙记](../scenes/create-and-edit-minutes.md)
```

---

## 四、原 lark-meeting/references/lark-minutes-detail.md

```markdown
# minutes +detail

通过 `minute_token` 查询妙记详情，按需获取 AI 产物（总结/待办/章节/逐字稿/关键词）。只读操作。

> `--summary` / `--todo` / `--chapter` / `--keyword` / `--transcript` 都是可选项；请求相应产物时必须显式传入，不传任何产物 flag 时只返回基础信息（如 `title`），AI 产物字段都不会出现。一次性获取所有产物：`--summary --todo --chapter --keyword --transcript`。

## 命令

```bash
# 仅基础信息
lark-cli minutes +detail --minute-tokens obcxxxxxxxxxx

# 批量（逗号分隔，最多 50 个）
lark-cli minutes +detail --minute-tokens obcxxx,obcyyy --summary --todo

# 全产物
lark-cli minutes +detail --minute-tokens obcxxx --summary --todo --chapter --keyword --transcript

# 仅逐字稿，覆盖已有文件，指定输出目录
lark-cli minutes +detail --minute-tokens obcxxx --transcript --overwrite --output-dir ./out
```

## 输出

`minutes` 数组每条含 `minute_token`、`title`、`note_id`、`meeting_id`（仅在该妙记由会议生成时返回）、`artifacts`。`note_id` 仅在该妙记关联了会议纪要时返回，可直接传给 [`note +detail`](lark-note-detail.md) 拿纪要文档 token，无需再绕回 `vc +detail`。`artifacts` 中**只包含本次请求的产物**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `artifacts.summary` | string | AI 总结。 |
| `artifacts.todos` | array | 待办事项列表。 |
| `artifacts.chapters` | array | 章节列表。 |
| `artifacts.keywords` | array | 关键词列表。 |
| `artifacts.transcript_file` | string | 逐字稿本地文件路径。 |

逐字稿默认落地 `./minutes/{minute_token}/transcript.txt`，与 `minutes +download` 同目录便于聚合。指定 `--output-dir <dir>` 时改写到 `<dir>/artifact-{title}-{minute_token}/transcript.txt`。

## 引用要求

凡在最终回复中使用、改写或总结工具返回的信息，须保留工具结果 `citations` 字段中 `<url>...</url>` 内的原始 URL，并紧随对应表述以 `["url"]` 格式标注。

## 反查关联会议

`meeting_id` 提供从妙记反向定位会议的入口，传给 `vc +detail --meeting-ids` 可继续查会议详情、参会人或反查日程（会议详情可含 `calendar_event_id`，用于再反查日程）。

批量结果要逐条检查 `data.minutes[]` 的 `status` 和 `error`，不能只看整个命令是否成功。`status=processing` 表示仍在生成，按 `retryable` / `next_command` 等待或重试；其他错误按实际失败处理。成功取得基础信息后仍缺少 `meeting_id` 时，只说明未取得关联会议 ID，不据此断言妙记为手动上传，也不猜测 ID 反查。

## minute_token 来源

| 来源 | 取值字段 |
|------|---------|
| 妙记 URL `https://*.feishu.cn/minutes/obcxxx` | 截路径最后一段 `obcxxx` |
| `vc +detail --meeting-ids` | `minute_token` |
| `vc +recording --meeting-ids` | `minute_token` |
| `minutes +search` | `minute_token` |

`minute_token` 不要直接传给 `note +detail`：需要关联 Note 时，先从本命令结果读取 `note_id`。跨产物流程由 [`query-minutes-and-artifacts`](../scenes/query-minutes-and-artifacts.md) 编排。

## 相关场景
- [查询妙记及其产物](../scenes/query-minutes-and-artifacts.md)
```
