"""Independent caption and sound-cue deliverables, prepared before full rendering."""
from pathlib import Path
import json,re
from PIL import ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out';OUT.mkdir(exist_ok=True)
font=ImageFont.truetype(str(ROOT/'assets/fonts/NotoSansCJKsc-Black.otf'),74);ascent,descent=font.getmetrics()
rows=[('S01',1,90,['你家客厅的画面'],None),('S02',91,180,['每一秒','都在离开你家'],None),('S03',181,270,['最后存在','谁的硬盘上？'],None),('S04',271,360,['别人的机房里','有一格是你家'],None),('S05',361,450,['想回看昨天？','先交月费'],None),('S06',451,540,['×3 台摄像头'],'云存储月费'),('S07',541,630,['可它','本来就不用出门'],'转折'),('S08',631,720,['录像','存回你自己家'],None),('S09',721,810,['云雀通','只打一条回家的路'],None),('S10',811,900,['点开，就是家里'],None),('S11',901,990,['同一个画面','两条完全不同的路'],None),('S12',991,1080,['画面','从没离开过你'],None),('S13',1081,1140,[],'装完就能用'),('S14',1141,1185,['云雀通 Larktun','把回家的路，','握在自己手里','docs.larktun.com'],None)]
def ass_time(t):
 c=round(t*100);return f'{c//360000}:{c//6000%60:02d}:{c//100%60:02d}.{c%100:02d}'
header='''[Script Info]
Title: Larktun 01 / independent captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Noto Sans CJK SC Black,74,&H00FFFFFF,&H00FFFFFF,&H00150C08,&H00000000,0,0,0,0,100,100,0,0,1,14,0,2,60,60,340,1
Style: Corner,Noto Sans CJK SC Black,34,&H00FFFFFF,&H00FFFFFF,&H00150C08,&H00000000,0,0,0,0,100,100,0,0,1,6,0,8,60,60,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
events=[];entries=[]
for shot,start,end,lines,corner in rows:
    visible_start=1149 if shot=='S14' else start
    for i,line in enumerate(lines):
        assert len(re.findall(r'[\u4e00-\u9fff]',line))<=9
        baseline=1560-(len(lines)-1-i)*102
        override=f'{{\\an2\\pos(540,{baseline+descent})}}'
        if shot=='S14':override='{\\fad(300,0)}'+override
        events.append(f'Dialogue: 0,{ass_time((visible_start-1)/30)},{ass_time(end/30)},Main,,0,0,0,,{override}{line}')
    if corner:events.append(f'Dialogue: 0,{ass_time((start-1)/30)},{ass_time(end/30)},Corner,,0,0,0,,{{\\an8\\pos(540,230)}}{corner}')
    entries.append(dict(shot=shot,start=start,visible_start=visible_start,end=end,lines=lines,corner=corner))
(OUT/'subtitles.ass').write_text(header+'\n'.join(events)+'\n')
manifest=dict(font='assets/fonts/NotoSansCJKsc-Black.otf',font_family='Noto Sans CJK SC',font_size_px=74,outline_px=14,outline_rgb='#080C15',final_line_baseline_y=1560,line_spacing_px=102,ass_baseline_compensation_px=descent,captions=entries,notes=['Narrative captions are independent of Blender.','Installed FFmpeg lacks libass; the final compositor uses an equivalent transparent raster caption layer drawn at the exact requested baselines, then overlays it with FFmpeg. ASS remains separately editable.','S14 caption fade overlaps the 1.2-second logo hold to retain reading time within the fixed 2-second shot and final 15 black frames.'])
(OUT/'caption_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
coin_frames=[457,467,476,484,491,497,502,506,509,512,514,516]
sound='''# 云雀通 01 · 帧级音效表（交声音制作）

本项目交付无声视频，不生成、不混入任何音轨。以下是制作指示，依据 `01-创意与分镜脚本.md` 第三节；具体单点按本片实际动作帧标定。

30 fps，帧号从 1 开始；帧 f 的起始时间为 `(f-1)/30` 秒。最后一帧为 1200，片长 40 秒。

| 起始帧 | 结束帧 | 时间范围 | 声音内容与同步 |
|---:|---:|---|---|
| 1 | 90 | 00:00–00:03 | 近乎无声，仅极低频 hum |
| 22 | 22 | 00:00.700 | 摄像头 LED 第一轮峰值：低声“嘀” |
| 64 | 64 | 00:02.100 | 第二轮 LED 峰值：“嘀” |
| 91 | 270 | 00:03–00:09 | 冷、稀疏、低音合成器 pad + 心跳感 kick，约 90 BPM；外传红流使用“嘶——”白噪声扫频 |
| 271 | 540 | 00:09–00:18 | 加入机房风扇底噪，承接前段冷色 BGM |
| 397 | 397 | 00:13.200 | S05 付费墙开始滑入：干涩“咔” |
| 457 | 516 | 00:15.200–00:17.200 | S06 每根月费柱一个清脆金属声；下面列出全部十二个精确起音帧，节奏渐快 |
| **541** | **549** | **00:18.000–00:18.300** | **BGM、风扇、扫频和其他持续音全部骤停，保持整整 9 帧。不要跨界保留尾音。** |
| **541** | **541** | **00:18.000** | 静音点只保留一声短“叮”，对齐青色截断脉冲；不恢复背景床 |
| 550 | 900 | 00:18.300–00:30 | 转为同一旋律动机的温暖琶音与轻微 lo-fi；数据流从“嘶”转为柔和“嗡” |
| 901 | 990 | 00:30–00:33 | S11 上下对比：红路径声音偏左、青路径偏右；上方一轮 36 帧，下方一轮 15 帧 |
| 991 | 1080 | 00:33–00:36 | 保持温暖动机，弱化节拍，避免打破熟睡夜景；小光点往返周期 24 帧，可轻微带动柔和“嗡” |
| 1081 | 1140 | 00:36–00:38 | 节奏回升；三张卡片各一声轻“咔哒” |
| 1081 | 1081 | 00:36.000 | 第一张卡片开始弹入：“咔哒” |
| 1087 | 1087 | 00:36.200 | 第二张卡片开始弹入：“咔哒” |
| 1093 | 1093 | 00:36.400 | 第三张卡片开始弹入：“咔哒” |
| 1141 | 1185 | 00:38.000–00:39.500 | 落版，BGM 收在长混响和弦；尾响必须在黑场前收住 |
| 1186 | 1200 | 00:39.500–00:40.000 | 最后 15 帧黑场留白，无新增声音 |

S06 十二根月费柱精确起音帧：**'''+', '.join(map(str,coin_frames))+'''**。金额保持 `¥ XX` 占位；声音不暗示真实收费金额。

风格方向：冷科技 + 一点人味儿；避免激昂的企业宣传片罐头音乐。
'''
(OUT/'audio_cue_sheet.md').write_text(sound)
(OUT/'graphics_timing.json').write_text(json.dumps(dict(coin_frames=coin_frames,card_start_frames=[1081,1087,1093],card_overshoot=1.06,S11_red_path_frames=36,S11_cyan_path_frames=15,S14_black_frames=[1186,1200],S14_logo_hold_frames=[1150,1185]),indent=2)+'\n')
print('ASS, caption manifest, frame-level sound cue sheet prepared')
