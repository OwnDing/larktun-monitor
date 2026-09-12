NET_HIGH=col('04a · Wall mounted security hardware',NET)
C=NET_HIGH
for c in L['cameras']:
    x,y,z=c['x'],c['y'],c['z']; tag=c['id']
    # A compact dome camera with actual optical lens, mount and indicator.
    if tag=='C3':
        box(tag+' wall plate',x-.055,y+.047,z-.06,.11,.024,.12,'white',.025)
        rod(tag+' bracket',(x,y+.055,z),(x,y+.18,z-.07),.025,'white')
        yy=y+.19; xx=x
    else:
        box(tag+' wall plate',x+.038,y-.055,z-.06,.024,.11,.12,'white',.025)
        rod(tag+' bracket',(x+.04,y,z),(x-.08,y,z-.055),.026,'white')
        xx=x-.09; yy=y
    body=sphere(tag+' camera housing',xx,yy,z-.075,.075,.073,.085,'white')
    body['larktun_role']='security_camera'; body['source_coordinate']=json.dumps([x,y,z]); body['camera_id']=tag
    target=Vector((6.0,6.2,1.0)) if tag=='C1' else (Vector((7.45,1.75,1.0)) if tag=='C2' else Vector((11.7,6.25,.6)))
    a=Vector((xx,yy,z-.07)); unit=(target-a).normalized()
    lenspos=a+unit*.061; outer=a+unit*.086
    rod(tag+' black optical surround',tuple(lenspos),tuple(outer),.045,'dark')
    lens=rod(tag+' optical glass',tuple(outer),tuple(outer+unit*.006),.027,'screen')
    led=sphere(tag+' LED',xx-.038,yy+.035,z-.101,.006,.006,.006,'led'); led['larktun_role']='camera_led'
    for k in range(4): sphere(tag+' IR sensor',xx+(.035 if k%2 else -.035),yy+.058,z-.065+(.025 if k<2 else -.025),.006,.003,.006,'dark')

C=NET
for d in L['devices']:
    if d['id'] in ('D4','D5'): continue
    x,y,z=d['x'],d['y'],1.127; w,dep,h=d['w'],d['d'],d['h']; tag=d['id']
    o=box(tag+' '+d['name'],x,y,z,w,dep,h,'dark',.008); o['larktun_role']='network_device'; o['device_id']=tag
    if tag=='D2':
        for i in range(4):
            yy=y+.012+i*(dep-.024)/4
            box('D2 removable drive bay',x-.007,yy,z+.014,.015,(dep-.032)/4,h-.028,'steel',.002)
            box('D2 drive pull recess',x-.013,yy+.008,z+.065,.004,.024,.055,'dark',.001)
            led=box('D2 bay LED',x-.012,yy+.008,z+.025,.003,.015,.004,'led',.001); led['larktun_role']='device_led'
    elif tag=='D3':
        for j in range(3): rod('D3 hinged antenna',(x+w-.02,y+.03+j*.065,z+h),(x+w-.01,y+.02+j*.07,z+h+.19),.009,'dark')
    else:
        for j in range(3):
            led=sphere('D1 status LED',x-.004,y+.06+j*.025,z+.025,.002,.004,.003,'led'); led['larktun_role']='device_led'
        box('D1 USB socket',x-.006,y+.20,z+.014,.004,.020,.009,'rubber',.001)
    for j in range(10): box(tag+' ventilation slot',x+.02,y+.018+j*dep*.085,z+h+.001,w-.04,.003,.001,'rubber',0)
    curve(tag+' ethernet lead',[(x+w-.02,y+dep*.7,z+.025),(13.19,y+dep*.7,z+.025),(13.19,y+dep*.7,.98)],.0028,'dark')
C=NET_HIGH
dev=box('D4 recessed network cabinet',8.364,.445,1.40,.030,.35,.30,'white',.006); dev['larktun_role']='network_device'; dev['device_id']='D4'
for i in range(12): box('D4 ventilation slot',8.357,.46+i*.025,1.45,.003,.013,.003,'steel',.001)
box('D4 access latch',8.356,.748,1.53,.004,.013,.035,'steel',.002)
dev=box('D5 AP faceplate',8.37,6.155,1.13,.018,.09,.14,'white',.006); dev['larktun_role']='network_device'; dev['device_id']='D5'
led=box('D5 connectivity LED',8.365,6.191,1.158,.002,.022,.002,'led',0); led['larktun_role']='device_led'

C=GUIDES
for shot, blocks in L['blocking'].items():
    for block in blocks:
        ob=bpy.data.objects.new(shot+' · '+block['person']+' / Mixamo anchor only',None); C.objects.link(ob)
        ob.location=loc((block['x'],block['y'],0)); ob.rotation_euler.z=-math.radians(block['yaw_deg'])
        ob.empty_display_type='PLAIN_AXES'; ob.empty_display_size=.12; ob.hide_render=True
        ob['character_source']='Mixamo asset to be imported at character stage; no proxy mesh'
for cable in L['cables']:
    ob=curve(cable['src']+' to '+cable['dst']+' / cable route guide',[(x,y,2.65) for x,y in cable['path']],.001,'led',collection=GUIDES)
    ob.hide_render=True; ob.hide_set(True); ob['larktun_role']='cable_route_guide'

def cam(name,xyz,target,ortho=None,lens=35):
    d=bpy.data.cameras.new(name); o=bpy.data.objects.new(name,d); CAMS.objects.link(o)
    o.location=loc(xyz); o.rotation_euler=(loc(target)-o.location).to_track_quat('-Z','Y').to_euler()
    d.clip_start=.025; d.clip_end=200
    if ortho: d.type='ORTHO'; d.ortho_scale=ortho
    else: d.lens=lens
    return o

for v in L['film_cameras']:
    t=v['look_at']; p=(t[0]+16,t[1]+16,t[2]+16) if v['type']=='ISO' else (6,5.3,1.7)
    o=cam(v['id']+' · '+v['name'],p,t,v['scale'] if v['type']=='ISO' else None,35)
    o['future_shots']=' '.join(v['shots']); o['note']='Static camera only; no timeline or film yet'
HERO=cam('REVIEW_01 · Entire apartment cutaway',(22.6,20.15,16.7),(6.6,4.15,.7),20.9)
TOP=cam('REVIEW_02 · Plan overview',(6.6,4.38,25),(6.6,4.38,0),16.4)
TOP.rotation_euler=(0,0,0)
LIVING=cam('REVIEW_03 · Living room',(7.91,8.31,2.22),(4.8,5.1,.97),lens=23)
KITCHEN=cam('REVIEW_04 · Kitchen',(3.23,2.13,1.82),(.57,1.06,1.13),lens=22)
BEDROOM=cam('REVIEW_05 · Master bedroom',(3.0,8.15,2.2),(1.36,5.60,.8),lens=25)
CHILD=cam('REVIEW_06 · Child room',(10.56,8.29,2.0),(11.87,5.76,.83),lens=25)
DETAIL_CAM=cam('REVIEW_07 · Coffee table craftsmanship',(6.50,6.80,1.47),(5.46,6.08,.44),lens=52)
STUDY=cam('REVIEW_08 · Study and local storage',(11.25,2.88,1.70),(12.97,1.67,1.18),lens=34)
BATH=cam('REVIEW_09 · Master bathroom',(.71,4.61,1.75),(2.12,3.60,1.10),lens=20)

def area(name,xyz,target,power,size,color='FFF1DC'):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.shape='DISK'; d.size=size; d.color=rgba(color)[:3]
    o=bpy.data.objects.new(name,d); LIGHTS.objects.link(o); o.location=loc(xyz)
    o.rotation_euler=(loc(target)-o.location).to_track_quat('-Z','Y').to_euler(); return o
area('Large soft daylight',(0,-4,12),(6.5,4,0),1800,8,'FFEFDB')
area('Broad cool fill',(17,6,10),(6,5,0),1000,7,'E3EDF1')
area('Balcony window light',(5.8,10.5,3.4),(5.8,5,1),430,3,'FFEFDB')
area('West bedroom window',(-1,6.8,3.1),(1.8,6.4,.7),220,2,'FFEDCD')
for r in L['rooms']:
    if r['id'] in ('R01','R13'): continue
    x=(r['x0']+r['x1'])/2; y=(r['y0']+r['y1'])/2
    area(r['id']+' interior bounce fill',(x,y,2.70),(x,y,0),40 if r['w']<2 else 65,min(2,r['w']*.7),'FFF0DA')
area('Dining pendant practical',(5.3,1.57,2.02),(5.3,1.57,.7),25,.22,'FFE3B1')

world=bpy.data.worlds.new('Soft neutral daylight'); world.use_nodes=True; SC.world=world
world.node_tree.nodes.get('Background').inputs[0].default_value=(.63,.71,.80,1)
world.node_tree.nodes.get('Background').inputs[1].default_value=.36
sun=bpy.data.lights.new('Late afternoon sunlight','SUN'); sun.energy=1.35; sun.angle=.10; sun.color=(1,.88,.72)
ob=bpy.data.objects.new('Late afternoon sunlight',sun); LIGHTS.objects.link(ob); ob.rotation_euler=(.48,-.35,-.5)
M['ground']=material('Gallery ground','E2DDD1',.9)
box('Matte presentation ground',-100,-100,-.295,200,200,.035,'ground',0,STAGE)

SC.view_layers[0].name='01 · CUTAWAY'
FULL=SC.view_layers.new('02 · FULL INTERIOR')
def exclude(layer,name,value=True):
    def walk(lc):
        if lc.name==name: lc.exclude=value; return True
        return any(walk(ch) for ch in lc.children)
    walk(layer.layer_collection)
for co in (UP,UPFIX,CEILING,NET_HIGH,GUIDES,FULLWALL,FULLFRAME,CUTFRAMEUP): exclude(SC.view_layers[0],co.name)
for co in (LOW,UP,GLAZE,CUTFRAMEUP,GUIDES): exclude(FULL,co.name)
SC.camera=HERO
FULL.use=False
SC.render.resolution_x=ARGS.resolution; SC.render.resolution_y=round(ARGS.resolution*.75)
for s in bpy.data.screens:
    for a in s.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_perspective='CAMERA'; a.spaces.active.clip_end=250
            a.spaces.active.shading.type='SOLID'; a.spaces.active.shading.color_type='MATERIAL'; a.spaces.active.overlay.show_overlays=False
SC['project']='Larktun house reconstruction / architecture and props only'
SC['coordinate_map']='Drawing (x east,y south,z up) -> Blender (x,-y,z)'
SC['source_files']='scene/平面布置图.svg; scene/等距总览.svg; scene/layout.json; 05-户型与场景说明.md'
SC['cutaway_height_m']=1.15
SC['plan_mode']='STRICT ORIGINAL' if ARGS.strict_plan else 'LOCAL CIRCULATION REPAIRS; see HOUSE_README.md'
SC['characters']='No renderable proxies. Mixamo anchors only. Character import/animation deferred.'
SC['architecture_height_m']=2.8

# Keep a compact inventory and the full source data in the portable .blend.
audit={'objects':len(bpy.data.objects),'meshes':len(bpy.data.meshes),'materials':len(bpy.data.materials),
       'rooms':len(L['rooms']),'doors':len(doors),'windows':len(L['windows']),
       'cameras':len(bpy.data.cameras),'renderable_character_proxies':0,
       'wall_height_m':2.8,'cutaway_height_m':1.15,
       'source_dimensions_m':[13.2,8.6],'local_circulation_repairs':not ARGS.strict_plan}
txt=bpy.data.texts.new('SOURCE_LAYOUT.json'); txt.write(json.dumps(L,ensure_ascii=False,indent=2))
txt=bpy.data.texts.new('MODEL_INVENTORY.json'); txt.write(json.dumps(audit,ensure_ascii=False,indent=2))
(ROOT/'blender/model_inventory.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
for name in ['build_home.py','architecture.py','furniture.py','wet_rooms.py','details.py','refine.py','finish_scene.py']:
    txt=bpy.data.texts.new(name); txt.write((ROOT/'blender'/name).read_text())
if (ROOT/'HOUSE_README.md').exists():
    txt=bpy.data.texts.new('START HERE · HOUSE_README.md'); txt.write((ROOT/'HOUSE_README.md').read_text())
for filename in ('平面布置图.svg','等距总览.svg'):
    txt=bpy.data.texts.new('REFERENCE · '+filename); txt.write((ROOT/'scene'/filename).read_text())
for filename in ('平面布置图.png','等距总览.png'):
    im=bpy.data.images.load(str(ROOT/'scene'/filename)); im.name='REFERENCE · '+filename; im.pack(); im.use_fake_user=True
SC.name='01 · House cutaway'
interior_scene=SC.copy(); interior_scene.name='02 · House interiors'; interior_scene.camera=LIVING
interior_scene.view_layers.remove(interior_scene.view_layers[0]); interior_scene.view_layers[0].use=True
interior_scene.view_settings.exposure=.5
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Larktun_Home.blend'),compress=True)
print('SAVED',json.dumps(audit),flush=True)
if ARGS.render:
    SC.render.filepath=str(ROOT/'renders'/ARGS.render)
    # Only evaluate the active review layer during a still render.
    FULL.use=False
    bpy.ops.render.render(write_still=True,layer=SC.view_layers[0].name)
