"""Procedural neon course — Peak-style random layouts, always hard."""

import random

import settings as s

# Difficulty floor: gaps tuned so walk jump never suffices after intro
HARD = {
    "sprint": {"fwd": (8.5, 10.5), "lat": (3.0, 7.5), "rise": (0.2, 1.4), "pad": (2.0, 2.6)},
    "double": {"fwd": (10.5, 13.5), "lat": (4.0, 8.5), "rise": (1.0, 2.6), "pad": (2.0, 2.4)},
    "wall": {"fwd": (6.5, 9.5), "lat": (4.0, 7.0), "rise": (0.6, 2.2), "pad": (2.0, 2.5)},
    "wall_sprint": {"fwd": (8.5, 11.5), "lat": (4.5, 8.0), "rise": (0.8, 2.0), "pad": (2.0, 2.4)},
    "wall_double": {"fwd": (10.0, 13.0), "lat": (5.0, 9.0), "rise": (1.2, 2.8), "pad": (2.0, 2.3)},
}

ZONE_ORDER = [
    ("THE PIT", 5, ("sprint_gap", "zigzag_sprint", "wall_chain", "double_arc", "combo_sprint")),
    ("NEON PIPES", 6, ("pipe_swing", "wall_chain", "sprint_gap", "wall_alley", "double_arc", "combo_wall")),
    ("THE GAP", 7, ("gap_marathon", "sprint_gap", "double_arc", "sprint_gap", "wall_sprint", "double_arc", "combo_double")),
    ("THE TOWER", 6, ("wall_alley", "switchback", "wall_chain", "climb_burst", "wall_alley", "combo_wall")),
    ("THE SUMMIT", 5, ("combo_wall", "gap_marathon", "wall_sprint", "double_arc", "final_gauntlet")),
]

_GENERATED_ZONES = [{"name": "SHORE", "z_start": 0}]


def _box(x, y, z, w, h, d):
    hw, hh, hd = w * 0.5, h * 0.5, d * 0.5
    return (x - hw, y - hh, z - hd, x + hw, y + hh, z + hd)


def _platform(x, y, z, w, d, thickness=0.4):
    return {
        "pos": (x, y, z),
        "size": (w, thickness, d),
        "collision": _box(x, y, z, w, thickness, d),
        "kind": "platform",
    }


def _surf_wall(x, y, z, w, h, d):
    return {
        "pos": (x, y, z),
        "size": (w, h, d),
        "collision": _box(x, y, z, w, h, d),
        "kind": "surf_wall",
    }


def _top_y(block):
    _, y, _ = block["pos"]
    _, h, _ = block["size"]
    return y + h * 0.5


def _plat(blocks, x, y, z, w, d):
    blocks.append(_platform(x, y, z, w, d))
    return x, _top_y(blocks[-1]), z


def _wall(blocks, x, y, z, h=10.0, w=0.55, d=8.0):
    blocks.append(_surf_wall(x, y, z, w, h, d))


def _pad_size(rng, mechanic):
    pw = rng.uniform(*HARD[mechanic]["pad"])
    pd = pw * rng.uniform(0.85, 1.15)
    return pw, pd


def _step(blocks, cx, cy, cz, rng, mechanic, lat_mul=1.0, rise_mul=1.0, wall=False, wall_side=None):
    spec = HARD[mechanic]
    fwd = rng.uniform(*spec["fwd"])
    lat = rng.choice([-1, 1]) * rng.uniform(*spec["lat"]) * lat_mul
    rise = rng.uniform(*spec["rise"]) * rise_mul
    w, d = _pad_size(rng, mechanic)
    nx, ny, nz = cx + lat, cy + rise, cz + fwd
    if wall:
        side = wall_side if wall_side else (-1 if lat >= 0 else 1)
        _wall(blocks, (cx + nx) * 0.5 + side * 3.0, cy + rise * 0.5 + 2.0, (cz + nz) * 0.5, h=rng.uniform(9, 12), d=rng.uniform(7, 10))
    return _plat(blocks, nx, ny, nz, w, d)


# --- Segment builders (each returns new cx, cy, cz) ---


def _seg_sprint_gap(blocks, cx, cy, cz, rng):
    return _step(blocks, cx, cy, cz, rng, "sprint", wall=rng.random() < 0.35)


def _seg_double_arc(blocks, cx, cy, cz, rng):
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "double")
    side = rng.choice([-1, 1])
    return _step(blocks, cx, cy, cz, rng, "double", lat_mul=side, rise_mul=rng.uniform(0.6, 1.0))


def _seg_wall_chain(blocks, cx, cy, cz, rng):
    mech = rng.choice(["wall", "wall_sprint", "wall_double"])
    return _step(blocks, cx, cy, cz, rng, mech, wall=True)


def _seg_wall_sprint(blocks, cx, cy, cz, rng):
    """Wall surf into a sprint-only gap — no walk jump."""
    return _step(blocks, cx, cy, cz, rng, "wall_sprint", wall=True)


def _seg_wall_alley(blocks, cx, cy, cz, rng):
    tz = cz + rng.uniform(8.0, 11.0)
    off = rng.uniform(3.0, 4.5)
    rise = rng.uniform(1.0, 2.5)
    _wall(blocks, cx - off, cy + rise + 1.0, tz - 2.0, h=rng.uniform(11, 14), d=rng.uniform(9, 12))
    _wall(blocks, cx + off, cy + rise + 1.0, tz - 2.0, h=rng.uniform(11, 14), d=rng.uniform(9, 12))
    w, d = _pad_size(rng, "wall_sprint")
    return _plat(blocks, cx + rng.uniform(-1.5, 1.5), cy + rise, tz, w, d)


def _seg_zigzag_sprint(blocks, cx, cy, cz, rng):
    side = 1
    for _ in range(rng.randint(3, 5)):
        cx, cy, cz = _step(blocks, cx, cy, cz, rng, "sprint", lat_mul=side * rng.uniform(0.8, 1.2), rise_mul=rng.uniform(0.2, 0.8))
        side *= -1
    return cx, cy, cz


def _seg_pipe_swing(blocks, cx, cy, cz, rng):
    """Neon pipes — big lateral swings, mostly flat height."""
    base = cy
    side = rng.choice([-1, 1])
    for i in range(rng.randint(4, 6)):
        lat = side * rng.uniform(5.5, 8.0)
        fwd = rng.uniform(4.5, 7.0)
        w, d = _pad_size(rng, "sprint")
        cx, cy, cz = _plat(blocks, cx + lat, base + rng.uniform(-0.2, 0.6), cz + fwd, w, d)
        if i % 2 == 0:
            _wall(blocks, cx - side * 2.8, base + 3.0, cz - 1.0, h=rng.uniform(8, 11), d=rng.uniform(6, 9))
        side *= -1
    return cx, cy, cz


def _seg_gap_marathon(blocks, cx, cy, cz, rng):
    """Tiny pads, sprint-only chain."""
    for _ in range(rng.randint(5, 8)):
        cx, cy, cz = _step(blocks, cx, cy, cz, rng, "sprint", lat_mul=rng.uniform(0.5, 1.2), rise_mul=rng.uniform(0.2, 1.0))
    return cx, cy, cz


def _seg_switchback(blocks, cx, cy, cz, rng):
    """Go sideways then back — not a straight ladder."""
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "wall_sprint", wall=True, wall_side=1)
    cx, cy, cz = _plat(blocks, cx - rng.uniform(8.0, 11.0), cy + rng.uniform(-0.8, 0.5), cz + rng.uniform(4.0, 7.0), 2.3, 2.6)
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "double", lat_mul=1.0)
    return cx, cy, cz


def _seg_climb_burst(blocks, cx, cy, cz, rng):
    """Short vertical burst then lateral escape."""
    for _ in range(2):
        cx, cy, cz = _step(blocks, cx, cy, cz, rng, "double", lat_mul=0.3, rise_mul=1.2)
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "wall_sprint", wall=True)
    return cx, cy, cz


def _seg_combo_sprint(blocks, cx, cy, cz, rng):
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "sprint")
    return _step(blocks, cx, cy, cz, rng, "double", rise_mul=0.8)


def _seg_combo_wall(blocks, cx, cy, cz, rng):
    cx, cy, cz = _seg_wall_chain(blocks, cx, cy, cz, rng)
    return _step(blocks, cx, cy, cz, rng, "double")


def _seg_combo_double(blocks, cx, cy, cz, rng):
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "double")
    return _seg_wall_chain(blocks, cx, cy, cz, rng)


def _seg_final_gauntlet(blocks, cx, cy, cz, rng):
    cx, cy, cz = _seg_sprint_gap(blocks, cx, cy, cz, rng)
    cx, cy, cz = _seg_wall_alley(blocks, cx, cy, cz, rng)
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "wall_double", wall=True)
    return _step(blocks, cx, cy, cz, rng, "double")


SEGMENTS = {
    "sprint_gap": _seg_sprint_gap,
    "double_arc": _seg_double_arc,
    "wall_chain": _seg_wall_chain,
    "wall_sprint": _seg_wall_sprint,
    "wall_alley": _seg_wall_alley,
    "zigzag_sprint": _seg_zigzag_sprint,
    "pipe_swing": _seg_pipe_swing,
    "gap_marathon": _seg_gap_marathon,
    "switchback": _seg_switchback,
    "climb_burst": _seg_climb_burst,
    "combo_sprint": _seg_combo_sprint,
    "combo_wall": _seg_combo_wall,
    "combo_double": _seg_combo_double,
    "final_gauntlet": _seg_final_gauntlet,
}


def _build_intro(blocks):
    blocks.append(_platform(0, 0, 12, 14, 34, thickness=0.6))
    cx, cy, cz = 0.0, 0.3, 4.0
    for ix, iy, iz, iw, id_ in [
        (0.0, 0.9, 22.0, 5.5, 5.5),
        (0.0, 1.5, 50.0, 4.5, 4.5),
        (2.0, 2.0, 60.0, 4.0, 4.5),
    ]:
        cx, cy, cz = _plat(blocks, ix, iy, iz, iw, id_)
    _wall(blocks, -3.0, 2.0, 50.0, h=10.0, d=9.0)
    return cx, cy, cz


def _pick_zone_segments(rng, count, pool):
    """Peak-style: different segment mix every run, same difficulty floor."""
    pool = list(pool)
    rng.shuffle(pool)
    count = max(4, count + rng.choice([-1, 0, 0, 1]))
    if count <= len(pool):
        picks = rng.sample(pool, count)
    else:
        picks = [rng.choice(pool) for _ in range(count)]
    rng.shuffle(picks)
    return picks


def _build_zone(blocks, cx, cy, cz, rng, zone_name, count, pool):
    global _GENERATED_ZONES
    _GENERATED_ZONES.append({"name": zone_name, "z_start": cz})
    for key in _pick_zone_segments(rng, count, pool):
        cx, cy, cz = SEGMENTS[key](blocks, cx, cy, cz, rng)
    return cx, cy, cz


def get_zone_name(z_pos):
    name = _GENERATED_ZONES[0]["name"]
    for zone in _GENERATED_ZONES:
        if z_pos >= zone["z_start"]:
            name = zone["name"]
    return name


def build_tower(seed=None):
    global _GENERATED_ZONES
    if seed is None:
        seed = random.randrange(1_000_000)
    rng = random.Random(seed)
    _GENERATED_ZONES = [{"name": "SHORE", "z_start": 0}]
    blocks = []

    cx, cy, cz = _build_intro(blocks)
    for zone_name, count, pool in ZONE_ORDER:
        cx, cy, cz = _build_zone(blocks, cx, cy, cz, rng, zone_name, count, pool)

    goal_z = cz + rng.uniform(10.0, 14.0)
    blocks.append(_platform(cx + rng.uniform(-2, 2), cy + rng.uniform(1.5, 3.0), goal_z, 12, 12, thickness=0.5))

    collisions = [b["collision"] for b in blocks]
    wall_solids = [b["collision"] for b in blocks if b["kind"] == "surf_wall"]
    platform_solids = [b["collision"] for b in blocks if b["kind"] == "platform"]
    summit_y = cy + 2.0
    return blocks, collisions, wall_solids, platform_solids, goal_z, summit_y, seed


def draw_block(block):
    from OpenGL.GL import (
        GL_LINES,
        GL_QUADS,
        glBegin,
        glColor3f,
        glEnd,
        glLineWidth,
        glVertex3f,
    )

    x, y, z = block["pos"]
    w, h, d = block["size"]
    hw, hh, hd = w * 0.5, h * 0.5, d * 0.5

    if block["kind"] == "surf_wall":
        glColor3f(1.0, 0.45, 0.12)
    else:
        glColor3f(*s.COLOUR_PLATFORM)

    glBegin(GL_QUADS)
    glVertex3f(x - hw, y + hh, z - hd)
    glVertex3f(x + hw, y + hh, z - hd)
    glVertex3f(x + hw, y + hh, z + hd)
    glVertex3f(x - hw, y + hh, z + hd)
    glEnd()

    glColor3f(*s.COLOUR_PLATFORM_EDGE)
    for face in _side_faces(x, y, z, hw, hh, hd):
        glBegin(GL_QUADS)
        for vx, vy, vz in face:
            glVertex3f(vx, vy, vz)
        glEnd()

    glLineWidth(1.5)
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_LINES)
    for e0, e1 in _edges(x, y, z, hw, hh, hd):
        glVertex3f(*e0)
        glVertex3f(*e1)
    glEnd()


def _side_faces(x, y, z, hw, hh, hd):
    return [
        [(x - hw, y - hh, z + hd), (x + hw, y - hh, z + hd), (x + hw, y + hh, z + hd), (x - hw, y + hh, z + hd)],
        [(x - hw, y - hh, z - hd), (x - hw, y + hh, z - hd), (x + hw, y + hh, z - hd), (x + hw, y - hh, z - hd)],
        [(x - hw, y - hh, z - hd), (x - hw, y - hh, z + hd), (x - hw, y + hh, z + hd), (x - hw, y + hh, z - hd)],
        [(x + hw, y - hh, z - hd), (x + hw, y + hh, z - hd), (x + hw, y + hh, z + hd), (x + hw, y - hh, z + hd)],
    ]


def _edges(x, y, z, hw, hh, hd):
    corners = [
        (x - hw, y - hh, z - hd),
        (x + hw, y - hh, z - hd),
        (x + hw, y + hh, z - hd),
        (x - hw, y + hh, z - hd),
        (x - hw, y - hh, z + hd),
        (x + hw, y - hh, z + hd),
        (x + hw, y + hh, z + hd),
        (x - hw, y + hh, z + hd),
    ]
    pairs = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
    return [(corners[a], corners[b]) for a, b in pairs]
