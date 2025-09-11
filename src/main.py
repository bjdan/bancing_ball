"""
M2：加入玩家小人与基本碰撞
在 M1 的基础上：
- 玩家小人是“方块”（与圆形弹球明显区分），键盘控制移动；
- 保持在屏幕内；
- 与弹球碰撞会扣生命；
- 左上角显示 生命：数字 + 血条；
- 生命为 0 时进入 Game Over（冻结），按 ESC 退出。

运行：python src/main.py
"""

import random
import math

import pygame


# ============ 可调的“配置区” ============
# 分辨率和帧率（沿用现有 1024x768）
WIDTH, HEIGHT = 800, 600
FPS = 60

# 颜色（RGB）
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

# 球的数量、半径范围、速度范围（像素/帧）
BALL_MIN, BALL_MAX = 10, 20
R_MIN, R_MAX = 12, 26
SPEED_MIN, SPEED_MAX = 2.0, 5.0

# 玩家（方块）设置
PLAYER_SIZE = 30              # 方块边长
PLAYER_SPEED = 5.0            # 每帧移动像素（键盘控制）
PLAYER_COLOR = (0, 200, 200)  # 青色，易与球区分
PLAYER_HP_MAX = 100
DAMAGE_PER_HIT = 20
HURT_COOLDOWN_FRAMES = 120     # 被击中后短暂无敌（约 0.5s@60FPS）


# 无敌期表现：颜色与速度提升
PLAYER_INVINCIBLE_COLOR = (255, 235, 59)  # 明亮黄，易识别
INVINCIBLE_SPEED_MULT = 1.6               # 无敌期移动速度加成倍数

# ============ 工具函数（简单明了） ============
def clamp(x, a, b):
    """把 x 限制在区间 [a, b] 内。"""
    if x < a:
        return a
    if x > b:
        return b
    return x


def make_ball():
    """
    生成一个球：
    - 随机半径 r
    - 随机位置 (x, y)，保证完全在屏幕内
    - 随机速度方向（用角度），设定速度分量 vx, vy
    - 随机颜色
    返回：字典 {x, y, vx, vy, r, color}
    """
    r = random.randint(R_MIN, R_MAX)

    # 位置要留出半径空间，避免一出生就“卡”在墙上
    x = random.uniform(r, WIDTH - r)
    y = random.uniform(r, HEIGHT - r)

    # 随机方向与速度大小
    angle = random.uniform(0, 2 * math.pi)
    speed = random.uniform(SPEED_MIN, SPEED_MAX)
    vx = math.cos(angle) * speed
    vy = math.sin(angle) * speed

    color = random.choice(COLOR_CHOICES)

    return {"x": x, "y": y, "vx": vx, "vy": vy, "r": r, "color": color}


def make_balls(n):
    """生成 n 个球，存入列表后返回。"""
    balls = []
    for _ in range(n):
        balls.append(make_ball())
    return balls


def update_balls(balls):
    """
    更新每个球的位置，并进行边界反弹：
    - 碰到左右边界：反转 vx
    - 碰到上下边界：反转 vy
    这里采用“镜面反弹”，并轻微校正位置避免粘墙。
    """
    for b in balls:
        b["x"] += b["vx"]
        b["y"] += b["vy"]

        r = b["r"]
        # 左右边界
        if b["x"] <= r:
            b["x"] = r  # 位置校正
            b["vx"] = -b["vx"]
        elif b["x"] >= WIDTH - r:
            b["x"] = WIDTH - r
            b["vx"] = -b["vx"]

        # 上下边界
        if b["y"] <= r:
            b["y"] = r
            b["vy"] = -b["vy"]
        elif b["y"] >= HEIGHT - r:
            b["y"] = HEIGHT - r
            b["vy"] = -b["vy"]


def draw_balls(screen, balls):
    """把所有的球画到屏幕上。"""
    for b in balls:
        pygame.draw.circle(
            screen,
            b["color"],
            (int(b["x"]), int(b["y"])) ,
            int(b["r"]) ,
        )


def handle_events():
    """
    处理窗口事件：
    - 关闭窗口或按 ESC 键，返回 True 表示需要退出。
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return True
    return False


def make_player():
    """
    生成玩家方块：放在屏幕中央。
    使用中心点坐标 (x, y) 记录，绘制时转换为左上角。
    """
    return {
        "x": WIDTH / 2,
        "y": HEIGHT / 2,
        "w": PLAYER_SIZE,
        "h": PLAYER_SIZE,
        "speed": PLAYER_SPEED,
        "color": PLAYER_COLOR,
        "hp": PLAYER_HP_MAX,
        "hp_max": PLAYER_HP_MAX,
        "hurt_cd": HURT_COOLDOWN_FRAMES,  # 短暂无敌计时器（帧）
    }


def handle_move_input():
    """
    读取键盘（WASD / 方向键）输入，返回 (dx, dy)。
    """
    keys = pygame.key.get_pressed()
    dx = 0
    dy = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        dx -= 1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        dx += 1
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        dy -= 1
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        dy += 1
    return dx, dy


def update_player(player):
    """
    根据输入移动玩家，并限制在屏幕内。
    """
    dx, dy = handle_move_input()

    # 斜向移动时做简单归一化，避免比直线更快
    if dx != 0 and dy != 0:
        norm = math.sqrt(2)
    else:
        norm = 1

    effective_speed = player["speed"] * (INVINCIBLE_SPEED_MULT if player["hurt_cd"] > 0 else 1.0)
    player["x"] += (effective_speed * dx) / norm
    player["y"] += (effective_speed * dy) / norm

    half_w = player["w"] / 2
    half_h = player["h"] / 2
    player["x"] = clamp(player["x"], half_w, WIDTH - half_w)
    player["y"] = clamp(player["y"], half_h, HEIGHT - half_h)

    # 受伤冷却帧数递减
    if player["hurt_cd"] > 0:
        player["hurt_cd"] -= 1


def circle_rect_collide(ball, player):
    """
    圆（球）- 矩形（玩家方块）碰撞：
    - 取圆心到矩形的“最近点”；
    - 若距离 <= 半径，则视为碰撞。
    """
    cx = ball["x"]
    cy = ball["y"]
    r = ball["r"]

    half_w = player["w"] / 2
    half_h = player["h"] / 2
    left = player["x"] - half_w
    top = player["y"] - half_h
    right = player["x"] + half_w
    bottom = player["y"] + half_h

    # 找到离圆心最近的点（夹在矩形范围内）
    nearest_x = clamp(cx, left, right)
    nearest_y = clamp(cy, top, bottom)

    dx = cx - nearest_x
    dy = cy - nearest_y
    return (dx * dx + dy * dy) <= (r * r)


def damage_player_if_hit(player, balls):
    """
    检测是否与任意弹球碰撞：
    - 若命中且不在冷却中，则扣血并进入短暂无敌。
    返回是否造成伤害（用于后续音效等扩展）。
    """
    if player["hurt_cd"] > 0 or player["hp"] <= 0:
        return False

    for b in balls:
        if circle_rect_collide(b, player):
            player["hp"] = max(0, player["hp"] - DAMAGE_PER_HIT)
            player["hurt_cd"] = HURT_COOLDOWN_FRAMES
            return True
    return False


def draw_player(screen, player):
    """绘制玩家方块。"""
    half_w = player["w"] / 2
    half_h = player["h"] / 2
    rect = pygame.Rect(int(player["x"] - half_w), int(player["y"] - half_h), int(player["w"]), int(player["h"]))
    color = PLAYER_INVINCIBLE_COLOR if player["hurt_cd"] > 0 else player["color"]
    pygame.draw.rect(screen, color, rect)


def draw_ui(screen, font, player, game_over):
    """
    左上角绘制 生命数字 + 血条；若游戏结束显示提示文字。
    """
    # 数字显示
    text = f"HP: {player['hp']}/{player['hp_max']}"
    text_surf = font.render(text, True, WHITE)
    screen.blit(text_surf, (16, 12))

    # 简单血条（背景红，前景绿）
    bar_x, bar_y = 16, 40
    bar_w, bar_h = 220, 16
    pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_w, bar_h))
    if player["hp_max"] > 0 and player["hp"] > 0:
        ratio = player["hp"] / player["hp_max"]
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_w * ratio), bar_h))
    # 边框
    pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 2)

    if game_over:
        msg = "GAME OVER"
        big_font = pygame.font.SysFont(None, 56)
        msg_surf = big_font.render(msg, True, WHITE)
        rect = msg_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(msg_surf, rect)


def main():
    # 初始化 pygame 与窗口
    pygame.init()
    pygame.display.set_caption("躲避球 M2：玩家、碰撞与生命显示（ESC 退出）")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    # 随机生成 3–5 个球
    ball_count = random.randint(BALL_MIN, BALL_MAX)
    balls = make_balls(ball_count)

    # 生成玩家方块
    player = make_player()

    game_over = False

    # 主循环
    running = True
    while running:
        # 1) 处理输入/事件
        if handle_events():
            running = False
            continue

        # 2) 更新数据（球的运动、玩家移动与碰撞）
        if not game_over:
            update_balls(balls)
            update_player(player)
            _ = damage_player_if_hit(player, balls)
            if player["hp"] <= 0:
                game_over = True

        # 3) 渲染到屏幕
        screen.fill(BG_COLOR)
        draw_balls(screen, balls)
        draw_player(screen, player)
        draw_ui(screen, font, player, game_over)

        # 4) 刷新画面并控制帧率
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
