"""World layout for Neon Ascent — one tall vertical climb with named zones."""

import pygame

import settings as s

# Level was originally designed at this width; it scales to the fullscreen width.
BASE_WORLD_WIDTH = 960

ZONES = [
    {"name": "THE PIT", "y": 2680},
    {"name": "NEON PIPES", "y": 1880},
    {"name": "THE GAP", "y": 1080},
    {"name": "THE TOWER", "y": 480},
    {"name": "THE SUMMIT", "y": 120},
]


def build_level():
    """Return platforms and metadata for the full climb."""
    w, h = s.WORLD_WIDTH, s.WORLD_HEIGHT
    scale = w / BASE_WORLD_WIDTH

    def sx(x):
        return int(x * scale)

    def sw(width):
        return max(20, int(width * scale))

    def R(x, y, rw, rh):
        return pygame.Rect(sx(x), y, sw(rw), rh)

    platforms = [
        # Full-width ground — invisible side barriers sit at x=0 and x=w
        pygame.Rect(0, h - 40, w, 40),
        # --- THE PIT (bottom) ---
        R(60, 3040, 220, 20),
        R(340, 2960, 160, 20),
        R(620, 2880, 180, 20),
        R(180, 2800, 140, 20),
        R(480, 2720, 160, 20),
        R(760, 2640, 140, 20),
        R(120, 2560, 120, 20),
        R(740, 2480, 20, 220),
        # Extra side routes on wider screens
        R(20, 2900, 100, 20),
        R(820, 2820, 100, 20),
        # --- NEON PIPES ---
        R(220, 2400, 140, 20),
        R(520, 2320, 140, 20),
        R(760, 2240, 120, 20),
        R(280, 2160, 160, 20),
        R(600, 2080, 140, 20),
        R(160, 2000, 120, 20),
        R(480, 1920, 180, 20),
        R(760, 1840, 120, 20),
        R(200, 1760, 20, 280),
        R(740, 1760, 20, 280),
        R(340, 1680, 280, 20),
        R(40, 2280, 120, 20),
        R(800, 2200, 120, 20),
        # --- THE GAP ---
        R(80, 1600, 160, 20),
        R(420, 1520, 140, 20),
        R(700, 1440, 160, 20),
        R(240, 1360, 120, 20),
        R(560, 1280, 140, 20),
        R(120, 1200, 180, 20),
        R(480, 1120, 160, 20),
        R(760, 1040, 120, 20),
        R(300, 960, 140, 20),
        R(620, 880, 120, 20),
        R(180, 800, 20, 240),
        R(760, 800, 20, 240),
        R(30, 1480, 100, 20),
        R(830, 1400, 100, 20),
        # --- THE TOWER ---
        R(400, 720, 160, 20),
        R(320, 640, 120, 20),
        R(520, 560, 120, 20),
        R(380, 480, 200, 20),
        R(360, 400, 20, 200),
        R(580, 400, 20, 200),
        R(420, 320, 120, 20),
        R(360, 240, 240, 20),
        R(80, 600, 140, 20),
        R(740, 520, 140, 20),
        # --- THE SUMMIT ---
        R(340, 160, 280, 24),
        R(400, 80, 160, 20),
        R(120, 120, 120, 20),
        R(720, 100, 120, 20),
    ]
    return {
        "platforms": platforms,
        "zones": ZONES,
        "world_width": w,
        "world_height": h,
    }


def scaled_start_x():
    return int(s.PLAYER_START_X * s.WORLD_WIDTH / BASE_WORLD_WIDTH)
