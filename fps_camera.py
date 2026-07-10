"""First-person camera — Titanfall-style wall surf + Celeste air movement."""

import math

import pygame

import settings as s


class FpsCamera:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.on_ground = False
        self.air_jumps_remaining = 0
        self.stamina = float(s.SPRINT_STAMINA_MAX)
        self.is_sprinting = False
        self.jump_buffer = 0.0
        self.coyote_timer = 0.0
        self.wall_normal = None
        self.wall_surfing = False
        self.wall_jump_available = False
        self.wall_regrab_timer = 0.0
        self._was_wall_surfing = False
        self._accumulated_mouse = [0.0, 0.0]

    @property
    def eye_y(self):
        return self.y + s.PLAYER_HEIGHT * 0.88

    @property
    def wall_sliding(self):
        return self.wall_surfing

    def forward(self):
        return (math.sin(self.yaw), 0.0, -math.cos(self.yaw))

    def right(self):
        return (math.cos(self.yaw), 0.0, math.sin(self.yaw))

    def process_mouse(self, rel):
        self._accumulated_mouse[0] += rel[0]
        self._accumulated_mouse[1] += rel[1]

    def apply_mouse(self):
        mx, my = self._accumulated_mouse
        self._accumulated_mouse = [0.0, 0.0]
        self.yaw += mx * s.MOUSE_SENSITIVITY * 0.01
        self.pitch += my * s.MOUSE_SENSITIVITY * 0.01
        self.pitch = max(-1.45, min(1.45, self.pitch))

    def request_jump(self):
        self.jump_buffer = s.JUMP_BUFFER_TIME

    def _wish_direction(self, keys):
        fx, _, fz = self.forward()
        rx, _, rz = self.right()
        wish_x = wish_z = 0.0
        if keys[pygame.K_w]:
            wish_x += fx
            wish_z += fz
        if keys[pygame.K_s]:
            wish_x -= fx
            wish_z -= fz
        if keys[pygame.K_d]:
            wish_x += rx
            wish_z += rz
        if keys[pygame.K_a]:
            wish_x -= rx
            wish_z -= rz
        length = math.hypot(wish_x, wish_z)
        if length > 0:
            wish_x /= length
            wish_z /= length
        return wish_x, wish_z

    def handle_input(self, keys, dt):
        if self.wall_surfing:
            if not self.is_sprinting and self.stamina < s.SPRINT_STAMINA_MAX:
                self.stamina = min(s.SPRINT_STAMINA_MAX, self.stamina + s.SPRINT_REGEN_RATE * dt)
            return

        wish_x, wish_z = self._wish_direction(keys)
        moving = wish_x != 0 or wish_z != 0
        wants_sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        self.is_sprinting = False
        speed = s.MOVE_SPEED
        if wants_sprint and moving and self.stamina > 0:
            speed = s.SPRINT_SPEED
            self.is_sprinting = True
            self.stamina = max(0.0, self.stamina - s.SPRINT_DRAIN_RATE * dt)
        elif self.stamina < s.SPRINT_STAMINA_MAX:
            self.stamina = min(s.SPRINT_STAMINA_MAX, self.stamina + s.SPRINT_REGEN_RATE * dt)

        self.vx = wish_x * speed
        self.vz = wish_z * speed

    def _apply_wall_surf_velocity(self, keys):
        if not self.wall_normal:
            return
        nx, nz = self.wall_normal
        tx, tz = -nz, nx
        wish_x, wish_z = self._wish_direction(keys)
        along = wish_x * tx + wish_z * tz
        lateral = s.WALL_SURF_LATERAL
        self.is_sprinting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        if self.is_sprinting and self.stamina > 0:
            lateral *= 1.25
            self.stamina = max(0.0, self.stamina - s.SPRINT_DRAIN_RATE * 0.016)
        else:
            self.is_sprinting = False
        self.vy = -s.WALL_SURF_SPEED
        self.vx = tx * along * lateral
        self.vz = tz * along * lateral
        into = self.vx * nx + self.vz * nz
        if into < 0:
            self.vx -= into * nx
            self.vz -= into * nz

    def update_timers(self, dt):
        if self.on_ground:
            self.coyote_timer = s.COYOTE_TIME
            self.wall_jump_available = True
        elif self.coyote_timer > 0:
            self.coyote_timer -= dt

        if self.jump_buffer > 0:
            self.jump_buffer -= dt
        if self.wall_regrab_timer > 0:
            self.wall_regrab_timer -= dt

    def _find_wall_contact(self, wall_solids):
        """Detect nearby surf-wall faces (works after collision pushes player to surface)."""
        r = s.PLAYER_RADIUS
        h = s.PLAYER_HEIGHT
        px0, py0, pz0, px1, py1, pz1 = self._player_box(r, h)
        slack = s.WALL_CONTACT_DIST

        best = None
        best_dist = slack + 1.0

        for sx0, sy0, sz0, sx1, sy1, sz1 in wall_solids:
            if sy1 - sy0 < s.WALL_MIN_HEIGHT:
                continue
            if py1 <= sy0 + 0.15 or py0 >= sy1 - 0.1:
                continue

            z_overlap = pz1 > sz0 + 0.05 and pz0 < sz1 - 0.05
            x_overlap = px1 > sx0 + 0.05 and px0 < sx1 - 0.05

            checks = []
            if z_overlap:
                checks.append((abs(px1 - sx0), (-1.0, 0.0)))
                checks.append((abs(px0 - sx1), (1.0, 0.0)))
            if x_overlap:
                checks.append((abs(pz1 - sz0), (0.0, -1.0)))
                checks.append((abs(pz0 - sz1), (0.0, 1.0)))

            for dist, normal in checks:
                if dist <= slack and dist < best_dist:
                    best_dist = dist
                    best = normal

        return best

    def update_wall_surf(self, wall_solids, keys):
        if self.on_ground or self.wall_regrab_timer > 0:
            self.wall_surfing = False
            self.wall_normal = None
            self._was_wall_surfing = False
            return

        contact = self._find_wall_contact(wall_solids)
        if contact is None:
            self.wall_surfing = False
            self.wall_normal = None
            self._was_wall_surfing = False
            return

        self.wall_normal = contact
        self.wall_surfing = True

        if not self._was_wall_surfing:
            self.wall_jump_available = True
            self.air_jumps_remaining = max(self.air_jumps_remaining, s.MAX_AIR_JUMPS)

        self._was_wall_surfing = True
        self._apply_wall_surf_velocity(keys)

    def try_jump(self, keys):
        if self.jump_buffer <= 0:
            return

        if self.on_ground or self.coyote_timer > 0:
            self.vy = s.JUMP_SPEED
            self.on_ground = False
            self.coyote_timer = 0.0
            self.air_jumps_remaining = s.MAX_AIR_JUMPS
            self.wall_jump_available = True
            self.jump_buffer = 0.0
            return

        if self.wall_surfing and self.wall_jump_available and self.wall_normal:
            nx, nz = self.wall_normal
            self.vy = s.WALL_JUMP_SPEED
            self.vx = nx * s.WALL_JUMP_PUSH
            self.vz = nz * s.WALL_JUMP_PUSH
            self.wall_surfing = False
            self.wall_normal = None
            self.wall_jump_available = False
            self._was_wall_surfing = False
            self.wall_regrab_timer = s.WALL_REGRAB_COOLDOWN
            self.jump_buffer = 0.0
            return

        if self.air_jumps_remaining > 0:
            self.vy = s.DOUBLE_JUMP_SPEED
            wish_x, wish_z = self._wish_direction(keys)
            if wish_x != 0 or wish_z != 0:
                self.vx += wish_x * s.DOUBLE_JUMP_BOOST
                self.vz += wish_z * s.DOUBLE_JUMP_BOOST
            self.air_jumps_remaining -= 1
            self.jump_buffer = 0.0

    def apply_gravity(self, dt):
        if self.wall_surfing:
            return
        self.vy -= s.GRAVITY * dt
        if self.vy < -s.MAX_FALL_SPEED:
            self.vy = -s.MAX_FALL_SPEED

    def move_with_collision(self, solids, wall_solids, dt):
        was_on_ground = self.on_ground
        self.on_ground = False
        wall_set = set(wall_solids)
        r = s.PLAYER_RADIUS
        h = s.PLAYER_HEIGHT

        self.x += self.vx * dt
        self._collide_axis(solids, wall_set, r, h, axis="x", was_on_ground=was_on_ground)

        self.y += self.vy * dt
        self._collide_axis(solids, wall_set, r, h, axis="y", was_on_ground=was_on_ground)

        self.z += self.vz * dt
        self._collide_axis(solids, wall_set, r, h, axis="z", was_on_ground=was_on_ground)

        if not self.on_ground and self.vy <= 0 and not self.wall_surfing:
            self._snap_to_ground(solids, r, h)

    def _snap_to_ground(self, solids, r, h):
        px0, _, pz0, px1, _, pz1 = self._player_box(r, h)
        feet = self.y
        best_top = None
        for sx0, sy0, sz0, sx1, sy1, sz1 in solids:
            if px1 <= sx0 or px0 >= sx1 or pz1 <= sz0 or pz0 >= sz1:
                continue
            gap = sy1 - feet
            if 0 <= gap <= s.LANDING_TOLERANCE:
                if best_top is None or sy1 > best_top:
                    best_top = sy1
        if best_top is not None:
            self.y = best_top
            self.vy = 0.0
            self.on_ground = True
            self.wall_surfing = False
            self.wall_normal = None
            self._was_wall_surfing = False

    def _player_box(self, r, h):
        return (self.x - r, self.y, self.z - r, self.x + r, self.y + h, self.z + r)

    def _collide_axis(self, solids, wall_set, r, h, axis, was_on_ground=False):
        px0, py0, pz0, px1, py1, pz1 = self._player_box(r, h)
        airborne = not was_on_ground

        for box in solids:
            sx0, sy0, sz0, sx1, sy1, sz1 = box
            if px1 <= sx0 or px0 >= sx1 or py1 <= sy0 or py0 >= sy1 or pz1 <= sz0 or pz0 >= sz1:
                continue

            is_wall = box in wall_set

            if axis == "x":
                if self.vx > 0:
                    if px1 > sx1:
                        self.x = sx1 - r
                        if is_wall and airborne:
                            self.wall_normal = (1.0, 0.0)
                        elif not (is_wall and airborne):
                            self.vx = 0
                    elif px0 < sx0 <= px1:
                        self.x = sx0 - r
                        if is_wall and airborne:
                            self.wall_normal = (-1.0, 0.0)
                        elif not (is_wall and airborne):
                            self.vx = 0
                elif self.vx < 0:
                    if px0 < sx0:
                        self.x = sx0 + r
                        if is_wall and airborne:
                            self.wall_normal = (-1.0, 0.0)
                        elif not (is_wall and airborne):
                            self.vx = 0
                    elif px0 < sx1 <= px1:
                        self.x = sx1 + r
                        if is_wall and airborne:
                            self.wall_normal = (1.0, 0.0)
                        elif not (is_wall and airborne):
                            self.vx = 0

            elif axis == "y":
                if self.vy < 0:
                    self.y = sy1
                    self.vy = 0
                    self.on_ground = True
                    self.wall_surfing = False
                    self.wall_normal = None
                    self._was_wall_surfing = False
                elif self.vy > 0:
                    self.y = sy0 - h
                    self.vy = 0

            elif axis == "z":
                if self.vz > 0:
                    if pz1 > sz1:
                        self.z = sz1 - r
                        if is_wall and airborne:
                            self.wall_normal = (0.0, 1.0)
                        elif not (is_wall and airborne):
                            self.vz = 0
                    elif pz0 < sz0 <= pz1:
                        self.z = sz0 - r
                        if is_wall and airborne:
                            self.wall_normal = (0.0, -1.0)
                        elif not (is_wall and airborne):
                            self.vz = 0
                elif self.vz < 0:
                    if pz0 < sz0:
                        self.z = sz0 + r
                        if is_wall and airborne:
                            self.wall_normal = (0.0, -1.0)
                        elif not (is_wall and airborne):
                            self.vz = 0
                    elif pz0 < sz1 <= pz1:
                        self.z = sz1 + r
                        if is_wall and airborne:
                            self.wall_normal = (0.0, 1.0)
                        elif not (is_wall and airborne):
                            self.vz = 0

    def apply_gl(self):
        from OpenGL.GL import (
            GL_MODELVIEW,
            glLoadIdentity,
            glMatrixMode,
            glRotatef,
            glTranslatef,
        )

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glRotatef(math.degrees(self.pitch), 1, 0, 0)
        glRotatef(math.degrees(self.yaw), 0, 1, 0)
        glTranslatef(-self.x, -self.eye_y, -self.z)
