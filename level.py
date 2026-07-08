"""Celeste-style climb — choreographed segments that require every movement tool."""

import random

import pygame

import settings as s

BASE_WORLD_WIDTH = 960

ZONES = [
    {"name": "THE PIT", "y": 2680},
    {"name": "NEON PIPES", "y": 1880},
    {"name": "THE GAP", "y": 1080},
    {"name": "THE TOWER", "y": 480},
    {"name": "THE SUMMIT", "y": 120},
]

ZONE_BANDS = [
    (2720, "pit"),
    (1920, "neon"),
    (1120, "gap"),
    (520, "tower"),
    (100, "summit"),
]

# Which challenge types appear per zone (gets harder / more tools)
ZONE_CHALLENGES = {
    "pit": ["basic", "sprint", "double", "sprint"],
    "neon": ["wall", "double", "wall", "sprint", "double"],
    "gap": ["sprint", "double", "sprint", "wall_sprint", "double"],
    "tower": ["wall", "wall_double", "double", "wall", "sprint"],
    "summit": ["wall_double", "double", "wall", "sprint", "wall_double"],
}


def _sw(width, world_width):
    return max(20, int(width * world_width / BASE_WORLD_WIDTH))


def _movement_limits(w):
    """Reach bands per mechanic (tuned to settings.py movement values)."""
    scale = w / BASE_WORLD_WIDTH
    return {
        "walk_dx": int(168 * scale),
        "walk_up": (int(52 * scale), int(76 * scale)),
        "sprint_dx": int(248 * scale),
        "sprint_up": (int(50 * scale), int(80 * scale)),
        "double_dx": int(268 * scale),
        "double_up": (int(88 * scale), int(118 * scale)),
        "wall_dx": int(210 * scale),
        "wall_up": (int(52 * scale), int(108 * scale)),
    }


def _reach(a, b, dx, up):
    return abs(b.centerx - a.centerx) <= dx and up[0] <= a.top - b.top <= up[1]


def _overlaps(platforms, rect, gap=12):
    return any(rect.inflate(gap, gap).colliderect(o) for o in platforms)


def _plat(cx, top, pw, ph, edge, w):
    cx = max(edge + pw // 2, min(w - edge - pw // 2, int(cx)))
    return pygame.Rect(int(cx - pw // 2), int(top), int(pw), ph)


def _wall(cx, top, height, w):
    ww = _sw(22, w)
    return pygame.Rect(int(cx - ww // 2), int(top), ww, int(height))


def _in_bounds(rect, edge, w):
    return rect.left >= edge and rect.right <= w - edge and rect.top >= 0


def _place(platforms, rect, edge, w):
    if not _in_bounds(rect, edge, w) or _overlaps(platforms, rect):
        return None
    platforms.append(rect)
    return rect


def _dy(rng, up):
    return rng.randint(up[0], up[1])


def _fits_mechanic(mechanic, a, b, m):
    walk = _reach(a, b, m["walk_dx"], m["walk_up"])
    sprint = _reach(a, b, m["sprint_dx"], m["sprint_up"])
    double = _reach(a, b, m["double_dx"], m["double_up"])

    if mechanic == "basic":
        return walk
    if mechanic == "sprint":
        return sprint and not walk
    if mechanic == "double":
        return double and not sprint
    if mechanic in ("wall", "wall_sprint", "wall_double"):
        return True
    return walk


def _seg_basic(anchor, rng, w, edge, ph, m):
    pw = _sw(rng.randint(95, 120), w)
    dy = _dy(rng, m["walk_up"])
    dx = rng.randint(-m["walk_dx"] // 2, m["walk_dx"] // 2)
    nxt = _plat(anchor.centerx + dx, anchor.top - dy, pw, ph, edge, w)
    return [nxt], nxt


def _seg_sprint(anchor, rng, w, edge, ph, m):
    pw = _sw(rng.randint(72, 92), w)
    dy = _dy(rng, m["sprint_up"])
    gap = rng.randint(m["walk_dx"] + _sw(24, w), m["sprint_dx"] - _sw(18, w))
    direction = rng.choice([-1, 1])
    nxt = _plat(anchor.centerx + direction * gap, anchor.top - dy, pw, ph, edge, w)
    for _ in range(6):
        if _fits_mechanic("sprint", anchor, nxt, m):
            return [nxt], nxt
        gap += _sw(12, w)
        nxt = _plat(anchor.centerx + direction * gap, anchor.top - dy, pw, ph, edge, w)
    return [nxt], nxt


def _seg_double(anchor, rng, w, edge, ph, m):
    pw = _sw(rng.randint(68, 88), w)
    kind = rng.choice(["high", "wide"])
    if kind == "high":
        dy = rng.randint(m["walk_up"][1] + 8, m["double_up"][1])
        dx = rng.randint(-m["walk_dx"] // 3, m["walk_dx"] // 3)
    else:
        dy = _dy(rng, m["walk_up"])
        dx = rng.choice([-1, 1]) * rng.randint(m["sprint_dx"] - _sw(20, w), m["double_dx"] - _sw(10, w))
    nxt = _plat(anchor.centerx + dx, anchor.top - dy, pw, ph, edge, w)
    for _ in range(8):
        if _fits_mechanic("double", anchor, nxt, m):
            return [nxt], nxt
        if kind == "high":
            dy -= 6
        else:
            dx = int(dx * 1.08)
        nxt = _plat(anchor.centerx + dx, anchor.top - dy, pw, ph, edge, w)
    return [nxt], nxt


def _seg_wall(anchor, rng, w, edge, ph, m):
    """Wall shaft — must wall-jump between ledges."""
    side = rng.choice([-1, 1])
    wall_x = anchor.centerx + side * _sw(95, w)
    rise = _dy(rng, m["wall_up"])
    wall_h = rise * 2 + _sw(140, w)
    wall_top = anchor.top - _sw(40, w)

    ledge1 = _plat(anchor.centerx - side * _sw(30, w), anchor.top - rise, _sw(88, w), ph, edge, w)
    ledge2 = _plat(anchor.centerx + side * _sw(110, w), anchor.top - rise * 2, _sw(82, w), ph, edge, w)
    wall = _wall(wall_x, wall_top, wall_h, w)

    if not _reach(anchor, ledge1, m["walk_dx"], m["walk_up"]):
        ledge1 = _plat(anchor.centerx, anchor.top - _dy(rng, m["walk_up"]), _sw(100, w), ph, edge, w)
    if not _reach(ledge1, ledge2, m["wall_dx"], m["wall_up"]):
        ledge2.top = ledge1.top - _dy(rng, m["wall_up"])

    return [ledge1, wall, ledge2], ledge2


def _seg_wall_sprint(anchor, rng, w, edge, ph, m):
    """Sprint gap into a wall-jump shaft."""
    rects, exit_p = _seg_sprint(anchor, rng, w, edge, ph, m)
    if not rects:
        return _seg_wall(anchor, rng, w, edge, ph, m)
    sprint_plat = rects[0]
    side = 1 if sprint_plat.centerx > anchor.centerx else -1
    wall_x = sprint_plat.centerx + side * _sw(55, w)
    rise = _dy(rng, m["wall_up"])
    wall = _wall(wall_x, sprint_plat.top - _sw(30, w), rise + _sw(120, w), w)
    top = _plat(sprint_plat.centerx + side * _sw(130, w), sprint_plat.top - rise, _sw(78, w), ph, edge, w)
    return rects + [wall, top], top


def _seg_wall_double(anchor, rng, w, edge, ph, m):
    """Wall jump, then double jump to a small distant ledge."""
    side = rng.choice([-1, 1])
    wall_x = anchor.centerx + side * _sw(88, w)
    mid_y = anchor.top - _dy(rng, m["wall_up"])
    mid = _plat(anchor.centerx - side * _sw(20, w), mid_y, _sw(80, w), ph, edge, w)
    wall = _wall(wall_x, mid_y - _sw(25, w), _sw(180, w), w)

    far_dx = side * rng.randint(m["wall_dx"] // 2, m["double_dx"] - _sw(30, w))
    far_dy = rng.randint(m["double_up"][0], m["double_up"][1])
    top = _plat(mid.centerx + far_dx, mid.top - far_dy, _sw(64, w), ph, edge, w)

    if not _reach(anchor, mid, m["walk_dx"], m["walk_up"]):
        mid = _plat(anchor.centerx, anchor.top - _dy(rng, m["walk_up"]), _sw(95, w), ph, edge, w)
    if not _fits_mechanic("double", mid, top, m):
        top = _plat(mid.centerx + far_dx, mid.top - m["double_up"][0], _sw(64, w), ph, edge, w)

    return [mid, wall, top], top


SEGMENT_BUILDERS = {
    "basic": _seg_basic,
    "sprint": _seg_sprint,
    "double": _seg_double,
    "wall": _seg_wall,
    "wall_sprint": _seg_wall_sprint,
    "wall_double": _seg_wall_double,
}


def _side_density(anchor, rng, w, edge, ph, m, platforms, mechanic):
    """Optional nearby platforms — harder than the main route."""
    extras = []
    for _ in range(rng.randint(1, 3)):
        pw = _sw(rng.randint(52, 72), w)
        cx = anchor.centerx + rng.randint(-m["sprint_dx"], m["sprint_dx"])
        top = anchor.top - rng.randint(m["walk_up"][0], m["double_up"][1] // 2)
        p = _plat(cx, top, pw, ph, edge, w)
        if mechanic != "basic" and _reach(anchor, p, m["walk_dx"], m["walk_up"]):
            continue
        if _place(platforms, p, edge, w):
            extras.append(p)
    return extras


def _build_zone(spine, y_top, style, rng, w, edge, ph, m, platforms):
    runway = 44 + m["walk_up"][0] + m["double_up"][1] + _sw(28, w)
    challenges = list(ZONE_CHALLENGES.get(style, ZONE_CHALLENGES["gap"]))
    rng.shuffle(challenges)

    for mechanic in challenges:
        if spine.top <= max(y_top + 40, runway):
            break

        builder = SEGMENT_BUILDERS.get(mechanic, _seg_basic)
        rects, exit_p = builder(spine, rng, w, edge, ph, m)

        placed_exit = None
        for r in rects:
            p = _place(platforms, r, edge, w)
            if p:
                placed_exit = p

        if placed_exit:
            spine = placed_exit
            _side_density(spine, rng, w, edge, ph, m, platforms, mechanic)

    return spine


def _finish_summit(spine, platforms, rng, edge, w, ph, m):
    summit_y = 44
    cur = spine

    while cur.top > summit_y + m["walk_up"][0] + 10:
        dy = _dy(rng, m["walk_up"])
        step = _plat(cur.centerx, cur.top - dy, _sw(100, w), ph, edge, w)
        if not _place(platforms, step, edge, w):
            break
        cur = step

    summit = _plat(w * 0.5, summit_y, _sw(240, w), 26, edge, w)
    _place(platforms, summit, edge, w)


def generate_level(seed=None):
    if seed is None:
        seed = random.randint(1, 999_999)
    rng = random.Random(seed)

    w, h = s.WORLD_WIDTH, s.WORLD_HEIGHT
    edge = max(40, int(40 * w / BASE_WORLD_WIDTH))
    ph = 20
    m = _movement_limits(w)

    platforms = [pygame.Rect(0, h - 40, w, 40)]
    start = _plat(w * 0.5, h - 88, _sw(200, w), ph, edge, w)
    platforms.append(start)
    spine = start

    for y_top, style in ZONE_BANDS:
        spine = _build_zone(spine, y_top, style, rng, w, edge, ph, m, platforms)

    _finish_summit(spine, platforms, rng, edge, w, ph, m)

    return {
        "platforms": platforms,
        "zones": ZONES,
        "world_width": w,
        "world_height": h,
        "seed": seed,
        "start_x": start.x + 28,
        "start_y": start.top - s.PLAYER_HEIGHT - 2,
    }


build_level = generate_level
