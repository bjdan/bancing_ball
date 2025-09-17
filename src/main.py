"""
躲避球（M3）。

对象关系（字典模拟对象，函数扮演方法）：
    game ──拥有──> hud
      │              └─读取 game.state / score / player
      ├─拥有──> player ──检测──> balls[*]
      └─拥有──> balls[*]

状态切换：
    READY --Space/Enter--> PLAYING --P--> PAUSED
      ^                        | ^          |
      |                        | |          |
      +----Space/Enter---------+ +----P-----+
                               |
                             HP<=0
                               v
                            GAMEOVER
                               ^
                               +--Space/Enter

运行：python src/main.py
"""

import math
import random
from typing import Any

import pygame

import config as cfg


Ball = dict[str, Any]
Balls = list[Ball]
Player = dict[str, Any]
HUD = dict[str, Any]
Game = dict[str, Any]


# ============ 球体相关 ============
def clamp(value: float, lower: float, upper: float) -> float:
    """将数值限制在 [lower, upper]，用于避免坐标越界。"""
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def ball_create() -> Ball:
    """创建单个随机弹球（位置、速度、半径、颜色）。"""
    radius = random.randint(cfg.R_MIN, cfg.R_MAX)
    x = random.uniform(radius, cfg.WIDTH - radius)
    y = random.uniform(radius, cfg.HEIGHT - radius)
    angle = random.uniform(0, 2 * math.pi)
    speed = random.uniform(cfg.SPEED_MIN, cfg.SPEED_MAX)
    vx = math.cos(angle) * speed
    vy = math.sin(angle) * speed
    color = random.choice(cfg.COLOR_CHOICES)
    return {"x": x, "y": y, "vx": vx, "vy": vy, "r": radius, "color": color}


def balls_create_many(count: int) -> Balls:
    """批量创建弹球列表。"""
    return [ball_create() for _ in range(count)]


def ball_update(ball: Ball) -> None:
    """更新单个弹球的位置并做镜面反弹。"""
    ball["x"] += ball["vx"]
    ball["y"] += ball["vy"]

    radius = ball["r"]
    if ball["x"] <= radius:
        ball["x"] = radius
        ball["vx"] = -ball["vx"]
    elif ball["x"] >= cfg.WIDTH - radius:
        ball["x"] = cfg.WIDTH - radius
        ball["vx"] = -ball["vx"]

    if ball["y"] <= radius:
        ball["y"] = radius
        ball["vy"] = -ball["vy"]
    elif ball["y"] >= cfg.HEIGHT - radius:
        ball["y"] = cfg.HEIGHT - radius
        ball["vy"] = -ball["vy"]


def balls_update_all(balls: Balls) -> None:
    """更新所有弹球。"""
    for ball in balls:
        ball_update(ball)


def balls_draw_all(balls: Balls, screen: pygame.Surface) -> None:
    """将所有弹球绘制到屏幕上。"""
    for ball in balls:
        pygame.draw.circle(
            screen,
            ball["color"],
            (int(ball["x"]), int(ball["y"])),
            int(ball["r"]),
        )


# ============ HUD 相关 ============
def hud_create(font_name: str = None) -> HUD:
    """创建 HUD 字典，缓存字体资源并预置默认值。"""
    return {
        "font_small": pygame.font.SysFont(font_name, 28),
        "font_normal": pygame.font.SysFont(font_name, 24),
        "font_big": pygame.font.SysFont(font_name, 56),
        "color_text": cfg.WHITE,
        "padding": 12,
        "player": None,
        "state": "ready",
        "score": 0,
        "high_score": 0,
    }


def hud_refresh(hud: HUD, game: Game) -> None:
    """将 game 中的实时数据同步到 HUD。"""
    hud["player"] = game.get("player")
    hud["state"] = game.get("state", "ready")
    hud["score"] = int(game.get("score", 0))
    hud["high_score"] = game.get("high_score", 0)


def hud_draw_hp(hud: HUD, screen: pygame.Surface) -> None:
    font = hud["font_normal"]
    color = hud["color_text"]
    pad = hud["padding"]
    player = hud["player"]

    if player is None:
        return

    text =  f"HP: {player['hp']}/{player['hp_max']}"
    text_surf = font.render(text, True, color)
    screen.blit(text_surf, (pad + 4, pad))


    bar_x, bar_y = pad + 4, pad + 28
    bar_w, bar_h = 220, 16
    pygame.draw.rect(screen, cfg.RED, (bar_x, bar_y, bar_w, bar_h))
    if player["hp_max"] > 0 and player["hp"] > 0:
        ratio = player["hp"] / player["hp_max"]
        pygame.draw.rect(screen, cfg.GREEN, (bar_x, bar_y, int(bar_w * ratio), bar_h))
    pygame.draw.rect(screen, cfg.WHITE, (bar_x, bar_y, bar_w, bar_h), 2)


def hud_draw_scores(hud: HUD, screen: pygame.Surface) -> None:
    font = hud["font_normal"]
    color = hud["color_text"]
    pad = hud["padding"]
    score = hud["score"]
    high_score = hud["high_score"]

    score_surf = font.render(f"Score: {score}", True, color)
    hs_surf = font.render(f"High: {high_score}", True, color)
    screen.blit(score_surf, (cfg.WIDTH - score_surf.get_width() - pad, pad))
    screen.blit(hs_surf, (cfg.WIDTH - hs_surf.get_width() - pad, pad + 24))


def hud_draw_state_banner(hud: HUD, screen: pygame.Surface) -> None:
    big_font = hud["font_big"]
    small_font = hud["font_small"]
    color = hud["color_text"]
    center = (cfg.WIDTH // 2, cfg.HEIGHT // 2)

    banner_map = {
        "ready": ("READY", "Press SPACE / ENTER to start"),
        "paused": ("PAUSED", "Press P to resume"),
        "gameover": ("GAME OVER", "Press SPACE / ENTER to restart"),
    }
    msg, tip = banner_map.get(hud["state"], (None, None))

    if msg is None:
        return

    msg_surf = big_font.render(msg, True, color)
    msg_rect = msg_surf.get_rect(center=center)
    screen.blit(msg_surf, msg_rect)

    if tip:
        tip_surf = small_font.render(tip, True, color)
        tip_rect = tip_surf.get_rect(center=(center[0], center[1] + 48))
        screen.blit(tip_surf, tip_rect)


def hud_draw_pause_hint(hud: HUD, screen: pygame.Surface) -> None:
    if hud["state"] != "playing":
        return

    small_font = hud["font_small"]
    color = hud["color_text"]
    pad = hud["padding"]
    tip = small_font.render("P: Pause", True, color)
    screen.blit(
        tip,
        (cfg.WIDTH - tip.get_width() - pad, cfg.HEIGHT - tip.get_height() - pad),
    )


def hud_draw(hud: HUD, screen: pygame.Surface) -> None:
    """绘制 HUD 的所有部分。"""
    hud_draw_hp(hud, screen)
    hud_draw_scores(hud, screen)
    hud_draw_state_banner(hud, screen)
    hud_draw_pause_hint(hud, screen)


# ============ 玩家相关 ============
def player_create() -> Player:
    """创建玩家，初始居中并带短暂无敌冷却。"""
    return {
        "x": cfg.WIDTH / 2,
        "y": cfg.HEIGHT / 2,
        "w": cfg.PLAYER_SIZE,
        "h": cfg.PLAYER_SIZE,
        "speed": cfg.PLAYER_SPEED,
        "color": cfg.PLAYER_COLOR,
        "hp": cfg.PLAYER_HP_MAX,
        "hp_max": cfg.PLAYER_HP_MAX,
        "hurt_cd": cfg.HURT_COOLDOWN_FRAMES,
    }


def player_handle_move_input() -> tuple[int, int]:
    """读取方向键 / WASD 输入，返回单位方向向量。"""
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


def player_update(player: Player) -> None:
    """根据输入移动玩家，并处理边界与受伤冷却。"""
    dx, dy = player_handle_move_input()
    norm = math.sqrt(2) if (dx != 0 and dy != 0) else 1

    speed = player["speed"]
    if player["hurt_cd"] > 0:
        speed *= cfg.INVINCIBLE_SPEED_MULT

    player["x"] += (speed * dx) / norm
    player["y"] += (speed * dy) / norm

    half_w = player["w"] / 2
    half_h = player["h"] / 2
    player["x"] = clamp(player["x"], half_w, cfg.WIDTH - half_w)
    player["y"] = clamp(player["y"], half_h, cfg.HEIGHT - half_h)

    if player["hurt_cd"] > 0:
        player["hurt_cd"] -= 1


def player_draw(player: Player, screen: pygame.Surface) -> None:
    """将玩家方块绘制到屏幕上。"""
    half_w = player["w"] / 2
    half_h = player["h"] / 2
    rect = pygame.Rect(
        int(player["x"] - half_w),
        int(player["y"] - half_h),
        int(player["w"]),
        int(player["h"]),
    )
    color = cfg.PLAYER_INVINCIBLE_COLOR if player["hurt_cd"] > 0 else player["color"]
    pygame.draw.rect(screen, color, rect)


def circle_rect_collide(ball: Ball, player: Player) -> bool:
    """检测圆形弹球与玩家矩形是否碰撞。"""
    cx = ball["x"]
    cy = ball["y"]
    radius = ball["r"]

    half_w = player["w"] / 2
    half_h = player["h"] / 2
    left = player["x"] - half_w
    top = player["y"] - half_h
    right = player["x"] + half_w
    bottom = player["y"] + half_h

    nearest_x = clamp(cx, left, right)
    nearest_y = clamp(cy, top, bottom)
    dx = cx - nearest_x
    dy = cy - nearest_y
    return (dx * dx + dy * dy) <= (radius * radius)


def player_take_damage_if_hit(player: Player, balls: Balls) -> bool:
    """若玩家未处于冷却，则检测碰撞并扣血。返回是否受伤。"""
    if player["hurt_cd"] > 0 or player["hp"] <= 0:
        return False

    for ball in balls:
        if circle_rect_collide(ball, player):
            player["hp"] = max(0, player["hp"] - cfg.DAMAGE_PER_HIT)
            player["hurt_cd"] = cfg.HURT_COOLDOWN_FRAMES
            return True
    return False


# ============ 游戏核心 ============
def game_create() -> Game:
    """创建游戏对象，集中存放所有运行时数据。"""
    return {
        "state": "ready",
        "score": 0.0,
        "high_score": 0,
        "balls": [],
        "player": None,
        "hud": hud_create(),
    }


def game_start(game: Game) -> None:
    """开始一次新回合，重置弹球与玩家，同时归零得分。"""
    ball_count = random.randint(cfg.BALL_MIN, cfg.BALL_MAX)
    game["balls"] = balls_create_many(ball_count)
    game["player"] = player_create()
    game["score"] = 0.0
    game["state"] = "playing"


def game_handle_keydown(game: Game, key: int) -> None:
    """处理会影响状态的按键。"""
    if game["state"] in ("ready", "gameover") and key in (pygame.K_SPACE, pygame.K_RETURN):
        game_start(game)
        return
    if game["state"] == "playing" and key == pygame.K_p:
        game["state"] = "paused"
        return
    if game["state"] == "paused" and key == pygame.K_p:
        game["state"] = "playing"


def game_handle_event(game: Game, event: pygame.event.Event) -> bool:
    """处理单个事件。返回 False 表示需要退出游戏循环。"""
    if event.type == pygame.QUIT:
        return False
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            return False
        game_handle_keydown(game, event.key)
    return True


def game_update(game: Game, dt: float) -> None:
    """根据当前状态推进一帧游戏逻辑。"""
    if game["state"] != "playing":
        return

    balls_update_all(game["balls"])
    if game["player"] is not None:
        player_update(game["player"])
        _ = player_take_damage_if_hit(game["player"], game["balls"])

    game["score"] += dt * cfg.BASE_SCORE_PER_SEC
    if game["player"] is not None and game["player"]["hp"] <= 0:
        game["state"] = "gameover"
        game["high_score"] = max(game["high_score"], int(game["score"]))


def game_draw_entities(game: Game, screen: pygame.Surface) -> None:
    """根据状态绘制弹球与玩家。"""
    if game["state"] not in ("playing", "paused", "gameover"):
        return

    if game["balls"]:
        balls_draw_all(game["balls"], screen)
    if game["player"] is not None:
        player_draw(game["player"], screen)


def game_render(game: Game, screen: pygame.Surface) -> None:
    """完成当前帧的所有绘制工作。"""
    screen.fill(cfg.BG_COLOR)
    game_draw_entities(game, screen)
    hud_refresh(game["hud"], game)
    hud_draw(game["hud"], screen)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("躲避球 M3：状态/分数/暂停（ESC 退出）")
    screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
    clock = pygame.time.Clock()

    game = game_create()

    running = True
    while running:
        dt = clock.tick(cfg.FPS) / 1000.0

        for event in pygame.event.get():
            if not game_handle_event(game, event):
                running = False
                break

        if not running:
            break

        game_update(game, dt)
        game_render(game, screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()