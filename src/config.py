"""
游戏配置常量（UTF-8 编码）。
针对里程碑 M4 进行了调整。
"""

# 显示参数
WIDTH, HEIGHT = 800, 600
FPS = 60

# 颜色（RGB）
BG_COLOR = (18, 18, 18)
WHITE = (240, 240, 240)
GREEN = (50, 205, 50)
RED = (220, 20, 60)
COLOR_CHOICES = [
    (255, 99, 71),    # 番茄红
    (65, 105, 225),   # 宝蓝
    (50, 205, 50),    # 酸橙绿
    (255, 215, 0),    # 金色
    (186, 85, 211),   # 蓝紫
    (255, 140, 0),    # 深橙
]

# 弹球参数
BALL_MIN, BALL_MAX = 10, 20
R_MIN, R_MAX = 12, 26
SPEED_MIN, SPEED_MAX = 1.0, 5.0

# 玩家参数
PLAYER_SIZE = 30                 # 玩家方块边长
PLAYER_SPEED = 6.0               # 每帧移动像素
PLAYER_COLOR = (0, 200, 200)
PLAYER_HP_MAX = 100
DAMAGE_PER_HIT = 20
HURT_COOLDOWN_FRAMES = 120       # 约 2 秒（@60FPS）
PLAYER_INVINCIBLE_COLOR = 'red'
INVINCIBLE_SPEED_MULT = 1.6

# 计分
BASE_SCORE_PER_SEC = 1.0

# 关卡推进
LEVEL_INTERVAL = 12.0            # 每隔多少秒升级
LEVEL_BONUS_PER_LEVEL = 0.5      # 每一级额外加速得分
LEVEL_BALL_INCREMENT = 1         # 每级新增弹球数量
LEVEL_INITIAL_BALLS = BALL_MIN   # 开局弹球基数
LEVEL_MAX_BALLS = BALL_MAX       # 弹球数量上限，避免过于拥挤
