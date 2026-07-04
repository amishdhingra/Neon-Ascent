"""World layout for Neon Ascent — one tall vertical climb with named zones."""

import pygame

import settings as s


ZONES = [
    {"name": "THE PIT", "y": 2680},
    {"name": "NEON PIPES", "y": 1880},
    {"name": "THE GAP", "y": 1080},
    {"name": "THE TOWER", "y": 480},
    {"name": "THE SUMMIT", "y": 120},
]


def _rect(x, y, w, h):
    return pygame.Rect(x, y, w, h)


def build_level():
    """Return platforms and metadata for the full climb."""
    w, h = s.WORLD_WIDTH, s.WORLD_HEIGHT
    platforms = [
        # World bounds
        _rect(0, h - 40, w, 40),
        _rect(0, 0, 20, h),
        _rect(w - 20, 0, 20, h),
        # --- THE PIT (bottom) ---
        _rect(60, 3040, 220, 20),
        _rect(340, 2960, 160, 20),
        _rect(620, 2880, 180, 20),
        _rect(180, 2800, 140, 20),
        _rect(480, 2720, 160, 20),
        _rect(760, 2640, 140, 20),
        _rect(120, 2560, 120, 20),
        _rect(740, 2480, 20, 220),
        # --- NEON PIPES ---
        _rect(220, 2400, 140, 20),
        _rect(520, 2320, 140, 20),
        _rect(760, 2240, 120, 20),
        _rect(280, 2160, 160, 20),
        _rect(600, 2080, 140, 20),
        _rect(160, 2000, 120, 20),
        _rect(480, 1920, 180, 20),
        _rect(760, 1840, 120, 20),
        _rect(200, 1760, 20, 280),
        _rect(740, 1760, 20, 280),
        _rect(340, 1680, 280, 20),
        # --- THE GAP ---
        _rect(80, 1600, 160, 20),
        _rect(420, 1520, 140, 20),
        _rect(700, 1440, 160, 20),
        _rect(240, 1360, 120, 20),
        _rect(560, 1280, 140, 20),
        _rect(120, 1200, 180, 20),
        _rect(480, 1120, 160, 20),
        _rect(760, 1040, 120, 20),
        _rect(300, 960, 140, 20),
        _rect(620, 880, 120, 20),
        _rect(180, 800, 20, 240),
        _rect(760, 800, 20, 240),
        # --- THE TOWER ---
        _rect(400, 720, 160, 20),
        _rect(320, 640, 120, 20),
        _rect(520, 560, 120, 20),
        _rect(380, 480, 200, 20),
        _rect(360, 400, 20, 200),
        _rect(580, 400, 20, 200),
        _rect(420, 320, 120, 20),
        _rect(360, 240, 240, 20),
        # --- THE SUMMIT ---
        _rect(340, 160, 280, 24),
        _rect(400, 80, 160, 20),
    ]
    return {
        "platforms": platforms,
        "zones": ZONES,
        "world_width": w,
        "world_height": h,
    }
