"""Reimport the original Blender hero and goblin without rebuilding the level."""
import os
import unreal

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
source_dir = os.path.join(root, 'blender', 'generated')
assets = unreal.AssetToolsHelpers.get_asset_tools()
library = unreal.EditorAssetLibrary
destination = '/Game/SoulwoodOriginal/Characters'

for name in ('SK_Adventurer', 'SK_Goblin'):
    filename = os.path.join(source_dir, name + '.fbx')
    if not os.path.exists(filename):
        raise RuntimeError('Missing Blender export: ' + filename)
    skeleton = library.load_asset(destination + '/' + name + '_Skeleton')
    if not skeleton:
        raise RuntimeError('Missing existing skeleton for ' + name)
    task = unreal.AssetImportTask()
    task.set_editor_property('filename', filename)
    task.set_editor_property('destination_path', destination)
    task.set_editor_property('automated', True)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('save', True)
    options = unreal.FbxImportUI()
    options.set_editor_property('import_mesh', True)
    options.set_editor_property('import_as_skeletal', True)
    options.set_editor_property('import_animations', True)
    options.set_editor_property('import_materials', True)
    options.set_editor_property('import_textures', False)
    options.set_editor_property('skeleton', skeleton)
    task.set_editor_property('options', options)
    assets.import_asset_tasks([task])
    paths = task.get_editor_property('imported_object_paths')
    unreal.log('SOULWOOD_CHARACTER: ' + name + ' imported ' + str(paths))

unreal.EditorLevelLibrary.save_current_level()
