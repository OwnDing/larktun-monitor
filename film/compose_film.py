"""Post-render graphics and independent caption plates. Never edits raw frames.

Preview mode explicitly uses production-setting benchmark plates when the full
sequence is incomplete. Full mode requires every one of the 1200 raw PNGs.
"""
from pathlib import Path
from functools import lru_cache
import argparse, hashlib, json, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from contact_sheets import grid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'out'
SIZE = (1080, 1920)
RED = '#FF4B4B'
CYAN = '#2FE0C8'
GOLD = '#E7BD68'
INK = '#080C15'
WHITE = '#F5F7FA'
SHOTS = [('S01',1,90,20), ('S02',91,180,135), ('S03',181,270,225),
         ('S04',271,360,340), ('S05',361,450,424), ('S06',451,540,495),
         ('S07',541,630,552), ('S08',631,720,675), ('S09',721,810,770),
         ('S10',811,900,840), ('S11',901,990,945), ('S12',991,1080,1030),
         ('S13',1081,1140,1110), ('S14',1141,1200,1155)]
CAPTIONS = json.loads((OUT / 'caption_manifest.json').read_text())
TIMING = json.loads((OUT / 'graphics_timing.json').read_text())

@lru_cache(maxsize=40)
def font(size, weight='Black'):
    return ImageFont.truetype(str(ROOT / f'assets/fonts/NotoSansCJKsc-{weight}.otf'), size)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def shot_for(frame):
    return next(s for s in SHOTS if s[1] <= frame <= s[2])

def ease(t):
    return 1 - (1 - max(0, min(1, t))) ** 3

def rgba(hexcolor, alpha=255):
    return tuple(int(hexcolor[i:i+2], 16) for i in (1,3,5)) + (alpha,)

def write_png(im, path):
    """Unlink first: a prior clean plate may be a hardlink to a raw PNG."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    im.save(path, compress_level=3)

def raw_plate(frame, preview=False):
    path = OUT / f'frames/{frame:04d}.png'
    if not path.exists():
        if not preview:
            raise FileNotFoundError(path)
        path = OUT / f'gates/G/benchmark/{shot_for(frame)[3]:04d}.png'
    with Image.open(path) as im:
        assert im.size == SIZE
        return im.convert('RGBA')

def text(draw, xy, value, size, fill=WHITE, anchor='mm', outline=0):
    draw.text(xy, value, font=font(size), fill=fill, anchor=anchor,
              stroke_width=outline, stroke_fill=INK)

def dim_plate(im, amount):
    return Image.alpha_composite(im, Image.new('RGBA', SIZE, (5,8,14,round(255*amount))))

def badge(im, label, color, center=(540,260), size=36):
    layer = Image.new('RGBA', SIZE)
    d = ImageDraw.Draw(layer)
    width = round(d.textlength(label, font=font(size))) + 80
    x,y = center
    d.rounded_rectangle((x-width/2,y-38,x+width/2,y+38), 24,
                        fill=(8,12,21,231), outline=rgba(color,210), width=2)
    d.ellipse((x-width/2+21,y-6,x-width/2+33,y+6), fill=color)
    text(d, (x+9,y-1),label,size)
    return Image.alpha_composite(im, layer)

def money_graphic(im, frame):
    age = frame - 451
    layer = Image.new('RGBA', SIZE)
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((76,970,1004,1404), 34, fill=(8,12,21,240),
                        outline=rgba(GOLD,125), width=2)
    text(d,(118,1023),'¥ XX /月  × 3 台',48,GOLD,'lm')
    text(d,(955,1023),'× 12 个月',32,WHITE,'rm')
    d.line((118,1080,962,1080), fill=rgba(GOLD,55),width=1)
    for index, onset in enumerate(TIMING['coin_frames']):
        x = 145 + index*71
        amount = ease((frame-onset)/8)
        count = index+2
        h = (35 + index*12)*amount
        if amount > 0:
            # Coin stacks retain separate rims instead of a flat bar chart.
            step = h / count
            for n in range(count):
                y = 1340 - n*step
                d.rounded_rectangle((x-23,y-step-5,x+23,y+2), 4, fill='#94723B')
                d.ellipse((x-23,y-step-11,x+23,y-step+3), fill=GOLD,
                          outline='#F7D895', width=1)
        text(d,(x,1370),str(index+1),24,'#CFD3DB')
    opacity = ease(age/8)
    if opacity < 1:
        layer.putalpha(layer.getchannel('A').point(lambda x: round(x*opacity)))
    return Image.alpha_composite(im, layer)

def sample_cubic(a,b,c,d,count=100):
    points=[]
    for i in range(count):
        t=i/(count-1);q=1-t
        points.append(tuple(q*q*q*a[j]+3*q*q*t*b[j]+3*q*t*t*c[j]+t*t*t*d[j] for j in range(2)))
    return points

def moving_path(layer, points, color, progress):
    lengths=[0]
    for p,q in zip(points,points[1:]):
        lengths.append(lengths[-1]+math.dist(p,q))
    distance=progress*lengths[-1]
    k=next((i for i,l in enumerate(lengths) if l>=distance),len(points)-1)
    if k:
        f=(distance-lengths[k-1])/max(1e-6,lengths[k]-lengths[k-1])
        head=tuple(points[k-1][j]+f*(points[k][j]-points[k-1][j]) for j in range(2))
    else:
        head=points[0]
    lit=points[:max(1,k)]+[head]
    # Supersample only the small path region for smooth curves in the final frame.
    ox=math.floor(min(p[0] for p in points)-40);oy=math.floor(min(p[1] for p in points)-40)
    w=math.ceil(max(p[0] for p in points)-ox+40);h=math.ceil(max(p[1] for p in points)-oy+40)
    scale=3
    def scaled(points):return [(round((x-ox)*scale),round((y-oy)*scale)) for x,y in points]
    patch=Image.new('RGBA',(w*scale,h*scale));d=ImageDraw.Draw(patch)
    d.line(scaled(points),fill=rgba(color,55),width=7*scale,joint='curve')
    glow=Image.new('RGBA',patch.size);gd=ImageDraw.Draw(glow)
    gd.line(scaled(lit),fill=rgba(color,210),width=14*scale,joint='curve')
    patch.alpha_composite(glow.filter(ImageFilter.GaussianBlur(12*scale)))
    d=ImageDraw.Draw(patch);d.line(scaled(lit),fill=color,width=5*scale,joint='curve')
    x,y=scaled([head])[0];r=10*scale
    d.ellipse((x-r,y-r,x+r,y+r),fill=color)
    for x,y in scaled([points[0],points[-1]]):
        r=7*scale;d.ellipse((x-r,y-r,x+r,y+r),fill=INK,outline=color,width=3*scale)
    layer.alpha_composite(patch.resize((w,h),Image.Resampling.LANCZOS),(ox,oy))

def split_screen(frame, preview=False):
    phase=frame-901
    im=Image.new('RGBA',SIZE,INK)
    for upper,start,y,color,label in [(True,91,170,RED,'云端绕行'),(False,631,760,CYAN,'本地直达')]:
        layer=Image.new('RGBA',SIZE);d=ImageDraw.Draw(layer)
        d.rounded_rectangle((60,y,1020,y+545),32,fill='#101720',outline=rgba(color,120),width=2)
        text(d,(104,y+46),label,40,color,'lm')
        text(d,(973,y+46),'同一间家',25,'#C4CBD5','rm')
        # Both plates use identical crop and destination transforms, never reframe independently.
        plate=raw_plate(start+phase,preview).crop((0,280,1080,1430)).resize((408,435),Image.Resampling.LANCZOS)
        mask=Image.new('L',plate.size);ImageDraw.Draw(mask).rounded_rectangle((0,0,407,434),16,fill=255)
        layer.paste(plate,(104,y+84),mask)
        if upper:
            pts=sample_cubic((603,y+390),(640,y+220),(995,y+480),(956,y+235))
            pts+=sample_cubic(pts[-1],(930,y+100),(600,y+95),(625,y+210))[1:]
            pts+=sample_cubic(pts[-1],(655,y+320),(856,y+145),(920,y+440))[1:]
            cycle=36
        else:
            pts=sample_cubic((603,y+390),(665,y+330),(850,y+325),(920,y+440))
            cycle=15
        moving_path(layer,pts,color,min(1,(phase%cycle)/(cycle-1)))
        d=ImageDraw.Draw(layer)
        text(d,(603,y+443),'摄像头',25,WHITE)
        text(d,(920,y+487),'回看',25,WHITE)
        if upper:
            d.rounded_rectangle((730,y+149,869,y+209),14,fill=INK,outline=color,width=2)
            text(d,(800,y+177),'云端',29)
        else:
            d.rounded_rectangle((664,y+140,963,y+222),20,fill=INK,outline=color,width=2)
            text(d,(815,y+179),'录像留在家里',30)
        im.alpha_composite(layer)
    return im

def card_icon(draw, x, y, kind):
    c=CYAN
    if kind==0:
        draw.ellipse((x-28,y-28,x+28,y+28),outline=c,width=4)
        draw.arc((x-15,y-28,x+15,y+28),0,360,fill=c,width=3)
        draw.line((x-28,y,x+28,y),fill=c,width=3)
    elif kind==1:
        draw.rounded_rectangle((x-31,y-24,x+31,y+24),7,outline=c,width=4)
        for j in (-17,0,17):draw.line((x+j,y-6,x+j,y+10),fill=c,width=3)
        draw.line((x,y+24,x,y+37),fill=c,width=4)
    else:
        draw.rounded_rectangle((x-36,y-27,x+17,y+11),5,outline=c,width=4)
        draw.line((x-10,y+11,x-10,y+24),fill=c,width=4)
        draw.line((x-25,y+24,x+4,y+24),fill=c,width=4)
        draw.rounded_rectangle((x+11,y-8,x+38,y+32),4,fill=INK,outline=c,width=3)

def cards(im,frame):
    im=dim_plate(im,.60)
    labels=['无需公网 IP','免端口映射','全平台客户端']
    for idx,(start,label) in enumerate(zip(TIMING['card_start_frames'],labels)):
        age=frame-start
        if age<0:continue
        if age<10:
            scale=.88+.18*ease(age/10)
        elif age<18:
            scale=1.06-.06*ease((age-10)/8)
        else:scale=1.
        y0=[430,735,1040][idx]
        y=round(y0+(1960-y0)*(1-ease(age/18)))
        card=Image.new('RGBA',(832,238));d=ImageDraw.Draw(card)
        d.rounded_rectangle((5,5,827,233),28,fill=(8,12,21,249),outline=rgba(CYAN,185),width=2)
        d.rounded_rectangle((36,47,166,183),22,fill='#0A2729')
        card_icon(d,101,115,idx)
        text(d,(202,114),label,61,WHITE,'lm')
        card=card.resize((round(832*scale),round(238*scale)),Image.Resampling.LANCZOS)
        im.alpha_composite(card,(round(540-card.width/2),round(y-card.height/2)))
    return im

@lru_cache(maxsize=1)
def bird_plate():
    return Image.open(OUT/'ui/frames/S14_bird_original/0001.png').convert('RGBA')

def closing(im,frame):
    if frame>=1186:return Image.new('RGBA',SIZE,'black')
    age=frame-1141
    im=ImageEnhance.Brightness(im).enhance(1-ease(age/8))
    bird=bird_plate().copy()
    t=max(0,min(1,age/9))
    opacity=t*t*(3-2*t)
    bird.putalpha(bird.getchannel('A').point(lambda p:round(p*opacity)))
    return Image.alpha_composite(im,bird)

def clean_frame(frame,preview=False):
    shot=shot_for(frame)[0]
    if shot=='S11':return split_screen(frame,preview)
    im=raw_plate(1081 if shot=='S13' else frame,preview)
    if shot=='S01':im=badge(im,'REC 24h',RED,(780,235),30)
    elif shot=='S02':im=badge(im,'上传中',RED)
    elif shot=='S06':im=money_graphic(im,frame)
    elif shot=='S08':im=badge(im,'本地录制 · 不出户',CYAN)
    elif shot=='S09':im=badge(im,'端到端加密',CYAN)
    elif shot=='S13':im=cards(im,frame)
    elif shot=='S14':im=closing(im,frame)
    return im

@lru_cache(maxsize=40)
def base_caption(shot):
    item=next(c for c in CAPTIONS['captions'] if c['shot']==shot)
    layer=Image.new('RGBA',SIZE);d=ImageDraw.Draw(layer)
    # Pillow's 's' anchor is the baseline. Multi-line text grows upwards.
    for index,line in enumerate(item['lines']):
        y=1560-(len(item['lines'])-1-index)*102
        d.text((540,y),line,font=font(74),fill='white',anchor='ms',
               stroke_width=14,stroke_fill=INK)
    if item['corner']:
        d.text((540,230),item['corner'],font=font(34),fill='white',anchor='mt',
               stroke_width=6,stroke_fill=INK)
    return layer

def caption_frame(frame):
    shot=shot_for(frame)[0]
    if shot=='S14':
        if frame<1149 or frame>=1186:return Image.new('RGBA',SIZE)
        plate=base_caption(shot).copy();opacity=min(1,(frame-1149)/9)
        plate.putalpha(plate.getchannel('A').point(lambda p:round(p*opacity)))
        return plate
    return base_caption(shot).copy()

def preview():
    dest=OUT/'gates/H/previews';dest.mkdir(parents=True,exist_ok=True)
    frames=[20,135,225,340,424,530,552,675,770,840,945,1030,1115,1165,1190]
    for frame in frames:
        im=clean_frame(frame,True)
        write_png(im,dest/f'{frame:04d}_clean.png')
        write_png(Image.alpha_composite(im,caption_frame(frame)),dest/f'{frame:04d}_sub.png')
    grid([dest/f'{f:04d}_sub.png' for f in frames],
         [f'{shot_for(f)[0]} / f{f}' for f in frames],OUT/'gates/H/preview_contact_sheet.png')
    (OUT/'gates/H/preview_status.json').write_text(json.dumps(dict(
        status='POST_GRAPHICS_PREVIEW',frames=frames,
        source='Available final raw PNGs, otherwise 64-sample production benchmark frames; not final frame validation.'),indent=2)+'\n')

def full():
    raw=OUT/'frames'
    assert all((raw/f'{f:04d}.png').exists() for f in range(1,1201)), 'Wait for all raw frames.'
    dest=OUT/'composite_frames/clean';dest.mkdir(parents=True,exist_ok=True)
    cap=OUT/'caption_frames';cap.mkdir(parents=True,exist_ok=True)
    rows=[];caption_cache={}
    for frame in range(1,1201):
        shot=shot_for(frame)[0];target=dest/f'{frame:04d}.png'
        # A uniform format avoids FFmpeg filter reinitialization at shot cuts.
        # The independent source PNG sequence stays 16-bit RGBA throughout.
        write_png(clean_frame(frame).convert('RGB'),target)
        cp=cap/f'{frame:04d}.png'
        cache_key=shot if shot!='S14' else ('black' if frame>=1186 or frame<=1149 else str(frame))
        if cache_key in caption_cache:
            if cp.exists():cp.unlink()
            os.link(caption_cache[cache_key],cp)
        else:
            write_png(caption_frame(frame),cp);caption_cache[cache_key]=cp
        rows.append(dict(frame=frame,shot=shot,clean_sha256=sha(target),caption_sha256=sha(cp),
                         raw_hardlink=False,
                         paired_source_frames=[91+frame-901,631+frame-901] if shot=='S11' else None))
        if frame%50==0:print('COMPOSED',frame,'/1200',flush=True)
    manifest=dict(status='COMPLETE',size=SIZE,fps=30,frame_count=1200,
        raw_frames_preserved=True,clean_format='Uniform 8-bit RGB lossless PNG for 8-bit H.264 export; independent raw plates remain 16-bit RGBA.',
        clean_note='No narrative captions. Device UI and essential in-story graphics remain.',
        subtitle_note='Independent RGBA plates overlaid by FFmpeg; Black 74 px, outline 14 px, final baseline 1560.',
        split_screen=dict(top_frames=[91,180],bottom_frames=[631,720],
                          crop=[0,280,1080,1430],plate_size=[408,435],
                          red_cycle_frames=36,cyan_cycle_frames=15),
        S13_static_base_frame=1081,closing_black_frames=[1186,1200],original_bird_png_sha256=sha(OUT/'ui/frames/S14_bird_original/0001.png'),
        frames=rows)
    (OUT/'composite_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    frames=list(range(50,1201,50));thumbs=[]
    for f in frames:
        im=Image.open(dest/f'{f:04d}.png').convert('RGBA')
        path=OUT/f'gates/H/selected/{f:04d}.png'
        write_png(Image.alpha_composite(im,caption_frame(f)),path);thumbs.append(path)
    grid(thumbs,[f'{shot_for(f)[0]} / f{f}' for f in frames],OUT/'gates/H/final_contact_sheet.png')
    representatives=[20,135,225,340,424,530,552,675,770,840,945,1030,1115,1165]
    pairs=[];labels=[]
    for f in representatives:
        shot=shot_for(f)[0]
        im=Image.open(dest/f'{f:04d}.png').convert('RGBA')
        path=OUT/f'gates/H/representatives/{shot}_{f:04d}.png'
        write_png(Image.alpha_composite(im,caption_frame(f)),path)
        pairs.extend([ROOT/f'frames/{shot}.png',path]);labels.extend([f'{shot} storyboard',f'{shot} final f{f}'])
    grid(pairs,labels,OUT/'gates/H/final_storyboard_comparison.png')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['preview','full'],default='preview')
    args=parser.parse_args()
    preview() if args.mode=='preview' else full()
