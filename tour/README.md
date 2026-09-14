# 房屋漫游视频（一镜到底）

用 `Larktun_Home.blend` 制作 16:9 房屋展示片：先航拍环绕 1.15 m 剖切的整户模型，再降到入户门前，墙体长到满高、天花闭合、入户门打开，然后以手持拍摄的视角走完 13 个房间/区域。全片一个镜头，没有剪切或跳转。

原房屋文件只读；漫游工程是根目录的 `Larktun_Tour.blend`，由脚本重建。

## 成片规格

| 项 | 值 |
|---|---|
| 画面 | 1920×1080，30 fps，6359 帧，约 3 分 32 秒 |
| 渲染 | Blender 5.2.1 EEVEE，光线追踪，32 采样，快门 0.3 的运动模糊，AgX |
| 成片 | `out/tour/larktun_house_tour_1080p.mp4`：H.264 / CRF 17 / yuv420p / BT.709，首 0.8 s 淡入、尾 1.4 s 淡出 |
| 预览 | `out/tour/larktun_house_tour_preview.mp4`：Workbench 960×540，用于检查路线与节奏（不显示升墙材质效果） |
| 路线图 | `out/tour/plan/path_overlay.png`：俯视图上的相机路径、每 10 秒时间点和停留点 |

## 路线

俯瞰环绕（东南→东→北）→ 降至入户门 → 玄关 → 过道（看公卫）→ 书房（书桌、书柜上的 NVR/NAS/路由器）→ 储藏间 → 走廊 → 儿童房 → 客厅入口 → 餐厅 → 厨房 → 生活阳台 → 主卧 → 飘窗 → 主卫 → 客厅 → 南阳台，回望客厅和餐厅结束。

走进死角房间后原路退出，像真人拍摄一样转身、边走边看，不穿墙，不从一个房间跳到另一个房间。

## 为走通路线所做的改动

只在漫游工程中生效，家具没有移动：

- 推拉门：厨房、公卫、储藏间的门扇隐藏，相当于收进墙内；生活阳台门、客厅阳台门的门扇叠到一侧。
- 入户门：镜头停在门外时打开到 80°。
- 主卧门：打开 70°，开向客厅；向卧室开会碰到床头柜，合页也装在客厅一侧。
- 书房门：由原来的 70° 开到 100°。原角度下门扇与沙发床之间过不去人。
- 主卫、儿童房门保持原有开启角度。

## 相机

- 航拍段：平稳环绕并下降，无抖动。
- 步行段：视高 1.52 m，焦距 22 mm（36 mm 画幅）；步速最高 0.8 m/s，门洞处降到 0.4 m/s，起步、停下都有加减速。
- 转头：最快约 42°/s，带加减速；行走时看向前方 1.3 m 处，停留时依次看向房间里的重点。
- 手持感：约 ±6.5 mm 的步伐起伏、左右晃动、轻微滚转和手抖；站立时只保留呼吸感。噪声使用固定种子，重建结果一致。
- 安全距离：按俯视网格，相机距墙、玻璃、门扇、高家具至少 0.2 m。低家具（≤1.12 m）只允许擦边通过，深入不超过 0.15 m。另外按三维逐帧检查最近几何距离，报告在 `out/tour/plan/check_report.json`。

## 重建与渲染

在仓库根目录运行。后期脚本需要 NumPy 与 Pillow：

```bash
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
FILM_PY=/Users/ownding/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3

# 1 可通行地图（门的开合状态改变后才需要重跑）
$BLENDER -b Larktun_Home.blend --python tour/plan_map.py -- out/tour/plan
# 2 相机路径与逐帧相机数据，打印每段长度、时长和最小间距
$FILM_PY tour/camera_path.py
# 3 路线图
$FILM_PY tour/draw_plan.py --path out/tour/plan/path.json
# 4 生成 Larktun_Tour.blend
$BLENDER -b Larktun_Home.blend --python tour/build_tour.py --
# 5 三维逐帧间距检查
$BLENDER -b Larktun_Tour.blend --python tour/check_tour.py -- --step 2
# 6 预览（约 20 分钟）或正式渲染（约 6 小时，可中断后续跑）
$BLENDER -b Larktun_Tour.blend --python tour/render_tour.py -- --mode preview
$BLENDER -b Larktun_Tour.blend --python tour/render_tour.py -- --mode final
# 7 编码成片与缩略图拼版
$FILM_PY tour/encode_tour.py --mode preview
$FILM_PY tour/encode_tour.py --mode final
```

`render_tour.py -- --mode still --frames 560,2933` 可以只渲染指定帧，输出到 `out/tour/stills/`。

渲染进度写在 `out/tour/render_progress_final.json`。已存在的帧会跳过，所以中断后重新执行同一命令即可续跑。若修改了路线或模型，应先清空 `out/tour/frames/`，否则会保留旧帧。

## 修改路线

编辑 `tour/route_def.py`：

- `SEQUENCE` 由停留点 `stop` 和路段 `leg` 交替组成，坐标为图纸坐标（x 向东，y 向南，单位 m）。
- 停留点的 `dwell` 是依次注视的 `(秒, 目标点)`。
- 路段的 `via` 是途经点，`speed` 是最高步速，`look` 是按路段进度切换的视线。
- 航拍段和升墙、开门时间在文件开头。

改完从第 2 步重跑；改变门的开合状态（`tour_scene.py`）时从第 1 步开始。`camera_path.py` 报告里出现 `<-- check` 时，说明这一段离障碍物过近，需要调整途经点。

## 文件

| 文件 | 作用 |
|---|---|
| `route_def.py` | 路线脚本：航拍关键帧、停留点、途经点、视线 |
| `tour_scene.py` | 共用函数：视图层切换、推拉门/平开门状态、EEVEE 设置 |
| `plan_map.py` | 在 Blender 中射线扫描，生成地面 / 低家具 / 障碍三类网格和间距场 |
| `camera_path.py` | A* 与弹性带平滑路径、步速曲线、视线弹簧、手持噪声，输出 `camera_frames.json` |
| `draw_plan.py` | 在 `renders/02_俯视平面.png` 上叠加地图与路径 |
| `build_tour.py` | 生成 `Larktun_Tour.blend`：TOUR 视图层、开门动画、升墙材质、逐帧相机与输出设置 |
| `check_tour.py` | 逐帧向 48 个方向射线，检查相机与几何的最近距离 |
| `render_tour.py` | 预览 / 正式 / 单帧渲染，断点续跑 |
| `encode_tour.py` | FFmpeg 编码与缩略图拼版 |
| `test_render.py` | 早期 EEVEE 画质与耗时探测 |

## 注意

- 升墙效果使用复制出的材质（名称以 `· tour cut` 结尾）：高于 `cut_z` 的部分透明，墙体内侧显示为实心截面。开启透明阴影会让每帧渲染慢约 6 倍（约 20 s 对 3.4 s），`render_tour.py` 只在升墙的约 73 帧开启。
- 1080p PNG 每帧约 2 MB，整片约 12 GB，渲染前确认磁盘空间。本机（Apple M5）实测全片 5 小时 50 分，平均 3.3 秒/帧。
