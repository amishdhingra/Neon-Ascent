"""Procedural level generation for Neon Ascent."""

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


def _scale_width(width, world_width):
    return max(20, int(width * world_width / BASE_WORLD_WIDTH))


def _reachable(from_rect, to_rect, max_x, min_up, max_up):
    dx = abs(to_rect.centerx - from_rect.centerx)
    dy = from_rect.top - to_rect.top
    return dx <= max_x and min_up <= dy <= max_up


def _overlaps(platforms, rect, gap=16):
    padded = rect.inflate(gap, gap)
    return any(padded.colliderect(other) for other in platforms)


def _clamp_platform_x(center_x, pw, edge, world_width):
    left = int(center_x - pw / 2)
    return max(edge, min(world_width - pw - edge, left))


def _resolve_clear_spot(platforms, rect, edge, world_width):
    """Nudge rect horizontally until it no longer overlaps anything."""
    if not _overlaps(platforms, rect):
        return rect

    for distance in range(20, 320, 20):
        for direction in (-1, 1):
            moved = rect.copy()
            moved.x += direction * distance
            if moved.left < edge or moved.right > world_width - edge:
                continue
            if not _overlaps(platforms, moved):
                return moved
    return None


def _place_main_step(path, platforms, rng, w, edge, plat_h, max_x, min_up, max_up, bias_x=0.0):
    """Place the next guaranteed step on the main climb route."""
    pw = rng.randint(_scale_width(110, w), _scale_width(165, w))
    step_up = rng.randint(min_up, max_up)
    target_x = path.centerx * (1 - bias_x) + (w / 2) * bias_x

    for attempt in range(32):
        shift = rng.randint(-int(max_x * 0.45), int(max_x * 0.45))
        y = path.top - step_up - (attempt // 10) * 6
        px = _clamp_platform_x(target_x + shift, pw, edge, w)
        candidate = pygame.Rect(px, y, pw, plat_h)

        if not _reachable(path, candidate, max_x, min_up, max_up + 15):
            continue

        cleared = _resolve_clear_spot(platforms, candidate, edge, w)
        if cleared:
            return cleared

    fallback = pygame.Rect(_clamp_platform_x(path.centerx, pw, edge, w), path.top - step_up, pw, plat_h)
    cleared = _resolve_clear_spot(platforms, fallback, edge, w)
    return cleared or fallback


def _try_extra_platform(recent_steps, platforms, rng, w, edge, plat_h, max_x, min_up, max_up):
    if rng.random() > 0.28:
        return None

    anchor = rng.choice(recent_steps[-3:])
    pw = rng.randint(_scale_width(85, w), _scale_width(125, w))

    for _ in range(24):
        px = rng.randint(edge, w - pw - edge)
        candidate = pygame.Rect(px, anchor.top, pw, plat_h)
        if _overlaps(platforms, candidate):
            continue
        if any(_reachable(step, candidate, max_x, min_up, max_up + 10) for step in recent_steps[-4:]):
            return candidate
    return None


def _try_wall(anchor, platforms, rng, w, edge, plat_h):
    if rng.random() > 0.12:
        return None

    wall_w = _scale_width(20, w)
    wall_h = rng.randint(130, 210)
    side = rng.choice([-1, 1])

    if side == -1:
        wx = anchor.left - wall_w - 14
    else:
        wx = anchor.right + 14

    if wx < edge or wx + wall_w > w - edge:
        return None

    wy = anchor.top - wall_h + plat_h
    wall = pygame.Rect(wx, wy, wall_w, wall_h)
    if _overlaps(platforms, wall, gap=10):
        return None
    return wall


def generate_level(seed=None):
    if seed is None:
        seed = random.randint(1, 999_999)
    rng = random.Random(seed)

    w, h = s.WORLD_WIDTH, s.WORLD_HEIGHT
    edge = max(40, int(40 * w / BASE_WORLD_WIDTH))
    plat_h = 20
    max_x = int(200 * w / BASE_WORLD_WIDTH)
    min_up = int(58 * w / BASE_WORLD_WIDTH)
    max_up = int(102 * w / BASE_WORLD_WIDTH)

    platforms = [pygame.Rect(0, h - 40, w, 40)]

    start_w = _scale_width(190, w)
    start = pygame.Rect(_clamp_platform_x(w * 0.18, start_w, edge, w), h - 84, start_w, plat_h)
    platforms.append(start)

    path = start
    recent_steps = [start]

    while path.top > 240:
        main = _place_main_step(path, platforms, rng, w, edge, plat_h, max_x, min_up, max_up)
        platforms.append(main)
        path = main
        recent_steps.append(main)

        extra = _try_extra_platform(recent_steps, platforms, rng, w, edge, plat_h, max_x, min_up, max_up)
        if extra:
            platforms.append(extra)

        wall = _try_wall(main, platforms, rng, w, edge, plat_h)
        if wall:
            platforms.append(wall)

    step2 = _place_main_step(path, platforms, rng, w, edge, plat_h, max_x, min_up, max_up, bias_x=0.35)
    platforms.append(step2)

    step1 = _place_main_step(step2, platforms, rng, w, edge, plat_h, max_x, min_up, max_up, bias_x=0.65)
    platforms.append(step1)

    summit_w = _scale_width(280, w)
    summit = pygame.Rect(w // 2 - summit_w // 2, 48, summit_w, 24)
    if not _overlaps(platforms, summit):
        platforms.append(summit)

    return {
        "platforms": platforms,
        "zones": ZONES,
        "world_width": w,
        "world_height": h,
        "seed": seed,
        "start_x": start.x + 24,
        "start_y": start.top - s.PLAYER_HEIGHT - 2,
    }


build_level = generate_level
