import pygame

import settings as s


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, s.PLAYER_WIDTH, s.PLAYER_HEIGHT)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.air_jumps_remaining = 0
        self.stamina = float(s.SPRINT_STAMINA_MAX)
        self.is_sprinting = False
        self.jump_buffer = 0
        self.coyote_timer = 0
        self.wall_touch_dir = 0
        self.wall_sliding = False
        self.can_wall_jump = True
        self.wall_regrab_timer = 0

    def handle_input(self, keys, dt=1.0):
        moving_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        moving_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        wants_sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        is_moving = moving_left or moving_right

        self.is_sprinting = False
        speed = s.MOVE_SPEED

        if wants_sprint and is_moving and self.stamina > 0:
            speed = s.SPRINT_SPEED
            self.is_sprinting = True
            self.stamina = max(0, self.stamina - s.SPRINT_DRAIN_RATE * dt)
        elif self.stamina < s.SPRINT_STAMINA_MAX:
            self.stamina = min(s.SPRINT_STAMINA_MAX, self.stamina + s.SPRINT_REGEN_RATE * dt)

        self.vel_x = 0
        if moving_left:
            self.vel_x = -speed
        if moving_right:
            self.vel_x = speed

    def request_jump(self):
        """Call when jump key is pressed — buffered so taps feel reliable."""
        self.jump_buffer = s.JUMP_BUFFER_FRAMES

    def update_wall_contact(self, platforms, keys):
        self.wall_touch_dir = 0
        self.wall_sliding = False

        if self.on_ground or self.wall_regrab_timer > 0:
            return

        # No wall cling at the top of the world
        if self.rect.top <= s.SCREEN_TOP_WALL_MARGIN:
            return

        moving_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        moving_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        left_wall = self._touching_wall(platforms, -1)
        right_wall = self._touching_wall(platforms, 1)

        if left_wall:
            self.wall_touch_dir = -1
        elif right_wall:
            self.wall_touch_dir = 1

        if left_wall and moving_left:
            self.wall_sliding = True
        elif right_wall and moving_right:
            self.wall_sliding = True

    def _touching_wall(self, platforms, direction):
        probe = self.rect.copy()
        if direction == -1:
            probe.left -= 2
        else:
            probe.right += 2

        for platform in platforms:
            if platform.height < s.WALL_MIN_HEIGHT:
                continue
            if probe.colliderect(platform):
                if self.rect.bottom > platform.top + 10:
                    return True
        return False

    def try_jump(self, keys):
        """Use buffered jump input after movement/collision for this frame."""
        if self.jump_buffer <= 0:
            return

        if self.on_ground or self.coyote_timer > 0:
            self.vel_y = s.JUMP_STRENGTH
            self.on_ground = False
            self.coyote_timer = 0
            self.air_jumps_remaining = s.MAX_AIR_JUMPS
            self.can_wall_jump = True
            self.jump_buffer = 0
            return

        if self.wall_touch_dir != 0 and self.can_wall_jump:
            self.vel_y = s.WALL_JUMP_STRENGTH
            self.vel_x = -self.wall_touch_dir * s.WALL_JUMP_PUSH
            self.wall_touch_dir = 0
            self.wall_sliding = False
            self.can_wall_jump = False
            self.wall_regrab_timer = s.WALL_REGRAB_COOLDOWN
            self.jump_buffer = 0
            return

        # Double jump only when fully off walls — use after wall jump to reach platforms
        if self.air_jumps_remaining > 0 and self.wall_touch_dir == 0:
            self.vel_y = s.DOUBLE_JUMP_STRENGTH
            moving_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
            moving_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
            if moving_left:
                self.vel_x = -s.DOUBLE_JUMP_HORIZONTAL
            elif moving_right:
                self.vel_x = s.DOUBLE_JUMP_HORIZONTAL
            self.air_jumps_remaining -= 1
            self.jump_buffer = 0

    def update_timers(self, dt=1.0):
        if self.on_ground:
            self.coyote_timer = s.COYOTE_TIME_FRAMES
            self.can_wall_jump = True
        elif self.coyote_timer > 0:
            self.coyote_timer -= dt

        if self.jump_buffer > 0:
            self.jump_buffer -= dt

        if self.wall_regrab_timer > 0:
            self.wall_regrab_timer -= dt

    def apply_gravity(self, dt=1.0):
        self.vel_y += s.GRAVITY * dt
        if self.wall_sliding and self.vel_y > s.WALL_SLIDE_SPEED:
            self.vel_y = s.WALL_SLIDE_SPEED
        elif self.vel_y > s.MAX_FALL_SPEED:
            self.vel_y = s.MAX_FALL_SPEED

    def clamp_to_world(self):
        """Invisible world edges — block movement but not wall jumps/slides."""
        if self.rect.left < 0:
            self.rect.left = 0
            if self.vel_x < 0:
                self.vel_x = 0
        if self.rect.right > s.WORLD_WIDTH:
            self.rect.right = s.WORLD_WIDTH
            if self.vel_x > 0:
                self.vel_x = 0
        if self.rect.top < 0:
            self.rect.top = 0
            if self.vel_y < 0:
                self.vel_y = 0
        if self.rect.bottom > s.WORLD_HEIGHT:
            self.rect.bottom = s.WORLD_HEIGHT
            self.vel_y = 0
            self.on_ground = True

    def move_and_collide(self, platforms, dt=1.0):
        self.on_ground = False

        self.rect.x += int(self.vel_x * dt)
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel_x > 0:
                    self.rect.right = platform.left
                elif self.vel_x < 0:
                    self.rect.left = platform.right

        prev_bottom = self.rect.bottom
        self.rect.y += int(self.vel_y * dt)
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel_y > 0:
                    # Only land on a top surface — not when sliding past a wall face
                    if prev_bottom <= platform.top + s.LANDING_TOLERANCE:
                        self.rect.bottom = platform.top
                        self.vel_y = 0
                        self.on_ground = True
                elif self.vel_y < 0:
                    prev_top = self.rect.top - int(self.vel_y * dt)
                    if prev_top >= platform.bottom - s.LANDING_TOLERANCE:
                        self.rect.top = platform.bottom
                        self.vel_y = 0

        if not self.on_ground and self.vel_y >= 0:
            for platform in platforms:
                overlap_x = self.rect.right > platform.left and self.rect.left < platform.right
                near_surface = 0 <= platform.top - self.rect.bottom <= 4
                if overlap_x and near_surface:
                    self.rect.bottom = platform.top
                    self.vel_y = 0
                    self.on_ground = True
                    break

        self.clamp_to_world()

    def draw(self, surface, camera):
        screen_rect = camera.world_to_screen(self.rect)
        if self.wall_sliding:
            colour = s.COLOUR_PLAYER_WALL
        elif self.is_sprinting:
            colour = s.COLOUR_PLAYER_SPRINT
        else:
            colour = s.COLOUR_PLAYER
        pygame.draw.rect(surface, colour, screen_rect, border_radius=4)
        eye_x = screen_rect.centerx + (4 if self.vel_x >= 0 else -4)
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, screen_rect.centery - 6), 3)

    def draw_stamina_bar(self, surface):
        bar_x, bar_y = 20, 20
        bar_w, bar_h = 160, 14
        fill_w = int(bar_w * (self.stamina / s.SPRINT_STAMINA_MAX))

        pygame.draw.rect(surface, s.COLOUR_STAMINA_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        if fill_w > 0:
            pygame.draw.rect(surface, s.COLOUR_STAMINA_FILL, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(surface, s.COLOUR_GROUND, (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=4)
