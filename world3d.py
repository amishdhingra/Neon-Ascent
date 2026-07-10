"""Neon course — choreographed zones with distinct layout patterns."""

import random

import settings as s

ZONES = [
    {"name": "THE PIT", "z_start": 68},
    {"name": "NEON PIPES", "z_start": 118},
    {"name": "THE GAP", "z_start": 178},
    {"name": "THE TOWER", "z_start": 248},
    {"name": "THE SUMMIT", "z_start": 318},
]


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


def _add_plat(blocks, x, y, z, w, d):
    blocks.append(_platform(x, y, z, w, d))
    return x, _top_y(blocks[-1]), z


def _add_wall(blocks, x, y, z, h=9.0, w=0.55, d=8.0):
    blocks.append(_surf_wall(x, y, z, w, h, d))
    return blocks[-1]


def _build_intro(blocks):
    spawn = _platform(0, 0, 12, 14, 34, thickness=0.6)
    blocks.append(spawn)
    cx, cy, cz = 0.0, 0.3, 4.0
    intro = [
        (0.0, 0.9, 22.0, 6.0, 6.0),
        (0.0, 0.9, 28.5, 6.0, 6.0),
        (1.5, 1.1, 35.0, 5.5, 5.5),
        (-1.0, 1.1, 42.0, 5.5, 5.5),
        (0.0, 1.5, 50.0, 5.0, 5.0),
        (2.0, 2.0, 60.0, 4.5, 5.0),
    ]
    for ix, iy, iz, iw, id_ in intro:
        cx, cy, cz = _add_plat(blocks, ix, iy, iz, iw, id_)
    _add_wall(blocks, -3.2, 2.0, 50.0, h=10.0, d=10.0)
    return cx, cy, cz


def _build_pit(blocks, cx, cy, cz, rng):
    """Wide shelves — learn spacing, mild zigzag."""
    pattern = [
        (0, 5.5, 4.5, 5.0),
        (-3, 5.8, 4.0, 4.5),
        (3, 6.2, 4.5, 4.5),
        (-2, 6.5, 5.5, 4.0),
        (0, 6.8, 6.0, 5.0),
        (4, 7.2, 4.5, 4.0),
        (-4, 7.5, 5.0, 4.0),
    ]
    for lat, fwd, w, d in pattern:
        cx, cy, cz = _add_plat(blocks, cx + lat, cy + 0.35, cz + fwd, w, d)
    return cx, cy, cz


def _build_neon(blocks, cx, cy, cz, rng):
    """Neon pipes — tight alternating corridor, narrow pads."""
    side = 1
    for i in range(8):
        lat = side * rng.uniform(5.0, 6.5)
        fwd = rng.uniform(4.5, 6.0)
        w = rng.uniform(2.6, 3.2)
        d = rng.uniform(3.0, 3.8)
        rise = 0.4 if i % 2 == 0 else 0.15
        cx, cy, cz = _add_plat(blocks, cx + lat, cy + rise, cz + fwd, w, d)
        if i in (2, 5):
            _add_wall(blocks, cx - side * 2.8, cy + 4.0, cz - 1.5, h=8.5, d=6.0)
        side *= -1
    # sprint squeeze through center
    cx, cy, cz = _add_plat(blocks, 0, cy + 0.5, cz + 9.5, 3.0, 3.5)
    return cx, cy, cz


def _build_gap(blocks, cx, cy, cz, rng):
    """The gap — long forward hops, tiny landing pads, sprint required."""
    gaps = [
        (0, 9.0, 0.6, 2.8, 3.0),
        (-2, 10.5, 0.8, 2.6, 2.8),
        (2.5, 11.0, 0.5, 2.5, 2.8),
        (0, 10.0, 1.0, 2.8, 3.0),
        (-3, 12.0, 0.7, 2.4, 2.6),
        (3, 11.5, 0.9, 2.5, 2.8),
        (0, 12.5, 1.2, 2.6, 3.0),
    ]
    for lat, fwd, rise, w, d in gaps:
        cx, cy, cz = _add_plat(blocks, cx + lat, cy + rise, cz + fwd, w, d)
    # double jump recovery shelf
    cx, cy, cz = _add_plat(blocks, cx, cy + 1.5, cz + 11.0, 4.0, 5.0)
    return cx, cy, cz


def _build_tower(blocks, cx, cy, cz, rng):
    """The tower — climb up with wall-surf alleys and switchbacks."""
    # stair climb
    for i in range(5):
        cx, cy, cz = _add_plat(blocks, cx + rng.uniform(-2, 2), cy + 1.1, cz + 5.5, 3.5, 4.0)
    # wall alley — surf down between two orange panels
    mid_z = cz + 4.0
    _add_wall(blocks, cx - 4.0, cy + 5.0, mid_z, h=12.0, d=10.0)
    _add_wall(blocks, cx + 4.0, cy + 5.0, mid_z, h=12.0, d=10.0)
    cx, cy, cz = _add_plat(blocks, cx, cy + 2.5, cz + 10.0, 3.0, 3.5)
    # switchback — drop then climb opposite side
    cx, cy, cz = _add_plat(blocks, cx - 6.0, cy - 0.5, cz + 6.0, 3.5, 4.0)
    cx, cy, cz = _add_plat(blocks, cx + 7.0, cy + 1.8, cz + 7.0, 3.0, 3.5)
    _add_wall(blocks, cx - 3.5, cy + 3.0, cz, h=10.0, d=7.0)
    cx, cy, cz = _add_plat(blocks, cx, cy + 2.0, cz + 9.0, 2.8, 3.2)
    return cx, cy, cz


def _build_summit(blocks, cx, cy, cz, rng):
    """Summit gauntlet — every tool chained, small pads, high risk."""
    chain = [
        (-2.5, 10.0, 1.0, 2.6, 3.0, True),
        (0, 11.5, 1.5, 2.4, 2.8, False),
        (3, 10.5, 0.8, 2.5, 2.8, True),
        (-1, 12.0, 2.0, 2.4, 2.6, False),
        (2, 11.0, 1.2, 2.6, 3.0, True),
        (0, 13.0, 2.5, 2.8, 3.2, False),
    ]
    for lat, fwd, rise, w, d, wall in chain:
        cx, cy, cz = _add_plat(blocks, cx + lat, cy + rise, cz + fwd, w, d)
        if wall:
            _add_wall(blocks, cx + (3.5 if lat <= 0 else -3.5), cy + 2.0, cz - 1.0, h=9.0, d=5.5)
    return cx, cy, cz


def get_zone_name(z_pos):
    name = ZONES[0]["name"]
    for zone in ZONES:
        if z_pos >= zone["z_start"]:
            name = zone["name"]
    return name


def build_tower(seed=None):
    if seed is None:
        seed = random.randrange(1_000_000)
    rng = random.Random(seed)
    blocks = []

    cx, cy, cz = _build_intro(blocks)
    cx, cy, cz = _build_pit(blocks, cx, cy, cz, rng)
    cx, cy, cz = _build_neon(blocks, cx, cy, cz, rng)
    cx, cy, cz = _build_gap(blocks, cx, cy, cz, rng)
    cx, cy, cz = _build_tower(blocks, cx, cy, cz, rng)
    cx, cy, cz = _build_summit(blocks, cx, cy, cz, rng)

    goal_z = cz + 10.0
    summit_y = cy + 2.0
    blocks.append(_platform(cx, cy + 2.0, goal_z, 14, 14, thickness=0.5))

    collisions = [b["collision"] for b in blocks]
    wall_solids = [b["collision"] for b in blocks if b["kind"] == "surf_wall"]
    return blocks, collisions, wall_solids, goal_z, summit_y, seed


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
