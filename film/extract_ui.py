"""Extract the supplied SVG inner screens and original placeholder bird by AST."""
import sys,ast,inspect,json,base64,io
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import scenes_a,scenes_b
OUT=ROOT/'out/ui';OUT.mkdir(exist_ok=True,parents=True)
def extract(fn,var):
    tree=ast.parse(inspect.getsource(fn));tree.body[0].name='_extract';tree.body[0].body[-1]=ast.Return(value=ast.Name(id=var,ctx=ast.Load()));ast.fix_missing_locations(tree)
    ns=fn.__globals__.copy();exec(compile(tree,'source_svg_extract','exec'),ns);return ns['_extract']()
def wrap(inner):return '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="2200" viewBox="0 0 312 652" preserveAspectRatio="none">'+inner+'</svg>'
original={s:extract(fn,'inner') for s,fn in [('S05',scenes_a.s05),('S10',scenes_b.s10)]}
for s,text in original.items():(OUT/(s+'_original.svg')).write_text(wrap(text))
# Work with SVG elements so the original UI typography and copy remain intact.
root=ET.fromstring(wrap(original['S05']));children=list(root)
groups=[e for e in children if e.tag.endswith('g')];groups[0].set('id','timeline');groups[1].set('id','lock')
idx=children.index(groups[1]);pay=ET.Element('g',id='paywall')
for e in children[idx+1:]:root.remove(e);pay.append(e)
root.append(pay);ET.SubElement(root,'circle',id='ripple',cx='156',cy='546',r='0',fill='none',stroke='#FF4B4B',**{'stroke-width':'3','opacity':'0'})
for e in root.iter():
    if e.get('text-anchor')=='center':e.set('text-anchor','middle')
(OUT/'S05.svg').write_text(ET.tostring(root,encoding='unicode'))
root=ET.fromstring(wrap(original['S10']));card=next(e for e in root if e.tag.endswith('g') and e.get('transform')=='translate(18,366)');card.set('id','livecard')
thumb=next(e for e in card if e.tag.endswith('g'))
for e in list(thumb):thumb.remove(e)
im=Image.open(ROOT/'out/gates/D/S08_0675.png').convert('RGB').crop((50,500,1030,1390));im.thumbnail((512,288));bg=Image.new('RGB',(512,288),'#101827');bg.paste(im,((512-im.width)//2,0));buffer=io.BytesIO();bg.save(buffer,format='PNG')
ET.SubElement(thumb,'image',x='0',y='0',width='256',height='144',href='data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode())
ET.SubElement(thumb,'circle',cx='14',cy='14',r='3',fill='#2FE0C8')
t=ET.SubElement(thumb,'text',x='24',y='19',fill='#2FE0C8',**{'font-size':'12','font-weight':'900'});t.text='LIVE · 客厅'
for e in card:
    if e.tag.endswith('text') and '18ms' in (e.text or ''):e.set('id','latency')
for e in root.iter():
    if e.get('text-anchor')=='center':e.set('text-anchor','middle')
(OUT/'S10.svg').write_text(ET.tostring(root,encoding='unicode'))
(OUT/'PAYMENT.svg').write_text(wrap('''<rect width="312" height="652" rx="30" fill="#0B1120"/><text x="26" y="70" fill="#E6ECF7" font-size="28" font-weight="900">扣费通知</text><rect x="20" y="260" width="272" height="154" rx="18" fill="#161F33" stroke="#FF4B4B"/><text x="40" y="302" fill="#E6ECF7" font-size="24">云录像月费</text><text x="40" y="359" fill="#FF4B4B" font-size="38" font-weight="900">¥ XX</text><text x="40" y="392" fill="#93A1BC" font-size="18">订阅已续期 · 金额占位</text>'''))
bird=extract(scenes_b.s14,'bird')
(OUT/'S14_bird_original.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920"><defs><filter id="glowS"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'+bird+'</svg>')
(OUT/'extraction_report.json').write_text(json.dumps(dict(source_S05='src/scenes_a.py:s05:inner',source_S10='src/scenes_b.py:s10:inner',source_bird='src/scenes_b.py:s14:bird',notes=['Source inner SVGs preserved verbatim in *_original.svg.','Animated DOM copies retain original UI copy, price placeholder and layout.','S10 replaces the generic room thumbnail with the actual S08 frame; LIVE indicator is cyan to keep semantic colour consistent.','The original bird paths and colour values are unchanged.']),ensure_ascii=False,indent=2)+'\n')
print('UI and bird extracted')
