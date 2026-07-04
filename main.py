import sys

import pygame

import settings as s
from camera import Camera
from level import build_level
from player import Player


def draw_platforms(surface, platforms, camera):
    for platform in platforms:
        if camera.is_visible(platform):
            screen_rect = camera.world_to_screen(platform)
            pygame.draw.rect(surface, s.COLOUR_PLATFORM, screen_rect, border_radius=6)
            pygame.draw.rect(surface, s.COLOUR_GROUND, screen_rect, width=2, border_radius=6)


def draw_zones(surface, zones, camera, font):
    for zone in zones:
        label_y = zone["y"]
        if not (camera.offset_y - 60 <= label_y <= camera.offset_y + s.SCREEN_HEIGHT + 60):
            continue
        text = font.render(zone["name"], True, s.COLOUR_ZONE_TEXT)
        screen_x = s.SCREEN_WIDTH // 2 - text.get_width() // 2
        screen_y = label_y - camera.offset_y
        surface.blit(text, (screen_x, screen_y))


def draw_height(surface, player, font):
    climbed = s.WORLD_HEIGHT - player.rect.bottom
    text = font.render(f"Height: {max(0, climbed // 10)}m", True, s.COLOUR_HEIGHT_TEXT)
    surface.blit(text, (s.SCREEN_WIDTH - text.get_width() - 20, 20))


def setup_display():
    pygame.init()
    if s.FULLSCREEN:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((s.SCREEN_WIDTH, s.SCREEN_HEIGHT))
    s.SCREEN_WIDTH, s.SCREEN_HEIGHT = screen.get_size()
    pygame.display.set_caption(s.TITLE)
    return screen


def main():
    screen = setup_display()
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 28)

    level = build_level()
    platforms = level["platforms"]
    zones = level["zones"]
    camera = Camera(level["world_width"], level["world_height"])
    player = Player(s.PLAYER_START_X, s.PLAYER_START_Y)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    player.request_jump()

        keys = pygame.key.get_pressed()
        player.handle_input(keys)
        player.update_wall_contact(platforms, keys)
        player.apply_gravity()
        player.move_and_collide(platforms)
        player.update_wall_contact(platforms, keys)
        player.try_jump(keys)
        player.update_timers()
        camera.update(player.rect)

        screen.fill(s.COLOUR_BG)
        draw_zones(screen, zones, camera, font)
        draw_platforms(screen, platforms, camera)
        player.draw(screen, camera)
        player.draw_stamina_bar(screen)
        draw_height(screen, player, small_font)

        pygame.display.flip()
        clock.tick(s.FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
