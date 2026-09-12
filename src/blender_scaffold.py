# -*- coding: utf-8 -*-
"""
云雀通 Larktun 宣传片 01 —— Blender 脚手架
==========================================
在 Blender 4.x 里运行（Scripting 工作区 → 新建 → 粘贴 → Run），或：
    blender --background --python blender_scaffold.py

这个脚本负责把「地基」打好：场景设置、等距相机、配色、材质工厂、
基础几何助手、数据流曲线、镜头标记。各镜头的具体内容由 build_S01() … build_S14()
逐个实现——脚手架里给出了 S02 / S08 的完整示范，其余照葫芦画瓢。

坐标约定（与分镜图一致）：
    分镜 (x, y, z)  →  Blender (x, -y, z)
    +x 朝屏幕右下，+y 朝屏幕左下，+z 朝上
用 sb() 做转换，不要手写负号。
"""

import bpy, math, os
from mathutils import Vector

# ----------------------------------------------------------------------------
# 配色
# ----------------------------------------------------------------------------
PALETTE = {
    "bg0":    "#05070E",  "bg1":   "#0C1220",  "bg2":  "#151E33",
    "wall":   "#EFE7DA",  "wallD": "#D6C9B6",
    "floor":  "#CFA271",  "wood":  "#9C6F45",  "sofa": "#3E4C6D",
    "risk":   "#FF4B4B",  "risk2": "#FF8A3D",
    "brand":  "#2FE0C8",  # ⚠️ 换成云雀通品牌正色
    "brand2": "#49A0FF",
    "gold":   "#FFC65C",  "cool":  "#8FD3FF",  "warm": "#FFC061",
    "steel":  "#3D4A66",  "ink":   "#F4F7FC",  "mute": "#93A1BC",
}

def hex_to_linear(h, alpha=1.0):
    """sRGB hex → Blender 需要的线性 RGBA。不做这步颜色会明显偏亮。"""
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i+2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, alpha)

def col(name, alpha=1.0):
    return hex_to_linear(PALETTE[name], alpha)

def sb(x, y, z):
    """分镜坐标 → Blender 坐标"""
    return (x, -y, z)

# ----------------------------------------------------------------------------
# 场景 / 渲染
# ----------------------------------------------------------------------------
FPS, TOTAL = 30, 1200
SHOTS = [("S%02d" % i, 1 + (i-1)*90, 90) for i in range(1, 13)] + \
        [("S13", 1081, 60), ("S14", 1141, 60)]

def setup_scene(out_dir="//render/"):
    sc = bpy.context.scene
    try:
        sc.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, TOTAL
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '16'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.filepath = out_dir

    ee = sc.eevee
    for attr, val in (("taa_render_samples", 64), ("use_gtao", True),
                      ("gtao_distance", 0.35), ("use_soft_shadows", True),
                      ("use_bloom", True), ("bloom_intensity", 0.06),
                      ("bloom_threshold", 1.2)):
        if hasattr(ee, attr):
            setattr(ee, attr, val)
    # EEVEE Next 去掉了 bloom，改在合成器里做 Glare
    if not hasattr(ee, "use_bloom"):
        add_glare_compositor(sc)

    vs = sc.view_settings
    for tf in ('AgX', 'Filmic'):
        try:
            vs.view_transform = tf; break
        except TypeError:
            continue
    try:
        vs.look = 'AgX - Medium High Contrast'
    except TypeError:
        pass

    # World
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = col("bg0")
    bg.inputs[1].default_value = 0.35
    return sc

def add_glare_compositor(sc):
    sc.use_nodes = True
    nt = sc.node_tree
    for n in list(nt.nodes):
        if n.type == 'GLARE':
            return
    rl = next((n for n in nt.nodes if n.type == 'R_LAYERS'), None)
    cp = next((n for n in nt.nodes if n.type == 'COMPOSITE'), None)
    if not (rl and cp):
        return
    g = nt.nodes.new("CompositorNodeGlare")
    g.glare_type, g.quality, g.threshold, g.mix = 'FOG_GLOW', 'HIGH', 1.0, -0.72
    g.location = (rl.location.x + 260, rl.location.y)
    nt.links.new(rl.outputs["Image"], g.inputs["Image"])
    nt.links.new(g.outputs["Image"], cp.inputs["Image"])

# ----------------------------------------------------------------------------
# 相机
# ----------------------------------------------------------------------------
ISO_ROT = (math.radians(54.7356), 0.0, math.radians(45.0))

def make_iso_camera(name="CAM_ISO", ortho_scale=9.0, target=(0, 0, 1.2), dist=18.0):
    cam_d = bpy.data.cameras.new(name)
    cam_d.type = 'ORTHO'
    cam_d.ortho_scale = ortho_scale
    cam_d.clip_start, cam_d.clip_end = 0.1, 200.0
    o = bpy.data.objects.new(name, cam_d)
    d = dist / math.sqrt(3)
    o.location = (target[0] + d, target[1] - d, target[2] + d)
    o.rotation_euler = ISO_ROT
    bpy.context.collection.objects.link(o)
    return o

def make_persp_camera(name, loc, look_at=(0, 0, 1.0), lens=55.0):
    cam_d = bpy.data.cameras.new(name); cam_d.lens = lens
    o = bpy.data.objects.new(name, cam_d)
    o.location = loc
    bpy.context.collection.objects.link(o)
    d = Vector(look_at) - Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o

def bind_shot_cameras(mapping):
    """mapping: {'S01': camera_object, ...}；按 SHOTS 的起帧打 Marker 并绑相机"""
    sc = bpy.context.scene
    for name, start, _ in SHOTS:
        camo = mapping.get(name)
        if not camo:
            continue
        m = sc.timeline_markers.new(name, frame=start)
        m.camera = camo

# ----------------------------------------------------------------------------
# 材质工厂
# ----------------------------------------------------------------------------
def _bsdf(mat):
    return mat.node_tree.nodes.get("Principled BSDF")

def _set(bsdf, key, val, *alts):
    for k in (key,) + alts:
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = val
            return True
    return False

def mat_matte(name, color_key, rough=0.8):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = _bsdf(m)
    _set(b, "Base Color", col(color_key))
    _set(b, "Roughness", rough)
    _set(b, "Metallic", 0.0)
    _set(b, "Specular IOR Level", 0.3, "Specular")
    return m

def mat_metal(name, color_key, rough=0.35, metallic=0.8):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = _bsdf(m)
    _set(b, "Base Color", col(color_key))
    _set(b, "Roughness", rough)
    _set(b, "Metallic", metallic)
    return m

def mat_emit(name, color_key, strength=10.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = _bsdf(m)
    c = col(color_key)
    _set(b, "Base Color", (c[0]*0.3, c[1]*0.3, c[2]*0.3, 1.0))
    _set(b, "Roughness", 1.0)
    _set(b, "Emission Color", c, "Emission")
    _set(b, "Emission Strength", strength)
    return m

# ----------------------------------------------------------------------------
# 几何助手（参数与分镜生成器 iso.py 的 box() 完全对应）
# ----------------------------------------------------------------------------
def box(name, x, y, z, dx, dy, dz, mat=None, parent=None):
    """分镜里的 a.box(x,y,z,dx,dy,dz) —— 原点在 (x,y,z) 角，向 +x/+y/+z 生长"""
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    o = bpy.context.object
    o.name = name
    o.scale = (dx/2, dy/2, dz/2)
    o.location = sb(x + dx/2, y + dy/2, z + dz/2)
    if mat: o.data.materials.append(mat)
    if parent: o.parent = parent
    return o

def empty(name, x=0, y=0, z=0):
    o = bpy.data.objects.new(name, None)
    o.empty_display_size = 0.3
    o.location = sb(x, y, z)
    bpy.context.collection.objects.link(o)
    return o

def collection(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c

def move_to(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)

# ----------------------------------------------------------------------------
# 房间（S02 / S08 / S09 共用）
# ----------------------------------------------------------------------------
def build_room(w=5.0, d=3.8, h=2.7, t=0.35, prefix="ROOM"):
    m_wall  = mat_matte("M_Wall",  "wall",  0.85)
    m_floor = mat_matte("M_Floor", "floor", 0.60)
    root = empty(prefix + "_root")
    box(prefix+"_WallA", -t, -t, 0, w+t, t, h, m_wall,  root)   # 后墙（沿 x）
    box(prefix+"_WallB", -t,  0, 0, t,   d, h, m_wall,  root)   # 侧墙（沿 y）
    box(prefix+"_Floor",  0,  0, -0.06, w, d, 0.06, m_floor, root)
    return root

# ----------------------------------------------------------------------------
# 数据流：光管 + 流动
# ----------------------------------------------------------------------------
def flow_curve(name, p0, p1, bow=1.2, color_key="risk", depth=0.06,
               strength=14.0, speed=1.0, grow=None):
    """
    在两点之间拉一条发光光管。
    p0/p1 : 分镜坐标 (x,y,z)
    bow   : 中点向 +z 抬起的高度（米），做出弧线
    grow  : None 或 (start_frame, end_frame) —— 让管子从 p0 生长到 p1（S09 隧道用）
    """
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = depth
    cu.bevel_resolution = 6
    cu.resolution_u = 24
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(2)
    a, b = Vector(sb(*p0)), Vector(sb(*p1))
    mid = (a + b) / 2 + Vector((0, 0, bow))
    for bp, co in zip(sp.bezier_points, (a, mid, b)):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)

    mat = flowing_emission(name + "_M", color_key, strength, speed)
    o.data.materials.append(mat)

    if grow:
        f0, f1 = grow
        cu.bevel_factor_end = 0.0
        cu.keyframe_insert("bevel_factor_end", frame=f0)
        cu.bevel_factor_end = 1.0
        cu.keyframe_insert("bevel_factor_end", frame=f1)
        for fc in cu.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.easing = 'EASE_OUT'
    return o

def flowing_emission(name, color_key, strength=14.0, speed=1.0):
    """条纹沿管子流动的自发光材质。speed = 每秒流过的条纹数。"""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    bsdf = _bsdf(m)
    c = col(color_key)
    _set(bsdf, "Base Color", (c[0]*0.25, c[1]*0.25, c[2]*0.25, 1.0))
    _set(bsdf, "Roughness", 1.0)

    tex = nt.nodes.new("ShaderNodeTexGradient"); tex.location = (-760, 0)
    mapn = nt.nodes.new("ShaderNodeMapping");    mapn.location = (-960, 0)
    coord = nt.nodes.new("ShaderNodeTexCoord");  coord.location = (-1160, 0)
    wave = nt.nodes.new("ShaderNodeTexWave");    wave.location = (-560, 0)
    wave.bands_direction = 'X'; wave.wave_profile = 'SIN'
    wave.inputs["Scale"].default_value = 6.0
    ramp = nt.nodes.new("ShaderNodeValToRGB");   ramp.location = (-360, 0)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.72
    mul = nt.nodes.new("ShaderNodeMath");        mul.location = (-160, -160)
    mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = strength

    nt.links.new(coord.outputs["Generated"], mapn.inputs["Vector"])
    nt.links.new(mapn.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Fac"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], mul.inputs[0])
    _set(bsdf, "Emission Color", c, "Emission")
    nt.links.new(mul.outputs[0], bsdf.inputs["Emission Strength"])

    # 用 driver 做无限流动，比关键帧省事
    drv = mapn.inputs["Location"].driver_add("default_value", 0).driver
    drv.type = 'SCRIPTED'
    drv.expression = f"frame * {speed / FPS:.6f}"
    return m

def pulse_ring(name, center, color_key="brand", f0=0, dur=30, r0=0.08, r1=3.2,
               s0=30.0, s1=0.0):
    """S07 切断 / S01 红环用的扩散圆环"""
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.05)
    o = bpy.context.object; o.name = name
    o.location = sb(*center)
    o.rotation_euler = ISO_ROT          # 让环正对相机
    mat = mat_emit(name + "_M", color_key, s0)
    o.data.materials.append(mat)
    o.scale = (r0, r0, r0); o.keyframe_insert("scale", frame=f0)
    o.scale = (r1, r1, r1); o.keyframe_insert("scale", frame=f0 + dur)
    b = _bsdf(mat)
    b.inputs["Emission Strength"].default_value = s0
    b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f0)
    b.inputs["Emission Strength"].default_value = s1
    b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f0 + dur)
    return o

# ----------------------------------------------------------------------------
# 灯光
# ----------------------------------------------------------------------------
def build_lights(key_power=450.0):
    specs = [
        ("KEY",  'AREA',  (-6, -9, 11), 8.0, key_power, (1.0, 0.97, 0.92)),
        ("FILL", 'AREA',  ( 9, -5,  5), 6.0,      90.0, col("cool")[:3]),
        ("RIM",  'AREA',  ( 4,  8,  7), 5.0,     160.0, col("brand2")[:3]),
    ]
    coll = collection("SHARED_LIGHTS")
    out = {}
    for name, kind, loc, size, power, color in specs:
        ld = bpy.data.lights.new("L_" + name, kind)
        ld.energy = power
        ld.color = color
        if hasattr(ld, "size"): ld.size = size
        o = bpy.data.objects.new("L_" + name, ld)
        o.location = loc
        d = Vector((0, 0, 1.2)) - Vector(loc)
        o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        bpy.context.collection.objects.link(o); move_to(o, coll)
        out[name] = o
    return out

# ----------------------------------------------------------------------------
# 示范：S02（数据外流） / S08（存回自己家）
# 两镜共用同一个房间和同一台相机——这是全片的记忆锚点，务必保持一致。
# ----------------------------------------------------------------------------
def build_S02_S08():
    room_c = collection("SHARED_ROOM")
    root = build_room()
    move_to(root, room_c)
    for ch in root.children_recursive:
        move_to(ch, room_c)

    m_cam_body = mat_matte("M_CamBody", "ink", 0.5)
    cam_pos = (4.2, 0.05, 2.2)
    camera_prop = box("PROP_Camera", *cam_pos, 0.33, 0.22, 0.22, m_cam_body)

    # --- S02：红流冲出屋顶 ---
    c02 = collection("SHOT_S02")
    led_r = box("LED_S02", 4.25, 0.28, 2.32, 0.05, 0.05, 0.05,
                mat_emit("M_LED_Risk", "risk", 20.0))
    flow_r = flow_curve("FLOW_S02", (4.35, 0.30, 2.30), (2.6, -3.4, 7.2),
                        bow=1.0, color_key="risk", depth=0.07, strength=16.0, speed=2.0)
    for o in (led_r, flow_r): move_to(o, c02)

    # --- S08：三条青流汇入家里的录像机 ---
    c08 = collection("SHOT_S08")
    hub = (3.28, 0.50, 0.96)
    nvr = box("PROP_NVR", 2.85, 0.18, 0.83, 0.78, 0.50, 0.16,
              mat_metal("M_NVR", "steel", 0.4, 0.7))
    move_to(nvr, c08)
    for i, src in enumerate([(4.35, 0.30, 2.25), (0.40, 2.50, 2.25), (1.30, 0.30, 2.30)]):
        f = flow_curve(f"FLOW_S08_{i}", src, hub, bow=0.55, color_key="brand",
                       depth=0.055, strength=12.0, speed=1.6)
        move_to(f, c08)
        led = box(f"LED_S08_{i}", src[0]-0.05, src[1]-0.02, src[2]+0.02, 0.05, 0.05, 0.05,
                  mat_emit("M_LED_Brand", "brand", 18.0))
        move_to(led, c08)

    # 按帧开关两个 collection
    for name, coll in (("S02", c02), ("S08", c08)):
        start = dict((s[0], s[1]) for s in SHOTS)[name]
        coll.hide_render = True;  coll.keyframe_insert("hide_render", frame=start - 1)
        coll.hide_render = False; coll.keyframe_insert("hide_render", frame=start)
        coll.hide_render = True;  coll.keyframe_insert("hide_render", frame=start + 90)
    return camera_prop

# ----------------------------------------------------------------------------
def main():
    setup_scene()
    build_lights()
    build_S02_S08()
    cams = {}
    iso = make_iso_camera("CAM_ISO", ortho_scale=9.0, target=(2.5, -1.9, 1.2))
    for name, _, _ in SHOTS:
        cams[name] = iso                      # 先全部指向等距主相机
    # 需要透视的镜头单独换：
    # cams["S03"] = make_persp_camera("CAM_S03", (16, -20, 22), (0, 0, 2), lens=45)
    bind_shot_cameras(cams)
    bpy.context.scene.camera = iso
    print("[larktun] 脚手架就绪：S02 / S08 已搭好，其余镜头照此实现 build_S##()")

if __name__ == "__main__":
    main()
