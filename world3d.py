"""Procedural neon course — varied layouts, short kick walls, always hard."""

import random

import settings as s

# Gaps require sprint / double / wall-kick — walk jump never enough after intro
HARD = {
    "sprint": {"fwd": (8.5, 10.5), "lat": (3.0, 7.5), "rise": (0.2, 1.4), "pad": (2.0, 2.6)},
    "double": {"fwd": (10.5, 13.5), "lat": (4.0, 8.5), "rise": (1.0, 2.6), "pad": (2.0, 2.4)},
    "wall": {"fwd": (6.5, 9.5), "lat": (4.0, 7.0), "rise": (0.6, 2.2), "pad": (2.0, 2.5)},
    "wall_sprint": {"fwd": (8.5, 11.5), "lat": (4.5, 8.0), "rise": (0.8, 2.0), "pad": (2.0, 2.4)},
    "wall_double": {"fwd": (10.0, 13.0), "lat": (5.0, 9.0), "rise": (1.2, 2.8), "pad": (2.0, 2.3)},
}

ZONE_THEMES = {
    "THE PIT": (0.31, 1.0, 0.86),
    "NEON PIPES": (0.95, 0.35, 0.95),
    "THE GAP": (0.35, 0.75, 1.0),
    "THE TOWER": (1.0, 0.55, 0.25),
    "THE SUMMIT": (1.0, 0.92, 0.35),
}

ZONE_ORDER = [
    ("THE PIT", 5, ("sprint_gap", "zigzag_sprint", "drop_recover", "double_arc", "ridge_run", "combo_sprint")),
    ("NEON PIPES", 6, ("pipe_swing", "island_arc", "kick_corridor", "sprint_gap", "void_cross", "double_arc", "combo_wall")),
    ("THE GAP", 7, ("gap_marathon", "falling_shelf", "overhang", "sprint_gap", "switchback", "double_arc", "combo_double")),
    ("THE TOWER", 6, ("stagger_climb", "kick_corridor", "wall_alley", "climb_burst", "ridge_run", "combo_wall")),
    ("THE SUMMIT", 5, ("combo_wall", "gap_marathon", "overhang", "kick_corridor", "final_gauntlet")),
]

_GENERATED_ZONES = [{"name": "SHORE", "z_start": 0}]
_CURRENT_THEME = (0.31, 1.0, 0.86)


def _box(x, y, z, w, h, d):
    hw, hh, hd = w * 0.5, h * 0.5, d * 0.5
    return (x - hw, y - hh, z - hd, x + hw, y + hh, z + hd)


def _platform(x, y, z, w, d, thickness=0.4, colour=None):
    return {
        "pos": (x, y, z),
        "size": (w, thickness, d),
        "collision": _box(x, y, z, w, thickness, d),
        "kind": "platform",
        "colour": colour or _CURRENT_THEME,
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


def _plat(blocks, x, y, z, w, d, colour=None):
    blocks.append(_platform(x, y, z, w, d, colour=colour))
    return x, _top_y(blocks[-1]), z


def _kick_panel(blocks, x, y, z, side_x=1, h=4.5, d=5.0):
    """Short wall beside a gap — kick off, don't climb."""
    blocks.append(_surf_wall(x + side_x * 0.3, y, z, 0.55, h, d))


def _pad_size(rng, mechanic):
    pw = rng.uniform(*HARD[mechanic]["pad"])
    pd = pw * rng.uniform(0.85, 1.15)
    return pw, pd


def _step(blocks, cx, cy, cz, rng, mechanic, lat_mul=1.0, rise_mul=1.0, kick_side=None):
    spec = HARD[mechanic]
    fwd = rng.uniform(*spec["fwd"])
    lat = rng.choice([-1, 1]) * rng.uniform(*spec["lat"]) * lat_mul
    rise = rng.uniform(*spec["rise"]) * rise_mul
    w, d = _pad_size(rng, mechanic)
    nx, ny, nz = cx + lat, cy + rise, cz + fwd
    if kick_side is not None:
        mid_y = cy + rise * 0.45 + 1.8
        _kick_panel(blocks, (cx + nx) * 0.5 + kick_side * 2.8, mid_y, (cz + nz) * 0.5, side_x=kick_side, d=rng.uniform(4.5, 6.5))
    return _plat(blocks, nx, ny, nz, w, d)


# --- Segments ---


def _seg_sprint_gap(blocks, cx, cy, cz, rng):
    kick = rng.choice([-1, 1]) if rng.random() < 0.5 else None
    return _step(blocks, cx, cy, cz, rng, "sprint", kick_side=kick)


def _seg_double_arc(blocks, cx, cy, cz, rng):
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "double")
    side = rng.choice([-1, 1])
    return _step(blocks, cx, cy, cz, rng, "double", lat_mul=side, rise_mul=rng.uniform(0.6, 1.0))


def _seg_wall_sprint(blocks, cx, cy, cz, rng):
    side = rng.choice([-1, 1])
    return _step(blocks, cx, cy, cz, rng, "wall_sprint", kick_side=side)


def _seg_wall_alley(blocks, cx, cy, cz, rng):
    """Two short kick panels — surf down one, jump to the pad between."""
    tz = cz + rng.uniform(8.0, 11.0)
    off = rng.uniform(3.5, 5.0)
    rise = rng.uniform(1.0, 2.5)
    mid_y = cy + rise * 0.5 + 1.5
    _kick_panel(blocks, cx - off, mid_y, tz - 2.5, side_x=-1, h=4.5, d=rng.uniform(5, 7))
    _kick_panel(blocks, cx + off, mid_y, tz - 2.5, side_x=1, h=4.5, d=rng.uniform(5, 7))
    w, d = _pad_size(rng, "wall_sprint")
    return _plat(blocks, cx + rng.uniform(-1.5, 1.5), cy + rise, tz, w, d)


def _seg_zigzag_sprint(blocks, cx, cy, cz, rng):
    side = 1
    for _ in range(rng.randint(3, 5)):
        cx, cy, cz = _step(blocks, cx, cy, cz, rng, "sprint", lat_mul=side * rng.uniform(0.8, 1.2), rise_mul=rng.uniform(0.2, 0.8))
        side *= -1
    return cx, cy, cz


def _seg_pipe_swing(blocks, cx, cy, cz, rng):
    base = cy
    side = rng.choice([-1, 1])
    for i in range(rng.randint(4, 6)):
        lat = side * rng.uniform(5.5, 8.0)
        fwd = rng.uniform(4.5, 7.0)
        w, d = _pad_size(rng, "sprint")
        cx, cy, cz = _plat(blocks, cx + lat, base + rng.uniform(-0.2, 0.6), cz + fwd, w, d)
        if i % 2 == 0:
            _kick_panel(blocks, cx - side * 2.5, base + 2.5, cz - 0.5, side_x=-side, h=4.0, d=rng.uniform(4, 6))
        side *= -1
    return cx, cy, cz


def _seg_gap_marathon(blocks, cx, cy, cz, rng):
    for _ in range(rng.randint(5, 8)):
        cx, cy, cz = _step(blocks, cx, cy, cz, rng, "sprint", lat_mul=rng.uniform(0.5, 1.2), rise_mul=rng.uniform(0.2, 1.0))
    return cx, cy, cz


def _seg_switchback(blocks, cx, cy, cz, rng):
    side = rng.choice([-1, 1])
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "wall_sprint", kick_side=side)
    cx, cy, cz = _plat(blocks, cx - side * rng.uniform(9.0, 12.0), cy + rng.uniform(-0.5, 0.8), cz + rng.uniform(5.0, 8.0), 2.2, 2.8)
    return _step(blocks, cx, cy, cz, rng, "double", lat_mul=side)


def _seg_climb_burst(blocks, cx, cy, cz, rng):
    for _ in range(2):
        cx, cy, cz = _step(blocks, cx, cy, cz, rng, "double", lat_mul=0.3, rise_mul=1.2)
    return _step(blocks, cx, cy, cz, rng, "wall_sprint", kick_side=rng.choice([-1, 1]))


def _seg_combo_sprint(blocks, cx, cy, cz, rng):
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "sprint")
    return _step(blocks, cx, cy, cz, rng, "double", rise_mul=0.8)


def _seg_combo_wall(blocks, cx, cy, cz, rng):
    cx, cy, cz = _seg_wall_sprint(blocks, cx, cy, cz, rng)
    return _step(blocks, cx, cy, cz, rng, "double")


def _seg_combo_double(blocks, cx, cy, cz, rng):
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "double")
    return _seg_wall_sprint(blocks, cx, cy, cz, rng)


def _seg_final_gauntlet(blocks, cx, cy, cz, rng):
    cx, cy, cz = _seg_sprint_gap(blocks, cx, cy, cz, rng)
    cx, cy, cz = _seg_wall_alley(blocks, cx, cy, cz, rng)
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "wall_double", kick_side=rng.choice([-1, 1]))
    return _step(blocks, cx, cy, cz, rng, "double")


def _seg_drop_recover(blocks, cx, cy, cz, rng):
    """Step down, then sprint back up — breaks the always-rising monotony."""
    cx, cy, cz = _plat(blocks, cx + rng.uniform(-2, 2), cy - rng.uniform(1.5, 3.0), cz + rng.uniform(5, 7), 3.0, 3.5)
    cx, cy, cz = _plat(blocks, cx + rng.uniform(-3, 3), cy - rng.uniform(0.5, 1.5), cz + rng.uniform(4, 6), 2.5, 2.8)
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "sprint", rise_mul=1.4)
    return _step(blocks, cx, cy, cz, rng, "double", rise_mul=0.9)


def _seg_ridge_run(blocks, cx, cy, cz, rng):
    """One long thin bridge, then a hard jump off the end."""
    length = rng.uniform(14, 22)
    cx, cy, cz = _plat(blocks, cx, cy, cz + length * 0.5, 2.0, length, colour=tuple(c * 0.85 for c in _CURRENT_THEME))
    return _step(blocks, cx, cy, cz, rng, "sprint", lat_mul=rng.choice([-1, 1]))


def _seg_island_arc(blocks, cx, cy, cz, rng):
    """Platforms curve sideways — you see the route bend ahead."""
    base_y = cy
    side = rng.choice([-1, 1])
    for i in range(rng.randint(4, 5)):
        angle = (i + 1) / 5.0 * 1.2
        lat = side * rng.uniform(4.0, 7.0) * (1.0 + angle * 0.3)
        fwd = rng.uniform(5.0, 8.0)
        w = rng.uniform(2.0, 2.8)
        cx, cy, cz = _plat(blocks, cx + lat, base_y + rng.uniform(-0.3, 1.2), cz + fwd, w, w)
    return cx, cy, cz


def _seg_kick_corridor(blocks, cx, cy, cz, rng):
    """Alternating short walls — wall-kick sideways, not climb up."""
    side = rng.choice([-1, 1])
    for _ in range(rng.randint(3, 4)):
        fwd = rng.uniform(7.0, 10.0)
        lat = side * rng.uniform(4.0, 6.5)
        w, d = _pad_size(rng, "wall")
        nz = cz + fwd
        nx = cx + lat
        _kick_panel(blocks, (cx + nx) * 0.5 - side * 1.5, cy + 2.0, (cz + nz) * 0.5, side_x=-side, h=4.0, d=fwd * 0.7)
        cx, cy, cz = _plat(blocks, nx, cy + rng.uniform(0.3, 1.2), nz, w, d)
        side *= -1
    return cx, cy, cz


def _seg_void_cross(blocks, cx, cy, cz, rng):
    """Tiny pad alone in space — sprint or double only."""
    fwd = rng.uniform(10.0, 13.0)
    lat = rng.choice([-1, 1]) * rng.uniform(2.0, 5.0)
    w, d = rng.uniform(1.8, 2.2), rng.uniform(1.8, 2.2)
    return _plat(blocks, cx + lat, cy + rng.uniform(0.0, 1.0), cz + fwd, w, d)


def _seg_falling_shelf(blocks, cx, cy, cz, rng):
    """Descend through stacked shelves, then double-jump out."""
    for i in range(rng.randint(3, 4)):
        drop = rng.uniform(1.0, 2.0)
        fwd = rng.uniform(4.0, 6.0)
        off = rng.choice([-1, 1]) * rng.uniform(2.0, 4.5)
        cx, cy, cz = _plat(blocks, cx + off, cy - drop, cz + fwd, rng.uniform(2.5, 3.5), rng.uniform(2.5, 3.5))
    return _step(blocks, cx, cy, cz, rng, "double", rise_mul=1.3, lat_mul=rng.choice([-1, 1]))


def _seg_overhang(blocks, cx, cy, cz, rng):
    """Target platform sits above and ahead — double jump or wall kick required."""
    side = rng.choice([-1, 1])
    fwd = rng.uniform(9.0, 12.0)
    rise = rng.uniform(2.5, 4.0)
    _kick_panel(blocks, cx + side * 3.5, cy + 1.5, cz + fwd * 0.45, side_x=-side, h=4.5, d=fwd * 0.6)
    w, d = _pad_size(rng, "double")
    return _plat(blocks, cx + side * rng.uniform(1.0, 3.0), cy + rise, cz + fwd, w, d)


def _seg_stagger_climb(blocks, cx, cy, cz, rng):
    """Platforms offset in X and Z — not a straight ladder."""
    for _ in range(rng.randint(4, 6)):
        fwd = rng.uniform(5.0, 8.0)
        lat = rng.choice([-1, 1]) * rng.uniform(5.0, 9.0)
        rise = rng.uniform(0.8, 2.2)
        w, d = _pad_size(rng, rng.choice(["double", "wall_sprint", "sprint"]))
        cx, cy, cz = _plat(blocks, cx + lat, cy + rise, cz + fwd, w, d)
    return cx, cy, cz


SEGMENTS = {
    "sprint_gap": _seg_sprint_gap,
    "double_arc": _seg_double_arc,
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
    "drop_recover": _seg_drop_recover,
    "ridge_run": _seg_ridge_run,
    "island_arc": _seg_island_arc,
    "kick_corridor": _seg_kick_corridor,
    "void_cross": _seg_void_cross,
    "falling_shelf": _seg_falling_shelf,
    "overhang": _seg_overhang,
    "stagger_climb": _seg_stagger_climb,
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
    _kick_panel(blocks, -3.0, 2.5, 50.0, side_x=-1, h=4.5, d=7.0)
    return cx, cy, cz


def _pick_zone_segments(rng, count, pool):
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
    global _GENERATED_ZONES, _CURRENT_THEME
    _GENERATED_ZONES.append({"name": zone_name, "z_start": cz})
    _CURRENT_THEME = ZONE_THEMES.get(zone_name, (0.31, 1.0, 0.86))
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
    global _GENERATED_ZONES, _CURRENT_THEME
    if seed is None:
        seed = random.randrange(1_000_000)
    rng = random.Random(seed)
    _GENERATED_ZONES = [{"name": "SHORE", "z_start": 0}]
    _CURRENT_THEME = (0.31, 1.0, 0.86)
    blocks = []

    cx, cy, cz = _build_intro(blocks)
    for zone_name, count, pool in ZONE_ORDER:
        cx, cy, cz = _build_zone(blocks, cx, cy, cz, rng, zone_name, count, pool)

    goal_z = cz + rng.uniform(10.0, 14.0)
    _CURRENT_THEME = ZONE_THEMES["THE SUMMIT"]
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
        colour = block.get("colour", s.COLOUR_PLATFORM)
        glColor3f(*colour)

    glBegin(GL_QUADS)
    glVertex3f(x - hw, y + hh, z - hd)
    glVertex3f(x + hw, y + hh, z - hd)
    glVertex3f(x + hw, y + hh, z + hd)
    glVertex3f(x - hw, y + hh, z + hd)
    glEnd()

    edge = block.get("colour", s.COLOUR_PLATFORM_EDGE)
    if block["kind"] == "platform":
        edge = tuple(c * 0.55 for c in edge)
    else:
        edge = s.COLOUR_PLATFORM_EDGE
    glColor3f(*edge)
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
