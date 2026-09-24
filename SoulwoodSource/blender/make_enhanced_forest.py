"""Original, procedural forest meshes for the existing Soulwood level.

Run in Blender 5.x. No downloaded geometry, images, or materials are used.
"""
import bpy
import math
import os
import random
from mathutils import Vector

random.seed(190724)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generated')
os.makedirs(OUT, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def mat(name, rgb, roughness=0.9):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    return m


bark = mat('SW_bark_deep_brown', (.085, .067, .047))
bark_light = mat('SW_bark_silver_ridge', (.20, .19, .155))
leaf_mats = [mat('SW_leaf_dark', (.055, .105, .033)),
             mat('SW_leaf_olive', (.11, .19, .049)),
             mat('SW_leaf_sun', (.23, .30, .085)),
             mat('SW_leaf_gold', (.31, .29, .085))]
fern_mats = [mat('SW_fern_dark', (.075, .16, .055)),
             mat('SW_fern_light', (.20, .29, .075))]
stone = mat('SW_granite', (.20, .22, .21))
moss = mat('SW_moss', (.10, .19, .055))
litter = mat('SW_litter', (.18, .105, .045))


def finish_mesh(name, vertices, faces, materials, indices=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for material in materials:
        mesh.materials.append(material)
    if indices:
        for poly, index in zip(mesh.polygons, indices):
            poly.material_index = index
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def tapered_segment(name, p0, p1, r0, r1, material, sides=9):
    a, b = Vector(p0), Vector(p1)
    direction = (b-a).normalized()
    u = direction.cross(Vector((0, 0, 1)))
    if u.length < .01:
        u = Vector((1, 0, 0))
    u.normalize()
    v = direction.cross(u).normalized()
    verts = []
    for center, radius in ((a, r0), (b, r1)):
        for j in range(sides):
            angle = j * math.tau / sides
            uneven = 1 + .10*math.sin(j*3.7+center.z)
            verts.append(tuple(center + radius*uneven*(u*math.cos(angle)+v*math.sin(angle))))
    faces = [(j,(j+1)%sides,(j+1)%sides+sides,j+sides) for j in range(sides)]
    faces.extend([tuple(range(sides-1,-1,-1)), tuple(range(sides,2*sides))])
    return finish_mesh(name, verts, faces, [material])


def leaf_cloud(name, centers, count, radius, palette):
    vertices, faces, indices = [], [], []
    for i in range(count):
        center, spread = random.choice(centers)
        theta = random.random()*math.tau
        zeta = random.uniform(-.85,.85)
        rr = math.sqrt(max(0,1-zeta*zeta))
        p = Vector(center) + Vector((math.cos(theta)*rr*spread[0],
                                     math.sin(theta)*rr*spread[1],
                                     zeta*spread[2]))
        length = random.uniform(.12,.27)
        width = length*random.uniform(.32,.60)
        tangent = Vector((random.uniform(-1,1),random.uniform(-1,1),random.uniform(-.18,.7))).normalized()
        side = tangent.cross(Vector((random.uniform(-.5,.5),random.uniform(-.5,.5),1))).normalized()
        if side.length < .1:
            side = Vector((1,0,0))
        base = len(vertices)
        vertices.extend([tuple(p-tangent*length*.52),tuple(p-side*width),
                         tuple(p+tangent*length*.55),tuple(p+side*width)])
        faces.append((base,base+1,base+2,base+3))
        faces.append((base+3,base+2,base+1,base))
        weights = [2,5,4,1][:len(palette)] if palette[0] == leaf_mats[0] else [3,4]
        material_id = random.choices(range(len(palette)),weights=weights)[0]
        indices.extend([material_id,material_id])
    return finish_mesh(name, vertices, faces, palette, indices)


def export(name, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,name+'.fbx'),
        use_selection=True, object_types={'MESH'}, axis_forward='-Y', axis_up='Z',
        apply_unit_scale=True, bake_anim=False)


objects = []
height = 8.1
trunk = [(0,0,0),(.07,-.02,1.1),(.11,.10,2.4),(.01,.17,4.0),(-.12,.2,5.6),(-.18,.17,height)]
for i in range(len(trunk)-1):
    objects.append(tapered_segment('Beech_bole',trunk[i],trunk[i+1],
                   .50*(1-i/6)+.10,.50*(1-(i+1)/6)+.07,bark_light if i%3==1 else bark,12))
for i in range(8):
    a=i*math.tau/8
    objects.append(tapered_segment('Exposed_root',(0,0,.34),
                   (math.cos(a)*1.5,math.sin(a)*1.5,.07),.23,.035,bark,7))
clouds=[]
for i in range(26):
    angle = i*2.39996323
    z = 2.65+(i%10)*.39
    length = 1.35 + (i%5)*.27
    base = Vector((.04*math.sin(z),.03*math.cos(z),z))
    mid = base + Vector((math.cos(angle)*length*.58,math.sin(angle)*length*.58,.34))
    tip = base + Vector((math.cos(angle)*length,math.sin(angle)*length,.68))
    objects.append(tapered_segment('Major_bough',base,mid,.19,.105,bark,7))
    objects.append(tapered_segment('Fine_bough',mid,tip,.105,.025,bark,6))
    for j in range(3):
        aa=angle+(j-1)*.65
        twig_tip=tip+Vector((math.cos(aa)*(.42+j*.12),math.sin(aa)*(.42+j*.12),.26+j*.08))
        objects.append(tapered_segment('Outer_twig',tip,twig_tip,.04,.007,bark,5))
        clouds.append((tuple(twig_tip),(.7,.7,.48)))
objects.append(leaf_cloud('Individual_beech_leaves',clouds,2600,1,leaf_mats))
export('SM_DetailedBeech',objects)

objects=[]
objects.append(tapered_segment('Fir_bole',(0,0,0),(0,0,9.5),.38,.015,bark,12))
needles=[]
for tier in range(19):
    z = .8+tier*.43
    spread = 2.55*(1-z/10.3)**1.1
    for j in range(8):
        angle = j*math.tau/8+tier*.37
        start=(0,0,z)
        tip=(math.cos(angle)*spread,math.sin(angle)*spread,z-.35)
        objects.append(tapered_segment('Fir_branch',start,tip,.06,.008,bark,5))
        for n in range(6):
            f=(n+1)/7
            p=(tip[0]*f,tip[1]*f,z-.35*f)
            needles.append((p,(.18+spread*.05,.16+spread*.05,.18)))
objects.append(leaf_cloud('Fine_needle_sprays',needles,3300,1,leaf_mats[:3]))
export('SM_DetailedFir',objects)

objects=[]
verts,faces,inds=[],[],[]
for frond in range(9):
    angle=frond*math.tau/9+random.uniform(-.2,.2)
    reach=random.uniform(.55,1.3)
    for pair in range(8):
        t=(pair+1)/9
        base=Vector((math.cos(angle)*reach*t,math.sin(angle)*reach*t,.05+.48*math.sin(math.pi*t)))
        w=(1-t)*.18+.035
        forward=Vector((math.cos(angle),math.sin(angle),0))
        cross=Vector((-math.sin(angle),math.cos(angle),0))
        for sign in (-1,1):
            a=base+cross*sign*.04
            b=base+cross*sign*w+forward*.10
            c=base+forward*.17
            q=len(verts)
            verts.extend([tuple(a),tuple(b),tuple(c)])
            faces.extend([(q,q+1,q+2),(q+2,q+1,q)])
            inds.extend([pair%2,pair%2])
objects.append(finish_mesh('Fern_pinnate_fronds',verts,faces,fern_mats,inds))
export('SM_FernClump',objects)

objects=[]
vertices,faces,indices=[],[],[]
for i in range(28):
    a=random.random()*math.tau
    radius=random.random()*1.1
    p=Vector((math.cos(a)*radius,math.sin(a)*radius,.02+random.random()*.018))
    theta=random.random()*math.tau
    v=Vector((math.cos(theta),math.sin(theta),0))
    side=Vector((-v.y,v.x,0))
    length=random.uniform(.12,.28)
    width=length*.38
    j=len(vertices)
    vertices.extend([tuple(p-v*length),tuple(p+side*width),
                     tuple(p+v*length),tuple(p-side*width)])
    faces.append((j,j+1,j+2,j+3))
    indices.append(i%2)
objects.append(finish_mesh('Dry_fallen_leaves',vertices,faces,[litter,leaf_mats[0]],indices))
export('SM_LeafLitter',objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'Soulwood_EnhancedForest.blend'))
print('SOULWOOD_ENHANCED_FOREST_COMPLETE', OUT)
