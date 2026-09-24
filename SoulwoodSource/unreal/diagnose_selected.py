"""Log the selected viewport actor to identify an obstructing scene object."""
import unreal

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_selected_level_actors()
for actor in actors:
    meshes = []
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property('static_mesh')
        meshes.append(mesh.get_name() if mesh else '(none)')
    unreal.log('SOULWOOD_SELECTED: ' + actor.get_actor_label() +
               ' location=' + str(actor.get_actor_location()) +
               ' meshes=' + str(meshes))
