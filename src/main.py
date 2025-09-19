"""
躲避球教学游戏（M5）：视觉与音效增强实现
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
Level = dict[str, Any]

BACKGROUND: pygame.Surface | None = None
SOUNDS: dict[str, pygame.mixer.Sound] = {}


# ============ 资源加载 ============


def load_graphics() -> None:
    """加载背景图片，失败时保持为 None。"""
    global BACKGROUND
    BACKGROUND = None
    path = cfg.IMAGE_BACKGROUND
    if not path.is_file():
        return
    try:
        image = pygame.image.load(str(path)).convert()
        BACKGROUND = pygame.transform.smoothscale(image, (cfg.WIDTH, cfg.HEIGHT))
    except pygame.error:
        BACKGROUND = None


def load_audio() -> None:
    """初始化混音器并加载音效资源。"""
    global SOUNDS
    SOUNDS = {}

    try:
        pygame.mixer.init()
    except pygame.error:
        return

    for name, sound_path in cfg.SOUND_FILES.items():
        if not sound_path.is_file():
            continue
        try:
            sound = pygame.mixer.Sound(str(sound_path))
            sound.set_volume(cfg.SFX_VOLUME)
        except pygame.error:
            continue
        SOUNDS[name] = sound


def play_sound(game: Game, name: str) -> None:
    """在未静音时播放指定事件的音效。"""
    sound = SOUNDS.get(name)
    if not sound or game.get("audio_muted", False):
        return
    sound.play()


def toggle_mute(game: Game) -> None:
    """切换静音标志。"""
    game["audio_muted"] = not game.get("audio_muted", False)


# ============ 球体相关 ============
def clamp(value: float, lower: float, upper: float) -> float:
    """将数值限制在给定范围内。"""
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def ball_create() -> Ball:
    """生成一个随机属性的弹球字典。"""
    radius = random.randint(cfg.R_MIN, cfg.R_MAX)
    x = random.uniform(radius, cfg.WIDTH - radius)
    y = random.uniform(radius, cfg.HEIGHT - radius)
    angle = random.uniform(0, 2 * math.pi)
    speed = random.uniform(cfg.SPEED_MIN, cfg.SPEED_MAX)
    vx = math.cos(angle) * speed
    vy = math.sin(angle) * speed
    color = random.choice(cfg.BALL_COLORS)
    return {
        "x": x,
        "y": y,
        "vx": vx,
        "vy": vy,
        "r": radius,
        "color": color,
    }


def balls_create_many(count: int) -> Balls:
    """批量创建指定数量的弹球。"""
    return [ball_create() for _ in range(count)]


def ball_update(ball: Ball) -> None:
    """推进单个弹球位置并处理边界反弹。"""
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
    """更新列表中所有弹球。"""
    for ball in balls:
        ball_update(ball)


def balls_draw_all(balls: Balls, screen: pygame.Surface) -> None:
    """在屏幕上绘制所有弹球。"""
    for ball in balls:
        pygame.draw.circle(
            screen,
            ball["color"],
            (int(ball["x"]), int(ball["y"])),
            int(ball["r"]),
        )


# ============ 难度与关卡 ============
def level_create() -> Level:
    """构造关卡管理用的基础字典。"""
    return {
        "index": 0,
        "timer": 0.0,
    }


def level_reset(level: Level) -> None:
    """将关卡信息重置为初始状态。"""
    level["index"] = 0
    level["timer"] = 0.0


def level_desired_ball_count(level: Level) -> int:
    """计算当前关卡应存在的弹球数量上限。"""
    base = cfg.LEVEL_INITIAL_BALLS
    increment = level["index"] * cfg.LEVEL_BALL_INCREMENT
    return min(base + increment, cfg.LEVEL_MAX_BALLS)


def level_apply_progression(game: Game) -> None:
    """根据关卡进度补足弹球数量。"""
    target = level_desired_ball_count(game["level"])
    current = len(game["balls"])
    to_add = target - current
    if to_add > 0:
        game["balls"].extend(balls_create_many(to_add))


def level_tick(game: Game, dt: float) -> bool:
    """累积关卡计时并在需要时升级，返回是否升级。"""
    level = game["level"]
    level["timer"] += dt
    leveled = False
    while level["timer"] >= cfg.LEVEL_INTERVAL:
        level["timer"] -= cfg.LEVEL_INTERVAL
        level["index"] += 1
        level_apply_progression(game)
        leveled = True
    return leveled


# ============ HUD ============
def hud_create(font_name: str | None = None) -> HUD:
    """初始化 HUD 状态字典与字体资源。"""
    return {
        "font_small": pygame.font.SysFont(font_name, 24),
        "font_normal": pygame.font.SysFont(font_name, 22),
        "font_big": pygame.font.SysFont(font_name, 56),
        "padding": 12,
        "player": None,
        "state": "ready",
        "score": 0,
        "high_score": 0,
        "level": None,
        "ball_count": 0,
        "muted": False,
        "level_flash_timer": 0.0,
    }


def hud_refresh(hud: HUD, game: Game) -> None:
    """从 Game 字典同步 HUD 展示数据。"""
    hud["player"] = game.get("player")
    hud["state"] = game.get("state", "ready")
    hud["score"] = int(game.get("score", 0))
    hud["high_score"] = game.get("high_score", 0)
    hud["level"] = game.get("level")
    hud["ball_count"] = len(game.get("balls") or [])
    hud["muted"] = game.get("audio_muted", False)
    hud["level_flash_timer"] = game.get("level_flash_timer", 0.0)


def hud_draw_panel(screen: pygame.Surface, x: int, y: int, w: int, h: int) -> None:
    """绘制带透明背景的 HUD 面板。"""
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((0, 0, 0, cfg.HUD_PANEL_ALPHA))
    screen.blit(panel, (x, y))


def hud_draw_hp(hud: HUD, screen: pygame.Surface) -> None:
    """绘制玩家生命值文字与血条。"""
    player = hud["player"]
    if player is None:
        return

    pad = hud["padding"]
    font = hud["font_normal"]
    text = font.render(f"HP: {player['hp']}/{player['hp_max']}", True, cfg.WHITE)
    hud_draw_panel(screen, pad, pad, 240, 60)
    screen.blit(text, (pad + 10, pad + 6))

    bar_x = pad + 10
    bar_y = pad + 30
    bar_w = 220
    bar_h = 16
    pygame.draw.rect(screen, cfg.RED, (bar_x, bar_y, bar_w, bar_h))
    if player["hp"] > 0:
        ratio = player["hp"] / player["hp_max"]
        pygame.draw.rect(screen, cfg.GREEN, (bar_x, bar_y, int(bar_w * ratio), bar_h))
    pygame.draw.rect(screen, cfg.WHITE, (bar_x, bar_y, bar_w, bar_h), 2)


def hud_draw_scores(hud: HUD, screen: pygame.Surface) -> None:
    """绘制当前分数与最高分信息。"""
    pad = hud["padding"]
    font = hud["font_normal"]
    score_text = font.render(f"Score: {hud['score']}", True, cfg.WHITE)
    best_text = font.render(f"High: {hud['high_score']}", True, cfg.WHITE)
    width = max(score_text.get_width(), best_text.get_width()) + 20
    height = score_text.get_height() + best_text.get_height() + 22
    x = cfg.WIDTH - width - pad
    y = pad
    hud_draw_panel(screen, x, y, width, height)
    screen.blit(score_text, (x + 10, y + 6))
    screen.blit(best_text, (x + 10, y + 14 + score_text.get_height()))


def hud_draw_level(hud: HUD, screen: pygame.Surface) -> None:
    """绘制关卡等级与弹球数量提示。"""
    level = hud["level"]
    if not level:
        return
    font = hud["font_normal"]
    color = cfg.LEVEL_FLASH_COLOR if hud["level_flash_timer"] > 0 else cfg.WHITE
    level_no = level.get("index", 0) + 1
    text = font.render(f"Level: {level_no}", True, color)
    balls_text = font.render(f"Balls: {hud['ball_count']}", True, color)
    screen.blit(text, text.get_rect(center=(cfg.WIDTH // 2, 24)))
    screen.blit(balls_text, balls_text.get_rect(center=(cfg.WIDTH // 2, 48)))


def hud_draw_banner(hud: HUD, screen: pygame.Surface) -> None:
    """在非 Playing 状态显示提示横幅。"""
    mapping = {
        "ready": ("READY", "Space/Enter Start · M Mute"),
        "paused": ("PAUSED", "P Pause · M Mute"),
        "gameover": ("GAME OVER", "Space/Enter Restart"),
    }
    title, tip = mapping.get(hud["state"], (None, None))
    if title is None:
        return
    big = hud["font_big"]
    small = hud["font_small"]
    title_surf = big.render(title, True, cfg.WHITE)
    tip_surf = small.render(tip, True, cfg.WHITE)
    center = (cfg.WIDTH // 2, cfg.HEIGHT // 2)
    screen.blit(title_surf, title_surf.get_rect(center=center))
    screen.blit(tip_surf, tip_surf.get_rect(center=(center[0], center[1] + 48)))


def hud_draw_sound_state(hud: HUD, screen: pygame.Surface) -> None:
    """绘制当前声音开关提示。"""
    pad = hud["padding"]
    font = hud["font_small"]
    text = "Sound: OFF" if hud["muted"] else "Sound: ON"
    surf = font.render(text, True, cfg.WHITE)
    hud_draw_panel(screen, pad, cfg.HEIGHT - surf.get_height() - pad - 8, surf.get_width() + 16, surf.get_height() + 12)
    screen.blit(surf, (pad + 8, cfg.HEIGHT - surf.get_height() - pad))


def hud_draw(hud: HUD, screen: pygame.Surface) -> None:
    """汇总调用各 HUD 绘制函数。"""
    hud_draw_hp(hud, screen)
    hud_draw_scores(hud, screen)
    hud_draw_level(hud, screen)
    hud_draw_banner(hud, screen)
    hud_draw_sound_state(hud, screen)


# ============ 玩家相关 ============
def player_create() -> Player:
    """创建玩家初始状态字典。"""
    size = cfg.PLAYER_SIZE
    return {
        "x": cfg.WIDTH / 2,
        "y": cfg.HEIGHT / 2,
        "w": size,
        "h": size,
        "speed": cfg.PLAYER_SPEED,
        "hp": cfg.PLAYER_HP_MAX,
        "hp_max": cfg.PLAYER_HP_MAX,
        "hurt_cd": 0,
    }


def player_handle_move_input() -> tuple[int, int]:
    """读取键盘方向输入并返回移动向量。"""
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
    """根据输入更新玩家位置与无敌计时。"""
    dx, dy = player_handle_move_input()
    norm = math.sqrt(2) if dx and dy else 1
    speed = player["speed"] * (cfg.INVINCIBLE_SPEED_MULT if player["hurt_cd"] > 0 else 1)
    player["x"] += (speed * dx) / norm
    player["y"] += (speed * dy) / norm

    half_w = player["w"] / 2
    half_h = player["h"] / 2
    player["x"] = clamp(player["x"], half_w, cfg.WIDTH - half_w)
    player["y"] = clamp(player["y"], half_h, cfg.HEIGHT - half_h)

    if player["hurt_cd"] > 0:
        player["hurt_cd"] -= 1


def player_draw(player: Player, screen: pygame.Surface) -> None:
    """使用矩形绘制玩家角色。"""
    half_w = player["w"] / 2
    half_h = player["h"] / 2
    rect = pygame.Rect(
        int(player["x"] - half_w),
        int(player["y"] - half_h),
        int(player["w"]),
        int(player["h"]),
    )
    color = cfg.PLAYER_HURT_COLOR if player["hurt_cd"] > 0 else cfg.PLAYER_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=6)


def circle_rect_collide(ball: Ball, player: Player) -> bool:
    """检测弹球与玩家矩形是否发生碰撞。"""
    cx, cy, radius = ball["x"], ball["y"], ball["r"]
    half_w = player["w"] / 2
    half_h = player["h"] / 2
    left = player["x"] - half_w
    right = player["x"] + half_w
    top = player["y"] - half_h
    bottom = player["y"] + half_h
    nearest_x = clamp(cx, left, right)
    nearest_y = clamp(cy, top, bottom)
    dx = cx - nearest_x
    dy = cy - nearest_y
    return dx * dx + dy * dy <= radius * radius


def player_take_damage_if_hit(player: Player, balls: Balls) -> bool:
    """若检测到碰撞则为玩家扣血并设置冷却。"""
    if player["hurt_cd"] > 0 or player["hp"] <= 0:
        return False
    for ball in balls:
        if circle_rect_collide(ball, player):
            player["hp"] = max(0, player["hp"] - cfg.DAMAGE_PER_HIT)
            player["hurt_cd"] = cfg.HURT_COOLDOWN_FRAMES
            return True
    return False


# ============ 游戏逻辑 ============
def game_create() -> Game:
    """构建游戏主状态字典的初始值。"""
    return {
        "state": "ready",
        "score": 0.0,
        "high_score": 0,
        "balls": [],
        "player": None,
        "hud": hud_create(),
        "level": level_create(),
        "audio_muted": False,
        "level_flash_timer": 0.0,
    }


def game_start(game: Game) -> None:
    """开始一局游戏并重置相关状态。"""
    level_reset(game["level"])
    game["balls"] = balls_create_many(level_desired_ball_count(game["level"]))
    game["player"] = player_create()
    game["score"] = 0.0
    game["state"] = "playing"
    game["level_flash_timer"] = 0.0
    play_sound(game, "start")


def game_handle_keydown(game: Game, key: int) -> None:
    """处理影响游戏状态与静音的按键。"""
    if key == pygame.K_m:
        toggle_mute(game)
        return
    if game["state"] in ("ready", "gameover") and key in (pygame.K_SPACE, pygame.K_RETURN):
        game_start(game)
        return
    if game["state"] == "playing" and key == pygame.K_p:
        game["state"] = "paused"
        return
    if game["state"] == "paused" and key == pygame.K_p:
        game["state"] = "playing"


def game_handle_event(game: Game, event: pygame.event.Event) -> bool:
    """统一处理事件队列并判断是否退出。"""
    if event.type == pygame.QUIT:
        return False
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            return False
        game_handle_keydown(game, event.key)
    return True


def game_update(game: Game, dt: float) -> None:
    """在 Playing 状态推进一帧游戏逻辑。"""
    if game["state"] != "playing":
        return

    leveled = level_tick(game, dt)
    if leveled:
        game["level_flash_timer"] = 1.5
        play_sound(game, "levelup")

    balls_update_all(game["balls"])
    player = game["player"]
    if player is not None:
        player_update(player)
        if player_take_damage_if_hit(player, game["balls"]):
            play_sound(game, "hit")

    level = game["level"]
    score_rate = cfg.BASE_SCORE_PER_SEC + level["index"] * cfg.LEVEL_BONUS_PER_LEVEL
    game["score"] += dt * score_rate
    game["high_score"] = max(game["high_score"], int(game["score"]))

    if player is not None and player["hp"] <= 0 and game["state"] != "gameover":
        game["state"] = "gameover"
        play_sound(game, "gameover")

    if game["level_flash_timer"] > 0:
        game["level_flash_timer"] = max(0.0, game["level_flash_timer"] - dt)


def game_draw_entities(game: Game, screen: pygame.Surface) -> None:
    """按需绘制弹球与玩家。"""
    if game["state"] not in ("playing", "paused", "gameover"):
        return
    if game["balls"]:
        balls_draw_all(game["balls"], screen)
    if game["player"] is not None:
        player_draw(game["player"], screen)


def render_background(screen: pygame.Surface) -> None:
    """绘制背景图或备用底色。"""
    if BACKGROUND:
        screen.blit(BACKGROUND, (0, 0))
    else:
        screen.fill(cfg.BG_COLOR)


def game_render(game: Game, screen: pygame.Surface) -> None:
    """执行完整一帧的渲染流程。"""
    render_background(screen)
    game_draw_entities(game, screen)
    hud_refresh(game["hud"], game)
    hud_draw(game["hud"], screen)


def main() -> None:
    """程序入口：初始化资源并运行主循环。"""
    pygame.init()
    screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT))
    pygame.display.set_caption("躲避球 M5：视觉与音效增强（ESC 退出）")

    load_graphics()
    load_audio()

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
