"""Deterministic labelled contact sheets; no image synthesis."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
FONT=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',19)
def grid(paths,labels,output,cols=4,w=270,h=480):
    result=Image.new('RGB',(cols*w,((len(paths)+cols-1)//cols)*(h+36)),'#11151e');d=ImageDraw.Draw(result)
    for i,(p,t) in enumerate(zip(paths,labels)):
        im=Image.open(p).convert('RGB');im.thumbnail((w,h));x=(i%cols)*w;y=(i//cols)*(h+36)
        result.paste(im,(x+(w-im.width)//2,y+36+(h-im.height)//2));d.text((x+8,y+7),t,font=FONT,fill='white')
    Path(output).parent.mkdir(parents=True,exist_ok=True);result.save(output)
if __name__=='__main__':
    report=json.loads((ROOT/'out/gates/B/framing_report.json').read_text())
    for vid in ('V2','V3','V4','V5','V6'):
        entries=sorted([e for e in report['candidates'] if e['camera_id']==vid],key=lambda e:(e['ortho_scale'],e['z_angle_deg']))
        grid([ROOT/'out/gates/B/candidates'/e['file'] for e in entries],[f"{vid} Z{e['z_angle_deg']} S{e['ortho_scale']}" for e in entries],ROOT/f'out/gates/B/{vid}_contact_sheet.png')
    entries=list(report['selected'].values())
    grid([ROOT/'out/gates/B/V1a_start.png']+[ROOT/'out/gates/B/candidates'/e['file'] for e in entries],['V1a / S1.6']+[f"{e['camera_id']} Z{e['z_angle_deg']} S{e['ortho_scale']}" for e in entries],ROOT/'out/gates/B/selected_contact_sheet.png',3,w=360,h=640)
