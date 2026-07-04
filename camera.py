import pygame

import settings as s


class Camera:
    def __init__(self, world_width, world_height):
        self.world_width = world_width
        self.world_height = world_height
        self.offset_x = 0
        self.offset_y = 0

    def update(self, target):
        self.offset_x = 0
        self.offset_y = target.centery - s.SCREEN_HEIGHT // 2
        max_offset_y = max(0, self.world_height - s.SCREEN_HEIGHT)
        self.offset_y = max(0, min(self.offset_y, max_offset_y))

    def world_to_screen(self, rect):
        return rect.move(-self.offset_x, -self.offset_y)

    def is_visible(self, rect, margin=40):
        view = pygame.Rect(
            self.offset_x - margin,
            self.offset_y - margin,
            s.SCREEN_WIDTH + margin * 2,
            s.SCREEN_HEIGHT + margin * 2,
        )
        return rect.colliderect(view)
