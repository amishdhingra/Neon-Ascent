"""Neon course geometry — horizontal platformer route with vertical accents."""

import random

import settings as s

ZONE_CHALLENGES = {
    "pit": ["basic", "basic", "basic", "sprint", "double"],
    "neon": ["basic", "sprint", "double", "wall", "sprint", "double"],
    "gap": ["sprint", "double", "sprint", "wall_sprint", "double", "sprint"],
    "tower": ["wall", "double", "sprint", "wall_double", "double", "sprint"],
    "summit": ["double", "sprint", "wall", "sprint", "double"],
}

# h = forward distance along +Z, v = small height step, lat = sideways offset
LIMITS = {
    "basic": {"h": (4.0, 7.0), "v": (0.15, 0.7), "lat": (0.0, 2.5)},
    "sprint": {"h": (7.0, 11.0), "v": (0.2, 1.0), "lat": (0.5, 4.0)},
    "double": {"h": (9.0, 13.5), "v": (0.6, 1.6), "lat": (1.0, 5.0)},
    "wall": {"h": (5.5, 8.5), "v": (0.8, 2.0), "lat": (2.0, 5.5)},
    "wall_sprint": {"h": (8.0, 11.5), "v": (0.8, 1.8), "lat": (2.0, 6.0)},
    "wall_double": {"h": (9.5, 13.0), "v": (1.0, 2.2), "lat": (2.5, 6.5)},
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


def _place_step(blocks, cx, cy, cz, challenge, rng):
    lim = LIMITS.get(challenge, LIMITS["basic"])
    forward = rng.uniform(*lim["h"])
    rise = rng.uniform(*lim["v"])
    lateral = rng.choice([-1, 1]) * rng.uniform(*lim["lat"])

    nx = cx + lateral
    nz = cz + forward
    ny = cy + rise

    if challenge.startswith("wall"):
        pw, pd = rng.uniform(3.0, 4.0), rng.uniform(3.5, 5.0)
    elif challenge in ("double", "sprint"):
        pw, pd = rng.uniform(3.5, 5.0), rng.uniform(4.0, 6.0)
    else:
        pw, pd = rng.uniform(5.0, 7.0), rng.uniform(5.0, 8.0)

    blocks.append(_platform(nx, ny, nz, pw, pd))

    if challenge.startswith("wall"):
        mid_x = (cx + nx) * 0.5
        mid_z = (cz + nz) * 0.5
        wh = rng.uniform(7.0, 11.0)
        side = -1.0 if lateral >= 0 else 1.0
        blocks.append(_surf_wall(mid_x + side * 3.5, cy + wh * 0.45, mid_z, 0.55, wh, 7.0))

    return nx, ny, nz


def build_tower(seed=None):
    """Build a mostly horizontal neon course that climbs gradually forward."""
    rng = random.Random(seed)
    blocks = []

    # Long spawn runway — climb runs forward along +Z
    blocks.append(_platform(0, 0, 12, 14, 34, thickness=0.6))
    spawn_top = 0.3

    # Tutorial chain: flat run forward, then introduce sprint/double
    intro = [
        (0.0, 0.9, 22.0, 6.0, 6.0),
        (0.0, 0.9, 28.5, 6.0, 6.0),
        (1.5, 1.1, 35.0, 5.5, 5.5),
        (-1.0, 1.1, 42.0, 5.5, 5.5),
        (0.0, 1.5, 50.0, 5.0, 5.0),   # sprint gap
        (2.0, 2.0, 60.0, 4.5, 5.0),   # double jump
    ]
    cx, cy, cz = 0.0, spawn_top, 4.0
    for ix, iy, iz, iw, id_ in intro:
        blocks.append(_platform(ix, iy, iz, iw, id_))
        cx, cy, cz = ix, _top_y(blocks[-1]), iz

    # Wall-surf tutorial — orange panel right beside the sprint platform
    blocks.append(_surf_wall(-3.2, 2.0, 50.0, 0.55, 10.0, 10.0))

    for zone in ("pit", "neon", "gap", "tower", "summit"):
        for challenge in ZONE_CHALLENGES[zone]:
            cx, cy, cz = _place_step(blocks, cx, cy, cz, challenge, rng)

    goal_z = cz + 8.0
    summit_y = cy + 1.5
    blocks.append(_platform(cx, summit_y, goal_z, 12, 12, thickness=0.5))

    collisions = [b["collision"] for b in blocks]
    wall_solids = [b["collision"] for b in blocks if b["kind"] == "surf_wall"]
    return blocks, collisions, wall_solids, goal_z, summit_y


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
