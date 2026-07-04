"""Procedural level generation — structured climb sections (platformer + Getting Over It)."""

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


def _sw(width, world_width):
    return max(20, int(width * world_width / BASE_WORLD_WIDTH))


def _reachable(from_rect, to_rect, max_x, min_up, max_up):
    dx = abs(to_rect.centerx - from_rect.centerx)
    dy = from_rect.top - to_rect.top
    return dx <= max_x and min_up <= dy <= max_up


def _overlaps(platforms, rect, gap=16):
    padded = rect.inflate(gap, gap)
    return any(padded.colliderect(other) for other in platforms)


def _clamp_x(center_x, pw, edge, world_width):
    return max(edge, min(world_width - pw - edge, int(center_x - pw / 2)))


def _shift_platforms(platforms, dx, dy, edge, world_width):
    shifted = []
    for rect in platforms:
        moved = rect.move(dx, dy)
        if moved.left < edge:
            moved.left = edge
        if moved.right > world_width - edge:
            moved.right = world_width - edge
        shifted.append(moved)
    return shifted


def _add_all(platforms, new_rects, edge, world_width):
    added = []
    for rect in new_rects:
        if _overlaps(platforms, rect):
            continue
        platforms.append(rect)
        added.append(rect)
    return added


def _section_zigzag(rng, w, edge, top_y, height, plat_h, hard):
    """Alternating left-right steps upward."""
    pw = _sw(130 if not hard else 90, w)
    steps = 4
    rects = []
    go_right = rng.choice([True, False])
    for i in range(steps):
        t = i / (steps - 1) if steps > 1 else 0
        cx = w * (0.22 + 0.56 * t) if go_right else w * (0.78 - 0.56 * t)
        cy = top_y + height - int((i + 1) * height / (steps + 1))
        rects.append(pygame.Rect(_clamp_x(cx, pw, edge, w), cy, pw, plat_h))
    return rects


def _section_gap_run(rng, w, edge, top_y, height, plat_h, hard):
    """Deliberate horizontal gaps — sprint or double jump."""
    pw = _sw(115 if not hard else 85, w)
    gap = _sw(200 if not hard else 260, w)
    y = top_y + height // 2
    x0 = rng.randint(edge, w // 2 - gap // 2 - pw)
    rects = [
        pygame.Rect(x0, y + height // 4, pw, plat_h),
        pygame.Rect(x0 + gap, y, pw, plat_h),
        pygame.Rect(min(w - edge - pw, x0 + gap * 2), y - height // 5, pw, plat_h),
    ]
    return rects


def _section_wall_climb(rng, w, edge, top_y, height, plat_h, hard):
    """Vertical wall with ledges — Getting Over It style."""
    wall_w = _sw(20, w)
    cx = w // 2 + rng.randint(-_sw(120, w), _sw(120, w))
    wall = pygame.Rect(cx - wall_w // 2, top_y + height // 5, wall_w, int(height * 0.75))
    pw = _sw(120 if not hard else 95, w)
    rects = [
        wall,
        pygame.Rect(cx - _sw(160, w), top_y + height - plat_h - 10, pw, plat_h),
        pygame.Rect(cx + _sw(40, w), top_y + height // 2, pw, plat_h),
        pygame.Rect(cx - _sw(150, w), top_y + plat_h + 20, pw, plat_h),
    ]
    return rects


def _section_rest_then_rise(rng, w, edge, top_y, height, plat_h, hard):
    """Wide rest ledge, then a short tricky hop."""
    wide = _sw(240 if not hard else 180, w)
    small = _sw(100 if not hard else 75, w)
    cx = rng.uniform(w * 0.25, w * 0.65)
    rects = [
        pygame.Rect(_clamp_x(cx, wide, edge, w), top_y + height - plat_h - 30, wide, plat_h),
        pygame.Rect(_clamp_x(cx + _sw(140, w), small, edge, w), top_y + height // 3, small, plat_h),
        pygame.Rect(_clamp_x(cx - _sw(80, w), small, edge, w), top_y + plat_h + 10, small, plat_h),
    ]
    return rects


def _section_fork(rng, w, edge, top_y, height, plat_h, hard):
    """Easier main line + optional harder side branch (may dead-end)."""
    pw = _sw(125, w)
    small = _sw(90, w)
    entry_y = top_y + height - plat_h - 20
    main_x = w * 0.35
    rects = [
        pygame.Rect(_clamp_x(main_x, pw, edge, w), entry_y, pw, plat_h),
        pygame.Rect(_clamp_x(main_x + _sw(100, w), pw, edge, w), top_y + height // 2, pw, plat_h),
        pygame.Rect(_clamp_x(main_x + _sw(60, w), pw, edge, w), top_y + plat_h + 15, pw, plat_h),
    ]
    # Harder side branch — tempting but sometimes a dead end
    if rng.random() < 0.55:
        branch_x = w * 0.72
        rects.append(pygame.Rect(_clamp_x(branch_x, small, edge, w), entry_y - height // 6, small, plat_h))
        if rng.random() < 0.45:
            rects.append(pygame.Rect(_clamp_x(branch_x + _sw(30, w), small, edge, w), top_y + height // 3, small, plat_h))
        # else: branch dead-ends — player must backtrack
    return rects


def _section_staircase(rng, w, edge, top_y, height, plat_h, hard):
    """Steady diagonal climb across the screen."""
    pw = _sw(135 if not hard else 100, w)
    steps = 5
    rects = []
    for i in range(steps):
        t = i / (steps - 1) if steps > 1 else 0
        cx = w * (0.15 + 0.7 * t)
        cy = top_y + height - int((i + 1) * height / (steps + 0.5))
        rects.append(pygame.Rect(_clamp_x(cx, pw, edge, w), cy, pw, plat_h))
    return rects


SECTION_BUILDERS = [
    _section_zigzag,
    _section_gap_run,
    _section_wall_climb,
    _section_rest_then_rise,
    _section_fork,
    _section_staircase,
]


def _entry_platform_index(section_rects):
    for i, rect in enumerate(section_rects):
        if rect.width >= rect.height * 2:
            return i
    return 0


def _exit_platform(section_rects):
    ledges = [r for r in section_rects if r.width >= r.height * 2]
    if ledges:
        return min(ledges, key=lambda r: r.top)
    return min(section_rects, key=lambda r: r.top)


def _align_section_to_entry(section_rects, anchor, rng, max_x, min_up, max_up):
    """Move a section so its entry platform is reachable from the previous anchor."""
    if not section_rects:
        return section_rects

    entry_index = _entry_platform_index(section_rects)
    entry = section_rects[entry_index]
    target_dy = -rng.randint(min_up, max_up)
    dx = anchor.centerx - entry.centerx
    dy = anchor.top + target_dy - entry.top

    aligned = [r.move(dx, dy) for r in section_rects]

    if not _reachable(anchor, aligned[entry_index], max_x, min_up, max_up + 25):
        aligned = [r.move(dx, dy - 20) for r in aligned]

    return aligned


def generate_level(seed=None):
    if seed is None:
        seed = random.randint(1, 999_999)
    rng = random.Random(seed)

    w, h = s.WORLD_WIDTH, s.WORLD_HEIGHT
    edge = max(40, int(40 * w / BASE_WORLD_WIDTH))
    plat_h = 20
    max_x = int(210 * w / BASE_WORLD_WIDTH)
    min_up = int(55 * w / BASE_WORLD_WIDTH)
    max_up = int(105 * w / BASE_WORLD_WIDTH)

    platforms = [pygame.Rect(0, h - 40, w, 40)]

    start_w = _sw(220, w)
    start = pygame.Rect(_clamp_x(w * 0.2, start_w, edge, w), h - 88, start_w, plat_h)
    platforms.append(start)
    anchor = start

    section_top = start.top - 30
    section_index = 0

    while section_top > 220:
        section_height = rng.randint(int(220 * w / BASE_WORLD_WIDTH), int(320 * w / BASE_WORLD_WIDTH))
        top_y = section_top - section_height
        hard = section_index > 2 and rng.random() < 0.35 + section_index * 0.02

        builder = rng.choice(SECTION_BUILDERS)
        section_rects = builder(rng, w, edge, top_y, section_height, plat_h, hard)

        entry_index = _entry_platform_index(section_rects)
        aligned = _align_section_to_entry(section_rects, anchor, rng, max_x, min_up, max_up)

        added = _add_all(platforms, aligned, edge, w)
        if not added:
            # Fallback: simple step up from anchor
            pw = _sw(140, w)
            fallback = pygame.Rect(
                _clamp_x(anchor.centerx, pw, edge, w),
                anchor.top - rng.randint(min_up, max_up),
                pw,
                plat_h,
            )
            if not _overlaps(platforms, fallback):
                platforms.append(fallback)
                added = [fallback]

        if added:
            anchor = _exit_platform(added)

        section_top = top_y - rng.randint(20, 50)
        section_index += 1

    summit_w = _sw(260, w)
    approach_w = _sw(150, w)
    approach = pygame.Rect(
        _clamp_x(anchor.centerx * 0.5 + w * 0.25, approach_w, edge, w),
        max(90, anchor.top - rng.randint(min_up, max_up)),
        approach_w,
        plat_h,
    )
    if not _overlaps(platforms, approach):
        platforms.append(approach)
        anchor = approach

    summit = pygame.Rect(w // 2 - summit_w // 2, 44, summit_w, 26)
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
