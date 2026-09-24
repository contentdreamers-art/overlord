"""Create every Soulwood prototype mesh in Blender, with no downloaded assets.

Run: blender -b -P make_soulwood.py
Outputs FBX files beside the .blend in the generated directory.
"""
import bpy
import math
import os
import random
from mathutils import Vector

random.seed(240926)
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated")
os.makedirs(ROOT, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def mat(name, rgb, metallic=0.0, roughness=0.8, emission=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*rgb, 1)
    bs.inputs["Metallic"].default_value = metallic
    bs.inputs["Roughness"].default_value = roughness
    if emission:
        bs.inputs["Emission Color"].default_value = (*rgb, 1)
        bs.inputs["Emission Strength"].default_value = emission
    return m


bark = mat("Bark_dark_walnut", (.12, .083, .047))
leaf = mat("Leaves_deep_olive", (.11, .19, .055))
leaf_light = mat("Leaves_sunlit_green", (.28, .34, .08))
stone = mat("Ruin_weathered_limestone", (.38, .36, .29))
moss = mat("Moss", (.16, .25, .07))
rock = mat("Rock_cool_slate", (.21, .23, .21))
skin = mat("Adventurer_skin", (.48, .29, .19))
hair = mat("Adventurer_hair", (.09, .05, .03))
cloth = mat("Charcoal_cloak", (.045, .052, .055))
leather = mat("Worn_brown_leather", (.15, .075, .035))
steel = mat("Blued_steel", (.18, .22, .26), .72, .32)
gold = mat("Old_gold_trim", (.48, .29, .075), .78, .28)
goblin_skin = mat("Goblin_moss_skin", (.24, .31, .12))
goblin_dark = mat("Goblin_shadow_skin", (.12, .18, .055))
ivory = mat("Ivory_feathers", (.88, .85, .75), 0, .43)
feather_shadow = mat("Feather_shadows", (.62, .63, .56), 0, .5)
eye = mat("Amber_eyes", (.8, .35, .025), 0, .3, .4)
fire = mat("Fire_magic", (1, .18, .015), 0, .2, 5)
electric = mat("Lightning_magic", (.025, .4, 1), 0, .2, 4)


def finish(obj, name, material, smooth=False):
    obj.name = name
    if material:
        obj.data.materials.append(material)
    if smooth and obj.type == "MESH":
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def cube(name, loc, scale, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new("Hand softened edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return finish(o, name, material)


def uv(name, loc, scale, material, segments=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=10, location=loc)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, name, material, True)


def cone(name, loc, r1, r2, depth, material, vertices=9):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=depth, location=loc)
    return finish(bpy.context.object, name, material)


def rod(name, a, b, radius, material, vertices=8):
    mid = (Vector(a) + Vector(b)) / 2
    direction = Vector(b) - Vector(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=direction.length, location=mid)
    o = bpy.context.object
    o.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return finish(o, name, material)


def select_export(objects, filename, animated=False):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(ROOT, filename + ".fbx"),
        use_selection=True,
        object_types={"MESH", "ARMATURE"} if animated else {"MESH"},
        axis_forward="-Y", axis_up="Z", apply_unit_scale=True,
        add_leaf_bones=False, bake_anim=animated, bake_anim_use_all_actions=animated,
    )


def made_since(before):
    return [o for o in bpy.context.scene.objects if o.name not in before]


# A mature beech with varied leaf masses, bifurcated branches and exposed roots.
before = set(bpy.data.objects.keys())
cone("Bole_taper", (0, 0, 2.8), .43, .20, 5.6, bark, 14)
for i in range(7):
    t = i * math.tau / 7
    p = (math.cos(t)*.28, math.sin(t)*.28, .35)
    q = (math.cos(t)*1.35, math.sin(t)*1.35, .1)
    rod("Buttress_root", p, q, .13, bark)
for i in range(11):
    t = i * 2.399
    z = 3.0 + (i % 5)*.58
    start = (0, 0, z)
    end = (math.cos(t)*(1.65+(i%3)*.28), math.sin(t)*(1.65+(i%3)*.28), z+.6)
    rod("Branch", start, end, .13, bark)
    uv("Leaf_cluster", (end[0]*1.08, end[1]*1.08, end[2]+.35),
       (.9+(i%3)*.13, .75, .7), leaf if i%3 else leaf_light)
uv("Upper_canopy", (0, 0, 6.2), (1.5, 1.35, 1.15), leaf)
select_export(made_since(before), "SM_Beech")

# Finer conifer silhouette for distance and a mossy boulder for forest dressing.
before = set(bpy.data.objects.keys())
cone("Fir_trunk", (0, 0, 2.4), .23, .09, 4.8, bark, 12)
for i in range(5):
    cone("Needle_whorl", (0, 0, 2.0+i*.7), 1.85-i*.27, .08, 1.8, leaf if i%2 else leaf_light, 10)
select_export(made_since(before), "SM_Fir")
before = set(bpy.data.objects.keys())
uv("Weathered_boulder", (0, 0, .67), (1.25, .88, .8), rock, 12)
for i in range(4):
    a = i*1.7
    uv("Moss_cushion", (math.cos(a)*.5, math.sin(a)*.35, 1.22), (.42, .26, .09), moss, 10)
select_export(made_since(before), "SM_MossBoulder")

# Broken arch as a hand built modular landmark.
before = set(bpy.data.objects.keys())
for side in (-1, 1):
    for z in range(4):
        block = cube("Limestone_arch_block", (side*1.75, 0, .38+z*.72), (.82, 1.05, .68), stone, .045)
        block.rotation_euler[2] = random.uniform(-.045, .045)
    cube("Moss_growth", (side*1.75, .02, 2.99), (.8, .4, .07), moss)
for j in range(7):
    angle = math.pi * j / 6
    x = 1.75 * math.cos(angle)
    z = 2.97 + 1.75*math.sin(angle)
    o = cube("Voussoir", (x, 0, z), (.75, 1.1, .66), stone, .03)
    o.rotation_euler[1] = -angle + math.pi/2
cube("Fallen_keystone", (2.8, .9, .32), (.92, .7, .52), stone, .05).rotation_euler[1] = .32
select_export(made_since(before), "SM_RuinedArch")

# The bow has a physical string and wrapped grip.
before = set(bpy.data.objects.keys())
last = None
for i in range(15):
    z = -.75 + i*1.5/14
    x = .22*math.sin(math.pi*i/14)
    cur = (x, 0, z)
    if last is not None:
        rod("Recurved_limb", last, cur, .027 if abs(z)>.25 else .037, bark, 10)
    last = cur
rod("Bowstring", (0,0,-.75), (0,0,.75), .006, ivory, 6)
cube("Grip_wrap", (.2,0,0), (.11,.09,.26), leather, .015)
for z in (-.67,.67):
    cube("Brass_nock", (0,0,z), (.10,.09,.055), gold, .008)
select_export(made_since(before), "SM_HunterBow")

# One readable arrow, suitable for a visible bow projectile.
before = set(bpy.data.objects.keys())
rod("Ash_shaft", (0,0,-.55), (0,0,.55), .012, bark, 8)
cone("Forged_broadhead", (0,0,.62), .065, 0, .17, steel, 4)
for i in range(3):
    t = i*math.tau/3
    o = cube("Fletching", (math.cos(t)*.035, math.sin(t)*.035, -.42), (.09,.015,.18), ivory)
    o.rotation_euler[2] = t
select_export(made_since(before), "SM_Arrow")


def bone(name, head, tail, parent=None):
    b = arm.data.edit_bones.new(name)
    b.head, b.tail = head, tail
    if parent:
        b.parent = arm.data.edit_bones[parent]
    return b


def limb_part(name, loc, scale, material, group, primitive="uv"):
    obj = uv(name, loc, scale, material, 12) if primitive == "uv" else cube(name, loc, scale, material, .015)
    vg = obj.vertex_groups.new(name=group)
    vg.add(list(range(len(obj.data.vertices))), 1, "REPLACE")
    return obj


def rig_character(label, is_goblin):
    global arm
    before = set(bpy.data.objects.keys())
    bpy.ops.object.armature_add(location=(0,0,0))
    arm = bpy.context.object
    arm.name = "SK_" + label
    arm.data.name = label + "_skeleton"
    bpy.ops.object.mode_set(mode="EDIT")
    arm.data.edit_bones.remove(arm.data.edit_bones[0])
    bone("root", (0,0,0), (0,0,.22))
    bone("pelvis", (0,0,.22), (0,0,1.05), "root")
    bone("spine", (0,0,1.05), (0,0,1.65), "pelvis")
    bone("head", (0,0,1.65), (0,0,2.12), "spine")
    for side, sign in (("L",-1),("R",1)):
        bone("upper_arm_"+side, (0,sign*.28,1.54), (0,sign*.68,1.30), "spine")
        bone("lower_arm_"+side, (0,sign*.68,1.30), (0,sign*.9,1.04), "upper_arm_"+side)
        bone("thigh_"+side, (0,sign*.19,1.02), (0,sign*.20,.57), "pelvis")
        bone("shin_"+side, (0,sign*.20,.57), (0,sign*.20,.11), "thigh_"+side)
    bpy.ops.object.mode_set(mode="OBJECT")
    parts = []
    cskin = goblin_skin if is_goblin else skin
    torso = goblin_dark if is_goblin else steel
    armor_shape = "uv" if is_goblin else "cube"
    parts.append(limb_part("Chest", (0,0,1.43), (.48,.64,.66) if not is_goblin else (.28,.38,.36), torso, "spine", armor_shape))
    parts.append(limb_part("Waist", (0,0,1.04), (.41,.50,.30) if not is_goblin else (.25,.29,.16), leather, "pelvis", armor_shape))
    parts.append(limb_part("Face", (.10,0,1.89), (.19,.18,.24), cskin, "head"))
    parts.append(limb_part("Hair_or_crest", (-.05,0,2.09), (.23,.23,.11), goblin_dark if is_goblin else hair, "head"))
    if not is_goblin:
        parts.append(limb_part("Deep_cloth_hood", (-.12,0,1.94), (.29,.28,.34), cloth, "head"))
    for sign, side in ((-1,"L"),(1,"R")):
        parts.append(limb_part("Upper_arm_"+side, (0,sign*.47,1.42), (.27,.25,.43), torso, "upper_arm_"+side, armor_shape))
        parts.append(limb_part("Forearm_"+side, (0,sign*.77,1.15), (.23,.20,.39), leather, "lower_arm_"+side, armor_shape))
        parts.append(limb_part("Hand_"+side, (.015,sign*.91,1.02), (.1,.10,.11), cskin, "lower_arm_"+side))
        parts.append(limb_part("Thigh_"+side, (0,sign*.19,.78), (.30,.27,.49), leather, "thigh_"+side, armor_shape))
        parts.append(limb_part("Boot_"+side, (.06,sign*.20,.29), (.30,.26,.52), leather, "shin_"+side, armor_shape))
        parts.append(limb_part("Toe_"+side, (.19,sign*.20,.10), (.37,.26,.18), leather, "shin_"+side, armor_shape))
        if is_goblin:
            parts.append(limb_part("Ear_"+side, (.01,sign*.29,1.90), (.08,.19,.07), cskin, "head"))
        else:
            parts.append(limb_part("Pauldron_"+side, (-.02,sign*.39,1.59), (.22,.20,.12), steel, "upper_arm_"+side))
    if is_goblin:
        parts.append(limb_part("Nose", (.28,0,1.83), (.14,.12,.11), cskin, "head"))
        for sign in (-1,1):
            parts.append(limb_part("Eye", (.24,sign*.105,1.96), (.035,.035,.035), eye, "head"))
    else:
        parts.append(limb_part("Cape", (-.44,0,1.08), (.09,.80,1.30), cloth, "spine", "cube"))
        parts.append(limb_part("Cloak_collar", (-.30,0,1.72), (.20,.72,.20), cloth, "spine"))
        for sign in (-1,1):
            parts.append(limb_part("Chest_gold_trim", (.21,sign*.21,1.51), (.035,.035,.26), gold, "spine"))
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    mesh = parts[0]
    mesh.name = "SK_" + label + "_mesh"
    modifier = mesh.modifiers.new("Soulwood_armature", "ARMATURE")
    modifier.object = arm
    mesh.parent = arm
    return arm, mesh


def animate(arm, name, length, poses):
    action = bpy.data.actions.new(name)
    arm.animation_data_create()
    arm.animation_data.action = action
    for frame, rotations in poses:
        for bone_name, angles in rotations.items():
            p = arm.pose.bones[bone_name]
            p.rotation_mode = "XYZ"
            p.rotation_euler = tuple(math.radians(a) for a in angles)
            p.keyframe_insert(data_path="rotation_euler", frame=frame, group=bone_name)
    action.use_fake_user = True
    return action


hero, hero_mesh = rig_character("Adventurer", False)
animate(hero, "Hero_Idle", 24, [(1, {"spine":(0,0,-2),"head":(0,0,2)}),(12,{"spine":(2,0,2),"head":(-1,0,-2)}),(24,{"spine":(0,0,-2),"head":(0,0,2)})])
animate(hero, "Hero_Run", 16, [(1,{"thigh_L":(30,0,0),"thigh_R":(-30,0,0),"upper_arm_L":(-22,0,0),"upper_arm_R":(22,0,0),"spine":(12,0,0)}),(9,{"thigh_L":(-30,0,0),"thigh_R":(30,0,0),"upper_arm_L":(22,0,0),"upper_arm_R":(-22,0,0)}),(17,{"thigh_L":(30,0,0),"thigh_R":(-30,0,0),"upper_arm_L":(-22,0,0),"upper_arm_R":(22,0,0)})])
animate(hero, "Hero_Bow_Draw", 20, [(1,{"upper_arm_L":(0,0,0),"upper_arm_R":(0,0,0)}),(20,{"upper_arm_L":(-70,0,30),"lower_arm_L":(-35,0,0),"upper_arm_R":(-75,0,-20),"lower_arm_R":(-70,0,0)})])
animate(hero, "Hero_Fireball_Cast", 22, [(1,{"upper_arm_R":(0,0,0)}),(10,{"upper_arm_R":(25,0,-60),"spine":(-12,0,20)}),(22,{"upper_arm_R":(-120,0,20),"spine":(10,0,-10)})])
animate(hero, "Hero_Flight", 24, [(1,{"spine":(25,0,0),"upper_arm_L":(-110,0,-20),"upper_arm_R":(-110,0,20),"thigh_L":(-15,0,0),"thigh_R":(-15,0,0)}),(24,{"spine":(25,0,0),"upper_arm_L":(-110,0,-20),"upper_arm_R":(-110,0,20)})])
select_export([hero, hero_mesh], "SK_Adventurer", True)

goblin, goblin_mesh = rig_character("Goblin", True)
animate(goblin, "Goblin_Idle", 28, [(1,{"head":(0,0,-12)}),(14,{"head":(0,0,12),"spine":(2,0,0)}),(28,{"head":(0,0,-12)})])
animate(goblin, "Goblin_Walk", 20, [(1,{"thigh_L":(25,0,0),"thigh_R":(-25,0,0)}),(11,{"thigh_L":(-25,0,0),"thigh_R":(25,0,0)}),(21,{"thigh_L":(25,0,0),"thigh_R":(-25,0,0)})])
animate(goblin, "Goblin_Attack", 24, [(1,{"upper_arm_R":(0,0,0)}),(10,{"upper_arm_R":(70,0,-30),"spine":(-12,0,0)}),(16,{"upper_arm_R":(-100,0,20),"spine":(20,0,0)}),(24,{"upper_arm_R":(0,0,0),"spine":(0,0,0)})])
animate(goblin, "Goblin_Death", 30, [(1,{"spine":(0,0,0)}),(30,{"spine":(82,0,0),"head":(-22,0,0),"upper_arm_L":(40,0,0),"upper_arm_R":(40,0,0)})])
select_export([goblin, goblin_mesh], "SK_Goblin", True)

# Wings contain overlapping, tapered feathers; exported separately so they can unlock.
before = set(bpy.data.objects.keys())
for side in (-1,1):
    rod("Wing_spar", (-.17,side*.20,1.55), (-.42,side*1.75,1.92), .085, ivory)
    for row in range(3):
        for i in range(13-row*2):
            span = .28 + i*.128
            x = -.40 - row*.095 - .18*math.sin(i*.25)
            y = side*span
            z = 1.70 + .25*math.sin(i*.22) - row*.105
            o = uv("Layered_flight_feather", (x,y,z), (.17+row*.035,.085,.035), ivory if (i+row)%4 else feather_shadow, 10)
            o.rotation_euler[2] = side*(.12+i*.025)
            o.rotation_euler[0] = side*.12
select_export(made_since(before), "SM_AngelWings")

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "Soulwood_original_assets.blend"))
print("SOULWOOD_BLENDER_DONE", ROOT)
