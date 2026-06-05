"""
Tile legend:
  >  dungeon entrance (down)    <  stairs up
  T  tree                       l/i  torch (flickers)
  $  ground loot                 &  Ash Forge craft station
  ~  stream / loom station       o/+  gatherable resources
  !  battle trigger (placed at gen)   @  story trigger
  =  road                        .  grass
"""

CELL_W = 10
CELL_H = 16
FPS = 120
TARGET_FRAME_MS = 1000.0 / FPS

# Display grid (chars)
SCREEN_W = 100
SCREEN_H = 45
STATUS_STRIP_H = 1
MAP_VIEW_W = SCREEN_W
MAP_VIEW_H = SCREEN_H - STATUS_STRIP_H
MAP_ORIGIN_Y = 0

# Isometric map (world tiles visible; each tile = multi-char stencil)
MAP_VIEW_TILES_W = 22
MAP_VIEW_TILES_H = 16
ISO_STEP_X = 2
ISO_STEP_Y = 1
ISO_SKY_ROWS = 2
ISO_ORIGIN_X = SCREEN_W // 2
# Vertical center of map band (below sky, above status strip)
ISO_MAP_BOTTOM_Y = SCREEN_H - STATUS_STRIP_H - 1
ISO_ORIGIN_Y = (ISO_SKY_ROWS + ISO_MAP_BOTTOM_Y) // 2
# LOS radius for live visibility (fog + draw); explored map is persistent (no r=100 LOS).
VISIBLE_LOS_RADIUS_SURFACE = 32
# Legacy name kept for tests/docs comparing old raycast budget at r=100.
SURFACE_FOV_RADIUS_TILES = 100
# Smooth locomotion (tiles per second between grid cells).
PLAYER_MOVE_SPEED_TPS = 8.0
# Held-key repeat before smooth stride takes over (ms between grid steps if not moving).
INPUT_REPEAT_INITIAL_MS = 120
INPUT_REPEAT_MS = 80
ISO_TILE_PIXEL_W = ISO_STEP_X * CELL_W
ISO_TILE_PIXEL_H = ISO_STEP_Y * CELL_H
ISO_Z_CHARS_PER_M = 1
TILE_METERS = 1.0
DEFAULT_PLAYER_HEIGHT_M = 1.8
ENTITY_DRAW_Z_M = DEFAULT_PLAYER_HEIGHT_M * 0.55

CHUNK_SIZE = 32
WORLD_RADIUS_CHUNKS = 12
STREAM_RADIUS = 3  # chunk load radius around player

DAY_CYCLE_TURNS = 240

# Colors (RGB)
COLOR_BG = (8, 8, 18)
COLOR_UI_BG = (16, 16, 28)
COLOR_UI_BORDER = (60, 80, 100)
COLOR_TEXT = (180, 190, 200)
COLOR_TEXT_DIM = (100, 110, 120)
COLOR_HIGHLIGHT = (120, 200, 255)
COLOR_HP = (200, 80, 80)
COLOR_MERcy = (255, 220, 120)
COLOR_GRASS = (60, 90, 60)
COLOR_GRASS_FG = (120, 140, 90)
COLOR_TORCH = (255, 180, 80)
COLOR_DUNGEON_WALL = (40, 40, 50)
COLOR_SURFACE_SKY = (30, 35, 55)

DATA_DIR = None  # set at runtime
AUDIO_DIR = None  # set at runtime


def init_paths(base_path):
    global DATA_DIR, AUDIO_DIR
    import os
    DATA_DIR = os.path.join(base_path, "src", "data")
    AUDIO_DIR = os.path.join(base_path, "assets", "audio")
