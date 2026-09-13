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
