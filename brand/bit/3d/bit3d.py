import numpy as np, trimesh
from manifold3d import Manifold, CrossSection, FillRule
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
u=0.26; BASE=5.0
def X(x): return (x-300)*u
def Z(y): return (674-y)*u+BASE
def ycyl(r,length,yc,x,z,n=64):  # cylinder along y centred at yc
    return Manifold.cylinder(length,r,r,n,True).rotate([90,0,0]).translate([x,yc,z])
def rbox(x0,y0,x1,y1,depth,r,bev=1.5,yc=0.0):
    """rounded-rect (front view) prism with bevelled front/back edges"""
    xa,xb,za,zb=X(x0),X(x1),Z(y1),Z(y0); R=r*u
    parts=[]
    for (rr,L) in ((R,depth-2*bev),(R-bev,depth)):
        for cx in (xa+R,xb-R):
            for cz in (za+R,zb-R): parts.append(ycyl(rr,L,yc,cx,cz))
    return Manifold.batch_hull(parts)
def sphere(r,x,y,z,n=48): return Manifold.sphere(r,n).translate([x,y,z])
def capsule(p,q,r):
    return Manifold.batch_hull([sphere(r,*p),sphere(r,*q)])
def front_plate(cs, yface, t):
    """extrude a 2D CrossSection (in mm, x right / z up) out of a front face at y=yface by t mm"""
    return cs.extrude(t).rotate([90,0,0]).translate([0,yface,0])
def rrect2d(x0,y0,x1,y1,r):
    xa,xb,za,zb=X(x0),X(x1),Z(y1),Z(y0); R=r*u
    return CrossSection.square([xb-xa-2*R,zb-za-2*R]).translate([xa+R,za+R]).offset(R,join_type=__import__('manifold3d').JoinType.Round)
# depths (mm)
HD=46; BD=40
head=rbox(140,95,460,335,HD,52)
body=rbox(168,350,432,590,BD,60)
neck=rbox(272,318,328,362,24,4,bev=0.5)
legs=[rbox(250,580,290,650,12,12,bev=0.8), rbox(310,580,350,650,12,12,bev=0.8)]
feet=[rbox(225,640,305,674,26,17,bev=1.5,yc=-4), rbox(295,640,375,674,26,17,bev=1.5,yc=-4)]
ar=25*u
arm_l=capsule((X(190),0,Z(400)),(X(125),0,Z(500)),ar)
arm_r=capsule((X(410),0,Z(400)),(X(478),0,Z(300)),ar)
hands=[sphere(30*u,X(118),0,Z(515)), sphere(30*u,X(488),0,Z(280))]
stem=Manifold.cylinder(Z(48)-Z(98)+3,5*u*1.4,5*u*1.4,32).translate([0,0,Z(98)-3])
ball=sphere(15*u*1.3,0,0,Z(38))
base=Manifold.cylinder(BASE,48,48,128).translate([0,-3,0])
# screens (dark) proud of front faces
hface=-HD/2; bface=-BD/2
scr_h=front_plate(rrect2d(172,125,428,295,32),hface,1.6)
scr_b=front_plate(rrect2d(225,400,375,495,22),bface,1.6)
# face features (cyan) on head screen
eyes=rrect2d(222,170,266,228,12)+rrect2d(334,170,378,228,12)
t=np.linspace(0,1,40); P0,P1,P2=np.array([262,255]),np.array([300,282]),np.array([338,255])
pts=[(1-tt)**2*P0+2*(1-tt)*tt*P1+tt**2*P2 for tt in t]
circ=[CrossSection.circle(4.5*u,32).translate([X(p[0]),Z(p[1])]) for p in pts]
mouth=circ[0]
for a_,b_ in zip(circ,circ[1:]): mouth=mouth+CrossSection.batch_hull([a_,b_])
face=front_plate(eyes+mouth,hface-1.6,0.9)
# </> on chest screen
tp=TextPath((0,0),"</>",size=46*u,prop=FontProperties(family="DejaVu Sans Mono",weight="bold"))
polys=[p for p in tp.to_polygons() if len(p)>2]
txt=CrossSection([[tuple(v) for v in p] for p in polys],FillRule.EvenOdd)
bb=txt.bounds(); w=bb[2]-bb[0]; h=bb[3]-bb[1]
txt=txt.translate([-(bb[0]+w/2), Z(447)-(bb[1]+h/2)])
code=front_plate(txt,bface-1.6,0.9)
groups={
 "pink":  Manifold.batch_boolean([head,body,arm_l,arm_r]+feet,__import__('manifold3d').OpType.Add),
 "dark":  scr_h+scr_b+base,
 "cyan":  face+code+ball,
 "grey":  Manifold.batch_boolean([neck,stem]+legs+hands,__import__('manifold3d').OpType.Add),
}
# make groups non-overlapping: lower priority loses overlap
order=["cyan","dark","grey","pink"]
acc=None; final={}
for k in order:
    m=groups[k]
    if acc is not None: m=m-acc
    final[k]=m; acc=m if acc is None else acc+m
COL={"pink":[240,53,158,255],"dark":[30,33,50,255],"cyan":[0,240,255,255],"grey":[70,76,105,255]}
meshes={}
for k,m in final.items():
    mm=m.to_mesh(); tm=trimesh.Trimesh(vertices=mm.vert_properties[:,:3],faces=mm.tri_verts,process=True)
    tm.visual.face_colors=COL[k]; meshes[k]=tm
    tm.export(f"bit_{k}.stl")
whole=acc.to_mesh(); trimesh.Trimesh(whole.vert_properties[:,:3],whole.tri_verts).export("bit_single_colour.stl")
sc=trimesh.Scene(); [sc.add_geometry(m,node_name=f"Bit {k}",geom_name=f"Bit {k}") for k,m in meshes.items()]
sc.export("bit_multicolour.3mf")
b=acc.bounding_box(); print("bounds mm",[round(v,1) for v in b], "watertight",{k:meshes[k].is_watertight for k in meshes})
import pickle; pickle.dump({k:(m.vertices,m.faces,COL[k]) for k,m in meshes.items()},open("meshes.pkl","wb"))
