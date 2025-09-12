"""
Game configuration constants (UTF-8).
Only the latest milestone (M3) is supported.
"""

# Display
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors (RGB)
BG_COLOR = (18, 18, 18)
WHITE = (240, 240, 240)
GREEN = (50, 205, 50)
RED = (220, 20, 60)
COLOR_CHOICES = [
    (255, 99, 71),    # tomato
    (65, 105, 225),   # royal blue
    (50, 205, 50),    # lime green
    (255, 215, 0),    # gold
    (186, 85, 211),   # medium orchid
    (255, 140, 0),    # dark orange
]

# Balls
BALL_MIN, BALL_MAX = 10, 20
R_MIN, R_MAX = 12, 26
SPEED_MIN, SPEED_MAX = 1.0, 5.0

# Player
PLAYER_SIZE = 30                 # square side length
PLAYER_SPEED = 6.0               # pixels per frame
PLAYER_COLOR = (0, 200, 200)
PLAYER_HP_MAX = 100
DAMAGE_PER_HIT = 20
HURT_COOLDOWN_FRAMES = 120       # ~2s @60FPS
PLAYER_INVINCIBLE_COLOR = 'red'
INVINCIBLE_SPEED_MULT = 1.6

# Scoring
BASE_SCORE_PER_SEC = 1.0

