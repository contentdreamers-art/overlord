"""Remove level-design stand-ins after the C++ actors are compiled.

The gameplay module spawns the adventurer, goblin, and reward pickups at runtime.
"""
import unreal

unreal.EditorLevelLibrary.load_level('/Game/soulwood')
world = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
labels = {
    'SW_Adventurer_display', 'SW_Goblin_encounter',
    'SW_GoldEssence', 'SW_BeastSoul', 'SW_AngelSoul',
    'SW_GoldEssenceGlow', 'SW_BeastSoulGlow', 'SW_AngelSoulGlow',
}
removed = 0
for actor in world.get_all_level_actors():
    if actor.get_actor_label() in labels:
        world.destroy_actor(actor)
        removed += 1
unreal.EditorLevelLibrary.save_current_level()
unreal.log('SOULWOOD: FINALIZED removed_standins=' + str(removed))
