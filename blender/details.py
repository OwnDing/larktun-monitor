C=DETAIL
def panel(x,y,z,axis='x',socket=False):
    # axis x means attached to an east/west wall, facing west.
    before=set(C.objects)
    box('Outlet plate' if socket else 'Switch plate',-.043,-.008,-.043,.086,.008,.086,'white',.004)
    if socket:
        for xx,zz,ang in [(-.019,.012,-25),(.019,.012,25),(0,-.02,0)]:
            o=box('Recessed socket aperture',xx-.002,-.010,zz-.009,.004,.002,.017,'dark',.001)
            o.rotation_euler.y=math.radians(ang)
    else:
        for xx in (-.034,.003): box('Rocker switch',xx,-.012,-.03,.031,.004,.06,'white',.002)
        box('Switch locator mark',-.022,-.014,-.017,.008,.001,.002,'ink',0)
    obs=set(C.objects)-before
    if axis=='x': rotate_group(obs,(0,0,0),-90)
    if axis=='X': rotate_group(obs,(0,0,0),90)
    if axis=='Y': rotate_group(obs,(0,0,0),180)
    for o in obs: o.location+=loc((x,y,z)); o['detail_type']='socket' if socket else 'switch'

# One or more real fittings in every enclosed room, with low sockets beside furniture.
for x,y,z,a in [(3.735,4.60,1.06,'X'),(3.735,7.50,.30,'X'),(8.384,6.8,.30,'x'),(6.88,2.45,1.06,'x'),
                 (3.735,2.84,1.06,'X'),(.015,2.75,1.06,'X'),(.015,1.10,1.18,'X'),(8.384,1.80,1.06,'x'),
                 (3.584,6.2,1.06,'x'),(.015,7.26,.70,'X'),(2.93,4.934,.70,'Y'),
                 (9.735,2.12,1.06,'X'),(11.6,.015,.92,'Y'),(12.9,3.334,.32,'Y'),
                 (9.735,5.0,1.06,'X'),(12.85,4.934,.7,'Y'),(10.73,8.585,.32,'y'),
                 (8.384,4.80,1.06,'x'),(.30,3.334,1.12,'Y'),(8.535,1.78,1.05,'X'),(.13,-1.284,1.05,'Y')]:
    panel(x,y,z,a,socket=z<.95 or z>1.15)

def curtain(o):
    x,y,w=o['x'],o['y'],o['width']; horizontal=o['axis']=='h'
    south=y>8; east=x>13; west=x<0
    # Place curtains on the room side of the window/wall.
    if horizontal: y=y+(.19 if y<0 else -.13)
    else: x=x+(.22 if west else -.22)
    def point(s,t,z): return (x+s,y+t,z) if horizontal else (x+t,y+s,z)
    rod('Curtain rod',point(-.17,0,2.53),point(w+.17,0,2.53),.015,'brass',collection=UPFIX)
    for s in (-.19,w+.19): sphere('Curtain rod finial',*point(s,0,2.53),.025,.025,.025,'brass',UPFIX)
    for side in (0,1):
        start=-.08 if side==0 else w-.24
        for zb,zt,collc in [(.12,1.15,GLAZE),(1.15,2.48,CUTFRAMEUP),(.12,2.48,FULLFRAME)]:
            verts=[]; faces=[]; nu,nv=32,26
            for j in range(nv+1):
                v=j/nv; z=zb+v*(zt-zb)
                for i in range(nu+1):
                    u=i/nu; flare=.015*(2.5-z)*sin(pi*u)
                    s=start+u*.33+flare
                    dep=.045*sin(u*10*pi)+.007*sin(z*5+u*14)
                    verts.append(point(s,dep,z+.009*cos(u*13*pi)*(2.5-z)/2.5))
            for j in range(nv):
                for i in range(nu): faces.append((j*(nu+1)+i,j*(nu+1)+i+1,(j+1)*(nu+1)+i+1,(j+1)*(nu+1)+i))
            cloth=mesh('Pleated linen curtain',verts,faces,'sheer',collc,True)
            thick=cloth.modifiers.new('Hemmed linen thickness','SOLIDIFY'); thick.thickness=.002
        for i in range(8):
            p=point(start+i*.046,0,2.50)
            ring('Curtain eyelet',p,.023,.0028,'brass','x' if horizontal else 'y',UPFIX)

for o in L['windows']:
    if o['name']=='书房东窗':
        # Recess-mounted roller blind sits behind the bookcase, not through it.
        rod('Study east roller-blind barrel',(13.30,1.08,2.43),(13.30,2.52,2.43),.025,'linen',collection=UPFIX)
        box('Study east recessed blind',13.295,1.10,1.02,.003,1.40,1.38,'linen',.001,UPFIX)
    elif any(a in o['name'] for a in ('卧','儿童','书房','餐厅')): curtain(o)
curtain(dict(x=4.35,y=8.6,width=3.4,axis='h'))

def shirt(x,y,z,w=.40,h=.56,mat='blue',name='Laundry shirt'):
    verts=[]; nu,nv=24,30
    for j in range(nv+1):
        v=j/nv; width=w*(.94 if v<.18 else (1.48 if v<.38 else .80))
        for i in range(nu+1):
            u=i/nu; xx=x+(u-.5)*width
            zz=z-v*h
            if v<.12: zz-=.055*sin(pi*u)**7*(1-v/.12)
            verts.append((xx,y+.016*sin(u*8*pi+v*4)+.012*sin(v*13),zz))
    faces=[(j*(nu+1)+i,j*(nu+1)+i+1,(j+1)*(nu+1)+i+1,(j+1)*(nu+1)+i) for j in range(nv) for i in range(nu)]
    ob=mesh(name,verts,faces,mat,smooth=True); so=ob.modifiers.new('Fabric thickness','SOLIDIFY'); so.thickness=.003
    curve(name+' lower hem',[(x+(i/24-.5)*w*.80,y+.017*sin(i/24*8*pi+4),z-h) for i in range(25)],.002,mat)

for y,x,w in [(-1.05,2.04,1.37),(9.9,6.3,1.6)]:
    rod('Laundry rail',(x,y,2.15),(x+w,y,2.15),.012,'steel')
    for xx in (x,x+w): rod('Laundry suspension',(xx,y,2.15),(xx,y,2.75),.005,'steel',collection=UPFIX)
    for i in range(3):
        xx=x+.22+i*.44
        curve('Wire clothes hanger',[(xx-.16,y,1.99),(xx,y,2.10),(xx+.16,y,1.99),(xx-.16,y,1.99)],.003,'steel')
        curve('Hanger hook',[(xx,y,2.10),(xx,y,2.18),(xx+.024,y,2.19),(xx+.033,y,2.16)],.003,'steel')
        shirt(xx,y,2.015,.30,.43,['linen','blue','rust'][i])

# Dining pendant: ribbed ceramic shade, cable and ceiling rose.
cyl('Pendant ceiling rose',5.3,1.57,2.73,.065,.04,'brass',collection=UPFIX)
rod('Pendant fabric cable',(5.3,1.57,2.26),(5.3,1.57,2.74),.003,'dark',collection=UPFIX)
lathe('Dining fluted pendant',5.3,1.57,2.04,[(.27,0),(.268,.022),(.20,.17),(.06,.23),(.04,.24)],'ceramic',collection=UPFIX)
for i in range(48):
    a=i*2*pi/48
    curve('Pendant fine ceramic flute',[(5.3+cos(a)*.27,1.57+sin(a)*.27,2.053),(5.3+cos(a)*.2,1.57+sin(a)*.2,2.21),(5.3+cos(a)*.065,1.57+sin(a)*.065,2.27)],.0018,'ceramic',collection=UPFIX)
cyl('Pendant opal diffuser',5.3,1.57,2.035,.20,.014,'warm',collection=UPFIX)

# Four non-identical settings, serving bowl, bills and little traces of daily use.
for xx,yy in [(4.94,1.34),(5.65,1.34),(4.94,1.80),(5.65,1.80)]:
    ob=box('Woven placemat',xx-.22,yy-.17,.751,.44,.32,.003,'linen',.015); ob.rotation_euler.z=RNG.uniform(-.07,.07)
    lathe('Porcelain dinner plate',xx,yy,.756,[(0,0),(.083,.003),(.12,.02),(.127,.018),(.122,.012),(.084,-.001)],'ceramic')
    rod('Table fork handle',(xx-.158,yy-.08,.763),(xx-.158,yy+.042,.763),.004,'steel')
    for i in range(4): rod('Fork tine',(xx-.167+i*.006,yy+.04,.763),(xx-.167+i*.006,yy+.075,.763),.0015,'steel')
    rod('Table knife handle',(xx+.159,yy-.08,.763),(xx+.159,yy+.075,.763),.004,'steel')
cup(5.94,1.78,.757,'sage','Dining tea cup')
lathe('Fruit bowl',5.31,1.58,.753,[(0,0),(.045,.003),(.13,.08),(.127,.09),(.11,.065),(.03,.008)],'oak')
for xx,yy,z in [(5.28,1.57,.826),(5.35,1.6,.825),(5.31,1.54,.87)]: sphere('Mandarin orange',xx,yy,z,.037,.039,.034,'terracotta')

# Living coffee table: remote, water cup, phone, book and paper with fine printed rules.
book(5.23,5.77,.404,.30,.23,.031,'sage','Living art book',-7)
box('Phone rounded body',5.37,6.25,.405,.077,.155,.009,'dark',.008)
box('Phone screen',5.374,6.254,.415,.069,.141,.001,'screen',.006)
box('Phone earpiece',5.404,6.388,.416,.021,.002,.001,'steel',.001)
cup(5.56,5.68,.404,'ceramic','Living mug')
box('Remote control',5.59,6.48,.405,.042,.16,.015,'dark',.009)
for i in range(6):
    for j in range(2): sphere('Remote button',5.602+j*.016,6.502+i*.02,.421,.0037,.005,.002,'steel')
box('Casual folded bill',5.22,6.06,.405,.14,.20,.001,'paper',.0005)
for j in range(11): box('Bill printed rule',5.232,6.082+j*.013,.406,.096 if j%3 else .071,.001,.0002,'ink',0)

# Desk equipment, task lamp and mixed books.
box('Computer display housing',10.57,.29,.91,.66,.031,.385,'dark',.01)
box('Computer screen',10.584,.324,.925,.632,.003,.355,'screen',.004)
rod('Monitor stand',(10.90,.307,.76),(10.90,.307,.92),.023,'steel')
box('Monitor stand base',10.78,.22,.755,.24,.22,.014,'steel',.012)
box('Keyboard',10.62,.60,.755,.46,.135,.014,'white',.01)
for i in range(14):
    for j in range(4): box('Keyboard key',10.631+i*.031,.61+j*.030,.770,.026,.024,.004,'white',.002)
sphere('Desk mouse',11.28,.66,.78,.029,.050,.019,'white')
lamp(11.66,.31,.753,.45,.12,'Study task lamp'); cup(10.41,.65,.754,'sage','Desk mug')
book(11.31,.30,.755,.18,.24,.023,'rust','Study notebook',7)
plant(6.64,.89,.85,.28,'Sideboard plant')
for i in range(3): book(6.49,1.5,.855+i*.035,.25,.23,.032,name='Sideboard book',angle=3-i*4)

# Bedside lights, cosmetics, slippers and toys are deliberately a little irregular.
lamp(.54 if ARGS.strict_plan else .38,5.20 if ARGS.strict_plan else 7.26,.553,.38,.11,'Bedside lamp'); lamp(12.86,5.23,.502,.32,.10,'Child night lamp')
book(2.76,5.08,.555,.15,.21,.025,'sage','Bedside reading',-9)
cup(2.99,5.30,.554,'white','Bedside water')
for i in range(3): bottle(.28+i*.16,7.78,.786,.08+i*.025,['glass','terracotta','white'][i],'Dressing cosmetics')
for x,y,a in [(7.50,1.89,10),(7.73,1.98,-15),(2.40,7.35,8),(2.64,7.32,-7)]:
    before=set(C.objects)
    shoe=sphere('Soft house slipper sole',x,y,.045,.05,.126,.023,'linen')
    toe=sphere('House slipper upper',x,y-.041,.078,.051,.075,.040,'green_fab')
    rotate_group(set(C.objects)-before,(x,y,0),a)
for i in range(11):
    x=10.45+RNG.random()*1.4; y=7.02+RNG.random()*.51
    o=box('Scattered wooden toy block',x,y,.025,.075,.075,.071,['rust','sage','blue','oak_light'][i%4],.005)
    o.rotation_euler.z=RNG.uniform(0,pi)
for j in range(3):
    box('Toy train carriage',11.46+j*.17,7.57,.07,.14,.085,.075,['oak','sage','rust'][j],.012)
    for xx in (11.49+j*.17,11.57+j*.17):
        for yy in (7.565,7.665): rod('Toy train wheel',(xx,yy,.066),(xx,yy+.012,.066),.026,'dark')
book(10.0,8.00,.724,.24,.18,.018,'rust','Child workbook',7)
cyl('Pencil cup',10.74,8.27,.725,.036,.083,'ceramic')
for i in range(6): rod('Colored pencil',(10.72+RNG.random()*.04,8.26,.75),(10.72+RNG.random()*.04,8.27,.89),.003,['rust','sage','blue'][i%3])
plant(9.25,8.08,.853,.32,'Corridor vase greenery')
shirt(4.23,7.155 if ARGS.strict_plan else 8.03,.70,.48,.53,'blue','Shirt casually draped on sofa arm')

print('Hardware and lived-in detail complete',len(bpy.data.objects),flush=True)
