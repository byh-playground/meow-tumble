import bpy, bmesh, math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
TINT = (1, 1, 1, 1)                       # alpha 1: takes the caller's coat colour
def fixed(r, g, b): return (r, g, b, 0)   # alpha 0: authored colour, never tinted

def game(v):                              # game axes (x right, y up, z forward) -> Blender (Z-up, forward = -Y)
    return Vector((v[0], -v[2], v[1]))

def sphere(bm, radii, centre=(0, 0, 0), segments=24, rings=16):
    res = bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0)
    for v in res['verts']:
        v.co = Vector((v.co.x * radii[0], v.co.y * radii[1], v.co.z * radii[2])) + Vector(centre)
    return res['verts']

def build(name, fn):
    """fn fills a bmesh in GAME axes and returns {vert: rgba}; vertices are converted afterwards."""
    bm = bmesh.new(); colours = fn(bm)
    for v in bm.verts: v.co = game(v.co)
    bm.normal_update()
    bm.verts.index_update()
    rgba = [colours.get(v, TINT) for v in bm.verts]   # colours are keyed by BMVert, indices are only valid now
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh)
    attr = mesh.color_attributes.new('detail', 'FLOAT_COLOR', 'POINT')
    for i, c in enumerate(rgba): attr.data[i].color = c
    bm.free()
    for p in mesh.polygons: p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj); return obj

def smoothstep(a, b, x):
    t = max(0, min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t)

# ---- body: unit-radius pear shape, drawn with the game's [.53,.43,.72]-style size ----
def body(bm):
    sphere(bm, (1, 1, 1), segments=28, rings=18)
    for v in bm.verts:
        z = v.co.y if False else v.co.z      # game z is forward (still game axes here)
        v.co.x *= 1 + .10 * smoothstep(-.2, -1, v.co.y * 0 + v.co.z)   # fuller hips behind
        v.co.y *= 1 - .06 * smoothstep(-.5, .6, v.co.z) * 0 + (.05 * smoothstep(0, 1, v.co.z))  # chest rises a little
        v.co.y -= .05 * math.cos(v.co.z * 1.6) * max(0, v.co.y)         # shallow back dip
    return {}

# ---- head with face: origin = head centre, absolute game units ----
def head(bm):
    colours = {}
    verts = sphere(bm, (.45, .43, .44), segments=32, rings=20)
    for v in verts:
        x, y, z = v.co
        cheek = smoothstep(.0, .5, z / .44) * smoothstep(.1, -.35, y / .43)
        v.co.x *= 1 + .12 * cheek                      # cheeks
        if z > .25 and y < 0: v.co.z += .045 * smoothstep(.25, .44, z) * (1 - abs(x) / .5)   # muzzle
        v.co.y += .02 * smoothstep(.1, .44, z) * (1 if y > 0 else 0)                          # brow
    def part(radii, centre, rgba, seg=14, rings=10):
        vs = sphere(bm, radii, centre, seg, rings)
        for v in vs: colours[v] = rgba
    bm.verts.ensure_lookup_table()
    for side in (-1, 1):
        part((.14, .17, .13), (side * .18, .065, .36), fixed(1, .98, .93), 16, 12)      # eye white
        part((.066, .118, .062), (side * .18, .065, .462), fixed(.12, .11, .20), 14, 10)  # pupil (front must clear the white)
        part((.03, .044, .026), (side * .152, .115, .52), fixed(1, 1, 1), 8, 6)          # highlight
        part((.05, .028, .03), (side * .10, -.14, .435), fixed(.99, .86, .80), 10, 8)   # muzzle pad
    part((.09, .07, .07), (0, -.10, .465), fixed(.99, .61, .66), 12, 10)               # nose
    return colours

# ---- ear: unit cone box (height 1, base 1), apex +y, inner ear painted on the front (+z) ----
def ear(bm):
    colours = {}
    seg = 14
    ring = []
    for i in range(seg):
        a = i / seg * math.tau
        ring.append(bm.verts.new((math.cos(a) * .5, -.5, math.sin(a) * .5 * .85)))
    apex = bm.verts.new((0, .5, .02))
    bm.verts.ensure_lookup_table()
    for i in range(seg):
        bm.faces.new((ring[i], ring[(i + 1) % seg], apex))
    bm.faces.new(list(reversed(ring)))
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        # soft rounded tip and a slight forward lean
        v.co.z += .06 * (v.co.y + .5) ** 2
    # inner ear: a smaller flattened cone sitting just in front of the outer surface, painted pink
    inner = []
    for i in range(seg):
        a = i / seg * math.tau
        inner.append(bm.verts.new((math.cos(a) * .27, -.40, .13 + math.sin(a) * .12)))
    tip = bm.verts.new((0, .30, .17))
    for i in range(seg): bm.faces.new((inner[i], inner[(i + 1) % seg], tip))
    bm.faces.new(list(reversed(inner)))
    for v in inner + [tip]: colours[v] = fixed(.99, .62, .70)
    return colours

# ---- paw: unit rounded foot, flat sole, toe bumps toward +z ----
def paw(bm):
    colours = {}
    vs = sphere(bm, (1, 1, 1), segments=20, rings=14)
    for v in vs:
        if v.co.y < -.62: v.co.y = -.62 - (v.co.y + .62) * .15       # flat sole
    for x in (-.45, 0, .45):
        for v in sphere(bm, (.30, .26, .30), (x, -.38, .78 - abs(x) * .25), 10, 8): pass
    for v in bm.verts:
        if v.co.y < -.55 and v.co.z > .1: colours[v] = fixed(.99, .66, .72)
    return colours

objs = [build('catBody', body), build('catHead', head), build('catEar', ear), build('catPaw', paw)]
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
win = bpy.context.window_manager.windows[0]
with bpy.context.temp_override(window=win, screen=win.screen, scene=bpy.context.scene, view_layer=bpy.context.view_layer, active_object=objs[0], selected_objects=objs):
    bpy.ops.export_scene.gltf(filepath=r'C:\projects\meow-tumble\assets\models\cat.glb', export_format='GLB', use_selection=True, export_apply=True,
                              export_vertex_color='ACTIVE', export_active_vertex_color_when_no_material=True, export_materials='NONE')
print({o.name: (len(o.data.vertices), tuple(round(x, 2) for x in o.dimensions)) for o in objs})
