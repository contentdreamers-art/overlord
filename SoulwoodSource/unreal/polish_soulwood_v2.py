"""Second in-editor pass: readable foliage, terrain coverage, and armor values.

Run in /Game/soulwood with: py /soulwoodsource/unreal/v2.py
"""
import unreal

ROOT = '/Game/SoulwoodOriginal'
EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EDIT = unreal.MaterialEditingLibrary


def note(message):
    unreal.log('SOULWOOD_V2: ' + str(message))


def surface(name, rgb, metallic=0.0, roughness=.83, two_sided=False):
    path = ROOT + '/Materials/' + name
    asset = EAL.load_asset(path)
    if asset:
        return asset
    asset = TOOLS.create_asset(name, ROOT + '/Materials', unreal.Material,
                               unreal.MaterialFactoryNew())
    color = EDIT.create_material_expression(asset,
                                            unreal.MaterialExpressionConstant3Vector,
                                            -250, 0)
    color.set_editor_property('constant', unreal.LinearColor(*rgb, 1.0))
    EDIT.connect_material_property(color, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    metal = EDIT.create_material_expression(asset, unreal.MaterialExpressionConstant,
                                            -250, 150)
    metal.set_editor_property('r', metallic)
    EDIT.connect_material_property(metal, '', unreal.MaterialProperty.MP_METALLIC)
    rough = EDIT.create_material_expression(asset, unreal.MaterialExpressionConstant,
                                            -250, 280)
    rough.set_editor_property('r', roughness)
    EDIT.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    if two_sided:
        asset.set_editor_property('two_sided', True)
    EDIT.recompile_material(asset)
    EAL.save_loaded_asset(asset)
    return asset


mats = {
    'skin': surface('M_V2_WarmSkin', (.65, .40, .28)),
    'hair': surface('M_V2_DarkHair', (.15, .09, .045)),
    'leather': surface('M_V2_WornLeather', (.32, .18, .085)),
    'steel': surface('M_V2_BlueSteel', (.27, .33, .39), .48, .54),
    'gold': surface('M_V2_OldGold', (.64, .44, .16), .60, .45),
    'goblin': surface('M_V2_GoblinSkin', (.27, .44, .13)),
    'goblin_dark': surface('M_V2_GoblinShadow', (.15, .24, .07)),
    'eye': surface('M_V2_AmberEye', (.8, .38, .02), 0, .25),
    'mountain': surface('M_V2_MountainSlate', (.27, .31, .31)),
    'bark': surface('M_V2_BeechBark', (.38, .36, .31)),
    'leaf_deep': surface('M_V2_LeafDeep', (.18, .29, .075), 0, .85, True),
    'leaf_mid': surface('M_V2_LeafMid', (.29, .39, .11), 0, .85, True),
    'leaf_sun': surface('M_V2_LeafSun', (.43, .50, .17), 0, .85, True),
}


def figure(slot, goblin):
    name = slot.lower()
    if 'gold' in name: return mats['gold']
    if 'steel' in name: return mats['steel']
    if 'leather' in name: return mats['leather']
    if 'hair' in name: return mats['hair']
    if 'eye' in name: return mats['eye']
    if 'shadow' in name or 'dark' in name:
        return mats['goblin_dark'] if goblin else mats['hair']
    if 'skin' in name: return mats['goblin'] if goblin else mats['skin']
    return None


for name in ('SK_Adventurer', 'SK_Goblin'):
    mesh = EAL.load_asset(ROOT + '/Characters/' + name)
    if not mesh:
        note('missing mesh ' + name)
        continue
    entries = list(mesh.get_editor_property('materials'))
    count = 0
    for entry in entries:
        slot = str(entry.get_editor_property('material_slot_name'))
        original = entry.get_editor_property('material_interface')
        target = figure(slot, name == 'SK_Goblin')
        if not target and original:
            target = figure(original.get_name(), name == 'SK_Goblin')
        if target:
            entry.set_editor_property('material_interface', target)
            count += 1
    mesh.set_editor_property('materials', entries)
    EAL.save_loaded_asset(mesh)
    note(name + ' slots updated ' + str(count))


terrain = EAL.load_asset(ROOT + '/Materials/M_ForestFloor_Photo_02')
counts = {'ground': 0, 'mountain': 0, 'tree': 0, 'sun': 0}
for actor in ACTORS.get_all_level_actors():
    label = actor.get_actor_label()
    if label == 'SW_MorningSun':
        light = actor.get_component_by_class(unreal.DirectionalLightComponent)
        if light:
            light.set_editor_property('intensity', 3.4)
            counts['sun'] += 1
    elif label == 'SW_Skylight':
        light = actor.get_component_by_class(unreal.SkyLightComponent)
        if light:
            light.set_editor_property('intensity', 1.2)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not comp:
        continue
    if label == 'SW_Forest_ground':
        if terrain:
            comp.set_material(0, terrain)
        pos = actor.get_actor_location()
        actor.set_actor_location(unreal.Vector(pos.x, pos.y, -65), False, False)
        counts['ground'] += 1
    elif label.startswith('SW_Vista_Mountain_'):
        for i in range(comp.get_num_materials()):
            comp.set_material(i, mats['mountain'])
        counts['mountain'] += 1
    elif label.startswith(('SW_Tree_', 'SW_Vista_Canopy_', 'SW_Vista_FarCanopy_')):
        for i in range(comp.get_num_materials()):
            old = comp.get_material(i)
            name = (old.get_name() if old else '').lower()
            if 'bark' in name or 'crevice' in name:
                comp.set_material(i, mats['bark'])
            elif 'leaf' in name or 'leaves' in name:
                key = 'leaf_sun' if 'sun' in name else ('leaf_deep' if 'deep' in name else 'leaf_mid')
                comp.set_material(i, mats[key])
        counts['tree'] += 1

unreal.EditorLevelLibrary.save_current_level()
note('APPLIED ' + str(counts))
