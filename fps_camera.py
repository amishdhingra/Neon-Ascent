"""First-person camera — Celeste-style movement in 3D."""

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
        self.wall_normal = None  # (nx, nz) pointing away from the wall
        self.wall_sliding = False
        self.can_wall_jump = True
        self.wall_regrab_timer = 0.0
        self._accumulated_mouse = [0.0, 0.0]

    @property
    def eye_y(self):
        return self.y + s.PLAYER_HEIGHT * 0.88

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
        self.pitch -= my * s.MOUSE_SENSITIVITY * 0.01
        self.pitch = max(-1.45, min(1.45, self.pitch))

    def request_jump(self):
        self.jump_buffer = s.JUMP_BUFFER_TIME

    def handle_input(self, keys, dt):
        fx, _, fz = self.forward()
        rx, _, rz = self.right()
        moving = any(keys[k] for k in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d))
        wants_sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        self.is_sprinting = False
        speed = s.MOVE_SPEED
        if wants_sprint and moving and self.stamina > 0:
            speed = s.SPRINT_SPEED
            self.is_sprinting = True
            self.stamina = max(0.0, self.stamina - s.SPRINT_DRAIN_RATE * dt)
        elif self.stamina < s.SPRINT_STAMINA_MAX:
            self.stamina = min(s.SPRINT_STAMINA_MAX, self.stamina + s.SPRINT_REGEN_RATE * dt)

        move_x = 0.0
        move_z = 0.0
        if keys[pygame.K_w]:
            move_x += fx
            move_z += fz
        if keys[pygame.K_s]:
            move_x -= fx
            move_z -= fz
        if keys[pygame.K_d]:
            move_x += rx
            move_z += rz
        if keys[pygame.K_a]:
            move_x -= rx
            move_z -= rz

        length = math.hypot(move_x, move_z)
        if length > 0:
            move_x /= length
            move_z /= length

        self.vx = move_x * speed
        self.vz = move_z * speed

    def update_timers(self, dt):
        if self.on_ground:
            self.coyote_timer = s.COYOTE_TIME
            self.can_wall_jump = True
        elif self.coyote_timer > 0:
            self.coyote_timer -= dt

        if self.jump_buffer > 0:
            self.jump_buffer -= dt
        if self.wall_regrab_timer > 0:
            self.wall_regrab_timer -= dt

    def update_wall_contact(self, wall_solids, keys):
        self.wall_normal = None
        self.wall_sliding = False

        if self.on_ground or self.wall_regrab_timer > 0:
            return

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

        wish_len = math.hypot(wish_x, wish_z)
        if wish_len > 0:
            wish_x /= wish_len
            wish_z /= wish_len

        contact = self._find_wall_contact(wall_solids)
        if contact is None:
            return

        nx, nz = contact
        # Pressing into the wall (dot product negative = moving toward wall)
        into_wall = wish_x * nx + wish_z * nz
        if into_wall < -0.25:
            self.wall_normal = (nx, nz)
            self.wall_sliding = True

    def _find_wall_contact(self, wall_solids):
        r = s.PLAYER_RADIUS
        h = s.PLAYER_HEIGHT
        px0, py0, pz0, px1, py1, pz1 = self._player_box(r, h)
        probe = 0.18

        best = None
        best_depth = 0.0

        for sx0, sy0, sz0, sx1, sy1, sz1 in wall_solids:
            if sy1 - sy0 < s.WALL_MIN_HEIGHT:
                continue
            if py1 <= sy0 + 0.2 or py0 >= sy1 - 0.2:
                continue

            # +X face (player on the right side of wall)
            if px0 <= sx1 <= px1 + probe and pz1 > sz0 + 0.1 and pz0 < sz1 - 0.1:
                depth = sx1 - px0
                if depth > best_depth:
                    best_depth = depth
                    best = (1.0, 0.0)
            # -X face
            if px1 >= sx0 >= px0 - probe and pz1 > sz0 + 0.1 and pz0 < sz1 - 0.1:
                depth = px1 - sx0
                if depth > best_depth:
                    best_depth = depth
                    best = (-1.0, 0.0)
            # +Z face
            if pz0 <= sz1 <= pz1 + probe and px1 > sx0 + 0.1 and px0 < sx1 - 0.1:
                depth = sz1 - pz0
                if depth > best_depth:
                    best_depth = depth
                    best = (0.0, 1.0)
            # -Z face
            if pz1 >= sz0 >= pz0 - probe and px1 > sx0 + 0.1 and px0 < sx1 - 0.1:
                depth = pz1 - sz0
                if depth > best_depth:
                    best_depth = depth
                    best = (0.0, -1.0)

        return best

    def try_jump(self, keys):
        if self.jump_buffer <= 0:
            return

        if self.on_ground or self.coyote_timer > 0:
            self.vy = s.JUMP_SPEED
            self.on_ground = False
            self.coyote_timer = 0.0
            self.air_jumps_remaining = s.MAX_AIR_JUMPS
            self.can_wall_jump = True
            self.jump_buffer = 0.0
            return

        if self.wall_normal and self.can_wall_jump:
            nx, nz = self.wall_normal
            self.vy = s.WALL_JUMP_SPEED
            self.vx = nx * s.WALL_JUMP_PUSH
            self.vz = nz * s.WALL_JUMP_PUSH
            self.wall_normal = None
            self.wall_sliding = False
            self.can_wall_jump = False
            self.wall_regrab_timer = s.WALL_REGRAB_COOLDOWN
            self.jump_buffer = 0.0
            return

        if self.air_jumps_remaining > 0 and not self.wall_sliding:
            self.vy = s.DOUBLE_JUMP_SPEED
            fx, _, fz = self.forward()
            rx, _, rz = self.right()
            steer_x = steer_z = 0.0
            if keys[pygame.K_a]:
                steer_x -= rx
                steer_z -= rz
            if keys[pygame.K_d]:
                steer_x += rx
                steer_z += rz
            if keys[pygame.K_w]:
                steer_x += fx
                steer_z += fz
            if steer_x != 0 or steer_z != 0:
                slen = math.hypot(steer_x, steer_z)
                self.vx += (steer_x / slen) * s.DOUBLE_JUMP_BOOST
                self.vz += (steer_z / slen) * s.DOUBLE_JUMP_BOOST
            self.air_jumps_remaining -= 1
            self.jump_buffer = 0.0

    def apply_gravity(self, dt):
        self.vy -= s.GRAVITY * dt
        if self.wall_sliding and self.vy < -s.WALL_SLIDE_SPEED:
            self.vy = -s.WALL_SLIDE_SPEED
        elif self.vy < -s.MAX_FALL_SPEED:
            self.vy = -s.MAX_FALL_SPEED

    def move_with_collision(self, solids, dt):
        self.on_ground = False
        r = s.PLAYER_RADIUS
        h = s.PLAYER_HEIGHT

        self.x += self.vx * dt
        self._collide_axis(solids, r, h, axis="x")

        self.y += self.vy * dt
        self._collide_axis(solids, r, h, axis="y")

        self.z += self.vz * dt
        self._collide_axis(solids, r, h, axis="z")

        if not self.on_ground and self.vy <= 0 and not self.wall_sliding:
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

    def _player_box(self, r, h):
        return (self.x - r, self.y, self.z - r, self.x + r, self.y + h, self.z + r)

    def _collide_axis(self, solids, r, h, axis):
        px0, py0, pz0, px1, py1, pz1 = self._player_box(r, h)
        for sx0, sy0, sz0, sx1, sy1, sz1 in solids:
            if px1 <= sx0 or px0 >= sx1 or py1 <= sy0 or py0 >= sy1 or pz1 <= sz0 or pz0 >= sz1:
                continue
            if axis == "x":
                if self.vx > 0:
                    self.x = sx0 - r
                elif self.vx < 0:
                    self.x = sx1 + r
                self.vx = 0
            elif axis == "y":
                if self.vy < 0:
                    self.y = sy1
                    self.vy = 0
                    self.on_ground = True
                elif self.vy > 0:
                    self.y = sy0 - h
                    self.vy = 0
            elif axis == "z":
                if self.vz > 0:
                    self.z = sz0 - r
                elif self.vz < 0:
                    self.z = sz1 + r
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
