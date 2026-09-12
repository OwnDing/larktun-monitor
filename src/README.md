# 分镜图生成器

这套 Python 脚本生成 `frames/S01.png … S14.png`（1080×1920 竖屏分镜图）。
改品牌色、改文案、改构图之后重跑即可全套更新，不用手工改图。

## 运行

```bash
pip install playwright --break-system-packages
playwright install chromium
python3 render.py ./out          # 输出 out/svg/*.svg 和 out/png/*.png
```

渲染走的是 Chromium（SVG 滤镜、渐变、中文字体的还原度最好）。
没有 Playwright 的话把 `render.py` 末尾换成 `cairosvg` 也能跑，但发光效果会弱一些。

## 文件

| 文件 | 作用 |
|---|---|
| `iso.py` | 等距投影、配色表 `P`、明暗计算、SVG 文档骨架（`frame_svg`：标题条/字幕/暗角/颗粒） |
| `comp.py` | 可复用组件：剖面屋、家具、摄像头、人物、NAS/录像机/路由器、数据流、隧道、手机 |
| `scenes_a.py` | S01–S07 |
| `scenes_b.py` | S08–S14 |
| `render.py` | 批量出图 |

## 改品牌色

`iso.py` 里：

```python
P = dict(
    ...
    brand="#2FE0C8",   # ← 换成云雀通正色
    brand2="#49A0FF",
)
```

改完重跑 `render.py`，14 张图全部更新。

## 坐标系

`iso(x, y, z)`：`+x → 屏幕右下`，`+y → 屏幕左下`，`+z → 上`。
真等距（30° / cos30°）。Blender 侧对应 `(x, -y, z)` + 相机 `rotation_euler=(54.7356°, 0, 45°)`。

## 加一个新镜头

```python
def s15():
    a = A(118, 505, 790)            # 缩放, 原点x, 原点y
    C.room(a, 0, 0, 5.0, 3.8, 2.7)  # 剖面房间
    C.sofa(a, .7, 2.55)
    C.cam(a, 4.2, .05, 2.2, led=P['brand'])
    C.stream(a, (4.35,.3,2.25), (3.2,.5,1.0), P['brand'], 6, 40)
    return frame_svg(a.out(), "S15", "0:40–0:43", "3s", "字幕", "角标", P['brand'],
                     topnote="镜头说明")
```
然后在 `render.py` 的 `SCENES` 里加一行。
