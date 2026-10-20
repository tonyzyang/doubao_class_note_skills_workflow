# 阶段六：构建、验证与交付

## 构建

```bash
python scripts/build_html.py content.json --out "课程·第X讲主题·完整讲义.html"
```

构建器会把幻灯片图 base64 内嵌、ECharts 内联，输出单个离线 HTML。

## 验证（按序）

0. **查漏补缺应已完成**：按 `06-gap-check.md` 建立"段→落点"清单，确认录音无遗漏（按话题逐段切分、段段有落点，超 1 分钟案例独立展开，人名/地名/数字齐全，无知识点只在复习区出现）。
1. **覆盖度核对**：逐字稿为基准，在 content.json 里数到每个知识点的落点；幻灯片数、问答数、结论/自测/模块/数字/易混/话术/迁移条数与实际一致；现场问答每问都有落点（同步区 + 复习区 qa）。数量对不上先补内容。
   - **反向核对（必做）**：逐条回逐字稿检索 content.json 里的每个知识点（尤其数字、参数、清单明细、台词），检索不到即删；幻灯片上有但录音没讲过的，一律不得保留。
2. **标签平衡**：`main/section/article/details/figure/script/style/figure` 开闭数相等。
3. **无外链**：全文件无 `http://`/`https://`（ECharts 与图片均已内联，仅允许页内锚点）。
4. **截图自检（本 skill 自带 scripts/shot.py，唯一自检方式；完整使用说明见 `html.md`）**：
   ```bash
   python scripts/shot.py "<产物.html>"
   ```
   要求 stdout JSON 中 `consoleErrors=[]`、`responsiveChartIssues=none`、`mobileFontIssues=none`；桌面与移动（390）截图都要 Read 逐片核对：图片清晰无黑块、口述要点正确、思维导图不重叠、各复习卡片正常、首尾屏无来源/页脚。
5. 注意已修复的坑：图片不要用 `loading="lazy"`（headless 全页截图会黑块），图片底色用纸色（构建器已内置）。

## 交付

- 用 present_files 交付**单个 HTML**；脚本、源逐字稿、截图中间物不交付。
- 最终回复 ≤8 行：产物简介、幻灯片/补讲/问答数、校验结果、数字为口述约数的提醒。
