"""Neon course — hard choreographed segments, each requiring specific movement tools."""

import random

import settings as s

# Reach bands tuned to settings.py (metres)
REACH = {
    "walk_h": 4.5,
    "sprint_h": (8.5, 10.5),
    "double_h": (11.0, 13.5),
    "wall_h": (7.5, 10.5),
}

ZONES = [
    {"name": "THE PIT", "z_start": 72},
    {"name": "NEON PIPES", "z_start": 145},
    {"name": "THE GAP", "z_start": 228},
    {"name": "THE TOWER", "z_start": 318},
    {"name": "THE SUMMIT", "z_start": 405},
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


def _plat(blocks, x, y, z, w, d):
    blocks.append(_platform(x, y, z, w, d))
    return x, _top_y(blocks[-1]), z


def _wall(blocks, x, y, z, h=10.0, w=0.55, d=9.0):
    blocks.append(_surf_wall(x, y, z, w, h, d))


def _build_intro(blocks):
    blocks.append(_platform(0, 0, 12, 14, 34, thickness=0.6))
    cx, cy, cz = 0.0, 0.3, 4.0
    for ix, iy, iz, iw, id_ in [
        (0.0, 0.9, 22.0, 5.5, 5.5),
        (0.0, 0.9, 30.0, 5.0, 5.0),
        (0.0, 1.5, 50.0, 4.5, 4.5),
        (2.0, 2.0, 60.0, 4.0, 4.5),
    ]:
        cx, cy, cz = _plat(blocks, ix, iy, iz, iw, id_)
    _wall(blocks, -3.0, 2.0, 50.0, h=10.0, d=9.0)
    return cx, cy, cz


def _seg_sprint(blocks, cx, cy, cz, tx, ty, tz, w=2.4, d=2.8):
    """Gap requires sprint jump — pad too far for walk."""
    _wall(blocks, (cx + tx) * 0.5 - 4.0, cy + 1.5, (cz + tz) * 0.5, h=8.0, d=6.0)
    return _plat(blocks, tx, ty, tz, w, d)


def _seg_double(blocks, cx, cy, cz, tx, ty, tz, w=2.3, d=2.6):
    """Gap requires double jump."""
    return _plat(blocks, tx, ty, tz, w, d)


def _seg_wall_chain(blocks, cx, cy, cz, tx, ty, tz, wall_side, w=2.4, d=2.6):
    """Wall beside gap — surf, wall jump, often double jump to land."""
    mid_z = (cz + tz) * 0.5
    _wall(blocks, cx + wall_side * 3.2, cy + 2.5, mid_z, h=11.0, d=8.0)
    return _plat(blocks, tx, ty, tz, w, d)


def _seg_wall_alley(blocks, cx, cy, cz, tz, wall_x_off=3.5):
    """Two walls — must surf between them to reach pad ahead."""
    _wall(blocks, cx - wall_x_off, cy + 3.0, tz - 2.0, h=12.0, d=10.0)
    _wall(blocks, cx + wall_x_off, cy + 3.0, tz - 2.0, h=12.0, d=10.0)
    return _plat(blocks, cx, cy + 1.5, tz, 2.5, 3.0)


def _build_pit(blocks, cx, cy, cz):
    """Flat shelf run → sprint → double corner (not a ladder)."""
    cx, cy, cz = _plat(blocks, cx, cy, cz + 8.0, 5.0, 6.0)
    cx, cy, cz = _plat(blocks, cx - 5.0, cy, cz + 6.0, 4.5, 5.0)
    cx, cy, cz = _seg_sprint(blocks, cx, cy, cz, cx + 6.0, cy + 0.4, cz + 10.0)
    cx, cy, cz = _seg_double(blocks, cx, cy, cz, cx - 4.0, cy + 2.2, cz + 12.5)
    cx, cy, cz = _plat(blocks, cx + 8.0, cy, cz + 5.0, 4.0, 4.5)
    cx, cy, cz = _seg_wall_chain(blocks, cx, cy, cz, cx, cy + 1.8, cz + 9.0, wall_side=1)
    return cx, cy, cz


def _build_neon(blocks, cx, cy, cz, rng):
    """Pipe corridor — same height, huge lateral swings, wall jumps between pipes."""
    base_y = cy
    cx, cy, cz = _plat(blocks, cx - 7.0, base_y, cz + 6.0, 2.6, 3.0)
    cx, cy, cz = _seg_wall_chain(blocks, cx, cy, cz, cx + 7.0, base_y + 0.2, cz + 5.5, wall_side=-1, w=2.4, d=2.8)
    cx, cy, cz = _seg_sprint(blocks, cx, cy, cz, cx - 6.5, base_y, cz + 10.0, w=2.3, d=2.6)
    cx, cy, cz = _seg_wall_chain(blocks, cx, cy, cz, cx + 7.5, base_y + 0.5, cz + 8.0, wall_side=1)
    cx, cy, cz = _seg_double(blocks, cx, cy, cz, cx - 5.0, base_y + 2.0, cz + 11.0)
    _wall(blocks, cx + 3.5, base_y + 2.5, cz + 5.0, h=10.0, d=12.0)
    cx, cy, cz = _seg_wall_chain(blocks, cx, cy, cz, cx + 6.0, base_y + 1.0, cz + 10.5, wall_side=-1, w=2.2, d=2.5)
    cx, cy, cz = _seg_sprint(blocks, cx, cy, cz, cx, base_y + 0.3, cz + 12.0, w=2.5, d=3.0)
    return cx, cy, cz


def _build_gap(blocks, cx, cy, cz):
    """Sprint marathon on tiny pads — no safe wide shelves."""
    pads = [
        (0, 10.0, 0.3, 2.2, 2.5),
        (-4, 10.5, 0.5, 2.1, 2.4),
        (4.5, 11.0, 0.8, 2.0, 2.3),
        (-2, 10.0, 1.2, 2.2, 2.5),
        (3, 12.0, 0.6, 2.1, 2.4),
        (0, 11.5, 1.5, 2.0, 2.3),
        (-5, 12.5, 1.0, 2.1, 2.4),
    ]
    for lat, fwd, rise, w, d in pads:
        cx, cy, cz = _plat(blocks, cx + lat, cy + rise, cz + fwd, w, d)
    cx, cy, cz = _seg_double(blocks, cx, cy, cz, cx + 5.0, cy + 2.5, cz + 13.0, w=2.2, d=2.5)
    cx, cy, cz = _seg_sprint(blocks, cx, cy, cz, cx - 6.0, cy + 0.5, cz + 11.0, w=2.1, d=2.4)
    return cx, cy, cz


def _build_tower(blocks, cx, cy, cz):
    """Wall alley climb + switchback — surf/jump chains, not straight up."""
    cx, cy, cz = _seg_wall_alley(blocks, cx, cy, cz, cz + 10.0)
    cx, cy, cz = _seg_wall_chain(blocks, cx, cy, cz, cx + 8.0, cy + 2.5, cz + 9.0, wall_side=-1)
    cx, cy, cz = _seg_double(blocks, cx, cy, cz, cx - 3.0, cy + 4.0, cz + 11.0)
    _wall(blocks, cx - 4.0, cy + 5.0, cz + 4.0, h=13.0, d=10.0)
    _wall(blocks, cx + 4.0, cy + 5.0, cz + 4.0, h=13.0, d=10.0)
    cx, cy, cz = _plat(blocks, cx, cy + 3.0, cz + 12.0, 2.3, 2.6)
    cx, cy, cz = _plat(blocks, cx - 9.0, cy + 1.0, cz + 8.0, 2.4, 2.8)
    cx, cy, cz = _seg_wall_chain(blocks, cx, cy, cz, cx + 10.0, cy + 3.5, cz + 10.0, wall_side=1, w=2.2, d=2.5)
    cx, cy, cz = _seg_sprint(blocks, cx, cy, cz, cx - 2.0, cy + 5.0, cz + 12.0, w=2.1, d=2.4)
    return cx, cy, cz


def _build_summit(blocks, cx, cy, cz):
    """Final exam — every tool in one chained route."""
    cx, cy, cz = _seg_sprint(blocks, cx, cy, cz, cx + 7.0, cy + 1.0, cz + 10.0, w=2.0, d=2.3)
    cx, cy, cz = _seg_wall_chain(blocks, cx, cy, cz, cx - 5.0, cy + 2.5, cz + 9.0, wall_side=1, w=2.1, d=2.4)
    cx, cy, cz = _seg_double(blocks, cx, cy, cz, cx + 6.0, cy + 4.5, cz + 12.0, w=2.0, d=2.3)
    cx, cy, cz = _seg_wall_alley(blocks, cx, cy, cz, cz + 11.0, wall_x_off=3.0)
    cx, cy, cz = _seg_wall_chain(blocks, cx, cy, cz, cx - 8.0, cy + 3.0, cz + 10.0, wall_side=-1, w=2.0, d=2.3)
    cx, cy, cz = _seg_sprint(blocks, cx, cy, cz, cx + 4.0, cy + 5.5, cz + 13.0, w=2.0, d=2.3)
    cx, cy, cz = _seg_double(blocks, cx, cy, cz, cx - 3.0, cy + 7.0, cz + 11.0, w=2.1, d=2.4)
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
    cx, cy, cz = _build_pit(blocks, cx, cy, cz)
    cx, cy, cz = _build_neon(blocks, cx, cy, cz, rng)
    cx, cy, cz = _build_gap(blocks, cx, cy, cz)
    cx, cy, cz = _build_tower(blocks, cx, cy, cz)
    cx, cy, cz = _build_summit(blocks, cx, cy, cz)

    goal_z = cz + 12.0
    blocks.append(_platform(cx, cy + 3.0, goal_z, 12, 12, thickness=0.5))

    collisions = [b["collision"] for b in blocks]
    wall_solids = [b["collision"] for b in blocks if b["kind"] == "surf_wall"]
    return blocks, collisions, wall_solids, goal_z, cy + 3.0, seed


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
