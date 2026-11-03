# ---- animation clips: poses are described in GAME axes (x right, y up, z forward), applied relative to each bone's rest frame ----
FPS = 30
rig.animation_data_create()
pb = rig.pose.bones
for b in pb: b.rotation_mode = 'QUATERNION'

def _basis(b): return b.bone.matrix_local.to_3x3()            # bone rest axes in armature space
def rot(bone, axis, deg):
    """Quaternion for a rotation of `deg` degrees about a game-space axis, expressed in the bone's local frame."""
    m = _basis(pb[bone]); a = (m.inverted() @ game(axis)).normalized(); return Quaternion(a, math.radians(deg))
def loc(bone, off): return _basis(pb[bone]).inverted() @ game(off)
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)

def make_clip(name, frames, spec, loop=True):
    """spec(frame) -> {bone: {'rot': [(axis, deg), ...], 'loc': (x, y, z), 'scale': (sx, sy, sz)}} in game axes; unnamed bones stay at rest."""
    act = bpy.data.actions.new(name); act.use_fake_user = True; rig.animation_data.action = act
    for f in frames:
        s = spec(f)
        for b in pb:
            p = s.get(b.name, {})
            q = Quaternion((1, 0, 0, 0))
            for axis, deg in p.get('rot', []): q = rot(b.name, axis, deg) @ q
            b.rotation_quaternion = q
            b.location = loc(b.name, p['loc']) if 'loc' in p else Vector((0, 0, 0))
            sc = p.get('scale', (1, 1, 1)); b.scale = Vector((sc[0], sc[2], sc[1]))        # local Y runs along the bone (game z for horizontal bones)
            b.keyframe_insert('rotation_quaternion', frame=f); b.keyframe_insert('location', frame=f); b.keyframe_insert('scale', frame=f)
    return act

def tail_wave(f, n, amp, speed, lag=7, base=0):
    """Yaw/pitch for the four tail bones with travelling lag, returns per-bone dict."""
    out = {}
    for i, bone in enumerate(('tail1', 'tail2', 'tail3', 'tail4')):
        ph = (f - lag * i) / n * math.tau * speed
        out[bone] = {'rot': [(Y, amp * (.5 + .35 * i) * math.sin(ph)), (X, base * (.6 + .2 * i))]}
    return out

def idle(f):
    n = 60; ph = f / n * math.tau
    s = {'spine': {'loc': (0, .012 * math.sin(ph * 2), 0)}, 'head': {'rot': [(X, 2.5 * math.sin(ph * 2 - .6))]}}
    s.update(tail_wave(f, n, 7, 1)); s['earL'] = {'rot': [(Z, 14 if 40 <= f < 46 else 0)]}
    return s

def walk(f):
    n = 18; ph = f / n * math.tau; s = {}
    for bone, sign in (('pawFL', 1), ('pawBR', 1), ('pawFR', -1), ('pawBL', -1)):
        a = ph if sign > 0 else ph + math.pi
        s[bone] = {'loc': (0, .10 * max(0, math.sin(a + 1.2)), .10 * math.sin(a))}
    s['spine'] = {'loc': (0, .028 * abs(math.sin(ph)), 0), 'rot': [(Y, 3.5 * math.sin(ph))]}
    s['head'] = {'rot': [(Y, -3 * math.sin(ph)), (X, 2 * math.sin(2 * ph))]}
    s.update(tail_wave(f, n, 10, 1, lag=3))
    return s

def ease(t): t = max(0, min(1, t)); return t * t * (3 - 2 * t)
def lerp_(a, b, t): return a + (b - a) * t
PAWS = {'pawFL': (-1, 1), 'pawFR': (1, 1), 'pawBL': (-1, -1), 'pawBR': (1, -1)}   # side (x sign), front(+1)/back(-1)

def charge(f):                       # scrubbed by charge ratio 0..1 (clip is 1 s long)
    r = f / 30; s = {}
    for bone, (sx, fz) in PAWS.items():
        s[bone] = {'loc': (sx * .06 * r, 0, (.11 if fz > 0 else -.15) * r)}
    shiver = math.sin(f * 2.3) * 1.4 * r * r
    s['spine'] = {'rot': [(X, -5 * r)]}; s['head'] = {'rot': [(X, 24 * r), (Y, shiver)]}
    s['earL'] = {'rot': [(X, -26 * r)]}; s['earR'] = {'rot': [(X, -26 * r)]}
    for i, b in enumerate(('tail1', 'tail2', 'tail3', 'tail4')): s[b] = {'rot': [(X, -16 * r * (1 - i * .2)), (Y, shiver * 3)]}
    return s

def dash(f):                         # ramps into a stretched lunge in 4 frames and holds
    r = ease(f / 4); s = {}
    for bone, (sx, fz) in PAWS.items():
        s[bone] = {'loc': (sx * .02 * r, (.07 if fz > 0 else .03) * r, (.30 if fz > 0 else -.30) * r)}
    s['spine'] = {'rot': [(X, -4 * r)]}; s['head'] = {'rot': [(X, 10 * r)]}
    s['earL'] = {'rot': [(X, -52 * r)]}; s['earR'] = {'rot': [(X, -52 * r)]}
    for i, b in enumerate(('tail1', 'tail2', 'tail3', 'tail4')): s[b] = {'rot': [(X, -20 * r * (1 - i * .15))]}
    return s

def claw(sign):                      # sign +1: right paw swipes across to the left; -1 mirrors it
    pawn = 'pawFR' if sign > 0 else 'pawFL'
    def fn(f):
        t = f / 24; s = {}
        if t < .30:   k = ease(t / .30); x, y, z, yaw = .08 * k, .30 * k, -.16 * k, 14 * k
        elif t < .55: k = ease((t - .30) / .25); x, y, z, yaw = lerp_(.08, -.30, k), .30 + .16 * math.sin(math.pi * k), lerp_(-.16, .85, k), lerp_(14, -20, k)
        else:         k = ease((t - .55) / .45); x, y, z, yaw = lerp_(-.30, 0, k), 0, lerp_(.85, 0, k), lerp_(-20, 0, k)
        if t >= .55: y = lerp_(.14, 0, k)
        s[pawn] = {'loc': (sign * x, y, z)}
        s['spine'] = {'rot': [(Y, sign * yaw), (X, -3 * math.sin(math.pi * min(1, t / .6)))]}
        s['head'] = {'rot': [(Y, sign * yaw * .8), (X, 6 * math.sin(math.pi * min(1, t / .8)))]}
        s['earL'] = {'rot': [(X, -12 * math.sin(math.pi * t))]}; s['earR'] = {'rot': [(X, -12 * math.sin(math.pi * t))]}
        s.update(tail_wave(f, 24, 14, 1, lag=3))
        return s
    return fn

def jump_up(f):
    r = ease(f / 5); s = {}
    for bone, (sx, fz) in PAWS.items(): s[bone] = {'loc': (0, (.10 if fz > 0 else 0) * r, (.18 if fz > 0 else -.20) * r)}
    s['head'] = {'rot': [(X, -6 * r)]}; s['spine'] = {'rot': [(X, 3 * r)]}
    s['earL'] = {'rot': [(X, -16 * r)]}; s['earR'] = {'rot': [(X, -16 * r)]}
    for i, b in enumerate(('tail1', 'tail2', 'tail3', 'tail4')): s[b] = {'rot': [(X, 8 * r)]}
    return s

def jump_down(f):
    r = ease(f / 5); s = {}
    for bone, (sx, fz) in PAWS.items(): s[bone] = {'loc': (sx * .10 * r, (.12 if fz > 0 else .08) * r, .04 * fz * r)}
    s['head'] = {'rot': [(X, 4 * r)]}
    s['earL'] = {'rot': [(X, 5 * r)]}; s['earR'] = {'rot': [(X, 5 * r)]}
    for i, b in enumerate(('tail1', 'tail2', 'tail3', 'tail4')): s[b] = {'rot': [(X, 10 * r * (1 + i * .2))]}
    return s

def fly(f):                          # launched: spread-eagle, tail whipping
    ph = f / 12 * math.tau; s = {}
    for bone, (sx, fz) in PAWS.items(): s[bone] = {'loc': (sx * .16, .12, .10 * fz)}
    s['head'] = {'rot': [(X, -8)]}; s['earL'] = {'rot': [(X, -30)]}; s['earR'] = {'rot': [(X, -30)]}
    s.update(tail_wave(f, 12, 26, 1, lag=2))
    return s

def roll(f):                         # scrubbed by tuck 0..1 (clip is 18 frames)
    r = f / 18; s = {}
    for bone, (sx, fz) in PAWS.items(): s[bone] = {'loc': (-sx * .14 * r, .26 * r, -.10 * fz * r)}
    s['head'] = {'rot': [(X, 25 * r)]}; s['earL'] = {'rot': [(X, -45 * r)]}; s['earR'] = {'rot': [(X, -45 * r)]}
    for b, k in (('tail1', 10), ('tail2', 25), ('tail3', 30), ('tail4', 30)): s[b] = {'rot': [(X, k * r)]}
    return s

def flop(f):                         # stunned / dead: splayed, drooping
    r = ease(f / 6); s = {}
    for bone, (sx, fz) in PAWS.items(): s[bone] = {'loc': (sx * .14 * r, -.04 * r, (.10 if fz > 0 else -.14) * r)}
    s['head'] = {'rot': [(X, 20 * r), (Y, 10 * r)]}
    s['earL'] = {'rot': [(X, -25 * r), (Z, 20 * r)]}; s['earR'] = {'rot': [(X, -25 * r), (Z, -20 * r)]}
    for b, k in (('tail1', -25), ('tail2', -18), ('tail3', -10), ('tail4', -5)): s[b] = {'rot': [(X, k * r), (Y, 12 * r)]}
    return s

make_clip('idle', range(0, 61, 5), idle); make_clip('walk', range(0, 19, 3), walk)
make_clip('charge', range(0, 31, 1), charge); make_clip('dash', range(0, 13, 2), dash)
make_clip('clawR', range(0, 25, 2), claw(1)); make_clip('clawL', range(0, 25, 2), claw(-1))
make_clip('jumpUp', range(0, 11, 5), jump_up); make_clip('jumpDown', range(0, 11, 5), jump_down)
make_clip('fly', range(0, 13, 2), fly); make_clip('roll', range(0, 19, 3), roll); make_clip('flop', range(0, 13, 6), flop)
for b in pb: b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0); b.scale = (1, 1, 1)
rig.animation_data.action = None
print('clips', [a.name for a in bpy.data.actions])
