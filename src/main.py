"""
躲避球（M3）。仅保留最新需求：
- 玩家方块可移动、与弹球碰撞扣血并短暂无敌；
- 左上角显示 HP 条；右上角显示分数与最高分；
- 支持 Ready/Playing/Paused/GameOver 状态切换；
运行：python src/main.py
"""

import math
import random
import pygame
import config as cfg


# ============ 工具函数 ============
def clamp(x: float, a: float, b: float) -> float:
    """将 x 限制在区间 [a, b] 内。"""
    if x < a:
        return a
    if x > b:
        return b
    return x


def make_ball():
    """
    生成一个随机弹球：
    - 随机半径 r；
    - 随机位置 (x, y)，保证完全在屏幕内；
    - 随机方向与速度；
    - 随机颜色。
    返回：dict{x, y, vx, vy, r, color}
    """
    r = random.randint(cfg.R_MIN, cfg.R_MAX)
    x = random.uniform(r, cfg.WIDTH - r)
    y = random.uniform(r, cfg.HEIGHT - r)
    angle = random.uniform(0, 2 * math.pi)
    speed = random.uniform(cfg.SPEED_MIN, cfg.SPEED_MAX)
    vx = math.cos(angle) * speed
    vy = math.sin(angle) * speed
    color = random.choice(cfg.COLOR_CHOICES)
    return {"x": x, "y": y, "vx": vx, "vy": vy, "r": r, "color": color}


def make_balls(n):
    """生成 n 个球，存入列表后返回。"""
    return [make_ball() for _ in range(n)]


def update_balls(balls):
    """
    更新每个球的位置，并进行边界反弹。
    - 碰到左右边界：反转 vx
    - 碰到上下边界：反转 vy
    采用镜面反弹，并轻微校正位置避免粘墙。
    """
    for b in balls:
        b["x"] += b["vx"]
        b["y"] += b["vy"]

        r = b["r"]
        # 左右边界
        if b["x"] <= r:
            b["x"] = r
            b["vx"] = -b["vx"]
        elif b["x"] >= cfg.WIDTH - r:
            b["x"] = cfg.WIDTH - r
            b["vx"] = -b["vx"]

        # 上下边界
        if b["y"] <= r:
            b["y"] = r
            b["vy"] = -b["vy"]
        elif b["y"] >= cfg.HEIGHT - r:
            b["y"] = cfg.HEIGHT - r
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
    处理窗口事件：关闭窗口或按 ESC 键返回 True。
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return True
    return False


def make_player():
    """
    生成玩家方块，初始在屏幕中央。
    使用中心点坐标 (x, y) 存储，绘制时转换为左上角。
    """
    return {
        "x": cfg.WIDTH / 2,
        "y": cfg.HEIGHT / 2,
        "w": cfg.PLAYER_SIZE,
        "h": cfg.PLAYER_SIZE,
        "speed": cfg.PLAYER_SPEED,
        "color": cfg.PLAYER_COLOR,
        "hp": cfg.PLAYER_HP_MAX,
        "hp_max": cfg.PLAYER_HP_MAX,
        "hurt_cd": cfg.HURT_COOLDOWN_FRAMES,  # 短暂无敌计时器（帧）
    }


def handle_move_input():
    """
    读取键盘（WASD/方向键）输入，返回 (dx, dy)。
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

    # 斜向移动时做简单归一化，避免更快
    norm = math.sqrt(2) if (dx != 0 and dy != 0) else 1

    effective_speed = player["speed"] * (cfg.INVINCIBLE_SPEED_MULT if player["hurt_cd"] > 0 else 1.0)
    player["x"] += (effective_speed * dx) / norm
    player["y"] += (effective_speed * dy) / norm

    half_w = player["w"] / 2
    half_h = player["h"] / 2
    player["x"] = clamp(player["x"], half_w, cfg.WIDTH - half_w)
    player["y"] = clamp(player["y"], half_h, cfg.HEIGHT - half_h)

    # 受伤冷却帧数递减
    if player["hurt_cd"] > 0:
        player["hurt_cd"] -= 1


def circle_rect_collide(ball, player):
    """
    圆（球）-矩形（玩家方块）碰撞：
    - 取圆心到矩形的最近点；
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
    检测是否与任意弹球碰撞。
    - 命中且不在冷却中：扣血并进入短暂无敌。
    返回是否造成伤害（便于扩展音效等）。
    """
    if player["hurt_cd"] > 0 or player["hp"] <= 0:
        return False

    for b in balls:
        if circle_rect_collide(b, player):
            player["hp"] = max(0, player["hp"] - cfg.DAMAGE_PER_HIT)
            player["hurt_cd"] = cfg.HURT_COOLDOWN_FRAMES
            return True
    return False


def draw_player(screen, player):
    """绘制玩家方块。"""
    half_w = player["w"] / 2
    half_h = player["h"] / 2
    rect = pygame.Rect(int(player["x"] - half_w), int(player["y"] - half_h), int(player["w"]), int(player["h"]))
    color = cfg.PLAYER_INVINCIBLE_COLOR if player["hurt_cd"] > 0 else player["color"]
    pygame.draw.rect(screen, color, rect)


def draw_hud(screen, font, player, state, score, high_score):
    """
    左上角：HP；右上角：Score/High；中央：状态提示。
    """
    # HP 文本
    if player is not None:
        text = f"HP: {player['hp']}/{player['hp_max']}"
    else:
        text = "HP: -/-"
    text_surf = font.render(text, True, cfg.WHITE)
    screen.blit(text_surf, (16, 12))

    # 血条
    if player is not None:
        bar_x, bar_y = 16, 40
        bar_w, bar_h = 220, 16
        pygame.draw.rect(screen, cfg.RED, (bar_x, bar_y, bar_w, bar_h))
        if player["hp_max"] > 0 and player["hp"] > 0:
            ratio = player["hp"] / player["hp_max"]
            pygame.draw.rect(screen, cfg.GREEN, (bar_x, bar_y, int(bar_w * ratio), bar_h))
        pygame.draw.rect(screen, cfg.WHITE, (bar_x, bar_y, bar_w, bar_h), 2)

    # 分数（右上角）
    score_text = f"Score: {int(score)}"
    hs_text = f"High: {high_score}"
    score_surf = font.render(score_text, True, cfg.WHITE)
    hs_surf = font.render(hs_text, True, cfg.WHITE)
    screen.blit(score_surf, (cfg.WIDTH - score_surf.get_width() - 16, 12))
    screen.blit(hs_surf, (cfg.WIDTH - hs_surf.get_width() - 16, 36))

    # 状态提示
    big_font = pygame.font.SysFont(None, 56)
    small_font = pygame.font.SysFont(None, 28)
    center = (cfg.WIDTH // 2, cfg.HEIGHT // 2)

    if state == "ready":
        msg, tip = "READY", "Press SPACE / ENTER to start"
    elif state == "paused":
        msg, tip = "PAUSED", "Press P to resume"
    elif state == "gameover":
        msg, tip = "GAME OVER", "Press SPACE / ENTER to restart"
    else:
        msg, tip = None, None

    if msg:
        msg_surf = big_font.render(msg, True, cfg.WHITE)
        rect = msg_surf.get_rect(center=center)
        screen.blit(msg_surf, rect)
        if tip:
            tip_surf = small_font.render(tip, True, cfg.WHITE)
            tip_rect = tip_surf.get_rect(center=(center[0], center[1] + 48))
            screen.blit(tip_surf, tip_rect)

    if state == "playing":
        tip2 = small_font.render("P: Pause", True, cfg.WHITE)
        screen.blit(tip2, (cfg.WIDTH - tip2.get_width() - 16, cfg.HEIGHT - tip2.get_height() - 12))


def main():
    # 初始化 pygame 与窗口
    pygame.init()
    pygame.display.set_caption("躲避球 M3：状态/分数/暂停（ESC 退出）")
    screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    def start_new_game():
        ball_count = random.randint(cfg.BALL_MIN, cfg.BALL_MAX)
        return make_balls(ball_count), make_player(), 0.0

    state = "ready"  # ready/playing/paused/gameover
    balls = []
    player = None
    score = 0.0
    high_score = 0

    running = True
    while running:
        dt = clock.tick(cfg.FPS) / 1000.0

        # 1) 处理输入 / 退出
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                break
            if event.type == pygame.KEYDOWN:
                if state == "ready":
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        balls, player, score = start_new_game()
                        state = "playing"
                elif state == "playing":
                    if event.key == pygame.K_p:
                        state = "paused"
                elif state == "paused":
                    if event.key == pygame.K_p:
                        state = "playing"
                elif state == "gameover":
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        balls, player, score = start_new_game()
                        state = "playing"

        if not running:
            break

        # 2) 更新（仅 playing）
        if state == "playing":
            update_balls(balls)
            update_player(player)
            _ = damage_player_if_hit(player, balls)
            score += dt * cfg.BASE_SCORE_PER_SEC
            if player["hp"] <= 0:
                state = "gameover"
                high_score = max(high_score, int(score))

        # 3) 渲染
        screen.fill(cfg.BG_COLOR)
        if state in ("playing", "paused", "gameover"):
            draw_balls(screen, balls)
            if player is not None:
                draw_player(screen, player)
        draw_hud(screen, font, player, state, score, high_score)

        # 4) 显示
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
