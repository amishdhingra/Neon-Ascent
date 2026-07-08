"""Dense Celeste / Silksong-style fields — packed shelves + guaranteed spine."""

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

COLUMNS = (0.13, 0.27, 0.41, 0.55, 0.69, 0.83)


def _sw(width, world_width):
    return max(20, int(width * world_width / BASE_WORLD_WIDTH))


def _jump_limits(w):
    scale = w / BASE_WORLD_WIDTH
    return {
        "std_dx": int(195 * scale),
        "std_up": (int(48 * scale), int(84 * scale)),
        "hard_dx": int(240 * scale),
        "hard_up": (int(48 * scale), int(118 * scale)),
    }


def _can_jump(a, b, dx_lim, up_rng):
    return abs(b.centerx - a.centerx) <= dx_lim and up_rng[0] <= a.top - b.top <= up_rng[1]


def _overlaps(platforms, rect, gap=12):
    return any(rect.inflate(gap, gap).colliderect(o) for o in platforms)


def _plat(cx, top, pw, ph, edge, w):
    cx = max(edge + pw // 2, min(w - edge - pw // 2, int(cx)))
    return pygame.Rect(int(cx - pw // 2), int(top), int(pw), ph)


def _in_bounds(rect, edge, w):
    return rect.left >= edge and rect.right <= w - edge and rect.top >= 0


def _add_spine(platforms, rect, edge, w, jump, from_p):
    if _can_jump(from_p, rect, jump["std_dx"], jump["std_up"]) is False and from_p is not rect:
        return None
    for nudge in (0, 8, 16, -12, 24, -20, 32):
        trial = rect.copy()
        trial.top += nudge
        if not _in_bounds(trial, edge, w) or _overlaps(platforms, trial):
            continue
        if not _can_jump(from_p, trial, jump["std_dx"], jump["std_up"]):
            continue
        platforms.append(trial)
        return trial
    return None


def _bfs(start, nodes, jump):
    seen = {id(start)}
    stack = [start]
    while stack:
        cur = stack.pop()
        for n in nodes:
            if id(n) in seen:
                continue
            if _can_jump(cur, n, jump["std_dx"], jump["std_up"]):
                seen.add(id(n))
                stack.append(n)
    return seen


def _bridge(from_p, rng, jump, edge, w, ph, y, target_x=None):
    lo, hi = jump["std_up"]
    tx = target_x if target_x is not None else from_p.centerx
    for _ in range(14):
        top = y if y else from_p.top - rng.randint(lo, hi)
        dx = int((tx - from_p.centerx) * rng.uniform(0.45, 1.0))
        pw = _sw(rng.randint(90, 130), w)
        p = _plat(from_p.centerx + dx, top, pw, ph, edge, w)
        if _can_jump(from_p, p, jump["std_dx"], jump["std_up"]):
            return p
    return _plat(tx, from_p.top - lo, _sw(115, w), ph, edge, w)


def _layer_cols(rng, style, layer_i, diff):
    n = len(COLUMNS)
    if layer_i % 5 == 0:
        return list(range(n))
    mode = rng.choice(["full", "left", "right", "wings", "center", "scatter"])
    if mode == "full":
        return rng.sample(range(n), rng.randint(4, n))
    if mode == "left":
        return [0, 1, 2, 3]
    if mode == "right":
        return [2, 3, 4, 5]
    if mode == "wings":
        return [0, 1, 4, 5]
    if mode == "center":
        return [1, 2, 3, 4]
    return rng.sample(range(n), rng.randint(3, 5))


def _shelf(y, cols, rng, w, edge, ph, diff, wide=False):
    if wide:
        return [_plat(w * 0.5, y, _sw(min(420, w - 80), w), ph, edge, w)]
    out = []
    for ci in cols:
        pw = _sw(rng.randint(70 if diff else 78, 128), w)
        cx = w * COLUMNS[ci] + rng.randint(-_sw(24, w), _sw(24, w))
        out.append(_plat(cx, y + rng.randint(-8, 8), pw, ph, edge, w))
    return out


def _zone_decor(style, rng, w, edge, ph, y, shelf):
    extras = []
    if style == "neon" and len(shelf) >= 2 and rng.random() < 0.5:
        a, b = rng.sample(shelf, 2)
        px = (a.centerx + b.centerx) // 2
        extras.append(pygame.Rect(px - _sw(12, w), min(a.top, b.top) - 8, _sw(24, w), _sw(120, w)))
    if style == "gap" and rng.random() < 0.35:
        extras.append(_plat(w * 0.5, y - _sw(18, w), _sw(min(300, w - 100), w), ph, edge, w))
    if style == "tower" and rng.random() < 0.4:
        cx = w * rng.choice(COLUMNS)
        extras.append(pygame.Rect(cx - _sw(11, w), y - _sw(20, w), _sw(22, w), _sw(150, w)))
    return extras


def _build_zone(spine_tip, y_top, style, rng, w, edge, ph, jump, diff, platforms):
    lo, hi = jump["std_up"]
    runway = 44 + lo + hi + int(24 * w / BASE_WORLD_WIDTH)
    y = spine_tip.top - rng.randint(lo, hi - 6)
    layer = 0

    while y > y_top + 20 and spine_tip.top > runway:
        layer += 1
        wide = layer % 4 == 0
        cols = _layer_cols(rng, style, layer, diff)
        candidates = _shelf(y, cols, rng, w, edge, ph, diff, wide=wide)

        linked = [p for p in candidates if _can_jump(spine_tip, p, jump["std_dx"], jump["std_up"])]
        if linked:
            spine_next = linked[0]
        else:
            far = w * (COLUMNS[5] if spine_tip.centerx < w * 0.5 else COLUMNS[0])
            spine_next = _bridge(spine_tip, rng, jump, edge, w, ph, y, target_x=far)

        added = _add_spine(platforms, spine_next, edge, w, jump, spine_tip)
        if not added:
            spine_next = _bridge(spine_tip, rng, jump, edge, w, ph, y + 20, target_x=spine_tip.centerx)
            added = _add_spine(platforms, spine_next, edge, w, jump, spine_tip)
        if not added:
            y -= rng.randint(lo, hi)
            continue
        spine_tip = added

        for p in candidates:
            if p is spine_next or p.top < runway:
                continue
            if not _overlaps(platforms, p) and _in_bounds(p, edge, w):
                platforms.append(p)

        if layer % 2 == 1:
            for ci in rng.sample(list(range(len(COLUMNS))), rng.randint(1, 2)):
                chip_y = y - rng.randint(14, 32)
                if chip_y < runway:
                    continue
                chip = _plat(
                    w * COLUMNS[ci] + rng.randint(-_sw(35, w), _sw(35, w)),
                    chip_y,
                    _sw(rng.randint(52, 72), w),
                    ph,
                    edge,
                    w,
                )
                if not _overlaps(platforms, chip) and _in_bounds(chip, edge, w):
                    platforms.append(chip)

        for d in _zone_decor(style, rng, w, edge, ph, y, candidates):
            if d.top < runway:
                continue
            if not _overlaps(platforms, d) and _in_bounds(d, edge, w):
                platforms.append(d)

        y -= rng.randint(max(lo, 50), hi)

    return spine_tip


def _finish_summit(spine_tip, platforms, rng, edge, w, ph, jump):
    summit_y = 44
    lo, hi = jump["std_up"]
    cur = spine_tip

    while cur.top > summit_y + lo + 8:
        step = _bridge(cur, rng, jump, edge, w, ph, None, target_x=cur.centerx)
        a = _add_spine(platforms, step, edge, w, jump, cur)
        if not a:
            break
        cur = a

    for dx in (0, 55, -55, 110, -110):
        summit = _plat(cur.centerx + dx, summit_y, _sw(260, w), 26, edge, w)
        if _overlaps(platforms, summit) or not _in_bounds(summit, edge, w):
            continue
        if _can_jump(cur, summit, jump["std_dx"], jump["std_up"]) or _can_jump(
            cur, summit, jump["hard_dx"], jump["hard_up"]
        ):
            platforms.append(summit)
            return

    summit = _plat(w * 0.5, summit_y, _sw(260, w), 26, edge, w)
    if not _overlaps(platforms, summit):
        platforms.append(summit)


def generate_level(seed=None):
    if seed is None:
        seed = random.randint(1, 999_999)
    rng = random.Random(seed)

    w, h = s.WORLD_WIDTH, s.WORLD_HEIGHT
    edge = max(40, int(40 * w / BASE_WORLD_WIDTH))
    ph = 20
    jump = _jump_limits(w)

    platforms = [pygame.Rect(0, h - 40, w, 40)]
    start = _plat(w * 0.5, h - 88, _sw(320, w), ph, edge, w)
    platforms.append(start)
    spine = start

    for zi, (y_top, style) in enumerate(ZONE_BANDS):
        spine = _build_zone(spine, y_top, style, rng, w, edge, ph, jump, zi >= 2, platforms)

    _finish_summit(spine, platforms, rng, edge, w, ph, jump)

    return {
        "platforms": platforms,
        "zones": ZONES,
        "world_width": w,
        "world_height": h,
        "seed": seed,
        "start_x": start.x + 40,
        "start_y": start.top - s.PLAYER_HEIGHT - 2,
    }


build_level = generate_level
