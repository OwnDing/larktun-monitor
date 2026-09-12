# Detailed room furniture; exec in build_home namespace.
def sofa(x,y,w,d,name='Sofa',mat='blue',single=False):
    for xx in (.10,w-.10):
        for yy in (.14,d-.14): cyl(name+' turned foot',x+xx,y+yy,.018,.027,.14,'walnut')
    box(name+' lower upholstery',x,y,.15,w,d,.19,mat,.045)
    box(name+' back shell',x,y,.28,.16,d,.57,mat,.07)
    for yy in (y,y+d-.13): box(name+' softened arm',x+.03,yy,.3,w-.03,.13,.34,mat,.025)
    count=1 if single else max(2,round(d/.79))
    for i in range(count):
        sy=(d-.28)/count; cy=y+.14+sy*(i+.5)
        pillow(name+' separate seat cushion',x+w*.59,cy,.445,w-.20,sy-.023,.21,mat)
        pillow(name+' soft back cushion',x+.225,cy,.725,.22,sy-.035,.40,mat,(0,-7,0))
    pillow(name+' informal rust pillow',x+.48,y+.43,.73,.20,.39,.39,'rust',(9,-14,7))
    if not single:
        pillow(name+' linen pillow',x+.48,y+d-.5,.69,.19,.42,.34,'linen',(-9,-13,-9))
        blanket(name+' draped throw',x+.27,y+d-.29,.66,w-.1,.33,'cream_fab')

def shelf(x,y,w,d,h,name='Open shelving',face='w'):
    box(name+' back',x+w-.028,y,.07,.025,d,h-.07,'oak_light',.003)
    for yy in (y,y+d-.025): box(name+' side',x,yy,.07,w,.025,h-.07,'oak_light',.003)
    levels=[.08,.48,.83,1.10,1.53,1.99]
    for zz in levels:
        if zz<h: box(name+' shelf',x,y,zz,w,d,.025,'oak_light',.002)
    for level in (.11,.51,1.56):
        for group in range(3):
            yy=y+.07+group*.58
            for i in range(RNG.randint(4,7)):
                width=RNG.uniform(.025,.055); height=RNG.uniform(.18,.29)
                if yy+width<y+d-.08:
                    mat=RNG.choice(['rust','sage','blue','linen','walnut'])
                    box(name+' book pages',x+.05,yy,level,.23,width,height,'paper',.001)
                    box(name+' book spine',x+.038,yy-.002,level,.017,width+.004,height,mat,.002)
                    for zstripe in (.03,height-.03): box(name+' foil spine rule',x+.036,yy+.006,level+zstripe,.002,width-.012,.003,'brass',0)
                yy+=width+.007
    book(x+.04,y+.75,.86,.25,.20,.033,'sage','Horizontal book',3)
    book(x+.055,y+.735,.895,.23,.22,.027,'rust','Horizontal book',-4)

def toilet(x,y,name='Toilet'):
    box(name+' cistern',x,y,.32,.40,.18,.40,'ceramic',.06)
    cyl(name+' dual flush',x+.2,y+.07,.724,.022,.003,'chrome')
    sphere(name+' pedestal',x+.20,y+.36,.19,.145,.235,.18,'ceramic')
    profile=[(.10,.20),(.16,.28),(.205,.385),(.201,.412),(.171,.421),(.151,.39),(.10,.292),(.025,.28),(0,.28)]
    verts=[]; n=64
    for r,z in profile:
        for i in range(n):
            a=2*pi*i/n; verts.append((x+.2+r*cos(a),y+.36+r*1.35*sin(a),z))
    faces=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(profile)-1) for i in range(n)]
    mesh(name+' hollow glazed bowl',verts,faces,'ceramic',smooth=True)
    curve(name+' oval seat',[(x+.20+.18*cos(i*pi/32),y+.37+.18*1.38*sin(i*pi/32),.435) for i in range(64)],.025,'ceramic',True)
    cyl(name+' water in trap',x+.2,y+.36,.294,.062,.003,'screen')
    lid=box(name+' raised lid',x+.025,y+.14,.435,.35,.041,.34,'ceramic',.055)
    rod(name+' water supply',(x+.07,y+.05,.16),(x+.07,y+.05,.37),.009,'chrome')

def shower(x,y,w,d,name='Shower'):
    box(name+' stone tray',x,y,.018,w,d,.042,'stone',.01)
    for xx in (x,x+w-.012): box(name+' glass side',xx,y,.06,.010,d,1.97,'glass',.001)
    box(name+' sliding glass',x,y+d-.012,.06,w,.010,1.97,'glass',.001)
    for xx in (x,x+w): rod(name+' slim upright',(xx,y+d,0.06),(xx,y+d,2.03),.008,'chrome')
    rod(name+' top channel',(x,y+d,2.03),(x+w,y+d,2.03),.011,'chrome')
    rod(name+' handle',(x+w*.55,y+d+.03,.94),(x+w*.55,y+d+.03,1.17),.009,'chrome')
    cx=x+w*.67
    curve(name+' shower riser',[(cx,y+.065,.84),(cx,y+.065,1.94),(cx,y+.33,1.94)],.012,'chrome')
    cyl(name+' rain head',cx,y+.33,1.91,.105,.024,'chrome')
    for i in range(5):
        for j in range(5):
            if (i-2)**2+(j-2)**2<6: cyl(name+' nozzle',cx+(i-2)*.03,y+.33+(j-2)*.03,1.907,.003,.004,'rubber')
    rod(name+' mixer',(cx-.13,y+.08,.92),(cx+.13,y+.08,.92),.022,'chrome')
    curve(name+' flexible hose',[(cx-.1,y+.1,.92),(cx-.18,y+.11,.5),(cx+.05,y+.11,.43),(cx+.15,y+.1,1.24)],.009,'steel')
    box(name+' linear drain',x+.10,y+d-.17,.061,w-.2,.038,.004,'steel',.003)
    for i in range(int((w-.22)/.018)): box(name+' drain slots',x+.12+i*.018,y+d-.165,.066,.005,.022,.001,'dark',0)
    box(name+' soap shelf',x+.07,y+.03,1.12,.24,.13,.022,'stone',.006)
    bottle(x+.13,y+.09,1.145,.17,'sage','Shampoo'); bottle(x+.25,y+.09,1.145,.14,'white','Body wash')

def vanity(x,y,w,d=.5,name='Vanity'):
    cabinet(name,x,y,w,d,.79,mat='oak_light',base=.21,drawers=True)
    box(name+' quartz top',x-.012,y-.008,.79,w+.024,d+.022,.036,'stone',.008)
    basin(x+w*.53,y+d*.57,.815,min(.56,w*.87),d*.78)
    faucet(x+w*.51,y+.055,.83)
    box(name+' brass mirror rim',x+.055,y+.015,1.13,w-.11,.035,.68,'brass',.015)
    box(name+' actual mirror',x+.066,y+.055,1.141,w-.132,.004,.658,'mirror',.012)
    bottle(x+.06,y+d-.08,.83,.13,'sage','Hand soap')

for f in L['furniture']:
    rid=f['room']; C=ROOM[rid]
    x,y,w,d,h=f['x'],f['y'],f['w'],f['d'],f['h']; name=rid+' · '+f['name']; sym=f['symbol']
    if not ARGS.strict_plan:
        if rid=='R07' and sym=='sofa': y=5.93; d=2.18
        if rid=='R07' and f['name']=='边几': x=4.85; y=5.02
        if rid=='R07' and sym=='lamp': y=4.30; x=3.80
        if rid=='R09' and sym=='wardrobe': y=5.92; d=2.35
        if rid=='R09' and f['name']=='床头柜 L': x=.14; y=7.05
        if rid=='R09' and f['name']=='床头柜 R': w=.28
        if rid=='R12' and sym=='chair': x=10.55; y=7.23
        if rid=='R04' and sym=='mirror': y=1.18
    # Wet-room and kitchen appliances are built as functioning assemblies below.
    if rid in ('R01','R02','R05','R08'): continue
    if sym in ('sofa','sofabed'):
        if rid=='R06' and not ARGS.strict_plan:
            before=set(C.objects); sofa(11.05,1.69,.92,1.92,name)
            rotate_group(set(C.objects)-before,(11.51,2.65,0),-90)
        else: sofa(x,y,w,d,name)
    elif sym=='armchair':
        before=set(C.objects); sofa(x,y,w,d,name,'green_fab',True); rotate_group(set(C.objects)-before,(x+w/2,y+d/2,0),-88)
    elif sym=='table': table(name,x,y,w,d,h,'walnut' if h<.6 else 'oak',h<.6)
    elif sym=='chair':
        if rid=='R13':
            for xx in (x,x+.78): chair(xx,y,.52,.52,.79,-8 if xx==x else 4,name,'linen')
        else:
            angle=(180 if rid=='R03' and y>1.5 else 0)+RNG.choice([-9,6,10,-5])
            if rid=='R06': angle=180
            if rid=='R12': angle=0
            chair(x,y,w,d,h,angle,name,'green_fab' if rid=='R12' else 'linen')
    elif sym=='bed': bed(x,y,w,d,name,rid=='R12')
    elif sym in ('wardrobe','cabinet','nightstand','bench'):
        face='s'
        if d>w: face='e' if rid in ('R04','R12') else 'w'
        if rid=='R09' and sym=='wardrobe' and not ARGS.strict_plan: w=.49
        cabinet(name,x,y,w,d,h,face,mat='oak_light',drawers=sym=='nightstand')
        if sym=='bench': pillow(name+' cushion',x+w/2,y+d/2,h+.027,w-.018,d-.02,.065,'linen')
    elif sym=='shelf':
        if rid=='R06': shelf(x,y,w,d,h,name)
        else:
            box(name+' backing',x,y,.03,w,.025,h,'oak_light',.003)
            for xx in (x,x+w-.025): box(name+' side',xx,y,.03,.025,d,h,'oak_light',.003)
            for zz in (.03,.34,.65,.95): box(name+' tier',x,y,zz,w,d,.025,'oak_light',.003)
            for i in range(3): box(name+' fabric bin',x+.03+i*.23,y+.04,.07,.20,d-.05,.22,['rust','sage','linen'][i],.013)
            for i in range(7): box(name+' uneven book',x+.05+i*.07,y+.03,.68,.047,.23,RNG.uniform(.13,.23),RNG.choice(['sage','rust','blue','linen']),.002)
    elif sym=='desk':
        table(name,x,y,w,d,h,'oak_light'); cabinet(name+' drawer pedestal',x+.02,y+.035,.30,d-.065,h-.08,drawers=True)
    elif sym=='rug': rug(x,y,w,d,name,angle=2 if rid=='R07' else -3)
    elif sym=='lamp':
        if rid=='R06' and not ARGS.strict_plan: x=12.45; y=2.67
        if rid!='R03': lamp(x+w/2,y+d/2,0,h,.17,name)
    elif sym=='tv':
        box(name+' slim housing',x-.01,y,.86,.036,d,.85,'dark',.017)
        box(name+' reflective screen',x-.017,y+.017,.881,.004,d-.034,.81,'screen',.01)
        box(name+' status diode',x-.024,y+d/2,.865,.002,.01,.003,'led',0)
        for yy in (y+.25,y+d-.25): rod(name+' bracket',(x+.018,yy,1.1),(8.395,yy,1.1),.013,'dark')
    elif sym=='plant': plant(x+w/2,y+d/2,0,h/1.0,name)
    elif sym=='mirror':
        box(name+' rim',x,y,.16,w,d,h,'brass',.016)
        box(name+' reflection',x-.003,y+.025,.185,.004,d-.05,h-.05,'mirror',.008)
    elif sym=='box':
        if rid=='R11':
            box(name+' suitcase',x,y,.07,w,d,h-.1,'sage',.06)
            for i in range(8): box(name+' luggage rib',x+.045+i*.062,y+d+.001,.14,.02,.015,h-.28,'sage',.006)
            for xx in (x+.07,x+w-.07): sphere(name+' wheel',xx,y+d-.08,.063,.035,.025,.04,'rubber')
            curve(name+' carry handle',[(x+w*.3,y+.2,h),(x+w*.3,y+.2,h+.08),(x+w*.7,y+.2,h+.08),(x+w*.7,y+.2,h)],.014,'dark')
        else:
            lathe(name+' woven basket',x+w/2,y+d/2,.025,[(.17,0),(.22,h),(.21,h),(.16,.035)],'linen')
            for zz in range(15): ring(name+' basket weave',(x+w/2,y+d/2,.035+zz*.021),.17+.05*zz/15,.0025,'oak_light')

print('Room furniture complete',len(bpy.data.objects),flush=True)
