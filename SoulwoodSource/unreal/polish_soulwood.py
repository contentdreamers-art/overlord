"""Give imported original Blender assets explicit fantasy materials in Soulwood.

Run in the Unreal editor with: py /soulwoodsource/unreal/polish.py
Safe to rerun: edits existing assets and actors without deleting level content.
"""
import unreal

ROOT = '/Game/SoulwoodOriginal'
EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
WORLD = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def note(message):
    unreal.log('SOULWOOD_POLISH: ' + str(message))


def color_material(name, rgb, metallic=0.0, roughness=0.82):
    path = ROOT + '/Materials/' + name
    result = EAL.load_asset(path)
    if result:
        return result
    result = TOOLS.create_asset(name, ROOT + '/Materials', unreal.Material,
                                unreal.MaterialFactoryNew())
    edit = unreal.MaterialEditingLibrary
    base = edit.create_material_expression(result,
                                           unreal.MaterialExpressionConstant3Vector,
                                           -250, 0)
    base.set_editor_property('constant', unreal.LinearColor(*rgb, 1.0))
    edit.connect_material_property(base, 'RGB', unreal.MaterialProperty.MP_BASE_COLOR)
    metal = edit.create_material_expression(result,
                                            unreal.MaterialExpressionConstant,
                                            -250, 150)
    metal.set_editor_property('r', metallic)
    edit.connect_material_property(metal, '', unreal.MaterialProperty.MP_METALLIC)
    rough = edit.create_material_expression(result,
                                            unreal.MaterialExpressionConstant,
                                            -250, 280)
    rough.set_editor_property('r', roughness)
    edit.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    edit.recompile_material(result)
    EAL.save_loaded_asset(result)
    return result


materials = {
    'skin': color_material('M_Polish_WarmSkin', (.44, .25, .17)),
    'hair': color_material('M_Polish_DarkHair', (.052, .027, .014)),
    'cloth': EAL.load_asset(ROOT + '/Materials/M_CloakCloth_Photo'),
    'leather': color_material('M_Polish_WornLeather', (.13, .057, .024)),
    'steel': color_material('M_Polish_DarkSteel', (.085, .12, .16), .74, .37),
    'gold': color_material('M_Polish_OldGold', (.48, .30, .075), .7, .43),
    'goblin': color_material('M_Polish_GoblinSkin', (.15, .26, .07)),
    'goblin_dark': color_material('M_Polish_GoblinShadow', (.065, .10, .025)),
    'eye': color_material('M_Polish_AmberEye', (.66, .27, .01), 0, .2),
    'mountain': color_material('M_Polish_MountainSlate', (.15, .19, .20)),
    'bark': color_material('M_Polish_BeechBark', (.24, .23, .19)),
    'leaf_deep': color_material('M_Polish_LeafDeep', (.045, .095, .025)),
    'leaf_mid': color_material('M_Polish_LeafMid', (.095, .16, .037)),
    'leaf_sun': color_material('M_Polish_LeafSun', (.17, .22, .055)),
}
if not materials['cloth']:
    materials['cloth'] = color_material('M_Polish_CloakFallback', (.045, .05, .058))


def figure_material(slot_name, goblin):
    name = slot_name.lower()
    if 'gold' in name: return materials['gold']
    if 'steel' in name: return materials['steel']
    if 'leather' in name: return materials['leather']
    if 'cloth' in name or 'cloak' in name: return materials['cloth']
    if 'hair' in name: return materials['hair']
    if 'eye' in name: return materials['eye']
    if 'shadow' in name or 'dark' in name: return materials['goblin_dark'] if goblin else materials['hair']
    if 'skin' in name: return materials['goblin'] if goblin else materials['skin']
    return None


for asset_name in ('SK_Adventurer', 'SK_Goblin'):
    mesh = EAL.load_asset(ROOT + '/Characters/' + asset_name)
    if not mesh:
        note('Missing character ' + asset_name)
        continue
    entries = list(mesh.get_editor_property('materials'))
    changed = 0
    for entry in entries:
        name = str(entry.get_editor_property('material_slot_name'))
        previous = entry.get_editor_property('material_interface')
        previous_name = previous.get_name() if previous else ''
        target = figure_material(name + ' ' + previous_name, asset_name == 'SK_Goblin')
        note(asset_name + ' slot ' + name + ' old ' + previous_name +
             ' -> ' + (target.get_name() if target else 'UNCHANGED'))
        if target:
            entry.set_editor_property('material_interface', target)
            changed += 1
    mesh.set_editor_property('materials', entries)
    EAL.save_loaded_asset(mesh)
    note(asset_name + ' material slots set: ' + str(changed))

trees = 0
mountains = 0
for actor in WORLD.get_all_level_actors():
    label = actor.get_actor_label()
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not component:
        continue
    if label.startswith('SW_Vista_Mountain_'):
        for slot in range(component.get_num_materials()):
            component.set_material(slot, materials['mountain'])
        mountains += 1
    elif label.startswith(('SW_Tree_', 'SW_Vista_Canopy_', 'SW_Vista_FarCanopy_')):
        for slot in range(component.get_num_materials()):
            current = component.get_material(slot)
            name = current.get_name().lower() if current else ''
            if 'bark' in name or 'crevice' in name:
                component.set_material(slot, materials['bark'])
            elif 'leaf' in name or 'leaves' in name:
                key = 'leaf_sun' if 'sun' in name else ('leaf_deep' if 'deep' in name else 'leaf_mid')
                component.set_material(slot, materials[key])
        trees += 1
    elif label == 'SW_MorningSun':
        actor.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property('intensity', 2.1)
    elif label == 'SW_Skylight':
        actor.get_component_by_class(unreal.SkyLightComponent).set_editor_property('intensity', .72)

unreal.EditorLevelLibrary.save_current_level()
note('APPLIED character surfaces, ' + str(mountains) + ' mountains, ' +
     str(trees) + ' trees and softer daylight')
