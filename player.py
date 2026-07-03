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

    def handle_input(self, keys):
        moving_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        moving_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        wants_sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        is_moving = moving_left or moving_right

        self.is_sprinting = False
        speed = s.MOVE_SPEED

        if wants_sprint and is_moving and self.stamina > 0:
            speed = s.SPRINT_SPEED
            self.is_sprinting = True
            self.stamina = max(0, self.stamina - s.SPRINT_DRAIN_RATE)
        elif self.stamina < s.SPRINT_STAMINA_MAX:
            self.stamina = min(s.SPRINT_STAMINA_MAX, self.stamina + s.SPRINT_REGEN_RATE)

        self.vel_x = 0
        if moving_left:
            self.vel_x = -speed
        if moving_right:
            self.vel_x = speed

    def request_jump(self):
        """Call when jump key is pressed — buffered so taps feel reliable."""
        self.jump_buffer = s.JUMP_BUFFER_FRAMES

    def try_jump(self):
        """Use buffered jump input after movement/collision for this frame."""
        if self.jump_buffer <= 0:
            return

        if self.on_ground or self.coyote_timer > 0:
            self.vel_y = s.JUMP_STRENGTH
            self.on_ground = False
            self.coyote_timer = 0
            self.air_jumps_remaining = s.MAX_AIR_JUMPS
            self.jump_buffer = 0
            return

        if self.air_jumps_remaining > 0:
            self.vel_y = s.DOUBLE_JUMP_STRENGTH
            self.air_jumps_remaining -= 1
            self.jump_buffer = 0

    def update_timers(self):
        if self.on_ground:
            self.coyote_timer = s.COYOTE_TIME_FRAMES
        elif self.coyote_timer > 0:
            self.coyote_timer -= 1

        if self.jump_buffer > 0:
            self.jump_buffer -= 1

    def apply_gravity(self):
        self.vel_y += s.GRAVITY
        if self.vel_y > s.MAX_FALL_SPEED:
            self.vel_y = s.MAX_FALL_SPEED

    def clamp_to_screen(self):
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > s.SCREEN_WIDTH:
            self.rect.right = s.SCREEN_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0

    def move_and_collide(self, platforms):
        self.on_ground = False

        self.rect.x += int(self.vel_x)
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel_x > 0:
                    self.rect.right = platform.left
                elif self.vel_x < 0:
                    self.rect.left = platform.right

        self.rect.y += int(self.vel_y)
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.vel_y > 0:
                    self.rect.bottom = platform.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = platform.bottom
                    self.vel_y = 0

        # Snap to ground when barely floating above a platform (fixes missed jumps)
        if not self.on_ground and self.vel_y >= 0:
            for platform in platforms:
                overlap_x = self.rect.right > platform.left and self.rect.left < platform.right
                near_surface = 0 <= platform.top - self.rect.bottom <= 4
                if overlap_x and near_surface:
                    self.rect.bottom = platform.top
                    self.vel_y = 0
                    self.on_ground = True
                    break

        self.clamp_to_screen()

    def draw(self, surface):
        colour = s.COLOUR_PLAYER_SPRINT if self.is_sprinting else s.COLOUR_PLAYER
        pygame.draw.rect(surface, colour, self.rect, border_radius=4)
        eye_x = self.rect.centerx + (4 if self.vel_x >= 0 else -4)
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, self.rect.centery - 6), 3)

    def draw_stamina_bar(self, surface):
        bar_x, bar_y = 20, 20
        bar_w, bar_h = 160, 14
        fill_w = int(bar_w * (self.stamina / s.SPRINT_STAMINA_MAX))

        pygame.draw.rect(surface, s.COLOUR_STAMINA_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        if fill_w > 0:
            pygame.draw.rect(surface, s.COLOUR_STAMINA_FILL, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(surface, s.COLOUR_GROUND, (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=4)
