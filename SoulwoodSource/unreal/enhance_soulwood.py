"""Replace Soulwood blockout foliage and surfaces with original procedural art.

Run in the Unreal editor Python console after make_enhanced_forest.py has exported
FBX files. This edits /Game/soulwood in place and is safe to rerun.
"""
import math
import os
import random
import unreal

random.seed(7081924)
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESH_DIR = os.path.join(BASE,'blender','generated')
TEXTURE_DIR = os.path.join(BASE,'unreal','generated_textures')
ROOT = '/Game/SoulwoodOriginal'
EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(message):
    unreal.log('SOULWOOD_ART: '+str(message))


def imported(name, directory, destination, mesh=False):
    existing=EAL.load_asset(destination+'/'+name)
    if existing and isinstance(existing,unreal.StaticMesh if mesh else unreal.Texture2D):
        return existing
    filename=os.path.join(directory,name+('.fbx' if mesh else '.png'))
    if not os.path.exists(filename):
        raise RuntimeError('Missing original source file: '+filename)
    task=unreal.AssetImportTask()
    task.set_editor_property('filename',filename)
    task.set_editor_property('destination_path',destination)
    task.set_editor_property('automated',True)
    task.set_editor_property('replace_existing',True)
    task.set_editor_property('save',True)
    if mesh:
        options=unreal.FbxImportUI()
        options.set_editor_property('import_mesh',True)
        options.set_editor_property('import_materials',True)
        options.set_editor_property('import_textures',False)
        options.set_editor_property('import_animations',False)
        options.static_mesh_import_data.set_editor_property('combine_meshes',True)
        options.static_mesh_import_data.set_editor_property('generate_lightmap_u_vs',False)
        task.set_editor_property('options',options)
    TOOLS.import_asset_tasks([task])
    for path in task.get_editor_property('imported_object_paths'):
        asset=EAL.load_asset(path)
        if isinstance(asset,unreal.StaticMesh if mesh else unreal.Texture2D):
            log('imported '+path)
            return asset
    raise RuntimeError('No usable Unreal asset imported from '+filename)


def texture_material(name, texture, tiling, roughness):
    path=ROOT+'/Materials/'+name
    m=EAL.load_asset(path)
    if m:
        return m
    m=TOOLS.create_asset(name,ROOT+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
    sample=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionTextureSample,-250,0)
    sample.set_editor_property('texture',texture)
    coord=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionTextureCoordinate,-500,0)
    coord.set_editor_property('u_tiling',tiling)
    coord.set_editor_property('v_tiling',tiling)
    unreal.MaterialEditingLibrary.connect_material_expressions(coord,'',sample,'Coordinates')
    unreal.MaterialEditingLibrary.connect_material_property(sample,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
    rough=unreal.MaterialEditingLibrary.create_material_expression(m,unreal.MaterialExpressionConstant,-250,160)
    rough.set_editor_property('r',roughness)
    unreal.MaterialEditingLibrary.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m


def spawn_scatter(name, mesh, x, y, scale, yaw):
    actor=ACTORS.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,y,0),unreal.Rotator(0,yaw,0))
    actor.set_actor_label(name)
    actor.set_actor_scale3d(unreal.Vector(scale,scale,scale))
    component=actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_static_mesh(mesh)
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)


unreal.EditorLevelLibrary.load_level('/Game/soulwood')
for actor in ACTORS.get_all_level_actors():
    if actor.get_actor_label().startswith(('SW_DetailFern_','SW_DetailLitter_')):
        ACTORS.destroy_actor(actor)

meshes={n:imported(n,MESH_DIR,ROOT+'/Meshes',True) for n in (
    'SM_DetailedBeech','SM_DetailedFir','SM_FernClump','SM_LeafLitter')}
textures={n:imported(n,TEXTURE_DIR,ROOT+'/Textures') for n in (
    'T_ForestFloor','T_ForestPath','T_WeatheredStone')}
floor_mat=texture_material('M_DetailedForestFloor',textures['T_ForestFloor'],100,1.0)
path_mat=texture_material('M_DetailedForestPath',textures['T_ForestPath'],5,1.0)
stone_mat=texture_material('M_DetailedWeatheredStone',textures['T_WeatheredStone'],3,.94)

swapped=0
relocated=0
for actor in ACTORS.get_all_level_actors():
    label=actor.get_actor_label()
    component=actor.get_component_by_class(unreal.StaticMeshComponent)
    if not component:
        continue
    if label.startswith('SW_Tree_'):
        old=component.get_editor_property('static_mesh')
        component.set_static_mesh(meshes['SM_DetailedFir'] if old and 'Fir' in old.get_name() else meshes['SM_DetailedBeech'])
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        location=actor.get_actor_location()
        path_y=125*math.sin((location.x+8400)/880*.43)
        if abs(location.y-path_y)<1050:
            side=1 if location.y>=path_y else -1
            actor.set_actor_location(unreal.Vector(location.x,path_y+side*1050,location.z),False,False)
            relocated+=1
        swapped+=1
    elif label=='SW_Forest_ground' or label.startswith('SW_Grass_glade_'):
        component.set_material(0,floor_mat)
    elif label.startswith('SW_Path_'):
        component.set_material(0,path_mat)
    elif label.startswith(('SW_Castle_','SW_Mountain_','SW_North_bank_','SW_South_bank_','SW_Stone_bridge')):
        component.set_material(0,stone_mat)

for i in range(1000):
    x=random.uniform(-8300,7000)
    path_y=125*math.sin((x+8400)/880*.43)
    side=random.choice((-1,1))
    y=path_y+side*random.uniform(650,2600)
    spawn_scatter('SW_DetailFern_%04d'%i,meshes['SM_FernClump'],x,y,
                  random.uniform(.40,.90),random.uniform(0,360))
for i in range(650):
    x=random.uniform(-8300,7000)
    path_y=125*math.sin((x+8400)/880*.43)
    y=path_y+random.choice((-1,1))*random.uniform(500,3000)
    spawn_scatter('SW_DetailLitter_%04d'%i,meshes['SM_LeafLitter'],x,y,
                  random.uniform(.28,.65),random.uniform(0,360))

unreal.EditorLevelLibrary.save_current_level()
log('ENHANCED trees='+str(swapped)+' relocated='+str(relocated)+' ferns=1000 litter=650')
