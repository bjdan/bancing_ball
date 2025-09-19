"""
游戏配置常量（UTF-8 编码）
保留字典数据结构，方便主模块引用。
"""

from pathlib import Path

# 资源路径
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
SOUNDS_DIR = ASSETS_DIR / "sounds"

IMAGE_BACKGROUND = IMAGES_DIR / "bg_layer.png"

SOUND_FILES = {
    "hit": SOUNDS_DIR / "sfx_hit.ogg",
    "levelup": SOUNDS_DIR / "sfx_levelup.ogg",
    "start": SOUNDS_DIR / "sfx_start.ogg",
    "gameover": SOUNDS_DIR / "sfx_gameover.ogg",
}

SFX_VOLUME = 0.6

# 屏幕参数
WIDTH, HEIGHT = 800, 600
FPS = 60
BG_FALLBACK_COLOR = (18, 20, 32)
BG_COLOR = BG_FALLBACK_COLOR

# 颜色
WHITE = (240, 240, 240)
GREEN = (50, 205, 50)
RED = (220, 20, 60)
BALL_COLORS = [
    (255, 99, 71),
    (65, 105, 225),
    (255, 215, 0),
    (186, 85, 211),
]
PLAYER_COLOR = (78, 205, 196)
PLAYER_HURT_COLOR = (255, 120, 120)
HUD_PANEL_ALPHA = 140
LEVEL_FLASH_COLOR = (255, 209, 102)

# 弹球参数
BALL_MIN = 5
BALL_MAX = 30
R_MIN, R_MAX = 12, 24
SPEED_MIN, SPEED_MAX = 1.5, 4.0

# 玩家参数
PLAYER_SIZE = 32
PLAYER_SPEED = 5.5
PLAYER_HP_MAX = 100
DAMAGE_PER_HIT = 20
HURT_COOLDOWN_FRAMES = 120
INVINCIBLE_SPEED_MULT = 1.5

# 计分
BASE_SCORE_PER_SEC = 1.0

# 关卡
LEVEL_INTERVAL = 12.0
LEVEL_BONUS_PER_LEVEL = 0.5
LEVEL_BALL_INCREMENT = 1
LEVEL_INITIAL_BALLS = BALL_MIN
LEVEL_MAX_BALLS = BALL_MAX
