# -*- coding: utf-8 -*-
"""
云雀通宣传片 01 —— Blender 户型自动搭建
=======================================
把 layout.json 里的户型一次性建成 Blender 场景：地面、带门窗洞的墙、梁、
家具体块、三台监控摄像头、网络设备、六个影片机位、灯光、人物占位。

用法（layout.json 与本脚本放同一目录）：
    blender --background --python build_apartment.py
    # 或在 Blender 的 Scripting 面板里打开运行

坐标：图纸 (x 东, y 南, z 上)  →  Blender (x, -y, z)
等距相机：rotation_euler = (54.7356°, 0, 45°)，东南上空朝西北看
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector, Euler

HERE = os.path.dirname(os.path.abspath(bpy.data.filepath or __file__)) or os.getcwd()
for cand in (HERE, os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
    p = os.path.join(cand, "layout.json")
    if os.path.exists(p):
        LAYOUT = json.load(open(p, encoding="utf-8")); break
else:
    raise SystemExit("找不到 layout.json —— 请把它和本脚本放在同一目录")

M   = LAYOUT["meta"]
CEIL, WI, WE = M["ceiling"], M["wall_int"], M["wall_ext"]
SILL, BAY    = M["sill"], M["bay_sill"]
OPEN_TOP = {"entry":2.10, "swing":2.10, "slide":2.30, "arch":2.30}
WIN_TOP  = 2.40
BUILD_CEILING = False        # 需要俯拍就关着；要拍室内透视再打开

# ══════════════════════ 基础工具 ══════════════════════
def bl(x, y, z=0.0):                      # 图纸 → Blender
    return (x, -y, z)

def srgb(h):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i+2], 16) / 255
        out.append(c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4)
    return (*out, 1.0)

def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c

def put(obj, c):
    for u in list(obj.users_collection): u.objects.unlink(obj)
    c.objects.link(obj)

def _setv(b, val, *keys):
    for k in keys:
        if k in b.inputs:
            b.inputs[k].default_value = val; return True
    return False

def mat(name, hexc, rough=.8, metal=0.0, emit=None, emit_str=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    _setv(b, srgb(hexc), "Base Color")
    _setv(b, rough, "Roughness"); _setv(b, metal, "Metallic")
    _setv(b, .3, "Specular IOR Level", "Specular")
    if emit:
        _setv(b, srgb(emit), "Emission Color", "Emission")
        _setv(b, emit_str, "Emission Strength")
    return m

def cube(name, x, y, z, dx, dy, dz, material=None, c=None):
    """x,y,z 为图纸坐标的最小角；dx,dy,dz 为尺寸"""
    if dx <= 0 or dy <= 0 or dz <= 0: return None
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    o.scale = (dx, dy, dz)
    o.location = bl(x + dx/2, y + dy/2, z + dz/2)
    bpy.context.scene.collection.objects.link(o)
    if material: o.data.materials.append(material)
    if c: put(o, c)
    return o

# ══════════════════════ 材质 ══════════════════════
MATS = {
 "wall_ext": ("#EFE7DA", .88), "wall_int": ("#F2ECE2", .88), "rail": ("#C6CCD6", .6),
 "beam":     ("#E4DED3", .9),  "ceiling":  ("#FAF7F2", .95),
 "floor_live":("#C79A68", .55),"floor_rest":("#B98F63", .6), "floor_wet":("#D3D7DA", .35),
 "floor_work":("#C09468", .55),"floor_util":("#C9CBC8", .45),
 "fab":  ("#4A5878", .92), "wood": ("#9C6F45", .62), "wood_l":("#C3A077", .6),
 "white":("#EDEFF3", .5),  "metal":("#9AA3AE", .35), "dark": ("#22283A", .45),
 "glass":("#BFD9E4", .12), "green":("#4E8B57", .8),  "linen":("#E2D8C8", .9),
 "dev":  ("#2B3242", .4),
}
MAT = {k: mat("M_"+k, v[0], v[1], .7 if k=="metal" else 0.0) for k, v in MATS.items()}
MAT["led_red"]   = mat("M_LED_Red",   "#FF4B4B", 1.0, 0, "#FF4B4B", 18)
MAT["led_brand"] = mat("M_LED_Brand", "#2FE0C8", 1.0, 0, "#2FE0C8", 16)
MAT["screen"]    = mat("M_Screen",    "#2A3550", 1.0, 0, "#8FD3FF",  3)

FURN_MAT = {
 "sofa":"fab","armchair":"fab","sofabed":"fab","bed":"linen","nightstand":"wood",
 "wardrobe":"wood_l","cabinet":"wood_l","shelf":"wood_l","bench":"wood",
 "counter":"white","upper":"white","fridge":"white","stove":"metal","sink":"white",
 "toilet":"white","shower":"glass","desk":"wood_l","table":"wood","chair":"wood",
 "tv":"dark","rug":"fab","plant":"green","lamp":"white","mirror":"glass",
 "box":"white","rail":"metal",
}

# ══════════════════════ 场景 ══════════════════════
def setup_scene():
    sc = bpy.context.scene
    try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError: sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
    sc.render.fps = 30; sc.frame_start, sc.frame_end = 1, 1200
    for k, v in (("use_gtao",True),("gtao_distance",.35),("taa_render_samples",64),
                 ("use_soft_shadows",True)):
        if hasattr(sc.eevee, k): setattr(sc.eevee, k, v)
    for tf in ('AgX','Filmic'):
        try: sc.view_settings.view_transform = tf; break
        except TypeError: pass
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    sc.world = w; w.use_nodes = True
    bgn = w.node_tree.nodes.get("Background")
    bgn.inputs[0].default_value = srgb("#0C1220"); bgn.inputs[1].default_value = .35

def wipe():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for d in list(blk):
            if d.users == 0: blk.remove(d)

# ══════════════════════ 地面 / 天花 ══════════════════════
def build_floors():
    c = coll("SET_Floors")
    for r in LAYOUT["rooms"]:
        m = MAT["floor_" + r["tint"]]
        cube(f'FLR_{r["id"]}_{r["name"]}', r["x0"], r["y0"], -0.06,
             r["x1"]-r["x0"], r["y1"]-r["y0"], 0.06, m, c)
        if BUILD_CEILING and r["id"] not in ("R01", "R13"):
            cube(f'CLG_{r["id"]}', r["x0"], r["y0"], CEIL,
                 r["x1"]-r["x0"], r["y1"]-r["y0"], 0.10, MAT["ceiling"], c)

# ══════════════════════ 墙 + 门窗洞 ══════════════════════
def openings():
    out = []
    for d in LAYOUT["doors"]:
        top = OPEN_TOP.get(d["type"], 2.10)
        out.append(dict(x=d["x"], y=d["y"], w=d["width"], axis=d["axis"],
                        z0=0.0, z1=top, name=d["name"], kind=d["type"]))
    for w in LAYOUT["windows"]:
        z0 = BAY if w["type"] == "bay" else SILL
        out.append(dict(x=w["x"], y=w["y"], w=w["width"], axis=w["axis"],
                        z0=z0, z1=WIN_TOP, name=w["name"], kind="window"))
    return out
OPENINGS = openings()

def build_walls():
    c = coll("SET_Walls"); cg = coll("SET_Glazing")
    for wi, w in enumerate(LAYOUT["walls"]):
        x0, y0, x1, y1 = w["x0"], w["y0"], w["x1"], w["y1"]
        kind = w["type"]
        h   = CEIL if kind != "P" else 1.10
        m   = MAT["wall_ext"] if kind == "E" else (MAT["rail"] if kind == "P" else MAT["wall_int"])
        horiz = (x1-x0) >= (y1-y0)
        lo, hi = (x0, x1) if horiz else (y0, y1)
        cuts = []
        for o in OPENINGS:
            if horiz and o["axis"] == "h" and (y0-.03) <= o["y"] <= (y1+.03) \
               and o["x"] >= x0-.03 and o["x"]+o["w"] <= x1+.03:
                cuts.append(o)
            if (not horiz) and o["axis"] == "v" and (x0-.03) <= o["x"] <= (x1+.03) \
               and o["y"] >= y0-.03 and o["y"]+o["w"] <= y1+.03:
                cuts.append(o)
        cuts.sort(key=lambda o: o["x"] if horiz else o["y"])
        cur = lo
        for o in cuts:
            s = o["x"] if horiz else o["y"]; e = s + o["w"]
            if s > cur:
                a, b = (cur, s)
                cube(f"WALL_{wi}_{kind}_seg", *( (a, y0, 0, b-a, y1-y0, h) if horiz
                                                 else (x0, a, 0, x1-x0, b-a, h) ), m, c)
            # 洞口上方过梁
            if o["z1"] < h - .001:
                cube(f'WALL_{wi}_lintel_{o["name"]}',
                     *((s, y0, o["z1"], e-s, y1-y0, h-o["z1"]) if horiz
                       else (x0, s, o["z1"], x1-x0, e-s, h-o["z1"])), m, c)
            # 洞口下方窗台墙
            if o["z0"] > .001:
                cube(f'WALL_{wi}_sill_{o["name"]}',
                     *((s, y0, 0, e-s, y1-y0, o["z0"]) if horiz
                       else (x0, s, 0, x1-x0, e-s, o["z0"])), m, c)
            # 玻璃
            if o["kind"] in ("window", "slide"):
                t = .02
                if horiz:
                    cube(f'GLASS_{o["name"]}', s, (y0+y1)/2 - t/2, o["z0"], e-s, t, o["z1"]-o["z0"], MAT["glass"], cg)
                else:
                    cube(f'GLASS_{o["name"]}', (x0+x1)/2 - t/2, s, o["z0"], t, e-s, o["z1"]-o["z0"], MAT["glass"], cg)
            cur = max(cur, e)
        if cur < hi:
            cube(f"WALL_{wi}_{kind}_seg", *((cur, y0, 0, hi-cur, y1-y0, h) if horiz
                                            else (x0, cur, 0, x1-x0, hi-cur, h)), m, c)
    for i, b in enumerate(LAYOUT["beams"]):
        cube(f"BEAM_{i}", b["x0"], b["y0"], M["beam_clear"],
             b["x1"]-b["x0"], b["y1"]-b["y0"], CEIL-M["beam_clear"], MAT["beam"], c)

# ══════════════════════ 家具 ══════════════════════
def build_furniture():
    byroom = {}
    for f in LAYOUT["furniture"]:
        byroom.setdefault(f["room"], []).append(f)
    rname = {r["id"]: r["name"] for r in LAYOUT["rooms"]}
    for rid, items in byroom.items():
        c = coll(f"PROPS_{rid}_{rname.get(rid,'')}")
        for f in items:
            m = MAT[FURN_MAT.get(f["symbol"], "white")]
            h = max(f["h"], 0.012)
            cube(f'{rid}_{f["name"]}', f["x"], f["y"], 0.0, f["w"], f["d"], h, m, c)

# ══════════════════════ 监控摄像头 / 设备 ══════════════════════
def build_cameras():
    c = coll("PROPS_Security")
    for cam in LAYOUT["cameras"]:
        x, y, z, yaw = cam["x"], cam["y"], cam["z"], math.radians(cam["yaw_deg"])
        body = cube(f'CAM_{cam["id"]}_body', x-.16, y-.11, z, .32, .22, .22, MAT["white"], c)
        body.rotation_euler = (0, 0, yaw)
        led = cube(f'CAM_{cam["id"]}_LED', x-.04, y-.03, z+.16, .05, .05, .04, MAT["led_red"], c)
        led["larktun_role"] = "camera_led"          # 自定义属性：换红/青只改这一批
        e = bpy.data.objects.new(f'CAM_{cam["id"]}_AIM', None)
        e.empty_display_size = .25
        e.location = bl(x + math.cos(yaw)*2.4, y - math.sin(yaw)*2.4, z - .9)
        bpy.context.scene.collection.objects.link(e); put(e, c)

def build_devices():
    c = coll("PROPS_Network")
    for d in LAYOUT["devices"]:
        o = cube(f'DEV_{d["id"]}_{d["name"]}', d["x"]-d["w"]/2, d["y"]-d["d"]/2, d["z"],
                 d["w"], d["d"], d["h"], MAT["dev"], c)
        led = cube(f'DEV_{d["id"]}_LED', d["x"]-.015, d["y"]+d["d"]/2-.004, d["z"]+d["h"]*.4,
                   .03, .006, .012, MAT["led_brand"], c)
        led["larktun_role"] = "device_led"

# ══════════════════════ 影片机位 ══════════════════════
def build_film_cameras():
    c = coll("CAMERAS")
    for v in LAYOUT["film_cameras"]:
        lx, ly, lz = v["look_at"]
        cd = bpy.data.cameras.new(v["id"])
        if v["type"] == "ISO":
            cd.type = 'ORTHO'; cd.ortho_scale = v["scale"]
        else:
            cd.type = 'PERSP'; cd.lens = v["scale"]
        cd.clip_start, cd.clip_end = .05, 300
        o = bpy.data.objects.new(f'{v["id"]}_{v["name"]}', cd)
        if v["type"] == "ISO":
            zr = math.radians(v["rot_z_deg"])
            o.rotation_euler = (math.radians(54.7356), 0.0, zr)
            # Z=45° 时相机在 Blender (+X, -Y, +Z)；换方位就把这个偏移绕 Z 转过去
            d = 26.0 / math.sqrt(3)
            off = Vector((d, -d, d))
            off.rotate(Euler((0.0, 0.0, zr - math.radians(45)), 'XYZ'))
            o.location = Vector(bl(lx, ly, lz)) + off
        else:
            o.location = Vector(bl(lx, ly, lz)) + Vector((0, 3.6, .35))
            aim = Vector(bl(lx, ly, lz)) - o.location
            o.rotation_euler = aim.to_track_quat('-Z', 'Y').to_euler()
        bpy.context.scene.collection.objects.link(o); put(o, c)
        o["shots"] = " ".join(v["shots"])
    first = bpy.data.objects.get("V1_客厅主机位")
    if first: bpy.context.scene.camera = first

# ══════════════════════ 人物占位 ══════════════════════
def build_people():
    """
    只放占位圆柱 + 身高标注。真人角色建议走以下任一条路（都不用手动建模）：
      1. Mixamo 免费角色 + 动作 → 下载 FBX → File > Import > FBX（最省事）
      2. MakeHuman（开源）导出 → Blender 插件导入 → 自己配家居服
      3. Human Generator / Character Creator（付费，质量最高）
    导入后把占位圆柱的 location / rotation 抄过去即可对位。
    """
    c = coll("PEOPLE")
    ph = {p["id"]: p for p in LAYOUT["people"]}
    for key, blocks in LAYOUT["blocking"].items():
        for b in blocks:
            p = ph[b["person"]]
            r = .17 if p["id"] != "P4" else .12
            o = cube(f'PERSON_{key}_{p["id"]}_{p["name"]}',
                     b["x"]-r, b["y"]-r, 0, r*2, r*2, p["height"], MAT["white"], c)
            o.rotation_euler = (0, 0, math.radians(b["yaw_deg"]))
            o["height_m"] = p["height"]; o["note"] = p["note"]
            o.display_type = 'WIRE'

# ══════════════════════ 灯光 ══════════════════════
def build_lights():
    c = coll("LIGHTS")
    specs = [("KEY",'AREA',(-7,9,13),9.0,600,"#FFF6E8"),
             ("FILL",'AREA',(11,7,6),7.0,120,"#8FD3FF"),
             ("RIM",'AREA',(5,-11,8),6.0,200,"#49A0FF")]
    for n,k,loc,size,pw,hx in specs:
        ld = bpy.data.lights.new("L_"+n, k); ld.energy = pw; ld.color = srgb(hx)[:3]
        if hasattr(ld,"size"): ld.size = size
        o = bpy.data.objects.new("L_"+n, ld); o.location = loc
        d = Vector((6.6,-4.3,1.2)) - Vector(loc)
        o.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
        bpy.context.scene.collection.objects.link(o); put(o, c)
    # 室内暖灯（每个主要房间一盏）
    for rid,(x,y,z,pw) in {"R07":(6.0,5.9,2.55,55),"R03":(5.3,1.6,2.35,35),
                           "R09":(1.8,6.7,2.55,30),"R12":(11.4,6.7,2.55,30),
                           "R02":(1.8,1.6,2.55,25),"R06":(11.4,1.6,2.55,28)}.items():
        ld = bpy.data.lights.new(f"L_WARM_{rid}", 'POINT')
        ld.energy = pw; ld.color = srgb("#FFC061")[:3]; ld.shadow_soft_size = .25
        o = bpy.data.objects.new(f"L_WARM_{rid}", ld); o.location = bl(x,y,z)
        bpy.context.scene.collection.objects.link(o); put(o, c)

# ══════════════════════ 主流程 ══════════════════════
def main():
    wipe(); setup_scene()
    build_floors(); build_walls(); build_furniture()
    build_cameras(); build_devices(); build_film_cameras(); build_people(); build_lights()
    n = len(bpy.context.scene.collection.all_objects)
    print(f"[larktun] 户型搭建完成：{n} 个物体，套内 {M['interior_area_m2']} ㎡")
    print("[larktun] 下一步：1) 家具体块替换成真模型  2) 导入真人角色  3) 按分镜连数据流曲线")

if __name__ == "__main__":
    main()
