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


def _font():
    global _FONT
    if _FONT is None:
        _FONT = pygame.font.SysFont("consolas", 22, bold=True)
    return _FONT


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


def draw_progress(distance, goal_distance, height):
    text = _font().render(f"Distance: {int(distance)}m  |  Height: {int(height)}m", True, (170, 230, 210))
    surf = pygame.Surface((text.get_width() + 16, text.get_height() + 8), pygame.SRCALPHA)
    surf.blit(text, (8, 4))
    _blit_surface(surf, s.SCREEN_WIDTH - surf.get_width() - 24, 24)
