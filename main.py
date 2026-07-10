"""Neon Ascent — 3D first-person platformer climb."""

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
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

import settings as s
from fps_camera import FpsCamera
from hud import draw_progress, draw_respawn_hint, draw_stamina_bar
from world3d import build_tower, draw_block, get_zone_name

SPAWN_Y = 0.3
SPAWN_Z = 4.0
START_Z = 0.0


def find_platform_top(platform_solids, x, z, radius=None):
    """Highest platform surface under the player's feet."""
    r = radius if radius is not None else s.PLAYER_RADIUS
    best = None
    for sx0, sy0, sz0, sx1, sy1, sz1 in platform_solids:
        if x + r <= sx0 or x - r >= sx1 or z + r <= sz0 or z - r >= sz1:
            continue
        if best is None or sy1 > best:
            best = sy1
    return best


def respawn_camera(camera, x, y, z, platform_solids):
    top = find_platform_top(platform_solids, x, z)
    if top is not None:
        y = top
    camera.x, camera.y, camera.z = x, y, z
    camera.vx = camera.vy = camera.vz = 0
    camera.air_jumps_remaining = 0
    camera.wall_surfing = False
    camera.wall_normal = None
    camera._was_wall_surfing = False
    camera.on_ground = top is not None


def setup_gl():
    glEnable(GL_DEPTH_TEST)
    glClearColor(*s.COLOUR_BG, 1.0)

    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_EXP2)
    glFogfv(GL_FOG_COLOR, (*s.COLOUR_FOG, 1.0))
    glFogf(GL_FOG_DENSITY, 0.006)
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 180.0)


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


def draw_grid():
    glColor3f(0.12, 0.1, 0.22)
    glBegin(GL_LINES)
    for i in range(-20, 21, 2):
        glVertex3f(i, -0.01, -20)
        glVertex3f(i, -0.01, 520)
        glVertex3f(-20, -0.01, i)
        glVertex3f(20, -0.01, i)
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

    blocks, collisions, wall_solids, platform_solids, goal_z, _summit_y, map_seed = build_tower()
    camera = FpsCamera(0, SPAWN_Y, SPAWN_Z)
    checkpoint = [0.0, SPAWN_Y, SPAWN_Z]
    has_platform_checkpoint = False
    respawn_grace = 0.0

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
                elif event.key == pygame.K_r and s.TESTING_RESPAWN:
                    respawn_camera(camera, checkpoint[0], checkpoint[1], checkpoint[2], platform_solids)
                    respawn_grace = s.RESPAWN_GRACE
            elif event.type == pygame.MOUSEMOTION and mouse_locked:
                camera.process_mouse(event.rel)

        keys = pygame.key.get_pressed()
        camera.apply_mouse()
        camera.handle_input(keys, dt)
        camera.update_timers(dt)
        camera.try_jump(keys)
        camera.apply_gravity(dt)
        camera.move_with_collision(collisions, wall_solids, dt)
        camera.update_wall_surf(wall_solids, keys)

        if respawn_grace > 0:
            respawn_grace -= dt

        if camera.on_ground:
            top = find_platform_top(platform_solids, camera.x, camera.z)
            if top is not None and abs(camera.y - top) <= s.LANDING_TOLERANCE + 0.05:
                checkpoint[0], checkpoint[1], checkpoint[2] = camera.x, top, camera.z
                has_platform_checkpoint = True

        if s.TESTING_RESPAWN and respawn_grace <= 0 and camera.y < s.FALL_RESPAWN_Y:
            respawn_camera(camera, checkpoint[0], checkpoint[1], checkpoint[2], platform_solids)
            respawn_grace = s.RESPAWN_GRACE

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        setup_projection(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
        camera.apply_gl()

        draw_grid()
        for block in blocks:
            draw_block(block)

        draw_crosshair()
        draw_stamina_bar(camera.stamina, camera.is_sprinting)

        distance = max(0.0, camera.z - START_Z)
        progress = min(100, int(100 * distance / goal_z))
        zone = get_zone_name(camera.z)
        draw_progress(distance, goal_z, camera.y, zone, map_seed)
        draw_respawn_hint(has_platform_checkpoint)
        state = "SURF" if camera.wall_surfing else ("SPRINT" if camera.is_sprinting else "RUN")
        caption = (
            f"{s.TITLE}  |  {int(distance)}m / {int(goal_z)}m  |  {progress}%  |  {state}  |  "
            f"Space: jump  |  Shift: sprint  |  Hit wall: surf down + bonus jump"
        )
        pygame.display.set_caption(caption)
        pygame.display.flip()

    pygame.event.set_grab(False)
    pygame.mouse.set_visible(True)
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
