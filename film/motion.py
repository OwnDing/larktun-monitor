"""Shot state and deterministic curve sampling, shared by gates and final timeline."""
from common import *
from mathutils.geometry import interpolate_bezier

PATH_CACHE={}
def path_samples(ob):
    if ob.name not in PATH_CACHE:
        pts=[];sp=ob.data.splines[0]
        for a,b in zip(sp.bezier_points, list(sp.bezier_points)[1:]):pts.extend(interpolate_bezier(a.co,a.handle_right,b.handle_left,b.co,33)[:-1])
        pts.append(sp.bezier_points[-1].co.copy());lens=[0.]
        for a,b in zip(pts,pts[1:]):lens.append(lens[-1]+(b-a).length)
        PATH_CACHE[ob.name]=(pts,lens)
    return PATH_CACHE[ob.name]
def point_on_curve(ob,t):
    import bisect
    pts,lens=path_samples(ob);distance=(t%1)*lens[-1];i=max(0,min(len(pts)-2,bisect.bisect_right(lens,distance)-1));u=(distance-lens[i])/(lens[i+1]-lens[i] or 1)
    return pts[i].lerp(pts[i+1],u)

def preview_frame(shot,frame):
    sc=bpy.context.scene;activate_look('DUSK');apply_v1_cut(225)
    for ob in sc.objects:
        if ob.get('shot_prop') or ob.get('film_role') in ('remote_tower','remote_window'):ob.hide_render=True
        if ob.get('film_shots'):ob.hide_render=shot not in ob['film_shots'].split()
    sc.camera=bpy.data.objects['V1 · Film locked living room'];sc.frame_set(frame)
    for ob in sc.objects:
        if ob.get('film_role')=='flow_fill':
            curve=bpy.data.objects[ob['flow_curve']];length=curve['path_length_m']
            ob.location=point_on_curve(curve,frame/30*1.2/length+ob['flow_phase'])+Vector((0,0,.08))
    for i in (1,2,3):
        node=bpy.data.materials[f'C{i} semantic LED'].node_tree.nodes.get('Principled BSDF');node.inputs['Emission Color'].default_value=linear('FF4B4B' if shot=='S02' else '2FE0C8')
    bpy.context.view_layer.update()

# Production controller. It applies shot visibility and fixed look banks only;
# editable camera, skeletal and paper keyframes are evaluated by Blender.
_STATE={'shot':None,'scene':None}

def apply_frame(sc,*args):
    if sc.name!='Larktun Film' or not sc.get('film_timeline'):return
    frame=sc.frame_current;timeline=json.loads(sc['film_timeline'])
    shot,start,end,vid,look=next((s for s in timeline if s[1]<=frame<=s[2]),timeline[-1])
    camera_names=json.loads(sc['film_camera_names']);sc.camera=bpy.data.objects[camera_names[vid]]
    if _STATE['shot']!=shot or _STATE['scene']!=sc.as_pointer():
        activate_look(look)
        if vid in ('V3','V5'):focus_cut('R03' if vid=='V3' else 'R12',225 if vid=='V3' else 45)
        else:apply_v1_cut(225)
        if vid=='V2':
            # Roof overview keeps the whole footprint; remove only the near exterior faces.
            groups=json.loads((ROOT/'renders/v1_framing/visibility_groups.json').read_text())
            hidden={n for name,g in groups.items() if 'Wall W00 ' in name or 'Wall W02 ' in name for n in g['objects']}
            for ob in sc.objects:
                if ob.type in ('CAMERA','LIGHT'):continue
                if not ob.get('film_retired') and not ob.get('film_base_hide'):ob.hide_render=ob.name in hidden
        for ob in sc.objects:
            prop=ob.get('shot_prop')
            if prop:ob.hide_render=(prop=='phone_close' and vid!='V4') or (prop=='dining_phone' and vid!='V3') or bool(ob.get('film_retired'))
            if ob.name in ('Phone rounded body','Phone screen','Phone earpiece'):ob.hide_render=vid=='V4'
            if ob.get('film_role') in ('remote_tower','remote_window'):ob.hide_render=vid!='V2'
            if ob.get('film_shots'):ob.hide_render=shot not in ob['film_shots'].split()
        _STATE.update(shot=shot,scene=sc.as_pointer())
    for ob in sc.objects:
        role=ob.get('film_role')
        if role=='flow_fill':
            curve=bpy.data.objects[ob['flow_curve']];length=curve['path_length_m']
            ob.location=point_on_curve(curve,frame/30*1.2/length+ob['flow_phase'])+Vector((0,0,.08))
            if shot=='S07':ob.hide_render=frame>=547 or 'S07' not in ob.get('film_shots','').split()
        elif role=='local_halo':ob.data.energy=3+2*(.5+.5*math.sin((frame-631)/30*2.1))
        elif role=='remote_window':
            b=ob.active_material.node_tree.nodes.get('Principled BSDF');row=ob['window_row'];b.inputs['Emission Strength'].default_value=.7+4*max(0,math.sin((frame-181)/9-row*.8))**8
        elif role=='shard':ob.hide_render=shot!='S07' or frame<548
        if ob.name.startswith('REMOTE RED'):
            if ob.type=='CURVE' and role=='light_tube':ob.data.bevel_factor_end=(1 if shot!='S07' or frame<541 else max(.56,1-(frame-541)/6*.44))
            if shot=='S07':ob.hide_render=frame>=561 or (role=='packets' and frame>=547)
    for i in (1,2,3):
        n=bpy.data.materials[f'C{i} semantic LED'].node_tree.nodes.get('Principled BSDF')
        n.inputs['Emission Color'].default_value=linear('FF4B4B' if shot in ('S01','S02','S03','S04','S07') else '2FE0C8')
        n.inputs['Emission Strength'].default_value=4*(.2+.8*(.5-.5*math.cos(2*math.pi*(frame-1)/42))) if shot=='S01' else 4
    for i in range(3):
        n=bpy.data.materials[f'D1 disk LED {i}'].node_tree.nodes.get('Principled BSDF')
        n.inputs['Emission Strength'].default_value=(1 if frame<631+i*7 else 7+.5*math.sin(frame*.7+i)) if shot=='S08' else .5
    tube=bpy.data.objects['S09 CYAN / private tunnel'];factor=max(0,min(1,(frame-721)/35));tube.data.bevel_factor_end=1-(1-factor)**3 if shot=='S09' else 1
    
    if 'S09 CYAN / moving light core' in bpy.data.objects:bpy.data.objects['S09 CYAN / moving light core'].data.bevel_factor_end=tube.data.bevel_factor_end
    packet=bpy.data.objects[tube.name+' / GN packets'];packet.hide_render=shot!='S09' or frame<757
    if shot=='S09':
        for ob in bpy.data.collections['FILM · Moving flow lights'].objects:
            if ob.get('flow_curve')==tube.name:ob.hide_render=frame<757
    if shot=='S12':
        bpy.data.lights['LOOK_NIGHT child night lamp'].energy=25*(.96+.04*math.sin((frame-991)/30*1.4))
        night=bpy.data.objects['S12 CYAN / local reassurance / GN packets']
        # Gentle round-trip light is created in F completion; this faint line remains local.
    else:bpy.data.lights['LOOK_NIGHT child night lamp'].energy=25
    if 'S04 frame emission' in bpy.data.materials:
        n=bpy.data.materials['S04 frame emission'].node_tree.nodes.get('Principled BSDF')
        # Two complete pulses across the 90-frame shot, peaking near frames 294/338.
        n.inputs['Emission Strength'].default_value=4+12*(.5-.5*math.cos(2*math.pi*(frame-271)/45))**6
    # Image sequences are selected by shot, with a real 90-frame UI sequence in F.
    if 'FILM UI S05' in bpy.data.materials:
        mat=bpy.data.materials['FILM UI S05' if shot=='S05' else 'FILM UI S10' if shot=='S10' else 'FILM UI PAYMENT']
        for name in ('SHOT PHONE · Phone screen','S06 PHONE · Phone screen'):
            ob=bpy.data.objects[name]
            if not ob.data.materials or ob.data.materials[0]!=mat:ob.data.materials.clear();ob.data.materials.append(mat)
        if mat.node_tree:
            for n in mat.node_tree.nodes:
                if n.type=='TEX_IMAGE' and n.image and n.image.source=='SEQUENCE':n.image_user.frame_start=start;n.image_user.frame_offset=0
    # Freeze visible family props outside the paired idle shots through their native keys.


def install():
    from bpy.app.handlers import persistent
    for h in list(bpy.app.handlers.frame_change_post):
        if getattr(h,'__name__','')=='film_frame_change':bpy.app.handlers.frame_change_post.remove(h)
    @persistent
    def film_frame_change(sc,*args):apply_frame(sc)
    bpy.app.handlers.frame_change_post.append(film_frame_change)
    _STATE['shot']=None
    sc=bpy.data.scenes.get('Larktun Film')
    if sc:bpy.context.window.scene=sc;apply_frame(sc)
