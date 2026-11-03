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

# ---- head with face: origin = head centre, absolute game units. EXPR picks the expression preset. ----
EXPR_NAME = globals().get('EXPR_NAME', 'final')
PRESETS = {
    'final': dict(left='dot', right='dot', lid=0, look=0, brows=[], mouth='smugcat'),
}
EX = PRESETS[EXPR_NAME]

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
        return vs
    bm.verts.ensure_lookup_table()
    BROW = fixed(.42, .26, .14); MOUTH = fixed(.27, .15, .15); TONGUE = fixed(.99, .45, .55); INK = fixed(.16, .12, .14)
    def surface_z(x, y):                              # approximate head surface in front, for placing flat details
        return .44 * math.sqrt(max(.2, 1 - (x / .45) ** 2 - (y / .43) ** 2)) + .045 * max(0, 1 - abs(x) / .5) * (1 if y < 0 else 0)
    def line(points, radius=.015, colour=MOUTH, lift=.006):
        for (x, y) in points:
            for v in sphere(bm, (radius, radius, radius * .8), (x, y, surface_z(x, y) + lift), 6, 4): colours[v] = colour
    def eye(kind, side, cx, cy, cz):
        if kind == 'dot':
            part((.04, .055, .03), (cx, cy, cz + .01), fixed(.10, .09, .14), 12, 9); return
        if kind == 'wink':                            # a closed, upward-arching eye ("^")
            line([(cx + (t / 10 - .5) * .17, cy - .01 + .05 * (1 - (t / 5 - 1) ** 2)) for t in range(11)], .013, INK, .008); return
        part((.10, .115, .09), (cx, cy, cz), fixed(1, .98, .93), 16, 12)
        part((.045, .07, .04), (cx + EX['look'], cy - .012, cz + .07), fixed(.12, .11, .20), 12, 9)
        part((.02, .028, .018), (cx + EX['look'] - .01, cy + .02, cz + .104), fixed(1, 1, 1), 8, 6)
        lid = sphere(bm, (.112, .13, .10), (cx, cy, cz + .004), 16, 12)       # upper lid in coat colour
        for v in lid:
            if v.co.y < cy + EX['lid']: v.co.y = cy + EX['lid']
        if kind == 'slit':                            # lower lid closes the eye to a thin slit
            low = sphere(bm, (.112, .13, .10), (cx, cy, cz + .004), 16, 12)
            for v in low:
                if v.co.y > cy - .045: v.co.y = cy - .045
    for side, key in ((-1, 'left'), (1, 'right')):
        eye(EX[key], side, side * .19, .06, .385)
        part((.05, .028, .03), (side * .10, -.14, .435), fixed(.99, .86, .80), 10, 8)       # muzzle pad
    def brow(centre_x, centre_y, tilt):               # a short brow bar rotated about the head's forward axis
        c = math.cos(tilt); sn = math.sin(tilt)
        for v in sphere(bm, (.085, .017, .02), (0, 0, 0), 10, 6):
            x, y = v.co.x * c - v.co.y * sn, v.co.x * sn + v.co.y * c
            v.co = Vector((x + centre_x, y + centre_y, surface_z(centre_x, centre_y) + .004)); colours[v] = BROW
    for (bx, by, bt) in EX['brows']: brow(bx, by, bt)
    m = EX['mouth']
    if m == 'smirk':
        line([(-.12 + .27 * t / 30, -.215 - .012 * math.sin(math.pi * t / 30) + .06 * max(0, t / 30 - .45) ** 1.4) for t in range(31)], .016)
    elif m == 'flat':
        line([(-.07 + .14 * t / 14, -.215) for t in range(15)], .013)
    elif m == 'grin':
        line([(-.17 + .34 * t / 34, -.245 + .075 * (-.17 + .34 * t / 34) ** 2 / .0289 * .55 - .0) for t in range(35)], .016)
    elif m == 'omega':
        line([(.0, -.15 - .03 * t / 5) for t in range(6)], .012)
        line([(-.07 * math.sin(math.pi * t / 14) - .0, -.18 - .03 * math.sin(math.pi * t / 14) - .0 * t) for t in range(0)], .012)
        for sgn in (-1, 1):
            line([(sgn * .075 * (1 - math.cos(math.pi * t / 14)) / 1.0 * .5 + sgn * .0, -.185 - .035 * math.sin(math.pi * t / 14)) for t in range(15)], .012)
    elif m == 'smugcat':
        # Expression lives in the mouth: a cat "w" whose right corner climbs into a dimple, plus one small fang.
        line([(0, -.165 - .06 * t / 6) for t in range(7)], .021)                                                    # philtrum
        line([(-.17 * t / 18, -.232 - .048 * math.sin(math.pi * t / 18) + .030 * (t / 18) ** 3) for t in range(19)], .021)    # left curl
        line([(.21 * t / 24, -.232 - .048 * math.sin(math.pi * t / 24) + .105 * (t / 24) ** 2.2) for t in range(25)], .021)   # right curl, lifted
        line([(.236, -.150), (.250, -.134), (.258, -.114)], .016)                                                   # dimple tick
        part((.018, .036, .014), (-.105, -.262, surface_z(-.105, -.262) + .005), fixed(1, .98, .93), 8, 6)         # fang
    elif m == 'tongue':
        line([(-.12 + .27 * t / 30, -.215 - .012 * math.sin(math.pi * t / 30) + .04 * max(0, t / 30 - .5) ** 1.4) for t in range(31)], .016)
        part((.05, .018, .075), (.035, -.25, surface_z(.035, -.25) + .02), TONGUE, 10, 8)
    for side in (-1, 1):                              # cheek blush, as in the reference
        bx, by = side * .30, -.075
        part((.09, .062, .03), (bx, by, surface_z(bx, by) + .006), fixed(1, .70, .66), 14, 10)
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

if not globals().get('NO_EXPORT'):
    objs = [build('catBody', body), build('catHead', head), build('catEar', ear), build('catPaw', paw)]
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    win = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=win, screen=win.screen, scene=bpy.context.scene, view_layer=bpy.context.view_layer, active_object=objs[0], selected_objects=objs):
        bpy.ops.export_scene.gltf(filepath=r'C:\projects\meow-tumble\assets\models\cat.glb', export_format='GLB', use_selection=True, export_apply=True,
                                  export_vertex_color='ACTIVE', export_active_vertex_color_when_no_material=True, export_materials='NONE')
    print({o.name: (len(o.data.vertices), tuple(round(x, 2) for x in o.dimensions)) for o in objs})
