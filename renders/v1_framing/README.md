# V1 构图验证

12 张原始渲染 + 12 张 S02 叠加图 + 1 张 4×3 拼版。
原始渲染及叠加图均为 **1080×1920**；Cycles 32 samples。

拼版 `_contact_sheet.png`：列为 Z45 / Z135 / Z225 / Z315，行为 scale 18 / 25 / 32。
`overlay/` 是同名渲染与 `frames/S02.png` 的 RGB 50% 混合，保持原尺寸。

## 投影与剖切结果

下表 true/false 使用 `world_to_camera_view` 判断实际物体包围盒中心是否在画幅内。
最后一列另外列出因剖切隐藏的目标。**投影在框内不等于参与渲染，也不证明没有遮挡。**
JSON 同时保留各组件投影范围、完整入框/部分入框判定、像素占幅和物体名称。

| 机位 / 尺度 | C1 | 电视 | 餐桌 | 沙发 | D1 | 剖切隐藏的目标 |
|---|---|---|---|---|---|---|
| Z45 / S18 | true | true | true | true | false | C1, TV |
| Z45 / S25 | true | true | true | true | false | C1, TV |
| Z45 / S32 | true | true | true | true | true | C1, TV |
| Z135 / S18 | true | true | true | true | true | C1, TV, D1 |
| Z135 / S25 | true | true | true | true | true | C1, TV, D1 |
| Z135 / S32 | true | true | true | true | true | C1, TV, D1 |
| Z225 / S18 | true | true | true | true | false | — |
| Z225 / S25 | true | true | true | true | false | — |
| Z225 / S32 | true | true | true | true | true | — |
| Z315 / S18 | true | true | true | true | true | — |
| Z315 / S25 | true | true | true | true | true | — |
| Z315 / S32 | true | true | true | true | true | — |

Z45 / Z135 的 C1 和电视随近侧东墙隐藏。Z225 要到 scale 32 才将 D1 纳入画幅。
Z315 三档尺度的五个目标均在框内且保留参与渲染；scale 越大，目标占像素越小。

## 相机与剖切

- 看点采用图纸坐标 `(6.0, 4.6, 1.3)`，对应 Blender `(6.0, -4.6, 1.3)`。
- 相机直接赋值 Euler `(54.7356°, 0°, Z)`，由旋转后的局部 +Z 轴后退 40 m 定位。
- 实测水平/垂直覆盖：S18 = 10.125 / 18 m；S25 = 14.0625 / 25 m；S32 = 18 / 32 m。
- 使用完整 01g/01h 源几何；关闭天花板及旧版分段墙体。远侧墙维持全高 2.8 m。
- 房间按“中心处于通向客厅/餐厅的前景射线”隐藏。墙、门窗、开关、踢脚线、窗帘杆和挂墙设备按宿主墙联动隐藏。
- 临时 collection 的完整成员表在 `visibility_groups.json`，逐帧隐藏清单及相机实际参数在 `framing.log` 和 `framing_report.json`。

## 完整性与复现

`framing_report.json` 中记录 `.blend`、`layout.json`、S02 的前后 SHA-256；三者完全一致。
模型几何与原物体变换、灯光、材质、世界环境、原有相机、色彩管理的内存指纹也完全一致。
曝光维持主场景原值 0.3；只有新相机、临时可见性、输出尺寸/路径和采样发生变化。
脚本不会保存 Blender 项目，也不会回写最终方位或尺度。

从项目根目录运行：

```sh
python3 blender/render_v1_framing.py
```

只做几何预检：`python3 blender/render_v1_framing.py --preflight`。
只重建叠加图/拼版/本说明：`python3 blender/render_v1_framing.py --postprocess-only`。
需要当前 macOS 已安装的 Blender 以及带 Pillow 的 Python。
