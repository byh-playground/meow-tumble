import bpy, bmesh
bpy.ops.wm.read_factory_settings(use_empty=True)
W, H, L = 1.07, 0.70, 3.48          # TOWER.width/height/length, game axes x/y/z
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts: v.co.x *= W; v.co.y *= L; v.co.z *= H     # Blender Z-up: X width, Y length, Z height -> glTF y=height, z=length
bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.05, segments=3, profile=0.5, affect='EDGES')
bm.normal_update()
mesh = bpy.data.meshes.new('JengaBlock'); bm.to_mesh(mesh); bm.free()
for p in mesh.polygons: p.use_smooth = True
obj = bpy.data.objects.new('JengaBlock', mesh); bpy.context.scene.collection.objects.link(obj)
mat = bpy.data.materials.new('Wood'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.85, 0.6, 0.33, 1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.8
obj.data.materials.append(mat)
bpy.context.view_layer.objects.active = obj; obj.select_set(True)
win = bpy.context.window_manager.windows[0]
with bpy.context.temp_override(window=win, screen=win.screen, scene=bpy.context.scene, view_layer=bpy.context.view_layer, active_object=obj, selected_objects=[obj]):
  bpy.ops.export_scene.gltf(filepath=r'C:\projects\meow-tumble\assets\models\block.glb', export_format='GLB', use_selection=True, export_apply=True)
print('verts', len(obj.data.vertices), 'faces', len(obj.data.polygons), 'dims', tuple(round(v,3) for v in obj.dimensions))
