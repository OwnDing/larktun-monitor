# Executed in build_home.py's modelling namespace.
C=FLOORS
for r in L['rooms']:
    x,y,w,d=r['x0'],r['y0'],r['w'],r['d']
    slab=box(r['id']+' structural slab',x-.03,y-.03,-.23,w+.06,d+.06,.20,'cut',.008)
    slab['source_room']=r['id']; slab['plan_dimensions_m']=f'{w} x {d}'
    box(r['id']+' subfloor',x,y,-.035,w,d,.04,'grout',0)
    wood=r['tint'] in ('live','rest','work') or r['id'] in ('R04','R10','R11')
    if wood:
        row=.18
        for j in range(math.ceil(d/row)):
            yy=y+j*row; dd=min(row,d-j*row)
            start=x-(j%3)*.43
            while start<x+w:
                end=min(start+1.28,x+w); xx=max(start,x)
                if end-xx>.008:
                    m=RNG.choice(['oak_light','oak_light','oak','oak_light'])
                    o=box(r['id']+' individual oak plank',xx+.0012,yy+.0012,.006,end-xx-.0024,dd-.0024,.012,m,.001)
                start+=1.28
    else:
        step=.60
        for i in range(math.ceil(w/step)):
            for j in range(math.ceil(d/step)):
                box(r['id']+' porcelain tile',x+i*step+.002,y+j*step+.002,.006,min(step,w-i*step)-.004,min(step,d-j*step)-.004,.013,'tile_warm' if r['id'] in ('R01','R13') else 'tile',.001)
    if r['id'] not in ('R01','R13'):
        box(r['id']+' ceiling',x,y,2.8,w,d,.12,'plaster',.002,CEILING)

doors=[dict(v) for v in L['doors']]
walls=[dict(v) for v in L['walls']]
if not ARGS.strict_plan:
    for d in doors:
        if d['name']=='主卧门': d['y']=4.97; d['width']=.82
        if d['name']=='儿童房门': d['y']=6.94; d['width']=.88
        if d['name']=='储藏门': d['y']=3.98; d['width']=.70; d['type']='slide'
        if d['name']=='主卫门': d['x']=.07; d['width']=.72
    doors=[d for d in doors if d['name'] not in ('书房门','公卫门')]
    doors += [dict(name='书房门 · corrected access',x=9.6,y=2.27,width=.81,axis='v',type='swing'),
              dict(name='玄关至书房过道',x=8.4,y=2.27,width=.81,axis='v',type='arch'),
              dict(name='公卫移门',x=8.65,y=2.12,width=.78,axis='h',type='slide'),
              dict(name='走廊至入口过道',x=8.7,y=3.2,width=.8,axis='h',type='arch')]
    walls.append(dict(type='I',x0=8.52,y0=2.12,x1=9.6,y1=2.24))

openings=[]
for d in doors: openings.append(dict(d,z0=0,z1=2.3 if d['type'] in ('slide','arch') else 2.1))
for w in L['windows']: openings.append(dict(w,z0=.45 if w['type']=='bay' else .9,z1=2.4,type='window'))

def wall_piece(name,x,y,z,w,d,h):
    box(name+' / continuous full height',x,y,z,w,d,h,'plaster',.002,FULLWALL)
    end=z+h
    if z<1.15: box(name+' / lower',x,y,z,w,d,min(end,1.15)-z,'plaster',.002,LOW)
    if end>1.15: box(name+' / upper',x,y,max(z,1.15),w,d,end-max(z,1.15),'plaster',.002,UP)

def split_frame(name,x,y,z,w,d,h,mat='oak_light'):
    box(name+' / continuous full height',x,y,z,w,d,h,mat,.002,FULLFRAME)
    end=z+h
    if z<1.15: box(name+' / lower',x,y,z,w,d,min(end,1.15)-z,mat,.002,GLAZE)
    if end>1.15: box(name+' / upper',x,y,max(z,1.15),w,d,end-max(z,1.15),mat,.002,CUTFRAMEUP)

for wi,w in enumerate(walls):
    x0,y0,x1,y1=[w[k] for k in ('x0','y0','x1','y1')]
    horiz=(x1-x0)>(y1-y0); h=1.1 if w['type']=='P' else 2.8
    lo,hi=(x0,x1) if horiz else (y0,y1)
    cuts=[]
    for o in openings:
        if horiz and o['axis']=='h' and y0-.04<=o['y']<=y1+.04 and x0-.03<=o['x'] and o['x']+o['width']<=x1+.03: cuts.append(o)
        if not horiz and o['axis']=='v' and x0-.07<=o['x']<=x1+.07 and y0-.03<=o['y'] and o['y']+o['width']<=y1+.03: cuts.append(o)
    cuts.sort(key=lambda a:a['x'] if horiz else a['y']); cur=lo
    def seg(a,b,z,height,skirting=False):
        if b-a<.002 or height<=0: return
        wall_piece(f'W{wi:02d}',*((a,y0,z,b-a,y1-y0,height) if horiz else (x0,a,z,x1-x0,b-a,height)))
        if skirting and w['type']!='P':
            if horiz:
                for yy in (y0-.014,y1): box('Oak skirting 80 mm',a,yy,.018,b-a,.014,.08,'oak_light',.002,FLOORS)
            else:
                for xx in (x0-.014,x1): box('Oak skirting 80 mm',xx,a,.018,.014,b-a,.08,'oak_light',.002,FLOORS)
    for o in cuts:
        a=o['x'] if horiz else o['y']; b=a+o['width']
        seg(cur,a,0,h,True)
        if o['z0']>0: seg(a,b,0,min(h,o['z0']),True)
        if h>o['z1']: seg(a,b,o['z1'],h-o['z1'])
        cur=max(cur,b)
    seg(cur,hi,0,h,True)
    if w['type']=='P':
        box('Balcony coping',x0-.02,y0-.02,1.1,x1-x0+.04,y1-y0+.04,.045,'stone',.007,LOW)
        box('Balcony coping / full',x0-.02,y0-.02,1.1,x1-x0+.04,y1-y0+.04,.045,'stone',.007,FULLWALL)
for b in L['beams']:
    box('Structural beam / 2.55 m clear',b['x0'],b['y0'],2.55,b['x1']-b['x0'],b['y1']-b['y0'],.25,'plaster',.002,FULLWALL)

# True framed glazing. Above-cut parts are separate, not deleted.
for o in openings:
    x,y,w,z0,z1=o['x'],o['y'],o['width'],o['z0'],o['z1']
    horizontal=o['axis']=='h'; name=o['name']; typ=o['type']
    if '主卧飘窗' in name: y=9.26
    thick=.10
    def part(n,s,z,length,height,depth=.06,offset=0,mat='dark'):
        return split_frame(name+' '+n,*((x+s,y-thick/2+offset,z,length,depth,height) if horizontal else (x-thick/2+offset,y+s,z,depth,length,height)),mat)
    if typ in ('slide','window'):
        count=max(2,round(w/.85))
        for k in range(count+1): part('frame vertical',k*w/count-.021,z0,.042,z1-z0)
        for zz in (z0,z1-.042): part('frame horizontal',0,zz,w,.042)
        for k in range(count):
            pane_mat='oak_light' if '储藏门' in name else ('frosted' if '公卫' in name else 'glass')
            part('glass',k*w/count+.025,z0+.046,w/count-.05,z1-z0-.091,.006,.026,pane_mat)
            part('handle',k*w/count+.04,1.03,.016,.12,.026,.068,'brass')
        part('stone sill',-.035,z0-.027,w+.07,.027,.24,-.05,'stone')
        if typ=='slide':
            for offset in (-.01,.02,.05): part('recessed floor track',0,.015,w,.005,.006,offset,'steel')
    elif typ in ('swing','entry'):
        for k in (0,w-.04): part('door jamb',k,0,.04,z1,.13,-.025,'oak_light')
        part('door header',0,z1-.04,w,.04,.13,-.025,'oak_light')
        for off in (-.045,.095):
            for k in (-.025,w-.025): part('architrave',k,0,.05,z1+.035,.016,off,'oak_light')
            part('architrave head',-.025,z1,w+.05,.05,.016,off,'oak_light')
        before=set(GLAZE.objects)|set(CUTFRAMEUP.objects)|set(FULLFRAME.objects)
        part('door leaf',.042,.025,w-.084,z1-.075,.042,.015,'walnut' if typ=='entry' else 'oak_light')
        for zz in (.24,1.7): part('hinge',.031,zz,.012,.09,.014,.065,'brass')
        part('lock escutcheon',w-.17,.92,.035,.16,.013,.061,'brass')
        part('lever',w-.23,1.01,.10,.015,.023,.073,'brass')
        for yyoff in (.073,-.016): part('keyhole',w-.16,.946,.008,.017,.006,yyoff,'dark')
        group=(set(GLAZE.objects)|set(CUTFRAMEUP.objects)|set(FULLFRAME.objects))-before
        angle=0 if typ=='entry' else (-65 if horizontal else 65)
        # Keep narrow door swing clear of wardrobe fronts; leaf remains editable.
        if '儿童房' in name: angle=-70
        if '书房' in name: angle=-70
        if '主卫' in name: angle=-70
        if '主卧' in name: angle=0
        rotate_group(group,(x,y,0),angle)
        part('threshold',0,.006,w,.012,.16,-.035,'stone')
    else:
        for k in (-.015,w-.015): part('open passage trim',k,0,.03,z1,.14,-.03,'oak_light')
        part('open passage head',-.015,z1,w+.03,.03,.14,-.03,'oak_light')

print('Architecture complete',len(bpy.data.objects),flush=True)

# Plan SVG explicitly projects the bay 450 mm beyond the south outer wall.
box('Master bay cantilever body',.60,8.78,.18,2.30,.53,.25,'plaster',.006,FLOORS)
box('Master bay stone sill',.62,8.60,.43,2.26,.71,.025,'stone',.006,FLOORS)
for xx in (.65,2.85):
    for yy in (8.73,9.25): split_frame('Bay corner mullion',xx-.018,yy-.02,.45,.036,.04,1.95,'dark')
    for zz in (.45,2.365): split_frame('Bay return transom',xx-.018,8.73,zz,.036,.54,.035,'dark')
    split_frame('Bay side glazing',xx-.003,8.754,.49,.006,.47,1.86,'glass')
box('Master bay insulated head',.60,8.73,2.4,2.30,.59,.10,'plaster',.005,FULLWALL)
C=ROOM['R09']
pillow('Bay window woven seat',1.75,8.91,.49,2.04,.47,.09,'linen')
book(.85,8.92,.542,.22,.19,.022,'sage','Bay window reading',-5)
