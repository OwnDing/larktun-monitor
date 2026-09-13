"""CC0 MakeHuman anatomy + original volumetric garments and seated posing."""
from common import *


def read_base():
    vertices=[]; faces={}; group='body'
    for line in (ROOT/'assets/characters/base.obj').read_text().splitlines():
        if line.startswith('v '): vertices.append(list(map(float,line.split()[1:4])))
        elif line.startswith('g '): group=line[2:]; faces.setdefault(group,[])
        elif line.startswith('f '): faces[group].append([int(v.split('/')[0])-1 for v in line.split()[1:]])
    return np.array(vertices),faces


def build_person(pid, height, target_name, position, yaw, shirt_hex):
    raw,faces=read_base()
    for line in (ROOT/'assets/characters'/target_name).read_text().splitlines():
        if not line or line.startswith('#'): continue
        fields=line.split(); raw[int(fields[0])]+=np.array(list(map(float,fields[1:4])))
    body_ids=sorted({i for f in faces['body'] for i in f})
    ground=raw[body_ids,1].min(); factor=height/(raw[body_ids,1].max()-ground)
    verts=np.column_stack((raw[:,0],-raw[:,2],raw[:,1]-ground))*factor
    rig=json.loads((ROOT/'assets/characters/default.mhskel').read_text())
    weights=json.loads((ROOT/'assets/characters/default_weights.mhw').read_text())['weights']
    joints={n:Vector(verts[indices].mean(axis=0)) for n,indices in rig['joints'].items()}
    coll=collection('FILM · '+pid+' MakeHuman character')
    arm_data=bpy.data.armatures.new(pid+' anatomical skeleton')
    arm=bpy.data.objects.new(pid+' seated rig',arm_data); coll.objects.link(arm)
    bpy.context.view_layer.objects.active=arm; arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name,b in rig['bones'].items():
        bone=arm_data.edit_bones.new(name); bone.head=joints[b['head']]; bone.tail=joints[b['tail']]
        if (bone.tail-bone.head).length<1e-5: bone.tail.z+=.01
        bone.align_roll(Vector((0,-1,0)))
    for name,b in rig['bones'].items():
        if b['parent']: arm_data.edit_bones[name].parent=arm_data.edit_bones[b['parent']]
    bpy.ops.object.mode_set(mode='OBJECT'); arm.select_set(False)
    skin=material(pid+' skin','BA967F',.62)
    cloth=material(pid+' cotton garment',shirt_hex,.94)
    pants=material(pid+' trousers','323948' if pid!='P3' else '746A61',.92)
    hair=material(pid+' hair','24201E',.94)

    def part(name, selected, mat, expand=0, thickness=0):
        used=sorted({i for f in selected for i in f}); remap={v:i for i,v in enumerate(used)}
        me=bpy.data.meshes.new(pid+' '+name);me.from_pydata([tuple(verts[i]) for i in used],[],[[remap[i] for i in f] for f in selected]);me.update()
        ob=bpy.data.objects.new(pid+' '+name,me);coll.objects.link(ob);me.materials.append(mat)
        for poly in me.polygons: poly.use_smooth=True
        if expand:
            normals=[v.normal.copy() for v in me.vertices]
            for v,n in zip(me.vertices,normals):
                v.co+=n*(expand+.0018*math.sin(v.co.z*83+v.co.x*47))
        for bone,items in weights.items():
            applicable=[(remap[i],w) for i,w in items if i in remap and w>0]
            if applicable:
                vg=ob.vertex_groups.new(name=bone)
                for index,w in applicable: vg.add([index],w,'REPLACE')
        mod=ob.modifiers.new('MakeHuman skin deformation','ARMATURE');mod.object=arm;mod.use_deform_preserve_volume=True
        sub=ob.modifiers.new('Smooth garment surface' if thickness else 'Anatomical surface','SUBSURF');sub.levels=1;sub.render_levels=1
        if thickness:
            sol=ob.modifiers.new('Physical fabric thickness','SOLIDIFY');sol.thickness=thickness;sol.offset=1
        ob.parent=arm;ob['film_room']='R03';ob['person_id']=pid;ob['character_source']='MakeHuman CC0 base + target + weights'
        ob['film_role']='character_garment' if thickness else 'character_anatomy'
        return ob

    body=part('anatomical body',faces['body'],skin)
    # Helper tights are a separate continuous clothing surface, with the same
    # canonical vertex weights. They are not a body-colour texture or primitives.
    helper=faces['helper-tights']
    def centre(f): return verts[f].mean(axis=0)
    tops=[f for f in helper if .50*height<centre(f)[2]<.825*height
          and (abs(centre(f)[0])<.18*height or centre(f)[2]>.63*height)]
    bottoms=[f for f in helper if .045*height<centre(f)[2]<.56*height and abs(centre(f)[0])<.22*height]
    top=part('cotton shirt geometry',tops,cloth,.015 if pid!='P3' else .011,.003)
    bottom=part('trouser geometry',bottoms,pants,.012,.003)
    short_hair=[f for f in faces['helper-hair'] if verts[f].mean(axis=0)[2]>.89*height]
    cap=part('sculpted short hair cap',short_hair,hair,.006,.004)
    # Feet use the anatomical foot geometry, with separate opaque sock material.
    sock=material(pid+' socks','BDB6A8',.97)
    body.data.materials.append(sock)
    for poly in body.data.polygons:
        if poly.center.z<height*.06: poly.material_index=1
    # Pose every deform bone in armature space using the official joint locations.
    # Thighs horizontal, shins vertical, elbows approximately 90 degrees.
    hip=(joints[rig['bones']['upperleg01.L']['head']]+joints[rig['bones']['upperleg01.R']['head']])/2
    seated_hip=.51 if pid!='P3' else .50
    dz=seated_hip-hip.z; body_matrix=Matrix.Translation((0,0,dz))
    transforms={}
    def align(a,b,aa,bb):
        q=(b-a).rotation_difference(bb-aa)
        return Matrix.Translation(aa)@q.to_matrix().to_4x4()@Matrix.Translation(-a)
    for side,sign in (('L',1),('R',-1)):
        def head(n): return joints[rig['bones'][n+'.'+side]['head']]
        hip0,knee0,ankle0=head('upperleg01'),head('lowerleg01'),head('foot')
        thigh=(knee0-hip0).length; calf=(ankle0-knee0).length
        hp=hip0+Vector((0,0,dz)); kp=hp+Vector((sign*.018,-thigh,-.018))
        ap=kp+Vector((sign*.012,-.025,-calf))
        transforms['upperleg',side]=align(hip0,knee0,hp,kp)
        transforms['lowerleg',side]=align(knee0,ankle0,kp,ap)
        transforms['foot',side]=Matrix.Translation(ap-ankle0)
        sh,el,wr=head('upperarm01'),head('lowerarm01'),head('wrist')
        sh1=sh+Vector((0,0,dz))
        upper=(el-sh).length;lower=(wr-el).length
        el1=sh1+Vector((-sign*upper*.20,-upper*.40,-upper*.895))
        wr1=el1+Vector((-sign*lower*.10,-lower*.985,lower*.08))
        transforms['upperarm',side]=align(sh,el,sh1,el1)
        transforms['lowerarm',side]=align(el,wr,el1,wr1)
    def depth(b): return 0 if b.parent is None else 1+depth(b.parent)
    desired={}
    for bone in sorted(arm.pose.bones,key=depth):
        side=bone.name[-1:] if bone.name.endswith(('.L','.R')) else None
        transform=body_matrix
        if side:
            for prefix,category in (('upperleg','upperleg'),('lowerleg','lowerleg'),('foot','foot'),('toe','foot'),
                                     ('upperarm','upperarm'),('lowerarm','lowerarm'),('wrist','lowerarm'),
                                     ('finger','lowerarm'),('metacarpal','lowerarm')):
                if bone.name.startswith(prefix): transform=transforms[category,side];break
        pose=transform@bone.bone.matrix_local;desired[bone.name]=pose
        if bone.parent:
            bone.matrix_basis=bone.bone.convert_local_to_pose(pose,bone.bone.matrix_local,
                parent_matrix=desired[bone.parent.name],parent_matrix_local=bone.parent.bone.matrix_local,invert=True)
        else: bone.matrix_basis=bone.bone.convert_local_to_pose(pose,bone.bone.matrix_local,invert=True)
    arm.location=loc(position);arm.rotation_euler.z=math.radians(yaw)
    arm['person_id']=pid;arm['standing_height_m']=height;arm['film_room']='R03'
    arm['pose_description']='Seated: horizontal thighs; vertical shins; bent elbows; official MakeHuman skin weights'
    arm['character_route']='MakeHuman core CC0; original volumetric cotton shirt and trousers'
    bpy.context.view_layer.update()
    return arm


def build_family():
    # Positions are centred on current, jittered chair seats, not obsolete blocking.
    people=[('P1',1.76,'asian-male-young.target',(4.925,.83,0),0,'B8B4A7'),
            ('P2',1.63,'asian-female-young.target',(5.775,2.32,0),180,'877975'),
            ('P3',1.12,'asian-male-child.target',(4.925,2.34,0),180,'AAA293')]
    result=[]
    for pid,height,target,pos,yaw,color in people:
        rig=build_person(pid,height,target,pos,yaw,color)
        result.append(dict(id=pid,height_m=height,position=list(pos),yaw_blender_deg=yaw,
                           route=rig['character_route'],mesh_vertices=sum(len(o.data.vertices) for o in rig.children if o.type=='MESH')))
    dump(OUT/'gates/A/characters.json',result)
    return result
