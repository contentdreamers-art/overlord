# Soulwood original asset build

This source builds the Soulwood encounter inside the existing Unreal project at
`C:\Users\Shadow\Documents\Unreal Projects\soulwoodgame`. The target map is
`/Game/soulwood`. All character, foliage, prop, and wing meshes are authored by
`blender/make_soulwood.py`; the generator also creates their animation clips.

## Build order

1. Run `blender/make_soulwood.py` in Blender's Scripting workspace. Blender's
   Text Editor may export to `C:\generated`; copy those FBX files into
   `SoulwoodSource/blender/generated` before importing in Unreal.
2. In Unreal's Python console, run `unreal/build_soulwood.py` to import those
   FBXs and populate the user's existing Soulwood map.
3. Run `install-to-project.ps1` in PowerShell. The script adds the gameplay C++
   module and legacy input mappings to the project.
4. With the Unreal editor closed, run `build-on-shadow.ps1` in PowerShell.
5. Reopen `soulwoodgame.uproject` and run `unreal/finalize_soulwood.py` in the
   Python console to remove the encounter display stand-ins. Play the map.

## Current art pass

Run `blender/make_enhanced_forest.py` in Blender's Scripting workspace. Copy
its detailed tree, fern, and litter FBX files from `C:\generated` into
`SoulwoodSource/blender/generated`. Run `unreal/make_forest_textures.py` with
Python to create original surface textures. In the Unreal Python console run
`unreal/enhance_soulwood.py` to replace trees, texture the floor and path, and
scatter scaled foliage. After editing and exporting either character in
Blender, run `unreal/reimport_characters.py` to update the existing meshes and
animations while keeping their skeletons.

The Microsoft Store Blender executable on the current Shadow PC cannot be
started by PowerShell directly. Open Blender and run the scripts from its
Scripting workspace.

## Visual status

This is a playable prototype and art blockout. The current hero, castle, terrain,
and forest are visibly simpler than the realistic reference images. The source
is designed for further original modeling and texture work; the present art
should not be presented as the requested final quality.

## Controls

WASD moves, mouse aims, Space jumps or rises in flight, Left Ctrl descends,
1 equips the bow, 2 selects Fireball after unlock, 0 holsters, left mouse
press and release attacks, Q toggles Beast speed, and F toggles wings/flight.

## Project boundary

`SoulwoodSource` is the original source. The actual Unreal `.uasset` files,
compiled binaries, and `.blend` output are generated on the Shadow PC inside
the existing `soulwoodgame` project. No marketplace meshes or animations are
used by these scripts.
