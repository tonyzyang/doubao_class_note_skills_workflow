# 阶段一：录音核查与妙记转写

目标：拿到完整、可信的逐字稿，作为后续图文对齐与撰写的唯一事实主源。

## 1. 核查录音完整性（最容易翻车，必做）

先确认录音是一整堂课，而不是片段：

- 若有 ffprobe：`ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 "<音频>"`，把秒数换算成分钟（一堂课通常 60–150 分钟）。
- 若环境未安装 ffmpeg（常见），从文件大小、用户描述判断；拿不准就直接问用户这是否为完整录音。
- 若只有几分钟、明显只是开场/课间安排，先暂停并向用户确认补发，不要急着写。

格式与上限：wav/mp3/m4a/aac 等；时长 ≤6 小时、大小 ≤6 GB。超限先告知，不自行压缩。

## 2. 妙记三步转写

先 Read `lark-meeting.md`（本目录，已内联 lark-meeting 主文件、「生成和修改妙记」场景手册及 `minutes +upload`、`minutes +detail` 命令参考）；其中 Drive 上传步骤按 `lark-drive.md`（本目录，已内联 lark-drive 主文件与 `drive +upload` 命令参考）执行，再执行：

```bash
# 1) 上传源文件到云空间，拿 file_token（注意 lark-cli 上传 allowlist，必要时先复制到 ~/Doubao 下）
lark-cli drive +upload --file "<本地音频>"
# 2) 用 file_token 创建妙记（异步，返回 minute_token）
lark-cli minutes +upload --file-token <file_token>
# 3) 等待就绪并一次性拉全产物；逐字稿默认落地 ./minutes/<minute_token>/transcript.txt
lark-cli minutes +detail --minute-tokens <minute_token> --wait-ready --transcript
```

- `--wait-ready` 是硬要求：长音频（约 2 小时）轮询约 20 分钟属正常，不要提前取稿。
- summary/chapter/keyword 经常为空，以 transcript 为准。
- 逐字稿首行是时间戳头，其后按 `Speaker 1 / Speaker 2…` 标注；主讲一般是 Speaker 1，提问者另算，判定不了保留原标签。
- 已存在的妙记/逐字稿直接复用，不要重复上传或创建。

错误处理：`quota_exceeded` 不可重试，告知用户去妙记详情页查看额度；网络/超时瞬时错误有限退避重试；禁止用本地 ASR（whisper/ffmpeg）替代妙记；不覆盖、不删除云端文件。

## 3. 通读并梳理讲课主线

拿到逐字稿后先完整通读，建立：整堂课分成哪几个大部分、每个部分的主题；每个知识点、公式、例子、问答的先后顺序；哪些是成体系的技术讲解，哪些是题外话。

这份顺序清单是图文对齐、查漏补缺的骨架。完成后再进入阶段二获取幻灯片——先转写、后取图，因为只有先知道讲了什么，才能把每张图对应到讲解段落。
