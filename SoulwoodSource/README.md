# Soulwood original asset build

This source builds the Soulwood encounter inside the existing Unreal project at
`C:\Users\Shadow\Documents\Unreal Projects\soulwoodgame`. The target map is
`/Game/soulwood`. All character, foliage, prop, and wing meshes are authored by
`blender/make_soulwood.py`; the generator also creates their animation clips.

## Build order

1. Run `blender/make_soulwood.py` in Blender's Scripting workspace. Move its
   `generated` folder beneath `SoulwoodSource/blender` if Blender's editor
   executes the script from a different current directory.
2. In Unreal's Python console, run `unreal/build_soulwood.py` to import those
   FBXs and populate the user's existing Soulwood map.
3. Run `install-to-project.ps1` in PowerShell. The script adds the gameplay C++
   module and legacy input mappings to the project.
4. With the Unreal editor closed, run `build-on-shadow.ps1` in PowerShell.
5. Reopen `soulwoodgame.uproject` and run `unreal/finalize_soulwood.py` in the
   Python console to remove the encounter display stand-ins. Play the map.

## Controls

WASD moves, mouse aims, Space jumps or rises in flight, Left Ctrl descends,
1 equips the bow, 2 selects Fireball after unlock, 0 holsters, left mouse
press and release attacks, Q toggles Beast speed, and F toggles wings/flight.

## Project boundary

`SoulwoodSource` is the original source. The actual Unreal `.uasset` files,
compiled binaries, and `.blend` output are generated on the Shadow PC inside
the existing `soulwoodgame` project. No marketplace meshes or animations are
used by these scripts.
