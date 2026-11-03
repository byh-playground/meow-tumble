# Builds assets/models/cat-rig.glb inside a running Blender (5.x): the face/parts (cat.py), the rig and skinning (cat_rig.py) and the
# animation clips (cat_clips.py) run as one script, then the glb is exported. Run it from Blender's Text editor with ASSETS_SRC
# pointing at this folder, or through the Blender MCP `execute_code` tool.
import os
ASSETS_SRC = globals().get('ASSETS_SRC', os.path.dirname(os.path.abspath(__file__)))
code = ''
for name in ('cat_rig.py', 'cat_clips.py'):
    code += open(os.path.join(ASSETS_SRC, name), encoding='utf-8').read() + '\n'
code += '''
objs = [obj, rig]
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = rig
win = bpy.context.window_manager.windows[0]
with bpy.context.temp_override(window=win, screen=win.screen, scene=bpy.context.scene, view_layer=bpy.context.view_layer, active_object=rig, selected_objects=objs):
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', use_selection=True, export_apply=False,
        export_vertex_color='ACTIVE', export_active_vertex_color_when_no_material=True, export_materials='NONE',
        export_animations=True, export_animation_mode='ACTIONS', export_skins=True, export_force_sampling=True)
print('exported', OUT_GLB)
'''
OUT_GLB = globals().get('OUT_GLB', os.path.join(ASSETS_SRC, '..', 'models', 'cat-rig.glb'))
exec(code)
