C=ROOM['R02']
# North counter is interrupted for the utility-balcony opening.
if ARGS.strict_plan:
    cabinet('Kitchen north base',.1,.1,3.3,.6,.86,mat='sage',drawers=True)
    box('Kitchen north quartz worktop',.09,.09,.86,3.32,.63,.037,'stone',.006)
else:
    cabinet('Kitchen sink cabinet',.1,.1,1.04,.6,.85,mat='sage')
    # Four countertop rails form a real opening around an inset bowl.
    for xx,yy,ww,dd in [(.09,.09,1.06,.1),(.09,.6,1.06,.12),(.09,.19,.18,.41),(.99,.19,.16,.41)]:
        box('Quartz / sink cutout',xx,yy,.85,ww,dd,.037,'stone',.005)
    cabinet('Kitchen right base',2.86,.1,.55,.6,.85,mat='sage',drawers=True)
    box('Right quartz top',2.85,.09,.85,.57,.63,.037,'stone',.006)
cabinet('Kitchen west base',.1,.72,.6,1.84,.85,face='e',mat='sage',drawers=True)
box('West quartz worktop',.09,.72,.85,.63,1.86,.037,'stone',.006)
basin(.63,.405,.767,.72,.43); faucet(.59,.20,.889)

# Gas hob, individual trivets, controls and hood.
box('Black glass gas hob',.16,1.44,.889,.50,.74,.016,'dark',.012)
for yy in (1.62,1.96):
    cyl('Gas burner',.41,yy,.906,.084,.014,'steel'); ring('Burner ports',(.41,yy,.923),.055,.011,'dark')
    for i in range(4):
        a=i*pi/2; rod('Cast iron pan support',(.41+cos(a)*.045,yy+sin(a)*.045,.941),(.41+cos(a)*.125,yy+sin(a)*.125,.941),.009,'dark')
for yy in (1.66,1.89): cyl('Hob dial',.615,yy,.91,.023,.020,'steel')
box('Brushed extractor hood',.10,1.43,1.65,.43,.78,.12,'steel',.02)
box('Extractor flue',.10,1.60,1.77,.23,.42,.67,'steel',.008)
for j in range(20): box('Extractor grille',.13+j*.016,1.50,1.646,.007,.59,.003,'dark',.001)
box('Extractor warm task strip',.49,1.50,1.648,.014,.58,.006,'warm',.001)
for yy in (.78,2.19):
    cabinet('West upper cabinet',.1,yy,.31,.38,.68,face='e',mat='white',base=.0)
    # Lift only this cabinet assembly from floor to upper wall.
    for o in list(C.objects):
        if o.name.startswith('West upper cabinet') and not o.get('lifted'):
            o.location.z+=1.55; o['lifted']=True
    box('Under cabinet light',.38,yy+.025,1.548,.012,.33,.008,'warm',.001)

box('Fridge body',2.86,2.45,.02,.68,.68,1.84,'white',.035)
for z,h in ((.06,.57),(.651,1.15)):
    box('Fridge door',2.86,2.42,z,.68,.038,h,'white',.022)
    rod('Fridge recessed handle',(3.36,2.401,z+.16),(3.36,2.401,z+h-.10),.009,'steel')
box('Fridge seal',2.867,2.415,.633,.666,.008,.012,'rubber',.001)
for i in range(3):
    o=box('Child drawing on fridge',2.98+i*.1,2.393,1.3-i*.13,.12,.001,.16,'paper',.001)
    sphere('Fridge magnet',3.035+i*.1,2.389,1.443-i*.13,.012,.005,.012,['rust','sage','brass'][i])

# Backsplash tile reveals, physically thin and individually grouted.
for j in range(5):
    for i in range(13):
        y=.13+i*.186
        if y<2.55: box('Kitchen vertical ceramic backsplash',.014,y,.89+j*.115,.016,.181,.110,'tile_warm',.001)
for yy in (1.05,1.17,1.31): bottle(.36,yy,.89,.16 if yy<1.2 else .23,'glass','Spice / oil')
bottle(.98,.40,.89,.17,'sage','Dishwashing liquid')
box('Dish sponge',1.02,.56,.89,.083,.05,.025,'green_fab',.007)
box('End grain cutting board',.24,2.28,.89,.32,.23,.018,'oak',.015)
rod('Knife handle',(.44,2.40,.92),(.56,2.40,.92),.012,'walnut')
box('Knife blade',.30,2.386,.918,.15,.028,.003,'steel',.004)
lathe('Saucepan',.41,1.96,.948,[(0,0),(.10,0),(.115,.09),(.11,.095),(.103,.014)],'steel')
rod('Saucepan handle',(.49,2.01,1.00),(.64,2.13,1.00),.019,'dark')
lathe('Utensil crock',3.17,.40,.89,[(0,0),(.061,0),(.061,.13),(.051,.13),(.049,.015)],'ceramic')
for i in range(4): rod('Wooden cooking utensil',(3.14+i*.019,.40,.93),(3.12+i*.026,.41,1.15+RNG.uniform(-.02,.03)),.009,'oak')

C=ROOM['R08']; vanity(.12,3.40,1.2,.52,'Master bath vanity'); toilet(1.55,3.38,'Master WC'); shower(2.45,3.38,1.05,1.25,'Master shower')
C=ROOM['R05']
if ARGS.strict_plan:
    vanity(8.53,.12,.96,.48,'Guest vanity'); toilet(8.72,.95,'Guest WC'); shower(8.55,2.05,.97,1.03,'Guest shower')
else:
    shower(8.55,.10,.96,.94,'Guest shower')
    toilet(9.06,1.13,'Guest WC'); vanity(8.55,1.29,.46,.46,'Guest vanity')
    box('Guest passage timber threshold',8.54,2.26,.019,1.04,.9,.013,'oak_light',.002,FLOORS)

for rid,x,y,w,d in [('R08',.03,3.33,3.55,1.40),('R05',8.54,.04,1.04,2.02 if not ARGS.strict_plan else 3.1)]:
    C=ROOM[rid]
    for j in range(7):
        z=.02+j*.31
        for i in range(math.ceil(w/.6)):
            xx=x+i*.6; zz=min(.306,2.2-z)
            collx=FLOORS if z+.306<=1.15 else UPFIX
            box(rid+' porcelain wall tile',xx,y,z,min(.594,w-i*.6),.012,zz,'tile_warm',.001,collx)
    # Towel rail and draped towel are near the vanity, reachable from basin.
    xx=x+.65 if rid=='R08' else x+.04
    yy=y+.69 if rid=='R08' else y+1.86
    rod(rid+' towel rail',(xx,yy,.85),(xx+.32,yy,.85),.01,'brass')
    o=blanket(rid+' hung hand towel',xx+.05,yy-.015,.85,.22,.40,'linen')
    # Rotate a folded textile surface into a hanging towel.
    # Cloth is generated flat around global origin, so convert vertices directly.
    for v in o.data.vertices:
        py=-v.co.y; t=(py-(yy-.015))/.4; v.co.y=-yy-.012*sin(t*pi); v.co.z=.85-t*.39
    bottle(x+.10,y+.61,.03,.25,'white','Bathroom waste bin liner')

C=ROOM['R01']
box('Washing machine cabinet',.25,-1.05,.025,.60,.62,.82,'white',.025)
box('Washer top lid',.24,-1.06,.845,.62,.64,.025,'white',.012)
ring('Washer chrome door',(.55,-.416,.43),.203,.027,'steel','y')
ring('Washer rubber seal',(.55,-.398,.43),.166,.020,'rubber','y')
sphere('Washer smoked glass',.55,-.384,.43,.153,.02,.153,'screen')
rod('Washer selector',(.35,-.413,.735),(.35,-.387,.735),.032,'steel')
box('Washer LCD',.55,-.410,.701,.16,.008,.06,'screen',.003)
for i in range(4): box('Washer control button',.56+i*.038,-.418,.69,.021,.005,.006,'steel',.001)
box('Utility sink pedestal',1.05,-1.05,.04,.50,.45,.48,'ceramic',.045)
basin(1.30,-.825,.48,.49,.43); faucet(1.30,-1.008,.60)
bottle(.71,-.83,.873,.24,'sage','Laundry detergent')
rod('Mop shaft',(1.69,-.95,.08),(1.78,-.99,1.38),.013,'steel')
box('Mop head',1.58,-1.04,.035,.25,.16,.045,'linen',.012)

print('Kitchen and bathrooms complete',len(bpy.data.objects),flush=True)
