"""Apply original photo textures and authored Blender vista assets to /Game/soulwood.

Run in the Unreal editor Python console after make_vista.py has exported its FBXs.
Safe to rerun: every added actor uses a SW_Vista_ label.
"""
import os
import random
import unreal

random.seed(46290)
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESHES=os.path.join(BASE,'blender','generated')
if not os.path.isfile(os.path.join(MESHES,'SM_VistaBeech_2041.fbx')):
    MESHES='C:/generated'
TEXTURES=os.path.join(BASE,'unreal','generated_textures')
ROOT='/Game/SoulwoodOriginal'
EAL=unreal.EditorAssetLibrary
ASSETS=unreal.AssetToolsHelpers.get_asset_tools()
WORLD=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def log(value):unreal.log('SOULWOOD_VISTA: '+str(value))

def import_asset(name,folder,destination,is_mesh=False):
    existing=EAL.load_asset(destination+'/'+name)
    if existing:return existing
    filename=os.path.join(folder,name+('.fbx' if is_mesh else '.png'))
    if not os.path.isfile(filename):raise RuntimeError('Missing '+filename)
    task=unreal.AssetImportTask()
    task.set_editor_property('filename',filename)
    task.set_editor_property('destination_path',destination)
    task.set_editor_property('automated',True)
    task.set_editor_property('replace_existing',True)
    task.set_editor_property('save',True)
    if is_mesh:
        options=unreal.FbxImportUI()
        options.set_editor_property('import_mesh',True)
        options.set_editor_property('import_materials',True)
        options.set_editor_property('import_textures',False)
        options.set_editor_property('import_animations',False)
        options.static_mesh_import_data.set_editor_property('combine_meshes',True)
        options.static_mesh_import_data.set_editor_property('generate_lightmap_u_vs',False)
        task.set_editor_property('options',options)
    ASSETS.import_asset_tasks([task])
    for path in task.get_editor_property('imported_object_paths'):
        obj=EAL.load_asset(path)
        if isinstance(obj,unreal.StaticMesh if is_mesh else unreal.Texture2D):
            log('Imported '+path)
            return obj
    raise RuntimeError('Import failed '+filename)

def material(name,texture,tiling):
    path=ROOT+'/Materials/'+name
    found=EAL.load_asset(path)
    if found:return found
    mat=ASSETS.create_asset(name,ROOT+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
    edit=unreal.MaterialEditingLibrary
    tex=edit.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-220,0)
    tex.set_editor_property('texture',texture)
    uv=edit.create_material_expression(mat,unreal.MaterialExpressionTextureCoordinate,-480,0)
    uv.set_editor_property('u_tiling',tiling)
    uv.set_editor_property('v_tiling',tiling)
    edit.connect_material_expressions(uv,'',tex,'Coordinates')
    edit.connect_material_property(tex,'RGB',unreal.MaterialProperty.MP_BASE_COLOR)
    rough=edit.create_material_expression(mat,unreal.MaterialExpressionConstant,-220,170)
    rough.set_editor_property('r',.94)
    edit.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    edit.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    return mat

forest=import_asset('T_ForestFloor_Photo',TEXTURES,ROOT+'/Textures')
path=import_asset('T_ForestPath_Photo',TEXTURES,ROOT+'/Textures')
forest_mat=material('M_ForestFloor_Photo_02',forest,260)
path_mat=material('M_ForestPath_Photo_01',path,3)
stone=import_asset('T_GothicStone_Photo',TEXTURES,ROOT+'/Textures')
stone_mat=material('M_GothicStone_Photo_01',stone,5)
cloak=import_asset('T_CloakCloth_Photo',TEXTURES,ROOT+'/Textures')
material('M_CloakCloth_Photo',cloak,1)
beech_a=import_asset('SM_VistaBeech_2041',MESHES,ROOT+'/Meshes',True)
beech_b=import_asset('SM_VistaBeech_2049',MESHES,ROOT+'/Meshes',True)
fortress=import_asset('SM_SoulwoodGothicFortress',MESHES,ROOT+'/Meshes',True)
crag=import_asset('SM_CastleCrag',MESHES,ROOT+'/Meshes',True)
mountain=import_asset('SM_DistantMountain',MESHES,ROOT+'/Meshes',True)

# Resolve every source asset before changing a saved level. A missing export must
# leave the existing Soulwood actors intact.
unreal.EditorLevelLibrary.load_level('/Game/soulwood')
for actor in WORLD.get_all_level_actors():
    if actor.get_actor_label().startswith('SW_Vista_'):
        WORLD.destroy_actor(actor)

tree_count=0
for actor in WORLD.get_all_level_actors():
    name=actor.get_actor_label()
    if name=='SW_MorningSun':
        actor.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property('intensity',3.4)
    component=actor.get_component_by_class(unreal.StaticMeshComponent)
    if name.startswith(('SW_Castle_','SW_Mountain_')):
        WORLD.destroy_actor(actor)
        continue
    if not component:continue
    if name.startswith('SW_Tree_'):
        current=component.get_editor_property('static_mesh')
        if current and 'Fir' not in current.get_name():
            component.set_static_mesh(beech_a if tree_count%2 else beech_b)
            tree_count+=1
    elif name=='SW_Forest_ground' or name.startswith('SW_Grass_glade_'):
        component.set_material(0,forest_mat)
        if name=='SW_Forest_ground':
            actor.set_actor_scale3d(unreal.Vector(620,620,1.5))
    elif name.startswith('SW_Path_'):
        component.set_material(0,path_mat)

def spawn(name,mesh,position,scale,yaw):
    actor=WORLD.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*position),unreal.Rotator(0,yaw,0))
    actor.set_actor_label('SW_Vista_'+name)
    actor.set_actor_scale3d(unreal.Vector(scale,scale,scale))
    comp=actor.get_component_by_class(unreal.StaticMeshComponent)
    comp.set_static_mesh(mesh)
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

spawn('CastleCrag',crag,(20000,11800,0),1,0)
spawn('GothicFortress',fortress,(20000,11800,3400),1,0)
for actor in WORLD.get_all_level_actors():
    if actor.get_actor_label().startswith(('SW_Vista_GothicFortress','SW_Vista_CastleCrag')):
        comp=actor.get_component_by_class(unreal.StaticMeshComponent)
        for slot in range(comp.get_num_materials()):
            previous=comp.get_material(slot)
            if not previous or not any(word in previous.get_name().lower() for word in ('slate','gold','shadow')):
                comp.set_material(slot,stone_mat)
for j,(x,y,s) in enumerate(((32000,25500,1.30),(35500,5500,1.55),
                             (33000,-21500,1.25),(43000,16500,1.85))):
    spawn('Mountain_%02d'%j,mountain,(x,y,-1800),s,j*61)
for i in range(180):
    x=random.uniform(-8600,8250)
    y=random.uniform(-6000,6000)
    center=125*__import__('math').sin((x+8400)/880*.43)
    if abs(y-center)<1000:continue
    if x>6100 and y>3500:continue
    scale=random.uniform(.77,1.42)
    spawn('Canopy_%03d'%i,beech_a if i%2 else beech_b,(x,y,0),scale,random.uniform(0,360))
for i in range(160):
    x=random.uniform(9200,23000)
    y=random.uniform(-11000,11000)
    if abs(y)<500:continue
    if abs(x-20000)<4300 and abs(y-11800)<6000:continue
    spawn('FarCanopy_%03d'%i,beech_a if i%2 else beech_b,(x,y,0),
          random.uniform(.85,1.45),random.uniform(0,360))

unreal.EditorLevelLibrary.save_current_level()
log('APPLIED floor and path photos; '+str(tree_count)+' old trees upgraded; dense extra canopy and fortress')
