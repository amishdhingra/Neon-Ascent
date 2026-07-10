"""Procedural neon course — setpieces, pacing, guide rails, summit."""

import math
import random

import settings as s

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

# Shorter runs — ~3–4 segments per zone plus setpiece
ZONE_ORDER = [
    ("THE PIT", 3, ("sprint_gap", "zigzag_sprint", "double_arc", "combo_sprint")),
    ("NEON PIPES", 4, ("pipe_swing", "kick_corridor", "void_cross", "combo_wall")),
    ("THE GAP", 4, ("gap_marathon", "falling_shelf", "overhang", "combo_double")),
    ("THE TOWER", 4, ("stagger_climb", "wall_alley", "climb_burst", "combo_wall")),
    ("THE SUMMIT", 3, ("overhang", "kick_corridor", "final_gauntlet")),
]

_GENERATED_ZONES = [{"name": "SHORE", "z_start": 0}]
_CURRENT_THEME = (0.31, 1.0, 0.86)
_GUIDE_RAILS = []
_CORE_COUNT = 0


def _box(x, y, z, w, h, d):
    hw, hh, hd = w * 0.5, h * 0.5, d * 0.5
    return (x - hw, y - hh, z - hd, x + hw, y + hh, z + hd)


def _platform(x, y, z, w, d, thickness=0.4, colour=None, kind="platform"):
    block = {
        "pos": (x, y, z),
        "size": (w, thickness, d),
        "collision": _box(x, y, z, w, thickness, d),
        "kind": kind,
        "colour": colour or _CURRENT_THEME,
    }
    return block


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


def _plat(blocks, x, y, z, w, d, colour=None, kind="platform"):
    blocks.append(_platform(x, y, z, w, d, colour=colour, kind=kind))
    return x, _top_y(blocks[-1]), z


def _wall(blocks, x, y, z, h=10.0, w=0.55, d=8.0):
    blocks.append(_surf_wall(x, y, z, w, h, d))


def _add_rail(x1, y1, z1, x2, y2, z2):
    _GUIDE_RAILS.append((x1, y1 + 0.35, z1, x2, y2 + 0.35, z2))


def _place_core(blocks, x, y, z):
    global _CORE_COUNT
    blocks.append({
        "kind": "core",
        "id": _CORE_COUNT,
        "pos": (x, y, z),
        "size": (0.9, 0.9, 0.9),
        "collision": None,
        "collected": False,
    })
    _CORE_COUNT += 1


def _zone_gate(blocks, zone_name, x, y, z):
    colour = ZONE_THEMES.get(zone_name, (0.5, 0.8, 1.0))
    blocks.append({
        "kind": "gate",
        "name": zone_name,
        "pos": (x, y + 3.5, z),
        "size": (14.0, 7.0, 0.6),
        "colour": colour,
        "collision": None,
    })


def _rest_pad(blocks, cx, cy, cz, rng):
    w, d = rng.uniform(8.0, 10.0), rng.uniform(8.0, 10.0)
    fwd = rng.uniform(5.0, 7.0)
    return _plat(blocks, cx, cy + rng.uniform(-0.1, 0.3), cz + fwd, w, d, kind="rest")


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


# --- Zone setpieces (memorable anchors) ---


def _setpiece_pit(blocks, cx, cy, cz, rng):
    """Neon ring — pads arc around a hollow drop."""
    side = rng.choice([-1, 1])
    pts = [
        (side * 6.0, 4.0),
        (side * 3.0, 10.0),
        (-side * 3.0, 14.0),
        (-side * 6.0, 8.0),
    ]
    for i, (lat, fwd) in enumerate(pts):
        cx, cy, cz = _plat(blocks, cx + lat, cy + i * 0.25, cz + fwd, 3.5, 3.5)
    _place_core(blocks, cx + side * 2.5, cy + 1.8, cz - 2.0)
    return cx, cy, cz


def _setpiece_pipes(blocks, cx, cy, cz, rng):
    """Enclosed tube — surf walls on both sides."""
    length = 26.0
    mid_z = cz + length * 0.5
    _wall(blocks, cx - 4.2, cy + 4.0, mid_z, h=12.0, d=length + 2.0)
    _wall(blocks, cx + 4.2, cy + 4.0, mid_z, h=12.0, d=length + 2.0)
    for _ in range(3):
        cz += rng.uniform(7.0, 9.0)
        cx, cy, cz = _plat(blocks, cx + rng.uniform(-1.0, 1.0), cy + rng.uniform(0.0, 0.6), cz, 3.5, 3.5)
    _place_core(blocks, cx - 3.5, cy + 2.5, cz - 3.0)
    return cx, cy, cz


def _setpiece_gap(blocks, cx, cy, cz, rng):
    """Void spine — one long narrow ridge."""
    length = 18.0
    cx, cy, cz = _plat(blocks, cx, cy, cz + length * 0.5, 1.8, length)
    _place_core(blocks, cx, cy + 1.6, cz - 3.0)
    return _step(blocks, cx, cy, cz, rng, "sprint", lat_mul=rng.choice([-1, 1]))


def _setpiece_tower(blocks, cx, cy, cz, rng):
    """Spiral shaft — platforms offset in X and Z."""
    side = 1
    for i in range(4):
        lat = side * rng.uniform(5.0, 7.5)
        fwd = rng.uniform(5.0, 7.0)
        rise = rng.uniform(1.0, 2.0)
        cx, cy, cz = _plat(blocks, cx + lat, cy + rise, cz + fwd, 3.0, 3.0)
        if i % 2 == 0:
            _wall(blocks, cx - side * 3.5, cy + 2.0, cz - 1.0, h=10.0, d=8.0)
        side *= -1
    _place_core(blocks, cx + side * 2.0, cy + 2.5, cz + 2.0)
    return cx, cy, cz


def _setpiece_summit(blocks, cx, cy, cz, rng):
    """Final gate arch before the last push."""
    _zone_gate(blocks, "SUMMIT GATE", cx, cy, cz + 2.0)
    return cx, cy, cz + 6.0


SETPIECES = {
    "THE PIT": _setpiece_pit,
    "NEON PIPES": _setpiece_pipes,
    "THE GAP": _setpiece_gap,
    "THE TOWER": _setpiece_tower,
    "THE SUMMIT": _setpiece_summit,
}


# --- Segments ---


def _seg_sprint_gap(blocks, cx, cy, cz, rng):
    return _step(blocks, cx, cy, cz, rng, "sprint", wall=rng.random() < 0.35)


def _seg_double_arc(blocks, cx, cy, cz, rng):
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "double")
    side = rng.choice([-1, 1])
    return _step(blocks, cx, cy, cz, rng, "double", lat_mul=side, rise_mul=rng.uniform(0.6, 1.0))


def _seg_wall_sprint(blocks, cx, cy, cz, rng):
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
    for _ in range(rng.randint(3, 4)):
        cx, cy, cz = _step(blocks, cx, cy, cz, rng, "sprint", lat_mul=side * rng.uniform(0.8, 1.2), rise_mul=rng.uniform(0.2, 0.8))
        side *= -1
    return cx, cy, cz


def _seg_pipe_swing(blocks, cx, cy, cz, rng):
    base = cy
    side = rng.choice([-1, 1])
    for i in range(rng.randint(3, 4)):
        lat = side * rng.uniform(5.5, 8.0)
        fwd = rng.uniform(4.5, 7.0)
        w, d = _pad_size(rng, "sprint")
        cx, cy, cz = _plat(blocks, cx + lat, base + rng.uniform(-0.2, 0.6), cz + fwd, w, d)
        if i % 2 == 0:
            _wall(blocks, cx - side * 2.8, base + 3.0, cz - 1.0, h=rng.uniform(8, 11), d=rng.uniform(6, 9))
        side *= -1
    return cx, cy, cz


def _seg_gap_marathon(blocks, cx, cy, cz, rng):
    for _ in range(rng.randint(4, 5)):
        cx, cy, cz = _step(blocks, cx, cy, cz, rng, "sprint", lat_mul=rng.uniform(0.5, 1.2), rise_mul=rng.uniform(0.2, 1.0))
    return cx, cy, cz


def _seg_switchback(blocks, cx, cy, cz, rng):
    side = rng.choice([-1, 1])
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "wall_sprint", wall=True, wall_side=side)
    cx, cy, cz = _plat(blocks, cx - side * rng.uniform(9.0, 12.0), cy + rng.uniform(-0.5, 0.8), cz + rng.uniform(5.0, 8.0), 2.2, 2.8)
    return _step(blocks, cx, cy, cz, rng, "double", lat_mul=side)


def _seg_climb_burst(blocks, cx, cy, cz, rng):
    for _ in range(2):
        cx, cy, cz = _step(blocks, cx, cy, cz, rng, "double", lat_mul=0.3, rise_mul=1.2)
    return _step(blocks, cx, cy, cz, rng, "wall_sprint", wall=True)


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
    cx, cy, cz = _step(blocks, cx, cy, cz, rng, "wall_double", wall=True)
    return _step(blocks, cx, cy, cz, rng, "double")


def _seg_falling_shelf(blocks, cx, cy, cz, rng):
    for _ in range(rng.randint(2, 3)):
        drop = rng.uniform(1.0, 2.0)
        fwd = rng.uniform(4.0, 6.0)
        off = rng.choice([-1, 1]) * rng.uniform(2.0, 4.5)
        cx, cy, cz = _plat(blocks, cx + off, cy - drop, cz + fwd, rng.uniform(2.5, 3.5), rng.uniform(2.5, 3.5))
    return _step(blocks, cx, cy, cz, rng, "double", rise_mul=1.3, lat_mul=rng.choice([-1, 1]))


def _seg_overhang(blocks, cx, cy, cz, rng):
    side = rng.choice([-1, 1])
    fwd = rng.uniform(9.0, 12.0)
    rise = rng.uniform(2.5, 4.0)
    _wall(blocks, cx + side * 3.5, cy + 1.5, cz + fwd * 0.45, h=rng.uniform(9, 12), d=rng.uniform(7, 10))
    w, d = _pad_size(rng, "double")
    return _plat(blocks, cx + side * rng.uniform(1.0, 3.0), cy + rise, cz + fwd, w, d)


def _seg_kick_corridor(blocks, cx, cy, cz, rng):
    side = rng.choice([-1, 1])
    for _ in range(rng.randint(2, 3)):
        fwd = rng.uniform(7.0, 10.0)
        lat = side * rng.uniform(4.0, 6.5)
        w, d = _pad_size(rng, "wall")
        nz = cz + fwd
        nx = cx + lat
        _wall(blocks, (cx + nx) * 0.5 - side * 3.0, cy + 2.0, (cz + nz) * 0.5, h=rng.uniform(9, 12), d=rng.uniform(7, 10))
        cx, cy, cz = _plat(blocks, nx, cy + rng.uniform(0.3, 1.2), nz, w, d)
        side *= -1
    return cx, cy, cz


def _seg_void_cross(blocks, cx, cy, cz, rng):
    fwd = rng.uniform(10.0, 13.0)
    lat = rng.choice([-1, 1]) * rng.uniform(2.0, 5.0)
    w, d = rng.uniform(1.8, 2.2), rng.uniform(1.8, 2.2)
    return _plat(blocks, cx + lat, cy + rng.uniform(0.0, 1.0), cz + fwd, w, d)


def _seg_stagger_climb(blocks, cx, cy, cz, rng):
    for _ in range(rng.randint(3, 4)):
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
    "falling_shelf": _seg_falling_shelf,
    "overhang": _seg_overhang,
    "kick_corridor": _seg_kick_corridor,
    "void_cross": _seg_void_cross,
    "stagger_climb": _seg_stagger_climb,
}


def _build_intro(blocks):
    blocks.append(_platform(0, 0, 0, 10, 10, thickness=0.6))
    cx, cy, cz = 0.0, 0.3, -2.0
    for ix, iy, iz, iw, id_ in [
        (0.0, 0.5, 5.0, 4.5, 4.5),
        (0.0, 0.8, 13.0, 4.0, 4.0),
        (0.0, 1.0, 22.0, 4.0, 4.0),
        (1.0, 1.3, 32.0, 4.0, 4.5),
    ]:
        cx, cy, cz = _plat(blocks, ix, iy, iz, iw, id_)
    _wall(blocks, -3.0, 2.0, 27.0, h=10.0, d=9.0)
    return cx, cy, cz


def _pick_zone_segments(rng, count, pool):
    pool = list(pool)
    rng.shuffle(pool)
    if count <= len(pool):
        picks = rng.sample(pool, count)
    else:
        picks = [rng.choice(pool) for _ in range(count)]
    rng.shuffle(picks)
    return picks


def _build_rails_from_platforms(blocks):
    plats = [b for b in blocks if b["kind"] in ("platform", "rest", "summit")]
    for i in range(len(plats) - 1):
        x1, y1, z1 = plats[i]["pos"]
        x2, y2, z2 = plats[i + 1]["pos"]
        if abs(z2 - z1) > 40:
            continue
        _add_rail(x1, y1, z1, x2, y2, z2)


def _build_zone(blocks, cx, cy, cz, rng, zone_name, count, pool):
    global _GENERATED_ZONES, _CURRENT_THEME
    _GENERATED_ZONES.append({"name": zone_name, "z_start": cz})
    _CURRENT_THEME = ZONE_THEMES.get(zone_name, (0.31, 1.0, 0.86))
    _zone_gate(blocks, zone_name, cx, cy, cz)

    setpiece = SETPIECES.get(zone_name)
    if setpiece:
        cx, cy, cz = setpiece(blocks, cx, cy, cz, rng)

    picks = _pick_zone_segments(rng, count, pool)
    for i, key in enumerate(picks):
        if i > 0 and i % 2 == 0:
            cx, cy, cz = _rest_pad(blocks, cx, cy, cz, rng)
        cx, cy, cz = SEGMENTS[key](blocks, cx, cy, cz, rng)
    return cx, cy, cz


def get_zone_name(z_pos):
    name = _GENERATED_ZONES[0]["name"]
    for zone in _GENERATED_ZONES:
        if z_pos >= zone["z_start"]:
            name = zone["name"]
    return name


def build_tower(seed=None):
    global _GENERATED_ZONES, _CURRENT_THEME, _GUIDE_RAILS, _CORE_COUNT
    if seed is None:
        seed = random.randrange(1_000_000)
    rng = random.Random(seed)
    _GENERATED_ZONES = [{"name": "SHORE", "z_start": 0}]
    _CURRENT_THEME = (0.31, 1.0, 0.86)
    _GUIDE_RAILS = []
    _CORE_COUNT = 0
    blocks = []

    cx, cy, cz = _build_intro(blocks)
    for zone_name, count, pool in ZONE_ORDER:
        cx, cy, cz = _build_zone(blocks, cx, cy, cz, rng, zone_name, count, pool)

    goal_z = cz + rng.uniform(6.0, 10.0)
    summit_y = cy + rng.uniform(1.5, 3.0)
    summit_x = cx + rng.uniform(-2, 2)
    blocks.append(_platform(summit_x, summit_y, goal_z, 14, 14, thickness=0.55, colour=s.SUMMIT_COLOUR, kind="summit"))

    _build_rails_from_platforms(blocks)

    collisions = [b["collision"] for b in blocks if b.get("collision")]
    wall_solids = [b["collision"] for b in blocks if b["kind"] == "surf_wall"]
    platform_solids = [b["collision"] for b in blocks if b["kind"] in ("platform", "rest", "summit")]
    summit_box = blocks[-1]["collision"]
    return blocks, collisions, wall_solids, platform_solids, goal_z, summit_y, seed, summit_box, list(_GUIDE_RAILS), _CORE_COUNT


def draw_guide_rails(rails):
    from OpenGL.GL import GL_LINES, glBegin, glColor3f, glEnd, glLineWidth, glVertex3f

    if not rails:
        return
    glLineWidth(1.8)
    glColor3f(0.35, 0.85, 1.0)
    glBegin(GL_LINES)
    for x1, y1, z1, x2, y2, z2 in rails:
        glVertex3f(x1, y1, z1)
        glVertex3f(x2, y2, z2)
    glEnd()


def draw_block(block, pulse=0.0):
    from OpenGL.GL import (
        GL_LINES,
        GL_QUADS,
        glBegin,
        glColor3f,
        glEnd,
        glLineWidth,
        glVertex3f,
    )

    kind = block["kind"]

    if kind == "core" and block.get("collected"):
        return

    x, y, z = block["pos"]

    if kind == "core":
        bob = math.sin(pulse * 4.0 + block["id"]) * 0.15
        s_core = 0.45 + math.sin(pulse * 6.0 + block["id"]) * 0.08
        glColor3f(*s.CORE_COLOUR)
        glBegin(GL_LINES)
        for dx, dy, dz in [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]:
            glVertex3f(x, y + bob, z)
            glVertex3f(x + dx * s_core, y + dy * s_core + bob, z + dz * s_core)
        glEnd()
        return

    if kind == "gate":
        w, h, d = block["size"]
        hw, hh, hd = w * 0.5, h * 0.5, d * 0.5
        colour = block.get("colour", (0.5, 0.8, 1.0))
        glColor3f(*colour)
        for px, pz in [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]:
            glBegin(GL_LINES)
            glVertex3f(x + px, y - hh, z + pz)
            glVertex3f(x + px, y + hh, z + pz)
            glEnd()
        glBegin(GL_LINES)
        glVertex3f(x - hw, y + hh, z - hd)
        glVertex3f(x + hw, y + hh, z - hd)
        glVertex3f(x + hw, y + hh, z - hd)
        glVertex3f(x + hw, y + hh, z + hd)
        glVertex3f(x + hw, y + hh, z + hd)
        glVertex3f(x - hw, y + hh, z + hd)
        glVertex3f(x - hw, y + hh, z + hd)
        glVertex3f(x - hw, y + hh, z - hd)
        glEnd()
        return

    w, h, d = block["size"]
    hw, hh, hd = w * 0.5, h * 0.5, d * 0.5

    if kind == "surf_wall":
        glColor3f(1.0, 0.45, 0.12)
    elif kind == "summit":
        glow = 0.85 + math.sin(pulse * 3.0) * 0.15
        glColor3f(s.SUMMIT_COLOUR[0] * glow, s.SUMMIT_COLOUR[1] * glow, s.SUMMIT_COLOUR[2] * glow)
    elif kind == "rest":
        colour = block.get("colour", s.COLOUR_PLATFORM)
        glColor3f(colour[0] * 0.7, colour[1] * 0.7, colour[2] * 0.7)
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
    if kind in ("platform", "rest", "summit"):
        edge = tuple(c * 0.55 for c in (block.get("colour") or s.COLOUR_PLATFORM))
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
