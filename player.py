import pygame

import settings as s


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, s.PLAYER_WIDTH, s.PLAYER_HEIGHT)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False

    def handle_input(self, keys):
        self.vel_x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel_x = -s.MOVE_SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel_x = s.MOVE_SPEED

        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vel_y = s.JUMP_STRENGTH
            self.on_ground = False

    def apply_gravity(self):
        self.vel_y += s.GRAVITY
        if self.vel_y > s.MAX_FALL_SPEED:
            self.vel_y = s.MAX_FALL_SPEED

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

    def draw(self, surface):
        pygame.draw.rect(surface, s.COLOUR_PLAYER, self.rect, border_radius=4)
        # Simple "face" direction hint
        eye_x = self.rect.centerx + (4 if self.vel_x >= 0 else -4)
        pygame.draw.circle(surface, (255, 255, 255), (eye_x, self.rect.centery - 6), 3)
