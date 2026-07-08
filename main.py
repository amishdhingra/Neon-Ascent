"""Neon Ascent — 3D first-person vertical climb."""

import sys

import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT

from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_FOG,
    GL_FOG_COLOR,
    GL_FOG_DENSITY,
    GL_FOG_END,
    GL_FOG_MODE,
    GL_FOG_START,
    GL_LINES,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    GL_EXP2,
    glBegin,
    glClear,
    glClearColor,
    glColor3f,
    glEnable,
    glEnd,
    glFogf,
    glFogfv,
    glFogi,
    glLineWidth,
    glLoadIdentity,
    glMatrixMode,
    glOrtho,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

import settings as s
from fps_camera import FpsCamera
from world3d import build_tower, draw_block

SPAWN_Y = 0.3


def setup_gl():
    glEnable(GL_DEPTH_TEST)
    glClearColor(*s.COLOUR_BG, 1.0)

    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_EXP2)
    glFogfv(GL_FOG_COLOR, (*s.COLOUR_FOG, 1.0))
    glFogf(GL_FOG_DENSITY, 0.012)
    glFogf(GL_FOG_START, 8.0)
    glFogf(GL_FOG_END, 90.0)


def setup_projection(width, height):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = width / max(height, 1)
    gluPerspective(s.FOV, aspect, s.NEAR_PLANE, s.FAR_PLANE)
    glMatrixMode(GL_MODELVIEW)


def draw_crosshair():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glLineWidth(2.0)
    glColor3f(0.9, 0.95, 1.0)
    glBegin(GL_LINES)
    glVertex3f(-0.02, 0.0, 0.0)
    glVertex3f(0.02, 0.0, 0.0)
    glVertex3f(0.0, -0.02, 0.0)
    glVertex3f(0.0, 0.02, 0.0)
    glEnd()


def draw_stamina_bar(stamina):
    """Screen-space stamina bar (top-left)."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, s.SCREEN_WIDTH, s.SCREEN_HEIGHT, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    bar_x, bar_y = 20, 20
    bar_w, bar_h = 180, 16
    fill = bar_w * (stamina / s.SPRINT_STAMINA_MAX)

    def rect(x, y, w, h, colour):
        glColor3f(*colour)
        glBegin(GL_QUADS)
        glVertex3f(x, y, 0)
        glVertex3f(x + w, y, 0)
        glVertex3f(x + w, y + h, 0)
        glVertex3f(x, y + h, 0)
        glEnd()

    rect(bar_x, bar_y, bar_w, bar_h, s.COLOUR_STAMINA_BG)
    if fill > 0:
        rect(bar_x, bar_y, fill, bar_h, s.COLOUR_STAMINA_FILL)
    glColor3f(0.35, 0.35, 0.5)
    glBegin(GL_LINES)
    glVertex3f(bar_x, bar_y, 0)
    glVertex3f(bar_x + bar_w, bar_y, 0)
    glVertex3f(bar_x + bar_w, bar_y, 0)
    glVertex3f(bar_x + bar_w, bar_y + bar_h, 0)
    glVertex3f(bar_x + bar_w, bar_y + bar_h, 0)
    glVertex3f(bar_x, bar_y + bar_h, 0)
    glVertex3f(bar_x, bar_y + bar_h, 0)
    glVertex3f(bar_x, bar_y, 0)
    glEnd()


def draw_grid():
    glColor3f(0.12, 0.1, 0.22)
    glBegin(GL_LINES)
    for i in range(-30, 31, 2):
        glVertex3f(i, -0.01, -30)
        glVertex3f(i, -0.01, 30)
        glVertex3f(-30, -0.01, i)
        glVertex3f(30, -0.01, i)
    glEnd()


def setup_display():
    pygame.init()
    flags = DOUBLEBUF | OPENGL
    if s.FULLSCREEN:
        screen = pygame.display.set_mode((0, 0), flags | pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((s.SCREEN_WIDTH, s.SCREEN_HEIGHT), flags)
    s.SCREEN_WIDTH, s.SCREEN_HEIGHT = screen.get_size()
    pygame.display.set_caption(s.TITLE)
    return screen


def main():
    setup_display()
    clock = pygame.time.Clock()

    setup_gl()
    setup_projection(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)

    blocks, collisions, wall_solids, summit_y = build_tower(seed=42)
    camera = FpsCamera(0, SPAWN_Y, 0)

    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    running = True
    mouse_locked = True

    while running:
        dt = clock.tick(s.FPS) / 1000.0
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_TAB:
                    mouse_locked = not mouse_locked
                    pygame.event.set_grab(mouse_locked)
                    pygame.mouse.set_visible(not mouse_locked)
                elif event.key == pygame.K_SPACE:
                    camera.request_jump()
            elif event.type == pygame.MOUSEMOTION and mouse_locked:
                camera.process_mouse(event.rel)

        keys = pygame.key.get_pressed()
        camera.apply_mouse()
        camera.handle_input(keys, dt)
        camera.update_timers(dt)
        camera.update_wall_contact(wall_solids, keys)
        camera.try_jump(keys)
        camera.apply_gravity(dt)
        camera.move_with_collision(collisions, dt)

        if camera.y < -15:
            camera.x, camera.y, camera.z = 0, SPAWN_Y, 0
            camera.vx = camera.vy = camera.vz = 0
            camera.air_jumps_remaining = 0

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        setup_projection(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
        camera.apply_gl()

        draw_grid()
        for block in blocks:
            draw_block(block)

        draw_crosshair()
        draw_stamina_bar(camera.stamina)

        height = max(0, int(camera.y))
        progress = min(100, int(100 * camera.y / summit_y))
        state = "WALL" if camera.wall_sliding else ("SPRINT" if camera.is_sprinting else "RUN")
        caption = (
            f"{s.TITLE}  |  {height}m  |  {progress}%  |  {state}  |  "
            f"Space: jump (double in air)  |  Shift: sprint  |  Hold into wall: slide"
        )
        pygame.display.set_caption(caption)
        pygame.display.flip()

    pygame.event.set_grab(False)
    pygame.mouse.set_visible(True)
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
