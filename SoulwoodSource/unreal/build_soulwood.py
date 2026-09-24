"""Populate the existing /Game/soulwood map using original Blender FBX assets.

Run in Unreal's Python console after make_soulwood.py has produced FBX files.
The script is repeatable: generated actors use a prefix and are replaced on rerun.
"""
import os
import random
import unreal

random.seed(240926)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FBX = os.path.join(ROOT, "blender", "generated")
ASSET_ROOT = "/Game/SoulwoodOriginal"
WORLD = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ASSETS = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
PREFIX = "SW_"


def log(message):
    unreal.log("SOULWOOD: " + str(message))


def material(name, rgb, roughness=0.85, metallic=0.0, glow=0.0):
    path = ASSET_ROOT + "/Materials/" + name
    existing = EAL.load_asset(path)
    if existing:
        return existing
    m = ASSETS.create_asset(name, ASSET_ROOT + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
    color = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -350, 0)
    color.set_editor_property("constant", unreal.LinearColor(*rgb, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionConstant, -350, 180)
    r.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if metallic:
        metal = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionConstant, -350, 310)
        metal.set_editor_property("r", metallic)
        unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if glow:
        em = unreal.MaterialEditingLibrary.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -350, 440)
        em.set_editor_property("constant", unreal.LinearColor(*(c * glow for c in rgb), 1.0))
        unreal.MaterialEditingLibrary.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m


def import_fbx(name, skeletal=False):
    source = os.path.join(FBX, name + ".fbx")
    if not os.path.exists(source):
        log("MISSING ORIGINAL FBX " + source)
        return None
    destination = ASSET_ROOT + ("/Characters" if skeletal else "/Meshes")
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", source)
    task.set_editor_property("destination_path", destination)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("import_as_skeletal", skeletal)
    if skeletal:
        options.set_editor_property("import_animations", True)
    else:
        options.set_editor_property("import_animations", False)
        options.static_mesh_import_data.set_editor_property("combine_meshes", True)
        options.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", True)
    task.set_editor_property("options", options)
    ASSETS.import_asset_tasks([task])
    for path in task.get_editor_property("imported_object_paths"):
        obj = EAL.load_asset(path)
        if isinstance(obj, unreal.SkeletalMesh if skeletal else unreal.StaticMesh):
            log("Imported " + path)
            return obj
    log("FBX imported no usable mesh: " + name)
    return None


def spawn_mesh(name, mesh, pos, scale=(1,1,1), yaw=0, override=None):
    if not mesh:
        return None
    actor_class = unreal.SkeletalMeshActor if isinstance(mesh, unreal.SkeletalMesh) else unreal.StaticMeshActor
    actor = WORLD.spawn_actor_from_class(actor_class, unreal.Vector(*pos), unreal.Rotator(0, yaw, 0))
    actor.set_actor_label(PREFIX + name)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    component = actor.get_component_by_class(unreal.SkeletalMeshComponent if actor_class == unreal.SkeletalMeshActor else unreal.StaticMeshComponent)
    if actor_class == unreal.SkeletalMeshActor:
        component.set_skeletal_mesh_asset(mesh)
    else:
        component.set_static_mesh(mesh)
    if override:
        component.set_material(0, override)
    return actor


def lit_actor(cls, name, pos, rotation=None):
    a = WORLD.spawn_actor_from_class(cls, unreal.Vector(*pos), rotation or unreal.Rotator())
    a.set_actor_label(PREFIX + name)
    return a


def run():
    # The user's Soulwood level is the target; no alternate map is created.
    unreal.EditorLevelLibrary.load_level("/Game/soulwood")
    for actor in WORLD.get_all_level_actors():
        if actor.get_actor_label().startswith(PREFIX):
            WORLD.destroy_actor(actor)

    meshes = {n: import_fbx(n) for n in (
        "SM_Beech", "SM_Fir", "SM_MossBoulder", "SM_RuinedArch", "SM_HunterBow", "SM_Arrow", "SM_AngelWings")}
    hero = import_fbx("SK_Adventurer", True)
    goblin = import_fbx("SK_Goblin", True)
    soil = material("M_ForestSoil", (.13,.115,.07), .98)
    path = material("M_PathEarth", (.30,.22,.12), .96)
    grass = material("M_MeadowGrass", (.18,.26,.08), .96)
    water = material("M_RiverBlue", (.035,.11,.16), .20, .12)
    cliff = material("M_CliffSlate", (.17,.19,.18), .95)
    dark_stone = material("M_CastleStone", (.30,.29,.26), .88)
    fire_mat = material("M_FireSoul", (1,.16,.012), .18, 0, 7)
    beast_mat = material("M_BeastSoul", (.025,.36,1), .18, 0, 8)
    angel_mat = material("M_AngelSoul", (.9,.89,.72), .18, 0, 5)
    cube_mesh = EAL.load_asset("/Engine/BasicShapes/Cube.Cube")
    sphere_mesh = EAL.load_asset("/Engine/BasicShapes/Sphere.Sphere")
    cone_mesh = EAL.load_asset("/Engine/BasicShapes/Cone.Cone")

    # Approx. 180 m of explorable ground, with a winding combat path.
    spawn_mesh("Forest_ground", cube_mesh, (0,0,-85), (180,130,1.5), override=soil)
    for i in range(20):
        x = -8400+i*880
        y = 125*__import__("math").sin(i*.43)
        spawn_mesh("Path_%02d" % i, cube_mesh, (x,y,4), (9.4,4.1,.18), override=path)
    for i in range(160):
        x = random.uniform(-8400,8500)
        y = random.uniform(-6100,6100)
        if abs(y - 125*__import__("math").sin((x+8400)/880*.43)) < 390:
            continue
        tree = meshes["SM_Beech"] if i%3 else meshes["SM_Fir"]
        s = random.uniform(.72,1.43)
        spawn_mesh("Tree_%03d" % i, tree, (x,y,0), (s,s,s), random.uniform(-180,180))
    for i in range(85):
        x = random.uniform(-8200,8300)
        y = random.uniform(-6000,6000)
        if abs(y)<470:
            continue
        s = random.uniform(.45,1.55)
        spawn_mesh("Boulder_%03d" % i, meshes["SM_MossBoulder"], (x,y,0), (s,s,s), random.uniform(0,360))
    for i in range(12):
        x = -7600+i*1300
        side = -1 if i%2 else 1
        spawn_mesh("Grass_glade_%02d" % i, cube_mesh, (x,side*3400,-4), (12,10,.12), override=grass)

    # Ruined gateway by the encounter, a stream/gorge, and a distant castle.
    spawn_mesh("Forest_gateway", meshes["SM_RuinedArch"], (2500,0,0), (1.6,1.6,1.6), 90)
    for i in range(8):
        x = -7600+i*2100
        spawn_mesh("River_%02d" % i, cube_mesh, (x,5200,-52), (21,12,.18), override=water)
        spawn_mesh("North_bank_%02d" % i, cube_mesh, (x,6050,-230), (21,2,3.4), override=cliff)
        spawn_mesh("South_bank_%02d" % i, cube_mesh, (x,4200,-230), (21,2,3.4), override=cliff)
    spawn_mesh("Stone_bridge", cube_mesh, (3700,5200,12), (13,12,.55), override=dark_stone)
    for i in range(9):
        x = 9000+i*300
        y = 8500+(i%3)*380
        h = 1700+(i%4)*650
        spawn_mesh("Mountain_%02d" % i, cone_mesh, (x,y,h*.40), (22,22,h/100), override=cliff)
    castle_x, castle_y = 11300,8300
    spawn_mesh("Castle_keep", cube_mesh, (castle_x,castle_y,1900), (20,18,38), override=dark_stone)
    for i,(ox,oy) in enumerate(((-1100,-700),(1000,-700),(-1100,750),(1000,750))):
        spawn_mesh("Castle_tower_%d" % i, cube_mesh, (castle_x+ox,castle_y+oy,2450), (7,7,49), override=dark_stone)
        spawn_mesh("Castle_spire_%d" % i, cone_mesh, (castle_x+ox,castle_y+oy,5050), (5.2,5.2,13), override=dark_stone)

    # Original Blender figures and colored pickups mark the gameplay loop.
    spawn_mesh("Adventurer_display", hero, (-3900,0,0), (1,1,1), 0)
    spawn_mesh("Goblin_encounter", goblin, (700,0,0), (1,1,1), 180)
    for n, x, y, material_ in (("GoldEssence",900,230,fire_mat),
                              ("BeastSoul",1050,-150,beast_mat),
                              ("AngelSoul",1200,200,angel_mat)):
        spawn_mesh(n, sphere_mesh, (x,y,140), (.55,.55,.55), override=material_)
        light = lit_actor(unreal.PointLight, n+"Glow", (x,y,150))
        comp = light.get_component_by_class(unreal.PointLightComponent)
        comp.set_editor_property("intensity", 950)
        comp.set_editor_property("attenuation_radius", 520)
    start = lit_actor(unreal.PlayerStart, "PlayerStart", (-4200,0,120), unreal.Rotator(0,0,0))
    start.set_actor_label("PlayerStart_Soulwood")
    sun = lit_actor(unreal.DirectionalLight, "MorningSun", (0,0,3600), unreal.Rotator(-39,-32,0))
    sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("intensity", 6.2)
    sky = lit_actor(unreal.SkyLight, "Skylight", (0,0,500))
    sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 1.0)
    lit_actor(unreal.SkyAtmosphere, "Atmosphere", (0,0,0))
    fog = lit_actor(unreal.ExponentialHeightFog, "ValleyMist", (0,0,-50))
    fog.get_component_by_class(unreal.ExponentialHeightFogComponent).set_editor_property("fog_density", .012)
    unreal.EditorLevelLibrary.save_current_level()
    log("LEVEL_BUILT actors=" + str(len(WORLD.get_all_level_actors())))


run()
