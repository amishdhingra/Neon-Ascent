"""Procedural level generation for Neon Ascent — multi-path vertical climbs."""

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

# Left, centre, and right climb routes (fraction of world width)
LANE_FRACTIONS = (0.17, 0.50, 0.83)


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
    if not _overlaps(platforms, rect):
        return rect

    for distance in range(24, 360, 24):
        for direction in (-1, 1):
            moved = rect.copy()
            moved.x += direction * distance
            if moved.left < edge or moved.right > world_width - edge:
                continue
            if not _overlaps(platforms, moved):
                return moved
    return None


def _add_platform(platforms, rect, edge, world_width):
    cleared = _resolve_clear_spot(platforms, rect, edge, world_width)
    if cleared and not _overlaps(platforms, cleared):
        platforms.append(cleared)
        return cleared
    return None


def _lane_x(lane_fraction, world_width):
    return lane_fraction * world_width


def _place_lane_step(parent, lane_fraction, platforms, rng, w, edge, plat_h, max_x, min_up, max_up):
    """Place the next platform for one lane, kept near that lane's horizontal band."""
    pw = rng.randint(_scale_width(95, w), _scale_width(150, w))
    step_up = rng.randint(min_up, max_up)
    band = int(max_x * 0.35)
    anchor_x = _lane_x(lane_fraction, w)

    for attempt in range(36):
        jitter = rng.randint(-band, band)
        y = parent.top - step_up - (attempt // 12) * 5
        px = _clamp_platform_x(anchor_x + jitter, pw, edge, w)
        candidate = pygame.Rect(px, y, pw, plat_h)

        if not _reachable(parent, candidate, max_x, min_up, max_up + 15):
            continue

        cleared = _resolve_clear_spot(platforms, candidate, edge, w)
        if cleared:
            return cleared

    fallback = pygame.Rect(_clamp_platform_x(anchor_x, pw, edge, w), parent.top - step_up, pw, plat_h)
    cleared = _resolve_clear_spot(platforms, fallback, edge, w)
    return cleared or fallback


def _spread_lane_start(from_platform, lane_fraction, platforms, rng, w, edge, plat_h, max_x, min_up, max_up):
    """First step onto a side lane from the starting area."""
    spread_x = int(340 * w / BASE_WORLD_WIDTH)
    pw = rng.randint(_scale_width(100, w), _scale_width(155, w))
    step_up = rng.randint(min_up, max_up)
    anchor_x = _lane_x(lane_fraction, w)

    for attempt in range(40):
        y = from_platform.top - step_up - (attempt // 10) * 4
        px = _clamp_platform_x(anchor_x, pw, edge, w)
        candidate = pygame.Rect(px, y, pw, plat_h)
        if not _reachable(from_platform, candidate, spread_x, min_up, max_up + 20):
            continue
        cleared = _resolve_clear_spot(platforms, candidate, edge, w)
        if cleared:
            return cleared
    return None


def _try_bridge(head_a, head_b, platforms, rng, w, edge, plat_h, max_x, min_up, max_up):
    """Optional platform between two lanes so you can switch routes."""
    mid_x = (head_a.centerx + head_b.centerx) / 2
    y = min(head_a.top, head_b.top) - rng.randint(min_up, max_up)
    pw = rng.randint(_scale_width(90, w), _scale_width(135, w))
    candidate = pygame.Rect(_clamp_platform_x(mid_x, pw, edge, w), y, pw, plat_h)
    bridge_max_x = int(max_x * 1.15)

    if not _reachable(head_a, candidate, bridge_max_x, min_up, max_up + 25):
        return None
    if not _reachable(head_b, candidate, bridge_max_x, min_up, max_up + 25):
        return None
    if _overlaps(platforms, candidate):
        return _resolve_clear_spot(platforms, candidate, edge, w)
    return candidate


def _try_wall(anchor, lane_fraction, platforms, rng, w, edge, plat_h):
    if rng.random() > 0.1:
        return None

    wall_w = _scale_width(20, w)
    wall_h = rng.randint(130, 210)

    # Walls face outward so they don't block neighbouring lanes
    if lane_fraction <= 0.25:
        wx = anchor.left - wall_w - 14
    elif lane_fraction >= 0.75:
        wx = anchor.right + 14
    else:
        side = rng.choice([-1, 1])
        wx = anchor.left - wall_w - 14 if side == -1 else anchor.right + 14

    if wx < edge or wx + wall_w > w - edge:
        return None

    wall = pygame.Rect(wx, anchor.top - wall_h + plat_h, wall_w, wall_h)
    if _overlaps(platforms, wall, gap=16):
        return None
    return wall


def _converge_lane(head, lane_fraction, platforms, rng, w, edge, plat_h, max_x, min_up, max_up, pull=0.45):
    """Final steps pull each lane toward the summit centre."""
    bias = _lane_x(lane_fraction, w) * (1 - pull) + (w / 2) * pull
    pw = rng.randint(_scale_width(105, w), _scale_width(160, w))
    step_up = rng.randint(min_up, max_up)
    px = _clamp_platform_x(bias, pw, edge, w)
    candidate = pygame.Rect(px, head.top - step_up, pw, plat_h)

    if not _reachable(head, candidate, max_x, min_up, max_up + 15):
        candidate.centerx = int(head.centerx * 0.55 + (w / 2) * 0.45)
        candidate.top = head.top - step_up
        candidate.left = _clamp_platform_x(candidate.centerx + candidate.width / 2, candidate.width, edge, w)

    cleared = _resolve_clear_spot(platforms, candidate, edge, w)
    return cleared or candidate


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

    start_w = _scale_width(200, w)
    start = pygame.Rect(_clamp_platform_x(_lane_x(LANE_FRACTIONS[0], w), start_w, edge, w), h - 84, start_w, plat_h)
    platforms.append(start)

    lane_heads = [start, None, None]

    for lane_idx in (1, 2):
        entry = _spread_lane_start(start, LANE_FRACTIONS[lane_idx], platforms, rng, w, edge, plat_h, max_x, min_up, max_up)
        if entry:
            platforms.append(entry)
            lane_heads[lane_idx] = entry
        else:
            entry = _place_lane_step(start, LANE_FRACTIONS[lane_idx], platforms, rng, w, edge, plat_h, max_x, min_up, max_up)
            platforms.append(entry)
            lane_heads[lane_idx] = entry

    row = 0
    while min(head.top for head in lane_heads) > 280:
        for lane_idx, lane_frac in enumerate(LANE_FRACTIONS):
            step = _place_lane_step(lane_heads[lane_idx], lane_frac, platforms, rng, w, edge, plat_h, max_x, min_up, max_up)
            platforms.append(step)
            lane_heads[lane_idx] = step

            wall = _try_wall(step, lane_frac, platforms, rng, w, edge, plat_h)
            if wall:
                platforms.append(wall)

        row += 1
        if row % 4 == 0:
            for left_idx, right_idx in ((0, 1), (1, 2)):
                bridge = _try_bridge(
                    lane_heads[left_idx], lane_heads[right_idx], platforms, rng, w, edge, plat_h, max_x, min_up, max_up
                )
                if bridge:
                    platforms.append(bridge)

    for lane_idx, lane_frac in enumerate(LANE_FRACTIONS):
        step = _converge_lane(lane_heads[lane_idx], lane_frac, platforms, rng, w, edge, plat_h, max_x, min_up, max_up, pull=0.5)
        platforms.append(step)
        lane_heads[lane_idx] = step

    merge = _try_bridge(lane_heads[0], lane_heads[2], platforms, rng, w, edge, plat_h, max_x, min_up, max_up)
    if merge:
        platforms.append(merge)
        anchor = merge
    else:
        anchor = lane_heads[1]

    summit_w = _scale_width(300, w)
    summit = pygame.Rect(w // 2 - summit_w // 2, 48, summit_w, 24)
    approach = _converge_lane(anchor, 0.5, platforms, rng, w, edge, plat_h, max_x, min_up, max_up, pull=1.0)
    _add_platform(platforms, approach, edge, w)
    _add_platform(platforms, summit, edge, w)

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
