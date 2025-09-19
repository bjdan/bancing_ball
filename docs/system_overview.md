# 躲避球教学游戏：结构概览（M5）

本页集中描述 `src/main.py` 中核心数据的组成方式与状态切换流程，便于教学时解释代码结构。代码仍使用字典 + 函数的组合方式，不引入类。

## 核心数据关系
```
Game ---> Player 
  |
  + ---*> Ball
  |
  +-----> HUD 
  |
  +-----> Level
```


- **Game（游戏总字典）**
  - `state`: 当前状态，取值 `ready / playing / paused / gameover`
  - `score` / `high_score`: 当前分数与最高分
  - `balls`: 弹球列表（`Ball` 字典）
  - `player`: 玩家字典（`Player`）
  - `hud`: HUD 状态（`HUD` 字典，记录字体与界面缓存）
  - `level`: 难度数据（`Level` 字典）
  - `audio_muted`: 是否静音
  - `level_flash_timer`: 升级后的 HUD 高亮计时

- **Ball（弹球）**
  - `x, y`: 位置（浮点）
  - `vx, vy`: 速度（浮点，包含方向）
  - `r`: 半径
  - `color`: 绘制颜色

- **Player（玩家）**
  - `x, y`: 中心位置
  - `w, h`: 方块宽高
  - `speed`: 移动速度
  - `hp` / `hp_max`: 当前生命与上限
  - `hurt_cd`: 受伤后的无敌（冷却帧数）

- **Level（关卡）**
  - `index`: 当前关卡等级（从 0 开始）
  - `timer`: 生存时间累计；每累积 `LEVEL_INTERVAL` 触发升级

- **HUD（界面）**
  - 缓存字体、面板偏移量等信息
  - `player / score / level / ball_count / muted`: 每帧刷新时同步自 `Game`

## 状态切换

```
READY ---Space/Enter-->  PLAYING  --P-->  PAUSED
                         ^   |  ^              |
                         |   |  |              |
               Space/Enter   |  +------P-------+
                         |   |
                         |   HP <= 0
                         |   v
                         GAMEOVER
```

- `READY`：显示操作提示，等待 Space/Enter 开局
- `PLAYING`：更新弹球、玩家、分数和关卡；`M` 键切换静音
- `PAUSED`：暂停逻辑更新，仅保留渲染，`P` 恢复
- `GAMEOVER`：玩家生命耗尽时进入，可立即按 Space/Enter 重开

## 更新循环分工

1. **事件处理**：`game_handle_event`（监听退出、状态切换、静音）
2. **逻辑推进**：`game_update`
   - `level_tick` 处理升级、补充弹球
   - `player_update` 读取输入与移动
   - `player_take_damage_if_hit` 判断碰撞与扣血
   - 依据状态播放音效，并刷新分数
3. **绘制阶段**：`game_render`
   - `render_background` 先绘制背景图片（若缺失则填充备用颜色）
  - `game_draw_entities` 画出弹球与玩家
   - `hud_refresh` + `hud_draw` 更新界面（生命、分数、关卡、静音提示）

## 音频与资源

- 初始化顺序：先创建窗口，再调用 `load_graphics` 和 `init_audio`/`load_audio`
- 音效字典 `SOUNDS` 缓存 `hit`, `levelup`, `start`, `gameover`
- `MUSIC_READY` 标记背景音乐是否成功加载；`ensure_music` 在状态变更（开局、解除静音）时保持播放
- 静音开关：`toggle_mute` 更新 `audio_muted`，暂停或恢复 `pygame.mixer.music`

> 若需要恢复旧版“顶部注释”，可直接参考本页内容或将 ASCII 图复制回 `main.py`。
