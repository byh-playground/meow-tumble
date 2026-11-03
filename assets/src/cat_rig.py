import bpy, bmesh, math, os
from mathutils import Vector, Quaternion
NO_EXPORT = True
exec(open(os.path.join(ASSETS_SRC, 'cat.py'), encoding='utf-8').read())   # part builders: body, head, ear, paw, sphere, fixed, game
bpy.ops.wm.read_factory_settings(use_empty=True)

FUR = (1, 1, 1, 1); ACCENT = (1, 1, 1, .5)
bm = bmesh.new(); colours = {}; groups = {}          # vert -> rgba ; vert -> [(bone, weight)]
def add(fn, scale, offset, bone, tint=None, rot=None):
    """Build the part in its own bmesh (some builders subdivide everything they can see), then copy it into the shared mesh."""
    tb = bmesh.new(); local = fn(tb) or {}; tb.verts.ensure_lookup_table()
    vmap = {}
    for v in tb.verts:
        co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
        if rot: co = rot @ co
        nv = bm.verts.new(co + Vector(offset)); vmap[v] = nv
        colours[nv] = local.get(v, tint or FUR); groups[nv] = [(bone, 1.0)]
    for f in tb.faces: bm.faces.new([vmap[v] for v in f.verts])
    tb.free()
    return list(vmap.values())

# --- parts at their rig-space positions (game axes), sizes from the old primitive draw calls ---
add(lambda b: sphere(b, (1, 1, 1), segments=28, rings=18) and None or {}, (.53, .43, .72), (0, .57, -.14), 'spine')
add(lambda b: (sphere(b, (1, 1, 1), segments=20, rings=12), {})[1], (.40, .31, .46), (0, .43, .23), 'spine', (1, .94, .82, 0))       # belly
add(lambda b: (sphere(b, (1, 1, 1), segments=20, rings=10), {})[1], (.34, .075, .56), (0, .905, -.22), 'spine', ACCENT)               # back patch
add(head, (1, 1, 1), (0, .79, .55), 'head')
for sx in (-1, 1): add(ear, (.28, .44, .25), (sx * .26, 1.16, .70), 'earL' if sx < 0 else 'earR')
for name, (sx, sz) in {'pawFL': (-1, 1), 'pawFR': (1, 1), 'pawBL': (-1, -1), 'pawBR': (1, -1)}.items():
    add(paw, (.18, .25, .23), (sx * .35, .27, sz * .45), name)

# --- banded tail: a tube along the old three-piece path, weighted smoothly across four bones ---
TAIL = [Vector(p) for p in [(0, .72, -.73), (.13, .97, -1.0), (.30, 1.3, -1.36), (.30, 1.6, -1.47)]]
def tail_at(u):
    s = min(2, int(u * 3)); f = u * 3 - s; return TAIL[s].lerp(TAIL[s + 1], f)
rings, seg = 22, 12
ring_verts = []
for i in range(rings + 1):
    u = i / rings; c = tail_at(u); d = (tail_at(min(1, u + .02)) - tail_at(max(0, u - .02))).normalized()
    a = d.cross(Vector((1, 0, 0))); a = a.normalized() if a.length > .1 else d.cross(Vector((0, 1, 0))).normalized(); b2 = d.cross(a).normalized()
    r = .14 - .055 * u
    ring = [bm.verts.new(c + (a * math.cos(k / seg * math.tau) + b2 * math.sin(k / seg * math.tau)) * r) for k in range(seg)]
    ring_verts.append(ring)
    band = ACCENT if int(u * 7.0 - 1e-6) % 2 == 0 else FUR
    w = u * 3.0                                         # tail bone chain t1..t3 share the weight
    for v in ring:
        colours[v] = band
        j = min(2, int(w)); f = w - j
        groups[v] = [(f'tail{j + 1}', 1 - f)] + ([(f'tail{j + 2}', f)] if f > 0 else [])
for i in range(rings):
    for k in range(seg):
        bm.faces.new((ring_verts[i][k], ring_verts[i][(k + 1) % seg], ring_verts[i + 1][(k + 1) % seg], ring_verts[i + 1][k]))
tip = bm.verts.new(TAIL[3] + (TAIL[3] - TAIL[2]).normalized() * .05); colours[tip] = ACCENT; groups[tip] = [('tail3', .5), ('tail4', .5)]
for k in range(seg): bm.faces.new((ring_verts[rings][(k + 1) % seg], ring_verts[rings][k], tip))
# --- short cheek whiskers (thin, cream) ---
for sx in (-1, 1):
    for n in range(2):
        a = Vector((sx * .33, .665 - n * .05, .905)); b = Vector((sx * .47, .68 - n * .095, .92))
        d = (b - a); r = .0065
        v0 = [bm.verts.new(a + Vector((0, math.cos(k * math.tau / 4) * r, math.sin(k * math.tau / 4) * r))) for k in range(4)]
        v1 = [bm.verts.new(b + Vector((0, math.cos(k * math.tau / 4) * r, math.sin(k * math.tau / 4) * r))) for k in range(4)]
        for k in range(4): bm.faces.new((v0[k], v0[(k + 1) % 4], v1[(k + 1) % 4], v1[k]))
        for v in v0 + v1: colours[v] = fixed(.99, .95, .86); groups[v] = [('head', 1.0)]

for v in bm.verts: v.co = game(v.co)
bm.normal_update(); bm.verts.index_update()
mesh = bpy.data.meshes.new('CatRig'); bm.to_mesh(mesh)
attr = mesh.color_attributes.new('detail', 'FLOAT_COLOR', 'POINT')
for v in bm.verts: attr.data[v.index].color = colours.get(v, FUR)
vert_groups = [(v.index, groups.get(v, [('spine', 1.0)])) for v in bm.verts]
bm.free()
for p in mesh.polygons: p.use_smooth = True
obj = bpy.data.objects.new('CatRig', mesh); bpy.context.scene.collection.objects.link(obj)
for idx, gl in vert_groups:
    for bone, w in gl:
        vg = obj.vertex_groups.get(bone) or obj.vertex_groups.new(name=bone); vg.add([idx], w, 'REPLACE')

# --- armature (game-space bone positions) ---
win = bpy.context.window_manager.windows[0]
area = next((a for a in win.screen.areas if a.type == 'VIEW_3D'), win.screen.areas[0]); region = next((r for r in area.regions if r.type == 'WINDOW'), None)
arm = bpy.data.armatures.new('CatArmature'); rig = bpy.data.objects.new('CatArmature', arm); bpy.context.scene.collection.objects.link(rig)
BONES = {   # name: (head, tail, parent)  game axes
    'root':  ((0, .30, -.2), (0, .30, .1), None),
    'spine': ((0, .55, -.40), (0, .62, .25), 'root'),
    'head':  ((0, .65, .35), (0, .90, .62), 'spine'),
    'earL':  ((-.26, 1.08, .68), (-.26, 1.42, .72), 'head'),
    'earR':  ((.26, 1.08, .68), (.26, 1.42, .72), 'head'),
    'pawFL': ((-.35, .50, .45), (-.35, .10, .50), 'spine'),
    'pawFR': ((.35, .50, .45), (.35, .10, .50), 'spine'),
    'pawBL': ((-.35, .50, -.45), (-.35, .10, -.40), 'spine'),
    'pawBR': ((.35, .50, -.45), (.35, .10, -.40), 'spine'),
    'tail1': ((0, .72, -.73), (.13, .97, -1.0), 'spine'),
    'tail2': ((.13, .97, -1.0), (.30, 1.3, -1.36), 'tail1'),
    'tail3': ((.30, 1.3, -1.36), (.30, 1.6, -1.47), 'tail2'),
    'tail4': ((.30, 1.6, -1.47), (.30, 1.72, -1.50), 'tail3'),
}
bpy.context.view_layer.objects.active = rig
with bpy.context.temp_override(window=win, screen=win.screen, area=area, region=region, scene=bpy.context.scene, view_layer=bpy.context.view_layer, active_object=rig, object=rig):
    bpy.ops.object.mode_set(mode='EDIT')
    for name, (h, t, parent) in BONES.items():
        eb = arm.edit_bones.new(name); eb.head = game(h); eb.tail = game(t)
        if parent: eb.parent = arm.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
obj.parent = rig; mod = obj.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
print('rig ok', len(arm.bones), 'verts', len(mesh.vertices))
