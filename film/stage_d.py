"""Editable light tubes, geometry-node packets and staggered torus pulses."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
sc=bpy.data.scenes['Larktun Film'];bpy.context.window.scene=sc;activate_look('DUSK');apply_v1_cut(225)
sc.render.fps=30;sc.frame_start=1;sc.frame_end=1200
flows=collection('FILM · Data flow geometry');pulses=collection('FILM · Pulse rings');fills=collection('FILM · Moving flow lights')

def tag(ob,shots,role):ob['film_shots']=shots;ob['film_role']=role;ob['film_base_hide']=False;return ob

def flowmat(name,color,strength):
    m=material(name,color,.35,strength);nt=m.node_tree;n=nt.nodes;l=nt.links;b=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexCoord');tex.location=(-900,100)
    mapping=n.new('ShaderNodeMapping');mapping.name='Flow Mapping / frame driver';mapping.location=(-700,100)
    mapping.inputs['Location'].driver_add('default_value',0).driver.expression='frame * 1.2 / 30'
    gradient=n.new('ShaderNodeTexGradient');gradient.gradient_type='LINEAR';gradient.location=(-500,100)
    wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='X';wave.inputs['Scale'].default_value=5;wave.location=(-300,100)
    ramp=n.new('ShaderNodeValToRGB');ramp.location=(-100,100)
    ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=(.14,.14,.14,1)
    ramp.color_ramp.elements[1].position=.75
    mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=strength;mul.location=(130,100)
    l.new(tex.outputs['Generated'],mapping.inputs['Vector']);l.new(mapping.outputs['Vector'],gradient.inputs[0]);l.new(gradient.outputs['Fac'],wave.inputs[0]);l.new(wave.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],mul.inputs[0]);l.new(mul.outputs[0],b.inputs['Emission Strength'])
    m['semantic_color']='#'+color;m['maximum_emission']=strength;return m
red=flowmat('FLOW RED / FF4B4B','FF4B4B',16);cyan=flowmat('FLOW CYAN / 2FE0C8','2FE0C8',14)
redpack=material('PACKET RED / FF4B4B','FF4B4B',.4,16);cyanpack=material('PACKET CYAN / 2FE0C8','2FE0C8',.4,14)


def packet_nodes(curve,mat,length,shots):
    ob=bpy.data.objects.new(curve.name+' / GN packets',curve.data.copy());flows.objects.link(ob)
    ob.data.bevel_depth=0;tag(ob,shots,'packets')
    ng=bpy.data.node_groups.new(curve.name+' / tangent packet conveyor','GeometryNodeTree')
    ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    n=ng.nodes;l=ng.links
    inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput')
    res=n.new('GeometryNodeResampleCurve');res.inputs['Mode'].default_value='Count';count=max(4,round(length/.85));res.inputs['Count'].default_value=count
    time=n.new('GeometryNodeInputSceneTime');index=n.new('GeometryNodeInputIndex')
    speed=n.new('ShaderNodeMath');speed.operation='MULTIPLY';speed.inputs[1].default_value=1.2/length
    div=n.new('ShaderNodeMath');div.operation='DIVIDE';div.inputs[1].default_value=count
    add=n.new('ShaderNodeMath');add.operation='ADD';fract=n.new('ShaderNodeMath');fract.operation='FRACT'
    sample=n.new('GeometryNodeSampleCurve');sample.mode='FACTOR'
    pos=n.new('GeometryNodeSetPosition');align=n.new('FunctionNodeAlignEulerToVector');align.axis='Z'
    cube=n.new('GeometryNodeMeshCube');cube.inputs['Size'].default_value=(.14,.065,.14)
    trans=n.new('GeometryNodeTransform');trans.inputs['Rotation'].default_value=(0,math.pi/4,0)
    setmat=n.new('GeometryNodeSetMaterial');setmat.inputs['Material'].default_value=mat
    inst=n.new('GeometryNodeInstanceOnPoints');real=n.new('GeometryNodeRealizeInstances')
    l.new(inp.outputs['Geometry'],res.inputs['Curve']);l.new(inp.outputs['Geometry'],sample.inputs['Curves'])
    l.new(time.outputs['Seconds'],speed.inputs[0]);l.new(index.outputs['Index'],div.inputs[0]);l.new(speed.outputs[0],add.inputs[0]);l.new(div.outputs[0],add.inputs[1]);l.new(add.outputs[0],fract.inputs[0]);l.new(fract.outputs[0],sample.inputs['Factor'])
    l.new(res.outputs['Curve'],pos.inputs['Geometry']);l.new(sample.outputs['Position'],pos.inputs['Position']);l.new(sample.outputs['Tangent'],align.inputs['Vector'])
    l.new(cube.outputs['Mesh'],trans.inputs['Geometry']);l.new(trans.outputs['Geometry'],setmat.inputs['Geometry']);l.new(setmat.outputs['Geometry'],inst.inputs['Instance']);l.new(pos.outputs['Geometry'],inst.inputs['Points']);l.new(align.outputs['Rotation'],inst.inputs['Rotation']);l.new(inst.outputs['Instances'],real.inputs[0]);l.new(real.outputs[0],out.inputs[0])
    for i,node in enumerate(n):node.location=(i%6*200,-(i//6)*220)
    mod=ob.modifiers.new('Resample → moving tangent packets','NODES');mod.node_group=ng
    ob['speed_m_s']=1.2;ob['path_length_m']=length
    return ob


def makeflow(name,points,color,shots,radius=.06):
    mat=red if color=='RED' else cyan;pm=redpack if color=='RED' else cyanpack
    ob=tag(bezier(name,points,radius,mat,flows),shots,'light_tube');ob['path_drawing_json']=json.dumps(points)
    length=ob.data.splines[0].calc_length(resolution=32);ob['path_length_m']=length
    packet_nodes(ob,pm,length,shots)
    for i in range(3):
        d=bpy.data.lights.new(name+f' / moving point {i}','POINT');d.energy=3 if color=='RED' else 2.5;d.color=linear('FF4B4B' if color=='RED' else '2FE0C8')[:3];d.shadow_soft_size=.3;d.use_shadow=False
        light=bpy.data.objects.new(d.name,d);fills.objects.link(light);light.location=loc(points[min(i,len(points)-1)])
        tag(light,shots,'flow_fill');light['flow_curve']=ob.name;light['flow_phase']=i/3;light['base_energy']=d.energy
    return ob

makeflow('S02 RED / C1 leaves home',[(8.24,3.52,2.37),(8.0,3.9,3.5),(7.3,5.3,5.2),(4.1,11,13)],'RED','S02')
for i,src in enumerate([(8.24,3.52,2.37),(8.24,.52,2.3),(10.62,5.04,2.2)]):
    makeflow(f'REMOTE RED / C{i+1}',[src,(src[0],src[1],4.0),(10.2+i*.28,9.8,5.5),(13+i*.12,13,8),(16.1,16,10.4)],'RED','S03 S04 S07')
for i,key in enumerate(('C1_D1','C2_D1','C3_D1')):
    cable=bpy.data.objects['CABLE · '+key];points=json.loads(cable['path_drawing_json'])
    points=[(p[0]-.055,p[1],p[2]+.035) for p in points]
    ob=makeflow('S08 CYAN / '+key,points,'CYAN','S08');ob['follows_physical_cable']=cable.name
    # Match the physical cable's limited handles, avoiding spline overshoot at jambs.
    for a,b in zip(ob.data.splines[0].bezier_points,cable.data.splines[0].bezier_points):
        a.handle_left_type=a.handle_right_type='FREE';delta=loc((-.055,0,.035));a.handle_left=b.handle_left+delta;a.handle_right=b.handle_right+delta
    packet=bpy.data.objects[ob.name+' / GN packets'];packet.data=ob.data.copy();packet.data.bevel_depth=0
makeflow('S09 CYAN / private tunnel',[(8.07,5.43,.2),(7.2,6.4,.7),(6.4,8.62,1.5),(7.0,12,4.6),(10,17,8.0)],'CYAN','S09',.18)
makeflow('S12 CYAN / local reassurance',[(10.62,5.04,2.2),(10.64,5.03,1.95),(11.2,5.08,1.9),(12.4,5.1,1.0)],'CYAN','S12',.012)
# Editable staggered rings, parallel to each corresponding camera plane.
for shot,origin,radius in [('S01',(8.16,3.56,2.26),.22),('S07',(12.6,12.6,7.8),2.4)]:
    for i in range(4):
        bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=.008 if shot=='S01' else .035,major_segments=96,minor_segments=12,location=loc(origin),rotation=(math.radians(54.7356),0,math.radians(225)))
        ob=bpy.context.object;ob.name=f'{shot} pulse ring {i}'
        for c in list(ob.users_collection):c.objects.unlink(ob)
        pulses.objects.link(ob);mat=material(ob.name+' emission','FF4B4B' if shot=='S01' else '2FE0C8',.4,16)
        ob.data.materials.append(mat);tag(ob,shot,'pulse_ring');ob['pulse_offset']=i*4
        starts=(1+i*4,43+i*4) if shot=='S01' else (541+i*4,)
        for start in starts:
            for f,s,e in [(start,.08,16),(start+9,1.1,12),(start+28,2.3,0)]:
                ob.scale=(s,s,s);ob.keyframe_insert('scale',frame=f)
                node=mat.node_tree.nodes.get('Principled BSDF');node.inputs['Emission Strength'].default_value=e;node.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
# Per-camera LED materials allow semantic change without changing unrelated LEDs.
for i in (1,2,3):
    ob=bpy.data.objects[f'C{i} LED'];ob.data.materials.clear();ob.data.materials.append(material(f'C{i} semantic LED','FF4B4B',.3,4))
# Restrained bloom in Blender 5.2's compositor node-group API.
nt=bpy.data.node_groups.new('FILM compositor / optical glow','CompositorNodeTree');sc.compositing_node_group=nt
nt.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
r=nt.nodes.new('CompositorNodeRLayers');r.scene=sc;r.layer='LOOK_DUSK';r.name='Active look render'
g=nt.nodes.new('CompositorNodeGlare');g.inputs['Type'].default_value='Fog Glow';g.inputs['Quality'].default_value='High';g.inputs['Threshold'].default_value=1.2;g.inputs['Strength'].default_value=.25;g.inputs['Size'].default_value=.18
out=nt.nodes.new('NodeGroupOutput');nt.links.new(r.outputs['Image'],g.inputs['Image']);nt.links.new(g.outputs['Image'],out.inputs['Image']);r.location=(-300,0);out.location=(300,0)
sc.render.use_compositing=True
save('D')
report={'gate':'D','status':'visual_review','frames':[],'semantic_colors':{'red':'#FF4B4B','cyan':'#2FE0C8'},'packet_method':'Resample Curve / Sample Curve at fraction(index/count + time*1.2/length) / tangent-aligned diamond instances','curve_radii_m':{'flow':.06,'tunnel':.18},'samples':32}
from motion import preview_frame
for shot,frames in [('S02',(91,135,180)),('S08',(631,675,720))]:
    for f in frames:
        preview_frame(shot,f)
        seconds=render(OUT/f'gates/D/{shot}_{f:04d}.png',sc.camera,32)
        report['frames'].append(dict(shot=shot,frame=f,render_seconds=seconds,camera_location=list(sc.camera.location),camera_rotation_euler_deg=[math.degrees(v) for v in sc.camera.rotation_euler],ortho_scale=sc.camera.data.ortho_scale))
dump(OUT/'gates/D/flow_report.json',report)
print('D PREVIEWS COMPLETE',flush=True)
