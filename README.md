# Neon Ascent

A punishing **3D first-person** vertical climb through a glowing neon tower. Jump between floating platforms — don't look down.

## Status

**3D first-person prototype** — pygame-ce + PyOpenGL (works on Windows ARM64).

The old 2D platformer lives in `legacy_2d/` if you want to reference it.

## Controls

- **W / A / S / D** — Move
- **Mouse** — Look around
- **Space** — Jump (double jump in mid-air; steer with WASD on double jump)
- **Shift** — Sprint (stamina bar top-left)
- **Hold into a wall in mid-air** — Wall slide, then jump to wall jump off
- **Tab** — Toggle mouse lock
- **Esc** — Quit (exits fullscreen)

The game runs in **fullscreen** using your monitor's resolution. Height and progress % show in the window title.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Or double-click `run.bat`, or press **F5** in Cursor.

## Requirements

- Python 3.11+ (ARM64 or x64)
- pygame-ce
- PyOpenGL

**Note:** Ursina/Panda3D need x64 Python on Windows — this stack avoids that.
