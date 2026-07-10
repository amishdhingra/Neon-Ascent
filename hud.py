"""2D HUD drawn with pygame and composited over the OpenGL frame."""

import pygame
from OpenGL.GL import (
    GL_BLEND,
    GL_LINEAR,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_QUADS,
    GL_RGBA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glBlendFunc,
    glDeleteTextures,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glOrtho,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glVertex2f,
)
from OpenGL.GL import GL_DEPTH_TEST, GL_FOG, GL_PROJECTION, GL_MODELVIEW

import settings as s

_FONT = None
_TITLE_FONT = None


def _font():
    global _FONT
    if _FONT is None:
        _FONT = pygame.font.SysFont("consolas", 22, bold=True)
    return _FONT


def _title_font():
    global _TITLE_FONT
    if _TITLE_FONT is None:
        _TITLE_FONT = pygame.font.SysFont("consolas", 42, bold=True)
    return _TITLE_FONT


def _format_time(seconds):
    mins = int(seconds // 60)
    secs = seconds - mins * 60
    return f"{mins}:{secs:05.2f}"


def _blit_surface(surface, x, y):
    tex_data = pygame.image.tostring(surface, "RGBA", True)
    w, h = surface.get_size()

    glDisable(GL_DEPTH_TEST)
    glDisable(GL_FOG)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, s.SCREEN_WIDTH, s.SCREEN_HEIGHT, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)

    glEnable(GL_TEXTURE_2D)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 1)
    glVertex2f(x, y)
    glTexCoord2f(1, 1)
    glVertex2f(x + w, y)
    glTexCoord2f(1, 0)
    glVertex2f(x + w, y + h)
    glTexCoord2f(0, 0)
    glVertex2f(x, y + h)
    glEnd()
    glDisable(GL_TEXTURE_2D)

    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_FOG)
    glDeleteTextures(int(texture))


def draw_stamina_bar(stamina, sprinting):
    bar_w, bar_h = 240, 24
    pad = 3
    surf = pygame.Surface((bar_w, bar_h + 28), pygame.SRCALPHA)

    label_colour = (255, 210, 80) if sprinting else (190, 195, 220)
    surf.blit(_font().render("SPRINT", True, label_colour), (0, 0))

    bg = (38, 38, 62)
    fill = (255, 196, 48) if sprinting else (255, 170, 40)
    border = (110, 110, 150)

    pygame.draw.rect(surf, bg, (0, 26, bar_w, bar_h), border_radius=5)
    ratio = max(0.0, min(1.0, stamina / s.SPRINT_STAMINA_MAX))
    fill_w = int((bar_w - pad * 2) * ratio)
    if fill_w > 0:
        pygame.draw.rect(surf, fill, (pad, 26 + pad, fill_w, bar_h - pad * 2), border_radius=4)
    pygame.draw.rect(surf, border, (0, 26, bar_w, bar_h), width=2, border_radius=5)

    pct = _font().render(f"{int(ratio * 100)}%", True, (220, 220, 235))
    surf.blit(pct, (bar_w - pct.get_width() - 8, 28))

    _blit_surface(surf, 24, 24)


def draw_air_jump_indicator(air_jumps_remaining, on_ground):
    """Shows whether the double jump is still available."""
    pip_r = 9
    gap = 10
    count = s.MAX_AIR_JUMPS
    label_h = 22
    width = count * pip_r * 2 + (count - 1) * gap + 4
    height = label_h + pip_r * 2 + 10
    surf = pygame.Surface((width, height), pygame.SRCALPHA)

    available = count if on_ground else air_jumps_remaining
    label_colour = (120, 220, 255) if available > 0 else (100, 105, 130)
    surf.blit(_font().render("AIR JUMP", True, label_colour), (0, 0))

    for i in range(count):
        cx = pip_r + 2 + i * (pip_r * 2 + gap)
        cy = label_h + pip_r + 2
        used = i >= available
        fill = (60, 65, 90) if used else (80, 240, 255)
        border = (90, 95, 120) if used else (160, 250, 255)
        pygame.draw.circle(surf, fill, (cx, cy), pip_r)
        pygame.draw.circle(surf, border, (cx, cy), pip_r, width=2)

    _blit_surface(surf, 24, 88)


def draw_timer(elapsed):
    text = _font().render(f"TIME  {_format_time(elapsed)}", True, (200, 210, 240))
    surf = pygame.Surface((text.get_width() + 16, text.get_height() + 8), pygame.SRCALPHA)
    surf.blit(text, (8, 4))
    _blit_surface(surf, 24, 148)


def draw_cores(collected, total):
    if total <= 0:
        return
    text = _font().render(f"CORES  {collected}/{total}", True, (255, 140, 255))
    surf = pygame.Surface((text.get_width() + 16, text.get_height() + 8), pygame.SRCALPHA)
    surf.blit(text, (8, 4))
    _blit_surface(surf, 24, 182)


def draw_zone_banner(zone_name, alpha):
    if alpha <= 0 or not zone_name:
        return
    a = max(0, min(255, int(alpha * 255)))
    title = _title_font().render(zone_name, True, (120, 255, 220))
    sub = _font().render("ZONE ENTERED", True, (180, 200, 220))
    pad_x, pad_y = 32, 20
    w = max(title.get_width(), sub.get_width()) + pad_x * 2
    h = title.get_height() + sub.get_height() + pad_y * 2 + 8
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((10, 12, 28, int(a * 0.75)))
    surf.blit(title, (pad_x, pad_y))
    surf.blit(sub, (pad_x, pad_y + title.get_height() + 8))
    _blit_surface(surf, (s.SCREEN_WIDTH - w) // 2, s.SCREEN_HEIGHT // 3)


def draw_win_screen(elapsed, map_seed, cores_collected, cores_total, is_new_best, previous_best):
    overlay = pygame.Surface((s.SCREEN_WIDTH, s.SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((5, 4, 14, 190))
    cx = s.SCREEN_WIDTH // 2

    lines = [
        (_title_font().render("SUMMIT REACHED", True, (255, 230, 90)), 0),
        (_font().render(f"Time:  {_format_time(elapsed)}", True, (200, 240, 220)), 56),
        (_font().render(f"Seed:  {map_seed}", True, (170, 210, 200)), 88),
        (_font().render(f"Cores:  {cores_collected}/{cores_total}", True, (255, 160, 255)), 120),
    ]
    if is_new_best:
        lines.append((_font().render("NEW BEST TIME!", True, (255, 210, 80)), 152))
    elif previous_best is not None:
        lines.append((_font().render(f"Best:  {_format_time(previous_best)}", True, (150, 170, 190)), 152))

    hint = _font().render("Enter — new run   Esc — quit", True, (140, 150, 175))
    total_h = 200
    for surf, yoff in lines:
        overlay.blit(surf, (cx - surf.get_width() // 2, s.SCREEN_HEIGHT // 3 + yoff))
        total_h = s.SCREEN_HEIGHT // 3 + yoff + surf.get_height()
    overlay.blit(hint, (cx - hint.get_width() // 2, total_h + 40))
    _blit_surface(overlay, 0, 0)


def draw_progress(distance, goal_distance, height, zone_name="", map_seed=0, elapsed=0.0):
    line = (
        f"{zone_name}  |  {int(distance)}m / {int(goal_distance)}m  |  "
        f"H:{int(height)}m  |  {_format_time(elapsed)}  |  Seed:{map_seed}"
    )
    text = _font().render(line, True, (170, 230, 210))
    surf = pygame.Surface((text.get_width() + 16, text.get_height() + 8), pygame.SRCALPHA)
    surf.blit(text, (8, 4))
    _blit_surface(surf, s.SCREEN_WIDTH - surf.get_width() - 24, 24)


def draw_respawn_hint(has_checkpoint):
    if not s.TESTING_RESPAWN:
        return
    label = "[R] Respawn — last platform" if has_checkpoint else "[R] Respawn — spawn"
    text = _font().render(label, True, (255, 140, 100))
    surf = pygame.Surface((text.get_width() + 16, text.get_height() + 8), pygame.SRCALPHA)
    surf.blit(text, (8, 4))
    _blit_surface(surf, s.SCREEN_WIDTH - surf.get_width() - 24, 58)
