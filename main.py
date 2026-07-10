"""Neon Ascent — 3D first-person platformer climb."""

import sys
import time

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
from hud import (
    draw_air_jump_indicator,
    draw_cores,
    draw_progress,
    draw_respawn_hint,
    draw_stamina_bar,
    draw_timer,
    draw_win_screen,
    draw_zone_banner,
)
from scores import get_best, save_best
from world3d import build_tower, draw_block, draw_guide_rails, get_zone_name

SPAWN_Y = 0.3
SPAWN_Z = -2.0
START_Z = 0.0


def find_platform_top(platform_solids, x, z, radius=None):
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
    camera.wall_jumps_this_air = 0
    camera._was_wall_surfing = False
    camera.on_ground = top is not None


def player_on_summit(camera, summit_box, platform_solids):
    if summit_box is None:
        return False
    sx0, sy0, sz0, sx1, sy1, sz1 = summit_box
    if not (camera.x >= sx0 and camera.x <= sx1 and camera.z >= sz0 and camera.z <= sz1):
        return False
    top = find_platform_top(platform_solids, camera.x, camera.z)
    if top is None or abs(camera.y - top) > s.LANDING_TOLERANCE + 0.08:
        return False
    return sy0 - 0.5 <= top <= sy1 + 0.05


def try_collect_cores(camera, blocks):
    collected = 0
    r = s.COLLECTIBLE_RADIUS
    px, py, pz = camera.x, camera.y + s.PLAYER_HEIGHT * 0.5, camera.z
    for block in blocks:
        if block["kind"] != "core" or block.get("collected"):
            continue
        cx, cy, cz = block["pos"]
        if (px - cx) ** 2 + (py - cy) ** 2 + (pz - cz) ** 2 <= r * r:
            block["collected"] = True
    for block in blocks:
        if block["kind"] == "core" and block.get("collected"):
            collected += 1
    return collected


def setup_gl():
    glEnable(GL_DEPTH_TEST)
    glClearColor(*s.COLOUR_BG, 1.0)

    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_EXP2)
    glFogfv(GL_FOG_COLOR, (*s.COLOUR_FOG, 1.0))
    glFogf(GL_FOG_DENSITY, 0.006)
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 180.0)


def setup_projection(width, height, fov=None):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect = width / max(height, 1)
    gluPerspective(fov if fov is not None else s.FOV, aspect, s.NEAR_PLANE, s.FAR_PLANE)
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


def new_run(seed=None):
    (
        blocks,
        collisions,
        wall_solids,
        platform_solids,
        goal_z,
        _summit_y,
        map_seed,
        summit_box,
        guide_rails,
        cores_total,
    ) = build_tower(seed)
    camera = FpsCamera(0, SPAWN_Y, SPAWN_Z)
    return {
        "blocks": blocks,
        "collisions": collisions,
        "wall_solids": wall_solids,
        "platform_solids": platform_solids,
        "goal_z": goal_z,
        "map_seed": map_seed,
        "summit_box": summit_box,
        "guide_rails": guide_rails,
        "cores_total": cores_total,
        "camera": camera,
        "checkpoint": [0.0, SPAWN_Y, SPAWN_Z],
        "has_platform_checkpoint": False,
        "respawn_grace": 0.0,
        "run_start": time.perf_counter(),
        "won": False,
        "win_time": 0.0,
        "is_new_best": False,
        "previous_best": None,
        "last_zone": "SHORE",
        "zone_banner": 0.0,
        "zone_banner_name": "",
    }


def main():
    setup_display()
    clock = pygame.time.Clock()
    setup_gl()

    run = new_run()
    mouse_locked = True
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    running = True
    while running:
        dt = clock.tick(s.FPS) / 1000.0
        dt = min(dt, 0.05)
        pulse = time.perf_counter() - run["run_start"]

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif run["won"] and event.key == pygame.K_RETURN:
                    run = new_run()
                    mouse_locked = True
                    pygame.event.set_grab(True)
                    pygame.mouse.set_visible(False)
                elif not run["won"]:
                    if event.key == pygame.K_TAB:
                        mouse_locked = not mouse_locked
                        pygame.event.set_grab(mouse_locked)
                        pygame.mouse.set_visible(not mouse_locked)
                    elif event.key == pygame.K_SPACE:
                        run["camera"].request_jump()
                    elif event.key == pygame.K_r and s.TESTING_RESPAWN:
                        respawn_camera(
                            run["camera"],
                            run["checkpoint"][0],
                            run["checkpoint"][1],
                            run["checkpoint"][2],
                            run["platform_solids"],
                        )
                        run["respawn_grace"] = s.RESPAWN_GRACE
            elif event.type == pygame.MOUSEMOTION and mouse_locked and not run["won"]:
                run["camera"].process_mouse(event.rel)

        camera = run["camera"]

        if not run["won"]:
            keys = pygame.key.get_pressed()
            camera.apply_mouse()
            camera.handle_input(keys, dt)
            camera.update_timers(dt)
            camera.try_jump(keys)
            camera.apply_gravity(dt)
            camera.move_with_collision(run["collisions"], run["wall_solids"], dt)
            camera.update_wall_surf(run["wall_solids"], keys)
            camera.update_juice(dt)

            if run["respawn_grace"] > 0:
                run["respawn_grace"] -= dt

            if camera.on_ground:
                top = find_platform_top(run["platform_solids"], camera.x, camera.z)
                if top is not None and abs(camera.y - top) <= s.LANDING_TOLERANCE + 0.05:
                    run["checkpoint"][0], run["checkpoint"][1], run["checkpoint"][2] = camera.x, top, camera.z
                    run["has_platform_checkpoint"] = True

            if s.TESTING_RESPAWN and run["respawn_grace"] <= 0 and camera.y < s.FALL_RESPAWN_Y:
                respawn_camera(
                    camera,
                    run["checkpoint"][0],
                    run["checkpoint"][1],
                    run["checkpoint"][2],
                    run["platform_solids"],
                )
                run["respawn_grace"] = s.RESPAWN_GRACE

            cores_collected = try_collect_cores(camera, run["blocks"])

            zone = get_zone_name(camera.z)
            if zone != run["last_zone"]:
                run["last_zone"] = zone
                run["zone_banner_name"] = zone
                run["zone_banner"] = s.ZONE_BANNER_TIME

            if run["zone_banner"] > 0:
                run["zone_banner"] -= dt

            if player_on_summit(camera, run["summit_box"], run["platform_solids"]):
                run["won"] = True
                run["win_time"] = time.perf_counter() - run["run_start"]
                prev = get_best(run["map_seed"])
                run["previous_best"] = prev["time"] if prev else None
                run["is_new_best"] = save_best(run["map_seed"], run["win_time"], cores_collected)
        else:
            cores_collected = sum(1 for b in run["blocks"] if b["kind"] == "core" and b.get("collected"))
            zone = "SUMMIT"

        elapsed = (run["win_time"] if run["won"] else time.perf_counter() - run["run_start"])

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        setup_projection(s.SCREEN_WIDTH, s.SCREEN_HEIGHT, camera.get_fov())
        camera.apply_gl()

        draw_grid()
        draw_guide_rails(run["guide_rails"])
        for block in run["blocks"]:
            draw_block(block, pulse=pulse)

        draw_crosshair()

        if not run["won"]:
            draw_stamina_bar(camera.stamina, camera.is_sprinting)
            draw_air_jump_indicator(camera.air_jumps_remaining, camera.on_ground)
            draw_timer(elapsed)
            draw_cores(cores_collected, run["cores_total"])
            if run["zone_banner"] > 0:
                draw_zone_banner(run["zone_banner_name"], run["zone_banner"] / s.ZONE_BANNER_TIME)
        else:
            draw_win_screen(
                run["win_time"],
                run["map_seed"],
                cores_collected,
                run["cores_total"],
                run["is_new_best"],
                run["previous_best"],
            )

        distance = max(0.0, camera.z - START_Z)
        progress = min(100, int(100 * distance / run["goal_z"]))
        if not run["won"]:
            draw_progress(distance, run["goal_z"], camera.y, zone, run["map_seed"], elapsed)
            draw_respawn_hint(run["has_platform_checkpoint"])

        state = "SURF" if camera.wall_surfing else ("SPRINT" if camera.is_sprinting else "RUN")
        caption = (
            f"{s.TITLE}  |  {int(distance)}m / {int(run['goal_z'])}m  |  {progress}%  |  {state}  |  "
            f"Reach the SUMMIT platform to win"
        )
        pygame.display.set_caption(caption)
        pygame.display.flip()

    pygame.event.set_grab(False)
    pygame.mouse.set_visible(True)
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
