"""Neon tower geometry — challenge-tuned platforms and wall pillars."""

import math
import random

import settings as s

ZONE_CHALLENGES = {
    "pit": ["basic", "basic", "sprint", "double"],
    "neon": ["sprint", "double", "wall", "double", "sprint"],
    "gap": ["double", "sprint", "wall_sprint", "double", "sprint"],
    "tower": ["wall", "wall_double", "double", "wall", "sprint"],
    "summit": ["wall_double", "double", "wall", "sprint"],
}

LIMITS = {
    "basic": {"h": (2.2, 3.8), "v": (1.0, 1.6)},
    "sprint": {"h": (3.8, 5.8), "v": (1.0, 2.0)},
    "double": {"h": (4.2, 6.8), "v": (1.8, 2.8)},
    "wall": {"h": (3.0, 5.2), "v": (1.4, 2.4)},
    "wall_sprint": {"h": (4.0, 6.0), "v": (1.6, 2.6)},
    "wall_double": {"h": (4.5, 6.5), "v": (2.0, 3.0)},
}


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


def _pillar(x, y, z, w, h, d):
    return {
        "pos": (x, y, z),
        "size": (w, h, d),
        "collision": _box(x, y, z, w, h, d),
        "kind": "pillar",
    }


def _top_y(block):
    x, y, z = block["pos"]
    _, h, _ = block["size"]
    return y + h * 0.5


def _place_step(blocks, cx, cy, cz, challenge, rng):
    """Place the next platform reachable for the given challenge type."""
    lim = LIMITS.get(challenge, LIMITS["basic"])
    dist = rng.uniform(*lim["h"])
    rise = rng.uniform(*lim["v"])
    angle = rng.uniform(-math.pi * 0.65, math.pi * 0.65)

    nx = cx + math.sin(angle) * dist
    nz = cz + math.cos(angle) * dist
    ny = cy + rise

    if challenge in ("wall", "wall_sprint", "wall_double"):
        pw, pd = 2.8, 2.8
    elif challenge in ("double", "sprint"):
        pw, pd = rng.uniform(3.0, 4.2), rng.uniform(3.0, 4.2)
    else:
        pw, pd = rng.uniform(4.0, 5.5), rng.uniform(4.0, 5.5)

    plat = _platform(nx, ny, nz, pw, pd)
    blocks.append(plat)

    if challenge.startswith("wall"):
        mid_x = (cx + nx) * 0.5 + rng.uniform(-1.0, 1.0)
        mid_z = (cz + nz) * 0.5 + rng.uniform(-1.0, 1.0)
        ph = rng.uniform(5.0, 9.0)
        wall_y = cy + ph * 0.5 - 0.5
        blocks.append(_pillar(mid_x, wall_y, mid_z, 0.7, ph, 0.7))

    return nx, ny, nz


def build_tower(seed=None):
    """Build a vertical neon ascent with tuned challenge spacing."""
    rng = random.Random(seed)
    blocks = []

    # Spawn floor — top surface at y = 0.3
    blocks.append(_platform(0, 0, 0, 24, 24, thickness=0.6))
    spawn_top = 0.3

    # Fixed tutorial chain — guaranteed reachable from spawn
    intro = [
        (0, 1.2, 3.5, 5.0, 5.0),
        (1.5, 2.3, 6.5, 4.5, 4.5),
        (-1.0, 3.4, 9.5, 4.0, 4.0),
        (3.0, 4.5, 12.0, 3.8, 3.8),  # sprint jump
        (0.5, 5.8, 16.5, 3.5, 3.5),  # double jump practice
    ]
    cx, cy, cz = 0.0, spawn_top, 0.0
    for ix, iy, iz, iw, id_ in intro:
        blocks.append(_platform(ix, iy, iz, iw, id_))
        cx, cy, cz = ix, _top_y(blocks[-1]), iz

    zones = ["pit", "neon", "gap", "tower", "summit"]
    for zone in zones:
        for challenge in ZONE_CHALLENGES[zone]:
            cx, cy, cz = _place_step(blocks, cx, cy, cz, challenge, rng)

    summit_y = cy + 4.0
    blocks.append(_platform(0, summit_y, 0, 10, 10, thickness=0.5))

    collisions = [b["collision"] for b in blocks]
    wall_solids = [b["collision"] for b in blocks if b["kind"] == "pillar"]
    return blocks, collisions, wall_solids, summit_y + 0.25


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

    if block["kind"] == "pillar":
        glColor3f(0.75, 0.2, 1.0)
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
