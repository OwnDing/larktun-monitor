"""Stage A: modify the film copy only; produce the mandatory V1 evidence."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from characters import build_family

sc=bpy.data.scenes['01 · House cutaway'];bpy.context.window.scene=sc
layer=full_layer();sc.name='Larktun Film'
props=collection('FILM · Scene refinements'); ns=helpers(props)
box,curve,sphere=ns['box'],ns['curve'],ns['sphere']
cabinet=collection('FILM · R07 open media cabinet')
network=collection('FILM · Physical network cables')
M=ns['M']; before_d2={o.name:[list(row) for row in o.matrix_world] for o in sc.objects if o.name.startswith('D2 ')}

# Replace the solid generated cabinet carcass with a real open shelf assembly.
for ob in list(sc.objects):
    if ob.name.startswith('R07 · 电视柜'):
        ob['film_retired']=True; ob.hide_render=True
for n,x,y,z,w,d,h in [
    ('top',7.92,5.05,.425,.42,1.9,.025),('bottom shelf',7.92,5.05,.105,.42,1.9,.025),
    ('back',8.317,5.05,.13,.023,1.9,.295),('north cheek',7.92,5.05,.13,.42,.022,.295),
    ('south cheek',7.92,6.928,.13,.42,.022,.295),('divider',7.92,5.80,.13,.42,.022,.295),
    ('right divider',7.92,6.39,.13,.42,.022,.295)]:
    ob=box('FILM TV cabinet / '+n,x,y,z,w,d,h,'oak_light',.003,cabinet);ob['film_room']='R07'
for y in (5.12,6.8):
    for x in (7.96,8.25):
        ob=box('FILM TV cabinet / foot',x,y,.025,.035,.04,.08,'walnut',.004,cabinet);ob['film_room']='R07'

destinations={'D1':(8.065,5.43,.157),'D3':(8.065,6.075,.155)}
device_changes=[]
for tag,target in destinations.items():
    body=next(o for o in sc.objects if o.get('device_id')==tag)
    old=center(body); rot=Matrix.Rotation(math.pi/2,4,'Z')
    transform=Matrix.Translation(loc(target))@rot@Matrix.Translation(-old)
    for ob in list(sc.objects):
        if ob.name.startswith(tag+' '):
            if 'ethernet lead' in ob.name:
                ob['film_retired']=True;ob.hide_render=True;continue
            ob.matrix_world=transform@ob.matrix_world
            ob['film_room']='R07'
            for c in list(ob.users_collection): c.objects.unlink(ob)
            cabinet.objects.link(ob)
    device_changes.append({'id':tag,'old_center':draw(old),'new_center':list(target),
                           'front_drawing_axis':'+y (south)','preserved_larktun_role':body.get('larktun_role')})

# A top-edge repeater makes the physical front LEDs readable from the fixed NW
# isometric angle, while the original front panel continues to face south.
led=material('FILM device status neutral','DDE2DE',.5,2)
for i in range(3):
    ob=sphere('D1 top status repeater '+str(i),7.925,5.48+i*.032,.186,.006,.007,.004,led,cabinet)
    ob['larktun_role']='device_led';ob['device_id']='D1';ob['film_room']='R07'

cablemat=material('FILM matte graphite cable','252932',.92)
paths={
 'C1_D1':[(8.315,3.54,2.33),(8.375,3.62,2.36),(8.375,4.39,2.36),(8.372,4.62,2.28),
           (8.370,4.66,1.12),(8.365,4.68,.24),(8.31,4.82,.145),(8.12,5.09,.145),(8.10,5.27,.17)],
 'C2_D1':[(8.315,.54,2.29),(8.375,.69,2.39),(8.375,1.8,2.39),(8.375,3.14,2.39),
           (8.375,3.49,2.40),(8.375,4.39,2.40),(8.370,4.71,2.28),(8.368,4.74,1.1),
           (8.365,4.76,.28),(8.30,4.87,.17),(8.08,5.17,.18),(8.03,5.28,.17)],
 'C3_D1':[(10.62,4.957,2.18),(10.32,4.98,2.21),(9.76,4.98,2.21),(9.48,4.96,2.21),
           (8.51,4.93,2.21),(8.372,4.91,2.15),(8.369,4.89,1.45),(8.365,4.87,.42),
           (8.29,4.95,.21),(7.99,5.14,.20),(7.97,5.27,.17)],
 'D1_D3':[(8.10,5.58,.17),(7.985,5.63,.17),(7.976,5.79,.145),(7.99,5.93,.17),(8.02,6.01,.17)],
 'D3_D4':[(8.13,6.17,.17),(8.27,6.23,.17),(8.29,6.08,.19),(8.29,4.45,.20),
          (8.30,3.60,.24),(8.30,3.35,.80),(8.30,3.11,2.25),(8.30,1.0,2.25),(8.32,.71,1.70),(8.35,.61,1.55)]}
for name,points in paths.items():
    ob=bezier('CABLE · '+name,points,.003,cablemat,network)
    bps=ob.data.splines[0].bezier_points
    for i,bp in enumerate(bps):
        previous=bps[max(0,i-1)].co;following=bps[min(len(bps)-1,i+1)].co
        direction=(following-previous).normalized()
        lengths=[(bp.co-v).length for v in (previous,following) if (bp.co-v).length>0]
        handle=min(lengths)*.16
        bp.handle_left_type=bp.handle_right_type='FREE'
        bp.handle_left=bp.co-direction*handle;bp.handle_right=bp.co+direction*handle
    ob['film_role']='physical_cable';ob['larktun_role']='physical_network_cable'
    ob['endpoints']=name;ob['path_drawing_json']=json.dumps(points)
    # Small clips make scale and wall contact credible without thickening cable.
    for p in points[1:-1:2]:
        clip=ns['ring']('Cable clip · '+name,p,.005,.0012,'white',axis='y',collection=network)
        clip['film_room']='R07'
dump(OUT/'gates/A/cable_routes.json',{'bevel_depth_m':.003,'material':'#252932 matte','routes':paths})

# Replace repeated artwork only on the child wall; add a separate master print.
for ob in list(sc.objects):
    if ob.name.startswith(('Gallery frame','Print ','Abstract landscape')):
        c=center(ob)
        if c.x>9.6 and -c.y>4.7:
            ob['film_retired']=True;ob.hide_render=True
paper=material('FILM child drawing paper','E6DED0',.96)
pencil=material('FILM crayon blue grey','4E6078',.95)
for i,(x,z) in enumerate(((11.58,1.68),(11.94,1.86),(12.29,1.61))):
    ob=box('Child drawing sheet '+str(i),x,4.94,z,.27,.008,.32,paper,.003,props);ob['film_room']='R12'
    if i==0:
        pts=[(x+.03,4.951,z+.08),(x+.03,4.951,z+.20),(x+.14,4.951,z+.28),(x+.25,4.951,z+.20),
             (x+.25,4.951,z+.08),(x+.03,4.951,z+.08)]
    elif i==1:
        pts=[(x+.14+.085*math.cos(a),4.951,z+.17+.085*math.sin(a)) for a in np.linspace(0,2*math.pi,40)]
    else:
        pts=[(x+.13+.08*math.cos(a)*math.cos(3*a),4.951,z+.18+.08*math.sin(a)*math.cos(3*a)) for a in np.linspace(0,2*math.pi,60)]
    ob=bezier('Child hand drawn crayon '+str(i),pts,.002,pencil,props);ob['film_room']='R12'
    for tx in (x+.015,x+.225):
        ob=box('Child paper tape',tx,4.952,z+.295,.042,.002,.027,'linen',.001,props);ob['film_room']='R12'
ob=box('Master botanical print mat',.02,6.02,1.42,.02,.76,.65,'paper',.005,props);ob['film_room']='R09'
for i in range(7):
    ob=bezier('Master ink botanical branch '+str(i),[(.045,6.4,1.47),(.045,6.32+i*.018,1.65),
                (.045,6.07+i*.10,1.95-.025*abs(i-3))],.002,pencil,props);ob['film_room']='R09'

# A backpack with a separate pocket, fabric straps and a zip, plus a plush rabbit.
bagmat=material('FILM canvas schoolbag','6D7686',.95)
for name,x,y,z,w,d,h,mat in [('backpack',10.9,7.51,.025,.25,.14,.34,bagmat),
                           ('backpack pocket',10.93,7.65,.07,.19,.04,.17,bagmat)]:
    ob=box('Child '+name,x,y,z,w,d,h,mat,.035,props);ob['film_room']='R12'
for dx in (.03,.20):
    ob=bezier('Child backpack strap',[(10.9+dx,7.53,.34),(10.9+dx,7.42,.22),(10.9+dx,7.51,.09)],.012,bagmat,props);ob['film_room']='R12'
for name,p,size in [('body',(12.35,5.93,.69),(.09,.10,.14)),('head',(12.35,5.9,.87),(.085,.078,.08)),
                    ('left ear',(12.31,5.92,.98),(.024,.031,.105)),('right ear',(12.39,5.92,.98),(.024,.031,.105)),
                    ('left paw',(12.27,5.84,.60),(.047,.067,.045)),('right paw',(12.42,5.84,.60),(.047,.067,.045))]:
    ob=sphere('Child plush rabbit '+name,*p,*size,'linen',props);ob['film_room']='R12'
for i in range(5):
    prev=set(props.objects);ns['book'](12.43,7.62,.18+i*.027,.22,.18,.022,['sage','linen','rust'][i%3],name='Child picture book '+str(i),angle=(i-2)*2)
    for ob in set(props.objects)-prev: ob['film_room']='R12'

screen=bpy.data.objects['Phone screen']; screenmat=screen.data.materials[0].copy();screenmat.name='FILM PHONE screen / independent UI slot'
screen.data.materials.clear();screen.data.materials.append(screenmat);screen['larktun_role']='phone_ui_surface'

# Jitter complete assemblies so their seams / hardware continue to match.
rng=random.Random(9131305);jitter=[]
groups={}
for ob in sc.objects:
    n=ob.name
    import re
    m=re.match(r'(R03 · 餐椅 \d)',n)
    if m: groups.setdefault(m.group(1),[]).append(ob)
for prefix in ('R07 · 三人沙发 informal rust pillow','R07 · 三人沙发 linen pillow',
               'R07 · 地毯','Living mug','Living art book','Dining tea cup'):
    obs=[ob for ob in sc.objects if ob.name.startswith(prefix)]
    if obs:groups[prefix]=obs
for name,obs in groups.items():
    pivot=sum((center(o) for o in obs),Vector())/len(obs)
    angle=rng.uniform(-3,3);offset=Vector((rng.uniform(-.015,.015),rng.uniform(-.015,.015),0))
    transform=Matrix.Translation(pivot+offset)@Matrix.Rotation(math.radians(angle),4,'Z')@Matrix.Translation(-pivot)
    for ob in obs:ob.matrix_world=transform@ob.matrix_world
    jitter.append({'assembly':name,'rotation_z_deg':angle,'translation_m':list(offset),'objects':len(obs)})
dump(OUT/'gates/A/jitter.json',{'seed':9131305,'assemblies':jitter})

characters=build_family()
ob=box('Child dining chair footrest',4.77,1.78,.18,.32,.28,.027,'oak_light',.006,props);ob['film_room']='R03'
cam=iso_camera('V1 · Film locked living room',(6,4.6,1.3),225,18)
hidden=apply_v1_cut(225);sc.camera=cam
sc.render.fps=30;sc.frame_start=1;sc.frame_end=1200
sc.render.resolution_x=1080;sc.render.resolution_y=1920;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1
layer.update()
after_d2={o.name:[list(row) for row in o.matrix_world] for o in sc.objects if o.name.startswith('D2 ')}
assert before_d2==after_d2
layout=json.loads((ROOT/'scene/layout.json').read_text())
v1=next(v for v in layout['film_cameras'] if v['id']=='V1')
v1.update(look_at=[6,4.6,1.3],azimuth='西北上空',rot_z_deg=225,rot_x_deg=54.7356,scale=18,
          ortho_scale=18,shots=['S02','S08','S11','S13','S14'])
for dev in layout['devices']:
    if dev['id'] in destinations:
        ob=next(o for o in sc.objects if o.get('device_id')==dev['id'] and o.get('larktun_role')=='network_device')
        pts=bounds(ob); mn=[min(p[i] for p in pts) for i in range(3)];mx=[max(p[i] for p in pts) for i in range(3)]
        dev.update(room='R07',x=mn[0],y=-mx[1],z=mn[2],w=mx[0]-mn[0],d=mx[1]-mn[1],h=mx[2]-mn[2],front_axis='+y')
layout['physical_cables']=[dict(id=n,path=p,radius_m=.003) for n,p in paths.items()]
layout['blocking']['S02_S08']=[dict(person=p['id'],x=p['position'][0],y=p['position'][1],yaw_blender_deg=p['yaw_blender_deg']) for p in characters]
dump(ROOT/'scene/layout.json',layout)
targets={
 'C1':bpy.data.objects['C1 camera housing'], 'TV':bpy.data.objects['R07 · 电视 65" reflective screen'],
 'D1':next(o for o in sc.objects if o.get('device_id')=='D1' and o.get('larktun_role')=='network_device'),
 'D3':next(o for o in sc.objects if o.get('device_id')=='D3' and o.get('larktun_role')=='network_device'),
 'dining_table':bpy.data.objects['R03 · 餐桌 solid top'], 'sofa':bpy.data.objects['R07 · 三人沙发 lower upholstery'],
 'TV_cabinet':bpy.data.objects['FILM TV cabinet / top'],
}
report={'gate':'A','status':'awaiting_visual_review','z_angle_deg':225,'ortho_scale':18,'look_at':[6,4.6,1.3],
        'resolution':[1080,1920],'camera_location':list(cam.location),
        'camera_rotation_euler_deg':[math.degrees(v) for v in cam.rotation_euler],
        'world_coverage_m':{'horizontal':10.125,'vertical':18},'hidden_collections':hidden,
        'objects':{k:projection(cam,o) for k,o in targets.items()},
        'cables':{k:projection(cam,bpy.data.objects['CABLE · '+k]) for k in paths},
        'device_changes':device_changes,'D2_unchanged':True,'character_route':'MakeHuman',
        'home_sha256':sha(HOME),'notes':['Original D1 front LEDs face south; added physical top-edge repeaters for the fixed NW viewing angle.']}
report['objects_in_frame']={k:v['in_frame'] for k,v in report['objects'].items()}
sc.render.engine='CYCLES'
save('A')
report['render_seconds']=render(OUT/'gates/A/V1_Z225_S18.png',cam,32)
dump(OUT/'gates/A/framing_report.json',report)
print('STAGE A BUILT; Gate A requires visual cable/character review.',flush=True)
