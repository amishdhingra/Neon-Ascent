# Neon Ascent

A punishing vertical climb through a glowing neon world. Double jump, sprint, wall jump — don't look down.

## Status

<<<<<<< HEAD
Work in progress — vertical climb with camera, sprint, double jump, and wall jump.
=======
Work in progress — run, jump, sprint, double jump, wall hold and wall jump.

## Controls

- **A / D** or **arrow keys** — Move
- **Space** or **W** — Jump (double jump in mid-air; one wall jump per airtime)
- **Shift** — Sprint (uses stamina — bar top-left)
- **Hold toward a wall in mid-air** — Wall slide (character turns purple)
- **Double jump + direction** — Hold A/D when double jumping to steer toward platforms
- **Esc** — Quit (exits fullscreen)

The game runs in **fullscreen** using your monitor's resolution.

Climb through five zones: **The Pit → Neon Pipes → The Gap → The Tower → The Summit**.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Requirements

- Python 3.11+
- pygame-ce
