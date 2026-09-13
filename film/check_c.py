"""Measure display-referred Rec.709 luma on the complete 1080x1920 frame."""
import json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out/gates/C';report={'gate':'C','status':'review','method':'Full-frame display-referred Rec.709 luma = .2126 R + .7152 G + .0722 B, PNG converted to 8-bit RGB for histogram bins; no masking or crop.','looks':{}}
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',20)
for name in ('DARK','DUSK','NIGHT'):
    im=Image.open(OUT/f'LOOK_{name}.png').convert('RGB');assert im.size==(1080,1920)
    hist=[0]*256;low=0;values=[]
    for r,g,b in im.getdata():
        l=(.2126*r+.7152*g+.0722*b)/255
        hist[min(255,int(l*255))]+=1
        if l<=.25:low+=1
    total=sum(hist);cumulative=0;median=0
    for i,n in enumerate(hist):
        cumulative+=n
        if cumulative>=total/2:median=i/255;break
    entry=dict(dark_fraction_0_to_025=low/total,median_luma=median,histogram_256=hist)
    if name=='DARK':entry['pass']=low/total>=.70
    if name=='DUSK':entry['pass']=.30<=median<=.45
    report['looks'][name]=entry
    plot=Image.new('RGB',(1080,480),'#11151e');d=ImageDraw.Draw(plot)
    d.rectangle((56,75,56+int(940*.25),402),fill='#1b2936')
    maxlog=math.log1p(max(hist))
    for i,n in enumerate(hist):
        x=56+i*940/255;h=math.log1p(n)/maxlog*310
        d.line((x,400-h,x,400),fill='#b7c1ce',width=3)
    d.text((56,15),f'{name} | <= .25: {low/total:.2%} | median: {median:.3f}',font=font,fill='white')
    for v in (0,.25,.5,.75,1):d.text((45+940*v,425),str(v),font=font,fill='#b7c1ce')
    d.text((740,54),'log count / full frame',font=font,fill='#b7c1ce')
    plot.save(OUT/f'LOOK_{name}_histogram.png')
report['numeric_gate_pass']=all(report['looks'][n]['pass'] for n in ('DARK','DUSK'))
(OUT/'histogram_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({n:{k:v for k,v in x.items() if k!='histogram_256'} for n,x in report['looks'].items()},indent=2))
