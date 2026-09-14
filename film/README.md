# 云雀通 01 · 影片工程与复现

本目录对应 `06-给Codex-整片制作.md` 的 A–H 阶段。最终验收状态与实际折扣见仓库根目录的 `PRODUCTION_REPORT.md`。

## 交付结构

| 路径 | 内容 |
|---|---|
| `Larktun_Home.blend` | 保留的房屋源工程 |
| `Larktun_Film.blend` | 可编辑人物、房屋、相机、灯光、数据流和动画 |
| `out/frames/0001.png` … `1200.png` | 1080×1920、16-bit RGBA、30 fps 的 Blender 原始输出 |
| `out/composite_frames/clean/` | 叠入必要图形后的无叙事字幕画面 |
| `out/caption_frames/` | 独立透明字幕层 |
| `out/larktun_01_clean.mp4` | 无叙事字幕、无音轨；保留手机 UI、金额、分屏、卡片、Logo |
| `out/larktun_01_sub.mp4` | 带叙事字幕、无音轨 |
| `out/subtitles.ass` | 可单独编辑的字幕时间轴 |
| `out/audio_cue_sheet.md` | 帧级声音规格；阶段 I 按此表生成音轨 |
| `out/larktun_01_clean_audio.mp4` / `out/larktun_01_sub_audio.mp4` | 两版有声成片：视频数据包与无声版逐包相同，AAC 256 kbps / 48 kHz 立体声 |
| `out/audio/` | 母带 WAV（48 kHz / 24-bit）、四轨分轨、`sound_manifest.json`、同步探针与 `SOUND_DESIGN.md` |
| `out/gates/` | 构图、光照、动态、叠图和最终编码验收证据 |
| `scene/layout.json` | 图纸坐标系下的最终设备、人物和机位参数 |

大型 PNG 序列保留在当前交付目录，不进入 Git。源码、模型、素材来源、Gate 证据及清单进入阶段提交。拷贝影片工程时应同时拷贝 `film/`、`out/ui/frames/` 和 `renders/v1_framing/`，保留相对目录结构。

## 在 Blender 打开

实际制作环境为 macOS / Apple M5 / Blender 5.2.1 LTS / Eevee、64 采样、raytracing、AgX。Blender 5.2 的引擎枚举为 `BLENDER_EEVEE`，不是旧文档中的 `BLENDER_EEVEE_NEXT`。

打开 `Larktun_Film.blend`，选择场景 `Larktun Film`。在 Text Editor 运行工程内的 `RUN_FILM_TIMELINE.py`，然后拖动时间轴。这个控制器根据镜头选择固定 View Layer、剖切和屏幕贴图，并计算数据流附光的位置；相机、骨骼、账单和脉冲环的关键帧仍可直接编辑。首次打开时若没有执行此控制器，单独拖动时间轴不能完整恢复所有镜头的显隐状态。命令行渲染脚本会主动安装控制器。

相机位置全程固定，推拉只改变正交尺度。图纸 `(x,y,z)` 到 Blender 为 `(x,-y,z)`；相机 X=54.7356°，Z 仅为 45/135/225/315°，直接赋 Euler。V1 的图纸看点为 `(6,4.6,1.3)`、Z225°、scale18；竖屏世界覆盖为水平 10.125 m、垂直 18 m。

`LOOK_DARK`、`LOOK_DUSK`、`LOOK_NIGHT` 是三个独立 View Layer，各自使用固定灯组及 World override。原白天灯组均排除。

## 从交付工程重渲

在仓库根目录执行。先对当前工程估时，再决定是否启动整片。下列路径是本次 Mac 的实际 Blender 路径。

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b Larktun_Film.blend -t 8 \
  --python film/render_film.py -- --mode benchmark
```

实测估时在 `out/gates/G/render_estimate.json`。本次用户已明确批准原规格超过两小时的估时，因此正式运行使用以下显式参数；未来再次重渲时也应先检查新估时和授权范围。

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b Larktun_Film.blend -t 8 \
  --python film/render_film.py -- --mode render --approved-over-two-hours
```

断点续渲追加 `--resume`。仅复用与已有 `out/frames_manifest.json` 中 SHA-256 一致的文件，其余帧重渲。若改变影响某些镜头的模型、灯光或动画，先将对应原始帧移出 `out/frames/`，再续渲；文件哈希一致不能替代内容是否过期的判断。

`out/render_progress.json` 保存进度；清单每 90 帧落盘，结束时覆盖全部 1200 帧。渲染脚本不会将临时逐镜显隐保存回房屋源文件。

本次生产中 S04 的两次红框脉冲、S05 的字幕安全区和 S07 的附光显隐曾经返工。最终源码已经包含修正，重新从头渲染不需要再次执行补丁。`render_final_patches.py --apply` 仅记录此次主渲染后替换 S05 全镜及 S07 前六帧的过程；前后哈希和原始帧备份位于 `out/gates/G/final_corrections/`。

## 字幕与后期

后期 Python 需要 Pillow 和 NumPy。当前系统 `python3` 有 Pillow；验收脚本使用带 NumPy 的现成运行时：

```bash
FILM_PY=/Users/ownding/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
"$FILM_PY" film/validate_delivery.py --stage G
python3 film/prepare_post.py
python3 film/compose_film.py --mode full
python3 film/export_video.py
"$FILM_PY" film/validate_delivery.py --stage H
```

改叙事文案：编辑 `film/prepare_post.py` 的字幕表，重跑以上后期步骤即可。改金额、分屏或卡片图形：编辑 `film/compose_film.py`。这些操作不需要重渲 Blender。`--mode preview` 使用已有正式帧，尚缺的帧明确回退到 benchmark 单帧，仅供图形排版预检。

当前 `/opt/homebrew/bin/ffmpeg` 构建没有 libass。成片通过独立 RGBA 字幕 PNG 在 FFmpeg 阶段叠加；实际字体文件为 `NotoSansCJKsc-Black.otf`，74 px、14 px 深描边、最后一行基线 1560。ASS 同时交付，使用字体内部完整家族名 `Noto Sans CJK SC Black`，在支持 libass 的工作站可编辑使用。跨字幕引擎的字体度量可能不同，以本次独立字幕层为已验收的排版。

两版 MP4 分别从无损图形帧编码，字幕版不再转码已压缩的 clean MP4。均为 H.264 / CRF18 / yuv420p / BT.709 / 30 fps / 40 秒 / 无音轨。RGB→YUV 明确使用 BT.709 矩阵。

后期中间帧统一为 8-bit RGB，匹配最终 8-bit H.264 交付；Blender 原始 16-bit RGBA 序列独立保留，可供后续高位深剪辑。

S11 上下画面逐帧对应 S02 的 91–180 帧及 S08 的 631–720 帧，使用相同裁切和缩放。上方红路径一轮 36 帧，下方青路径一轮 15 帧。两者原始相机和全身骨骼的 90 对比较见 E；全部 90 张 50% 叠图见 G。

S14：1141–1149 淡出房屋并显出原始雀鸟；1150–1185 共 36 帧保持 Logo；字幕淡入与这段重叠；1186–1200 共 15 帧纯黑。这个重叠是固定两秒时长下的明确时序折扣。

## 声音与混音

音轨全部由 NumPy 程序化合成，没有外部音频素材。完整结构、逐镜 cue、响度与限制见 `out/audio/SOUND_DESIGN.md`。在仓库根目录执行即可，约 1 分钟，不需要重渲 Blender 或字幕：

```bash
FILM_PY=/Users/ownding/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
"$FILM_PY" film/sound_design.py
"$FILM_PY" film/validate_audio.py --stage master
"$FILM_PY" film/mux_audio.py
"$FILM_PY" film/validate_audio.py --stage mux
```

帧 f 起点为采样 `(f-1)×1600`。`sound_design.py` 的 `cue()` 按帧号放置声音，并拒绝在 541–549 放入“叮”以外的声音；冷段及其混响尾巴从 541 帧起逐采样为 0，1186 帧起全轨为数字零。

修改后要重跑两个验收步骤：
- **master**：检查静音窗口、响度（−14 LUFS / ≤−1 dBTP）、分轨求和，以及 29 个关键 cue 的逐采样同步。
- **mux**：确认视频数据包与无声版逐包一致，A/V 偏移为 0。

WAV 母带与分轨是确定性输出，不进入 Git；有声 MP4、manifest 和验收证据进入阶段提交。

## 重新生成手机 UI

源 SVG 从 `src/scenes_a.py:s05:inner` 和 `src/scenes_b.py:s10:inner` 提取；原始版本保留为 `out/ui/*_original.svg`。动画修改在 DOM 副本上进行，价格保持 `¥ XX`。

```bash
python3 film/extract_ui.py
/Users/ownding/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node film/render_ui.cjs
```

生成 S05/S10 各 90 张 1080×2200 PNG、扣费通知和原始雀鸟图。现有工程使用相对路径贴图，保留序列目录即可读取。修改手机 UI 后，需重渲 S05/S10（以及改变了扣费通知时的 S06）。

## 阶段证据索引

| 阶段 | 主要源码 | 主要证据 |
|---|---|---|
| A | `stage_a.py`, `characters.py`, `audit_gate_a.py` | `out/gates/A/framing_report.json` |
| B | `stage_b.py`, `audit_b.py`, `finalize_b.py` | 60 个候选及 `out/gates/B/framing_report.json` |
| C | `stage_c.py`, `refine_c.py`, `finalize_c.py`, `check_c.py` | `out/gates/C/histogram_report.json` |
| D | `stage_d.py` | `out/gates/D/` 首中尾六帧 |
| E | `stage_e.py`, `finalize_e.py`, `polish_e.py`, `motion.py` | `out/gates/E/timeline_report.json` 与 90 对矩阵 |
| F | `extract_ui.py`, `render_ui.cjs`, `stage_f.py` | `out/gates/F/ui_report.json` |
| G | `render_film.py`, `validate_delivery.py --stage G` | 原始全片 24 帧拼版、90 对叠图、清单和校验 |
| H | `prepare_post.py`, `compose_film.py`, `export_video.py` | `out/gates/H/` 最终拼版、ffprobe 与完整解码 |
| I | `sound_design.py`, `sound_kit.py`, `audio_dsp.py`, `mux_audio.py`, `validate_audio.py` | `out/gates/I/` 同步、静音窗口、响度与封装报告，以及频谱图 |

阶段建模脚本会修改影片工程，不是日常播放入口。日常查看及重渲使用最终 `.blend` 与 `motion.py` / `render_film.py`。本项目所有资产与许可的逐文件来源在 `assets/characters/provenance.json`、`assets/fonts/provenance.json`。
