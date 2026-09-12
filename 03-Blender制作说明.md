# Blender 制作说明（给 Codex 的技术规格）

这份文档是**唯一的技术真相来源**。分镜图 `frames/S01–S14.png` 是视觉参考，
数值以本文档为准。配套脚手架脚本：`src/blender_scaffold.py`。

---

## 0. 结论先行：为什么选等距

等距（isometric）正交投影在 Blender 里是**零风险**的选择：
- 没有透视畸变 → 摆放物体靠坐标算就行，不用反复试机位
- 所有镜头共享一个摄像机角度 → 资产在任何镜头里都能直接复用
- 大面积平色 + 硬边阴影 → EEVEE 就够，不用 Cycles，渲染 1200 帧只要几分钟

**代价**：想要"电影感"的推轨和景深就别指望了。需要冲击力的地方（S01 拉开、S03 航拍、
S04 机柜穿行）允许临时切成透视相机，但**S02 和 S08 必须严格保持同一台正交相机**。

---

## 1. 场景与坐标系

### 单位
1 Blender 单位 = 1 米。房间尺寸按真实居室：客厅 5.0 × 3.8 × 2.7 m。

### 分镜坐标 → Blender 坐标

分镜生成器用的是左手等距系：`+x → 屏幕右下`、`+y → 屏幕左下`、`+z → 上`。
映射到 Blender：

```
blender_x =  storyboard_x
blender_y = -storyboard_y
blender_z =  storyboard_z
```

配合下面的相机设置，画面方向与分镜图**完全一致**。分镜里所有坐标都能直接搬。

### 等距相机（关键）

```python
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 9.0          # 视野宽度（米），越大看到越多
cam.location = (14.0, -14.0, 14.0)  # 方向重要，距离对正交相机无影响
cam.rotation_euler = (radians(54.7356), 0.0, radians(45.0))
```

`54.7356° = atan(√2)`，这是**真·等距**（三轴等长）。
游戏里常用的 `60°` 是"伪等距"，会让垂直方向略微拉长——本片用 54.7356。

**推拉镜头**：正交相机移动位置画面不会变。要"推近"请**给 `ortho_scale` 打关键帧**
（S01 拉开：`ortho_scale` 4.0 → 11.0；S04 穿行：11.0 → 6.5）。

**允许切透视的镜头**：S01（起幅）、S03（航拍）、S04（机柜穿行）、S12（push-in）。
切法：另建一台 `CAM_S03_PERSP`，`type='PERSP'`，`lens=50~85mm`。
其余镜头一律用 `CAM_ISO`。

---

## 2. 渲染设置

```python
scene.render.engine = 'BLENDER_EEVEE_NEXT'   # 4.2+；旧版用 'BLENDER_EEVEE'
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.resolution_percentage = 100
scene.render.fps = 30
scene.frame_start, scene.frame_end = 1, 1200

scene.eevee.use_bloom = True          # 4.2 起改为在合成器里做 Glare
scene.eevee.bloom_intensity = 0.06
scene.eevee.bloom_threshold = 1.2
scene.eevee.use_gtao = True           # 环境光遮蔽，等距风格的立体感全靠它
scene.eevee.gtao_distance = 0.35
scene.eevee.taa_render_samples = 64
scene.eevee.use_shadow_high_bitdepth = True
scene.eevee.use_soft_shadows = True

scene.view_settings.view_transform = 'AgX'   # 4.0+；3.x 用 'Filmic'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = 0.0
```

**输出**：PNG 序列（16-bit，带 alpha 便于后期加字幕），路径 `render/S##/####.png`。
最后用 ffmpeg 合成：

```bash
ffmpeg -r 30 -i render/all/%04d.png -c:v libx264 -crf 18 -pix_fmt yuv420p \
       -vf "scale=1080:1920" larktun_01.mp4
```

**不要在 Blender 里烧字幕**——放到剪辑软件做，改文案不用重渲。

---

## 3. 配色表

直接复制成 `PALETTE` 字典用。所有颜色都是 sRGB hex，在 Blender 里**必须做 sRGB→Linear 转换**
（脚手架里的 `hex_to_linear()` 已经处理）。

| 用途 | Hex | 说明 |
|---|---|---|
| 背景（最深） | `#05070E` | World 背景色 |
| 背景（中） | `#0C1220` | 远景地面 |
| 背景（浅） | `#151E33` | 近景平台 |
| 墙面 | `#EFE7DA` | roughness 0.85 |
| 墙面暗部 | `#D6C9B6` | — |
| 地板 | `#CFA271` | roughness 0.60，可叠 Noise 做木纹 |
| 木家具 | `#9C6F45` | roughness 0.70 |
| 沙发布 | `#3E4C6D` | roughness 0.95 |
| **危险/外流 红** | `#FF4B4B` | Emission strength 12 |
| 危险辅助 橙 | `#FF8A3D` | — |
| **云雀通 青（占位）** | `#2FE0C8` | Emission strength 10 ⚠️ **换成品牌正色** |
| 云雀通 辅助蓝 | `#49A0FF` | — |
| 金钱 金 | `#FFC65C` | metallic 0.8, roughness 0.25 |
| 冷光（窗/屏） | `#8FD3FF` | Emission strength 3 |
| 暖灯 | `#FFC061` | Emission strength 6 |
| 金属/机柜 | `#3D4A66` | metallic 0.6, roughness 0.4 |
| 文字主色 | `#F4F7FC` | — |
| 文字次级 | `#93A1BC` | — |

> **⚠️ 品牌色**：`#2FE0C8` 是我为分镜定的占位青色。请换成云雀通官方品牌色，
> 改 `src/iso.py` 里 `P['brand']` 一个值，重跑 `render.py` 就能出一套新分镜图；
> Blender 里改 `PALETTE['brand']` 一个值即可。

---

## 4. 灯光

三点布光 + 环境，全片通用，不同镜头只调强度：

| 灯 | 类型 | 位置 | 参数 |
|---|---|---|---|
| Key | Area | `(-6, -9, 11)` | size 8m，power 450W，色温 6200K，指向原点 |
| Fill | Area | `(9, -5, 5)` | size 6m，power 90W，色 `#8FD3FF` |
| Rim | Area | `(4, 8, 7)` | size 5m，power 160W，色 `#49A0FF` |
| 室内暖灯 | Point | 房间内 `(2.5, -1.0, 2.2)` | power 40W，色温 2700K，radius 0.3 |
| World | — | — | 色 `#05070E`，strength 0.35 |

**暗场镜头（S01 / S03 / S07 / S14）**：Key 降到 80W，全靠自发光物体和 World 撑。
不要用后期压暗——直接让灯暗，噪点和层次都更好。

**S12 夜景**：Key 降到 60W 并换成冷蓝 `#3A5580`；室内暖灯升到 120W，
再加一盏 Point 做夜灯（色 `#FFC061`，power 25W，radius 0.15）。

---

## 5. 材质

统一用 Principled BSDF。三类就够：

### 5.1 哑光实体（墙、地板、家具）
```
Base Color = PALETTE[x]
Roughness  = 0.6 ~ 0.95
Metallic   = 0
Specular    = 0.3
```

### 5.2 自发光（数据流、LED、屏幕、隧道）
```
Emission Color    = PALETTE[x]
Emission Strength = 8 ~ 20
Base Color        = 同色但亮度 ×0.3
Roughness         = 1.0
```
**注意**：EEVEE 里自发光不产生真实光照。要让数据流"照亮"周围，
在流的路径上加几盏低强度 Point light 跟着动。

### 5.3 金属（机柜、金币、NAS 外壳）
```
Metallic  = 0.7 ~ 0.9
Roughness = 0.25 ~ 0.45
```

---

## 6. 数据流的三种做法（本片全部用得到）

### 6.1 光管（S02 红流主体、S09 隧道）
1. 建 Bezier Curve，`bevel_depth = 0.06`（隧道用 0.18），`bevel_resolution = 6`
2. 给 Emission 材质
3. **流动**：材质里 `Gradient Texture (Linear)` → `Color Ramp`（做成几段条纹）→ 接 Emission Strength
   给 `Mapping` 节点的 `Location.X` 打关键帧，每秒移动 1.0，`interpolation='LINEAR'`，
   再把 F-Curve 的 modifier 设成 `Cycles` → 无限循环流动
4. **生长**（S09 隧道从家里长出去）：给 `curve.data.bevel_factor_end` 打关键帧 0 → 1

### 6.2 数据包（S02、S08 的菱形小方块）
Geometry Nodes：
```
Curve → Resample Curve (Count=12)
      → Instance on Points  [Instance = 小立方体, Rotation = 45° on Z]
      → Set Position (Offset = 沿曲线切线 × frame*speed)  ← 或直接给 Resample 的起点打关键帧
      → Realize Instances
```
更省事的做法：Curve Modifier + Array Modifier，把一串立方体沿曲线排开，
给物体的 `location` 沿曲线打关键帧循环。

### 6.3 脉冲圆环（S07 切断、S01 红环）
一圈 Torus，`Emission`，给 `scale` 和材质 `Emission Strength` 打关键帧：
```
frame 0 : scale 0.1,  strength 30
frame 12: scale 3.0,  strength 8
frame 30: scale 6.5,  strength 0
```
错开 4 帧复制 3～4 份，就是分镜图里的多层扩散环。

---

## 7. 镜头切换

**不要**用一台相机去飞 14 个镜头。做法：

1. 每镜一台相机：`CAM_S01` … `CAM_S14`
2. 在时间轴上每 90 帧打一个 Marker，选中对应相机按 `Ctrl+B` 绑定
3. Python 里：
```python
marker = scene.timeline_markers.new(f"S{n:02d}", frame=start)
marker.camera = bpy.data.objects[f"CAM_S{n:02d}"]
```
这样一次渲染就能出全片，不用分段拼。

**Collection 组织**：
```
SHOT_S01 / SHOT_S02 / ... / SHOT_S14     ← 每镜独有的物体
SHARED_ROOM        ← 客厅（S02/S08 共用，两镜只切换数据流和 LED 颜色）
SHARED_PROPS       ← 沙发/桌椅/电视/绿植/摄像头/录像机/NAS/路由器
SHARED_LIGHTS      ← 三点布光
CAMERAS
```
用 `collection.hide_render` 按帧打关键帧来控制哪个镜头可见。

---

## 8. 资产清单（做一次，全片复用）

| 资产 | 说明 | 用在 |
|---|---|---|
| `PROP_Camera` | 白色方形摄像头，镜头黑罩 + 可换色 LED | S01,02,03,06,07,08,09,11,12 |
| `PROP_NVR` | 扁平硬盘录像机，正面 3 颗指示灯 | S08,09,11,12 |
| `PROP_NAS` | 4 盘位方形 NAS，侧面槽位 + 青色 LED | S08 |
| `PROP_Router` | 路由器 + 3 根天线 | S08,13 |
| `PROP_Sofa` / `Table` / `Chair` / `TV` / `Shelf` / `Plant` / `Crib` | 低模家具 | S01,02,08,09,12 |
| `PROP_Person` | 简化人形（球头 + 锥形身体），3 种配色 | S01,02,09,12 |
| `PROP_Phone` | 手机（屏幕用单独材质槽，贴 UI 图） | S05,10,11 |
| `PROP_Rack` | 机柜 + 7 格小屏（小屏用 emission 数组） | S04 |
| `PROP_Tower` | 无品牌机房塔（6 条红色灯带） | S03,11 |
| `PROP_House` | 等距小屋（方体 + 四坡屋顶 + 亮窗） | S03,07 |
| `PROP_Coin` | 金币（圆柱，metallic） | S06 |
| `ROOM_Living` | 客厅剖面（地板 + 两面后墙 + 窗） | S02,08,09 |

**建议**：先做 `ROOM_Living` + `PROP_Camera` + 数据流三件套，把 S02 和 S08 跑通。
这两镜一成，全片 70% 的技术问题就都解决了。

---

## 9. 手机 UI 的处理（S05 / S10 / S11）

**不要在 Blender 里建 UI。** 做法：
1. 用 HTML/SVG 画出 UI 全图（1080×2200，就是分镜图里手机屏幕的内容）
2. 导出成 PNG
3. 在 Blender 里给手机屏幕面片贴一张 Emission 贴图（strength 2.5）
4. 需要动效（付费墙滑入、实时画面展开）时导出成 PNG 序列，用 Image Sequence 贴图

分镜生成器 `src/scenes_a.py` 里 `s05()` 和 `src/scenes_b.py` 里 `s10()` 的 `inner` 变量
就是完整的 UI SVG，可以直接抠出来单独渲染成贴图。

---

## 10. 质量检查清单

渲染完过一遍：

- [ ] S02 和 S08 的机位、家具位置、房间朝向**逐像素一致**（叠图对比）
- [ ] 全片没有出现任何真实品牌的 logo、UI 或可识别建筑
- [ ] S05 的 `¥XX` 已替换成真实数字
- [ ] 品牌青色已换成云雀通正色（S07–S14 全部）
- [ ] S14 的雀鸟标志已换成官方 logo
- [ ] S07 的音频空拍确实是 0.3 秒（在剪辑软件里量）
- [ ] 手机竖屏观看时，字幕没有被平台 UI（点赞栏、进度条）挡住——底部留 320px 安全区
- [ ] 静音播放时，只看画面和字幕，信息是否完整
- [ ] 前 3 秒单独播放，能不能让人停下来
