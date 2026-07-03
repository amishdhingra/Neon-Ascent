import sys

import pygame

import settings as s
from player import Player


def build_platforms():
    """Starter layout: ground + a few platforms to jump on."""
    ground = pygame.Rect(0, s.SCREEN_HEIGHT - 40, s.SCREEN_WIDTH, 40)
    platforms = [
        ground,
        pygame.Rect(200, 420, 160, 20),
        pygame.Rect(450, 340, 140, 20),
        pygame.Rect(700, 260, 160, 20),
        pygame.Rect(320, 180, 120, 20),
    ]
    return platforms


def draw_platforms(surface, platforms):
    for platform in platforms:
        pygame.draw.rect(surface, s.COLOUR_PLATFORM, platform, border_radius=6)
        pygame.draw.rect(surface, s.COLOUR_GROUND, platform, width=2, border_radius=6)


def main():
    pygame.init()
    screen = pygame.display.set_mode((s.SCREEN_WIDTH, s.SCREEN_HEIGHT))
    pygame.display.set_caption(s.TITLE)
    clock = pygame.time.Clock()

    player = Player(s.PLAYER_START_X, s.PLAYER_START_Y)
    platforms = build_platforms()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        player.handle_input(keys)
        player.apply_gravity()
        player.move_and_collide(platforms)

        screen.fill(s.COLOUR_BG)
        draw_platforms(screen, platforms)
        player.draw(screen)

        pygame.display.flip()
        clock.tick(s.FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
