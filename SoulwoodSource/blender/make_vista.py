"""Author original Soulwood forest and fortress meshes in Blender 5.x."""
import bpy
import math
import os
import random
from mathutils import Vector

random.seed(91625)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Blender's Text Editor can report the open .blend as a pseudo parent of __file__.
OUT = os.path.join(SCRIPT_DIR, 'generated') if os.path.isdir(SCRIPT_DIR) else 'C:/generated'
os.makedirs(OUT, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, color, roughness=.88, metal=0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=roughness
    bs.inputs['Metallic'].default_value=metal
    return m

bark=material('SW_Beech_bark_silver',(.27,.25,.21))
bark_dark=material('SW_Beech_bark_crevice',(.10,.09,.07))
leaves=[material('SW_Leaves_deep_green',(.035,.085,.028)),
        material('SW_Leaves_oak_olive',(.075,.135,.037)),
        material('SW_Leaves_mid_green',(.12,.18,.055)),
        material('SW_Leaves_sun_glint',(.25,.29,.09))]
limestone=material('SW_Limestone_weathered',(.28,.275,.24))
shadow=material('SW_Limestone_shaded',(.13,.145,.14))
roof=material('SW_Slate_roof',(.075,.095,.115))
gold=material('SW_Gilded_details',(.35,.25,.075),.48,.58)

def mesh(name, vertices, faces, mats, indices=None):
    data=bpy.data.meshes.new(name)
    data.from_pydata(vertices,[],faces)
    data.update()
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    for m in mats:data.materials.append(m)
    if indices:
        for polygon,i in zip(data.polygons,indices):polygon.material_index=i
    for polygon in data.polygons:polygon.use_smooth=True
    return obj

def exporter(name,objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,name+'.fbx'),use_selection=True,
        object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,
        bake_anim=False)

def segment(vertices,faces,indices,start,end,r0,r1,mat=0,sides=9):
    a,b=Vector(start),Vector(end)
    direction=(b-a).normalized()
    u=direction.cross(Vector((0,0,1)))
    if u.length<.05:u=Vector((1,0,0))
    u.normalize();v=direction.cross(u).normalized()
    start_index=len(vertices)
    for center,radius in ((a,r0),(b,r1)):
        for i in range(sides):
            angle=math.tau*i/sides
            wobble=1+.11*math.sin(i*2.7+center.z*.8)
            vertices.append(tuple(center+radius*wobble*(u*math.cos(angle)+v*math.sin(angle))))
    for i in range(sides):
        faces.append((start_index+i,start_index+(i+1)%sides,start_index+sides+(i+1)%sides,start_index+sides+i))
        indices.append(mat)

def leaf(vertices,faces,indices,center,length,angle,mat):
    p=Vector(center)
    tangent=Vector((math.cos(angle),math.sin(angle),random.uniform(-.3,.48))).normalized()
    sideways=Vector((-tangent.y,tangent.x,random.uniform(-.15,.15))).normalized()
    width=length*random.uniform(.34,.48)
    q=len(vertices)
    vertices.extend([tuple(p-tangent*length*.52),tuple(p-sideways*width),
                     tuple(p+tangent*length*.50+Vector((0,0,.025))),tuple(p+sideways*width)])
    faces.extend([(q,q+1,q+2,q+3),(q+3,q+2,q+1,q)])
    indices.extend([mat,mat])

def beech_variant(seed,height):
    random.seed(seed)
    verts=[];faces=[];inds=[];clusters=[]
    trunk=[(0,0,0),(.06,.04,.8),(.13,.10,2.1),(.17,.05,4.2),(.03,.17,6.5),(-.11,.17,height)]
    for i in range(len(trunk)-1):
        segment(verts,faces,inds,trunk[i],trunk[i+1],.63*(1-i/6)+.07,.63*(1-(i+1)/6)+.05,i%3==0 and 1 or 0,13)
    for i in range(9):
        a=i*math.tau/9
        segment(verts,faces,inds,(0,0,.5),(math.cos(a)*1.7,math.sin(a)*1.7,.06),.27,.025,0,8)
    for i in range(48):
        az=i*2.39996323+random.uniform(-.18,.18)
        z=2.8+(i%16)*.38+random.uniform(-.20,.20)
        radius=(1.25+random.random()*1.6)*(1-.28*z/height)
        base=Vector((.06*math.sin(z),.06*math.cos(z),z))
        elbow=base+Vector((math.cos(az)*radius*.54,math.sin(az)*radius*.54,.3))
        tip=base+Vector((math.cos(az)*radius,math.sin(az)*radius,.85))
        segment(verts,faces,inds,base,elbow,.19,.08,0,7)
        segment(verts,faces,inds,elbow,tip,.08,.017,0,6)
        for j in range(4):
            direction=az+(j-1.5)*.48
            end=tip+Vector((math.cos(direction)*(.35+j*.12),math.sin(direction)*(.35+j*.12),.15+j*.08))
            segment(verts,faces,inds,tip,end,.025,.005,0,5)
            clusters.append((end,Vector((.58,.53,.38))))
    for _ in range(7600):
        center,extent=random.choice(clusters)
        direction=Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(-1,1))).normalized()
        p=center+Vector((direction.x*extent.x,direction.y*extent.y,direction.z*extent.z))
        leaf(verts,faces,inds,p,random.uniform(.10,.23),random.random()*math.tau,random.choices((2,3,4,5),(2,6,5,1))[0])
    obj=mesh('Soulwood_beech_geometry',verts,faces,[bark,bark_dark]+leaves,inds)
    exporter('SM_VistaBeech_'+str(seed),[obj])
    bpy.data.objects.remove(obj,do_unlink=True)

def box(objects,name,loc,dimensions,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    obj=bpy.context.object;obj.name=name
    obj.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod=obj.modifiers.new('Eroded stone edges','BEVEL');mod.width=bevel;mod.segments=2
        bpy.context.view_layer.objects.active=obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        mod=obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
        bpy.ops.object.modifier_apply(modifier=mod.name)
    objects.append(obj)
    return obj

def spire(objects,name,loc,radius,height,sides=8,mat=roof):
    bpy.ops.mesh.primitive_cone_add(vertices=sides,radius1=radius,radius2=.05,depth=height,location=loc)
    obj=bpy.context.object;obj.name=name;obj.data.materials.append(mat);objects.append(obj)
    return obj

def cylinder(objects,name,loc,radius,height,sides=12,mat=limestone):
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides,radius=radius,depth=height,location=loc)
    obj=bpy.context.object;obj.name=name;obj.data.materials.append(mat);objects.append(obj)
    return obj

beech_variant(2041,10.8)
beech_variant(2049,11.5)

# One architectural mesh gives the distant objective a readable Gothic silhouette.
objects=[]
box(objects,'Fortress_lower_mass',(0,0,12),(45,36,24),limestone,1.0)
box(objects,'Great_hall',(0,0,30),(27,22,37),limestone,.75)
box(objects,'Central_keep',(0,0,48),(16,16,40),limestone,.65)
spire(objects,'Great_keep_roof',(0,0,76),11,22,8)
for x,y in ((-19,-15),(19,-15),(-19,15),(19,15)):
    cylinder(objects,'Octagonal_watchtower',(x,y,27),5.2,54,10)
    cylinder(objects,'Tower_cornice',(x,y,54.5),6.0,2.0,10)
    spire(objects,'Tower_slate_spire',(x,y,63),6.0,16,10)
    for j in range(10):
        a=j*math.tau/10
        box(objects,'Crenellation',(x+math.cos(a)*5,y+math.sin(a)*5,55.8),(1.4,1.4,2.7),limestone,.10)
for x,y in ((-10,-8),(10,-8),(-10,8),(10,8)):
    cylinder(objects,'Narrow_stair_turret',(x,y,38),2.2,76,8)
    spire(objects,'Turret_needle',(x,y,82),2.7,14,8)
for side in (-1,1):
    for k in range(7):
        x=-17+k*5.7
        box(objects,'Parapet_merlon',(x,side*18,25.2),(2.0,2.2,3.2),limestone,.12)
        box(objects,'Hall_window_shaft',(x*.65,side*11.1,29),(1.0,.13,7.5),shadow,.08)
        spire(objects,'Pointed_window_head',(x*.65,side*11.15,33.8),.65,2.3,4,shadow)
for x in (-21,21):
    for k in range(5):
        y=-11+k*5.5
        box(objects,'End_merlon',(x,y,25.2),(2.2,2.0,3.0),limestone,.12)
for z in (29,37,45,53,61):
    for side in (-1,1):
        box(objects,'Keep_arrow_slit',(side*8.1,0,z),(.15,.7,3.4),shadow,.03)
box(objects,'Front_gate_shadow',(0,-18.2,6),(6,.18,11),shadow,.15)
for side in (-1,1):
    box(objects,'Gate_jamb',(side*3.6,-18.45,6),(.9,.8,13),limestone,.15)
    cylinder(objects,'Gate_pinnacle',(side*3.6,-18.4,14),.75,3,8,gold)
exporter('SM_SoulwoodGothicFortress',objects)

def rocky_mass(name, rings, seed):
    random.seed(seed)
    count=48
    vertices=[];faces=[];indices=[]
    wobble=[random.uniform(.81,1.18) for _ in range(count)]
    for height,radius in rings:
        for j in range(count):
            angle=j*math.tau/count
            r=radius*wobble[j]*(1+.055*math.sin(angle*7+height*.08))
            z=height+random.uniform(-.8,.8) if height else 0
            vertices.append((math.cos(angle)*r,math.sin(angle)*r,z))
    for row in range(len(rings)-1):
        for j in range(count):
            a=row*count+j;b=row*count+(j+1)%count
            faces.append((a,b,b+count,a+count))
            indices.append(0 if j%7 else 1)
    faces.append(tuple(reversed(range((len(rings)-1)*count,len(rings)*count))))
    indices.append(1)
    obj=mesh(name,vertices,faces,[limestone,shadow],indices)
    exporter(name,[obj])
    bpy.data.objects.remove(obj,do_unlink=True)

rocky_mass('SM_CastleCrag',[(0,81),(6,72),(17,59),(27,42),(34,39)],8270)
rocky_mass('SM_DistantMountain',[(0,122),(17,103),(34,77),(54,49),(76,20),(85,5)],10137)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Soulwood_Vista.blend'))
print('SOULWOOD_VISTA_COMPLETE',OUT)
