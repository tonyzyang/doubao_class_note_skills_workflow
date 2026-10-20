# 阶段二：获取幻灯片（PPT 导出 或 引导分批上传照片）

幻灯片有两条来源路径，按用户提供的材料选择，最终都汇合到「按讲课顺序、去重、已压缩」的 `images/` 与 manifest。

## 路径 A：用户提供 PPTX（更完整，优先）

把 PPTX 每页导出为图片：

- Windows 且装了桌面版 PowerPoint（本环境默认）：
  ```bash
  python scripts/extract_ppt_windows.py "<deck.pptx>" --out raw --width 1600
  ```
  输出 `raw/01.png … raw/NN.png`（保留幻灯片原貌，4:3 幻灯片为 1600×1200）。
- 缺 pywin32：`pip install pywin32`；没有 PowerPoint 时改用 LibreOffice：
  ```bash
  soffice --headless --convert-to pdf --outdir raw "<deck.pptx>"
  # 再把 pdf 转成每页 png（需 poppler/pdftoppm 或直接让构建器处理 pdf；也可在 PowerPoint/WPS 里另存）
  ```
  PPT 导出基本不缺页，也无需重排。

## 路径 B：引导用户分批上传现场照片

转写完成后，主动引导用户上传，讲清规则：

- 每批最多 **20 张**；传完一批、等处理后再传下一批，直到用户说「传完了」，不要假设一批即全部。
- 尽量每页拍一张；模糊、反光、缺角的重拍；同一页不必重复拍。
- 照片顺序可以乱，后续按讲课顺序重排，不必用户自己排。

收到每批后先确认张数，再请用户继续。

## 汇合：识别、重排、去重、压缩

1. **逐张识别**：用 Read 打开每张图，看清标题、公式、要点、页码，记录真实主题。
2. **按讲课顺序重排**（照片路径）：以阶段一主线为基准，按讲解先后编号 01、02…；板书也算一页。
3. **去重**：剔除同一页在不同批次的重复照片。
4. **剔除无内容页**：如「谢谢」、纯致谢、纯空白、与本讲无关的图——不放进 staging（PPT 路径用 `--exclude` 按序号排除）。
5. 把要保留的文件复制进一个 staging 目录，以 `01_、02_…` 顺序命名（PPT 路径直接用 raw/）。
6. **压缩并生成 manifest**：
   ```bash
   python scripts/prepare_images.py <staging_dir> --out images --width 1600 --quality 82
   # PPT 排除致谢页示例：--exclude 40
   ```
   输出 `images/01.jpg …`（幻灯片文字仍清晰）与 `manifest.json`。

照片路径若发现某环节明显该有幻灯片却没拍到，先记下位置，留给阶段四查漏（无图补讲），不要自行编造图片。
