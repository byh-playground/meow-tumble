import bpy, bmesh, math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
TINT = (1, 1, 1, 1)                       # alpha 1: takes the caller's colour (shirt, skin, hair, shoes...)
def fixed(r, g, b): return (r, g, b, 0)   # alpha 0: authored colour

def game(v): return Vector((v[0], -v[2], v[1]))   # game (x right, y up, z forward) -> Blender Z-up, forward -Y

def smoothstep(a, b, x):
    t = max(0, min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t)

def rbox(bm, size, centre=(0, 0, 0), r=.1, seg=4):
    """Rounded box in game axes; size is the full extent. Returns its verts."""
    existing = set(bm.verts)
    res = bmesh.ops.create_cube(bm, size=1.0)
    verts = res['verts']
    for v in verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    edges = list({e for v in verts for e in v.link_edges})
    bmesh.ops.bevel(bm, geom=edges, offset=r, segments=seg, profile=.5, affect='EDGES')
    made = [v for v in bm.verts if v not in existing]      # bevel replaces the cube's own verts
    for v in made: v.co += Vector(centre)
    return made

def ball(bm, radii, centre, seg=14, rings=10):
    res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in res['verts']: v.co = Vector((v.co.x * radii[0], v.co.y * radii[1], v.co.z * radii[2])) + Vector(centre)
    return res['verts']

def build(name, fn):
    bm = bmesh.new(); colours = fn(bm)
    for v in bm.verts: v.co = game(v.co)
    bm.normal_update(); bm.verts.index_update()
    rgba = [colours.get(v, TINT) for v in bm.verts]
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh)
    attr = mesh.color_attributes.new('detail', 'FLOAT_COLOR', 'POINT')
    for i, c in enumerate(rgba): attr.data[i].color = c
    bm.free()
    for p in mesh.polygons: p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj); return obj

def torso(bm):                               # cube [1.27, 1.25, .74]
    vs = rbox(bm, (1.27, 1.25, .74), r=.17, seg=5)
    for v in vs:
        ny = v.co.y / .625
        v.co.x *= 1 + .05 * ny - .035 * max(0, -ny)          # broader shoulders, slimmer waist
        if v.co.z > 0: v.co.z += .035 * max(0, ny)            # chest
    return {}

def hips(bm):                                # cube [.98, .52, .52]
    rbox(bm, (.98, .52, .52), r=.13, seg=4); return {}

def head(bm):                                # cube [.91, 1.09, .79]; origin = head centre
    colours = {}
    for v in rbox(bm, (.91, 1.09, .79), r=.30, seg=6):
        ny = v.co.y / .545
        k = 1 - .09 * smoothstep(0, 1, -ny)                   # tapered jaw
        v.co.x *= k; v.co.z *= 1 - .05 * smoothstep(0, 1, -ny)
    for side in (-1, 1): ball(bm, (.085, .14, .10), (side * .49, .01, -.01), 12, 9)   # ears
    ball(bm, (.06, .08, .055), (0, -.09, .413), 12, 9)                                  # nose
    return colours

def hair(tuft_x, tuft_size, tuft_y, tuft_z):
    def fn(bm):
        rbox(bm, (.97, .27, .86), (0, .45, -.06), r=.11, seg=4)        # crown
        rbox(bm, (.97, .16, .20), (0, .36, .32), r=.07, seg=3)         # fringe
        rbox(bm, tuft_size, (tuft_x, tuft_y, tuft_z), r=.10, seg=3)    # side tuft
        return {}
    return fn

def shoe(bm):                                # cube [.48, .21, .77]
    colours = {}
    vs = rbox(bm, (.48, .21, .77), r=.085, seg=4)
    for v in vs:
        if v.co.z > .1: v.co.y += .025 * smoothstep(.1, .38, v.co.z) * (1 if v.co.y > 0 else 0)   # toe cap rises
        if v.co.y < -.06: colours[v] = fixed(.93, .92, .88)                                        # pale sole
    return colours

def hand(bm):                                # cube [.30, .26, .23]
    rbox(bm, (.30, .26, .23), r=.085, seg=4); return {}

objs = [build('humanTorso', torso), build('humanHips', hips), build('humanHead', head),
        build('humanHair0', hair(-.31, (.37, .24, .76), .32, -.12)), build('humanHair1', hair(.22, (.50, .25, .81), .38, -.11)),
        build('humanShoe', shoe), build('humanHand', hand)]
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
win = bpy.context.window_manager.windows[0]
with bpy.context.temp_override(window=win, screen=win.screen, scene=bpy.context.scene, view_layer=bpy.context.view_layer, active_object=objs[0], selected_objects=objs):
    bpy.ops.export_scene.gltf(filepath=r'C:\projects\meow-tumble\assets\models\human.glb', export_format='GLB', use_selection=True, export_apply=True,
                              export_vertex_color='ACTIVE', export_active_vertex_color_when_no_material=True, export_materials='NONE')
print({o.name: (len(o.data.vertices), tuple(round(x, 2) for x in o.dimensions)) for o in objs})
