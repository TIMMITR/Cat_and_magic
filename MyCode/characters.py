import pygame
from constants import *
from pathfinding import bfs


class Character(pygame.sprite.Sprite):
    """Базовый класс для персонажей (игрок, враги)."""
    def __init__(self, x: int, y: int,
                 *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.image_size = (TILE_SIZE, TILE_SIZE)
        self.image = pygame.Surface(self.image_size)
        self.rect = self.image.get_rect(topleft=(x, y))

    def is_alive(self) -> bool:
        return getattr(self, "health", 0) > 0


class Player(Character):
    def __init__(self, x: int, y: int,
                 *groups: pygame.sprite.Group) -> None:
        super().__init__(x, y, *groups)

        # Idle-кадры (когда стоит)
        self.idle_frames = {
            'down':   pygame.image.load('../Images/Player/Player_d1.png').convert_alpha(),
            'up':     pygame.image.load('../Images/Player/Player_u1.png').convert_alpha(),
            'left':   pygame.image.load('../Images/Player/Player_l1.png').convert_alpha(),
            'right':  pygame.image.load('../Images/Player/Player_r1.png').convert_alpha()
        }

        # Ходьба: по 8 кадров в каждом направлении
        self.walk_frames = {
            'down': [
                pygame.image.load(f'../Images/Player/Player_rd/Player_rd_0{i}.png').convert_alpha()
                for i in range(8)
            ],
            'up': [
                pygame.image.load(f'../Images/Player/Player_ru/Player_ru_0{i}.png').convert_alpha()
                for i in range(8)
            ],
            'left': [
                pygame.image.load(f'../Images/Player/Player_rl/Player_rl_0{i}.png').convert_alpha()
                for i in range(8)
            ],
            'right': [
                pygame.image.load(f'../Images/Player/Player_rr/Player_rr_0{i}.png').convert_alpha()
                for i in range(8)
            ],
        }

        self.size = (TILE_SIZE, TILE_SIZE)

        # Текущее состояние анимации
        self.direction = 'down'
        self.is_moving = False
        self.walk_frame_index = 0
        self.walk_frame_timer = 0
        self.walk_frame_delay = 1

        # Текущее изображение (idle)
        self.image = pygame.transform.scale(self.idle_frames[self.direction],
                                            self.size)
        self.rect = self.image.get_rect(topleft=(x, y))

        self.health = HEALTH
        self.angle = 180  # смотрит вниз
        self.projectiles = pygame.sprite.Group()

    def update(self, event: pygame.event.Event, board, set_element: list[str], enemy=None) -> bool:
        if not self.is_alive():
            self.kill()
            return False

        moved = False
        if event.type == pygame.KEYUP:
            moved = self.handle_keys(event, board,
                                     set_element, enemy)

        self.animate()
        return moved

    def handle_keys(self, event, board, set_element: list[str,], enemy) -> bool:
        """Обработка перемещений игрока + применение заклинаний."""
        moved = False
        ex, ey = (-1, -1)
        if enemy and enemy.is_alive():
            ex, ey = (enemy.rect.x // TILE_SIZE, enemy.rect.y // TILE_SIZE)

        if event.key == pygame.K_w:
            nx = self.rect.x // TILE_SIZE
            ny = (self.rect.y - TILE_SIZE) // TILE_SIZE
            if (nx, ny) != (ex, ey):
                if 0 <= nx < MAP_SIZE[0] and 0 <= ny < MAP_SIZE[1]:
                    if board.map_data[ny][nx] in IS_PASSABLE:
                        self.rect.y -= TILE_SIZE
                        self.angle = 0
                        self.direction = 'up'
                        self.is_moving = True
                        moved = True

        elif event.key == pygame.K_s:
            nx = self.rect.x // TILE_SIZE
            ny = (self.rect.y + TILE_SIZE) // TILE_SIZE
            if (nx, ny) != (ex, ey):
                if 0 <= nx < MAP_SIZE[0] and 0 <= ny < MAP_SIZE[1]:
                    if board.map_data[ny][nx] in IS_PASSABLE:
                        self.rect.y += TILE_SIZE
                        self.angle = 180
                        self.direction = 'down'
                        self.is_moving = True
                        moved = True

        elif event.key == pygame.K_a:
            nx = (self.rect.x - TILE_SIZE) // TILE_SIZE
            ny = self.rect.y // TILE_SIZE
            if (nx, ny) != (ex, ey):
                if 0 <= nx < MAP_SIZE[0] and 0 <= ny < MAP_SIZE[1]:
                    if board.map_data[ny][nx] in IS_PASSABLE:
                        self.rect.x -= TILE_SIZE
                        self.angle = 90
                        self.direction = 'left'
                        self.is_moving = True
                        moved = True

        elif event.key == pygame.K_d:
            nx = (self.rect.x + TILE_SIZE) // TILE_SIZE
            ny = self.rect.y // TILE_SIZE
            if (nx, ny) != (ex, ey):
                if 0 <= nx < MAP_SIZE[0] and 0 <= ny < MAP_SIZE[1]:
                    if board.map_data[ny][nx] in IS_PASSABLE:
                        self.rect.x += TILE_SIZE
                        self.angle = 270
                        self.direction = 'right'
                        self.is_moving = True
                        moved = True

        elif event.key == pygame.K_SPACE:
            # Применение стихий
            elements = board.spell_class(set_element, self.angle, self.rect.x, self.rect.y,
                                         board, self, enemy)
            elements.set_elements()
            moved = True

        elif event.key == pygame.K_q:
            # Поворот на 90° влево
            self.angle = (self.angle + 90) % 360
            self.update_direction_by_angle()

        elif event.key == pygame.K_e:
            # Поворот на 90° вправо
            self.angle = (self.angle + 270) % 360
            self.update_direction_by_angle()

        # Если игрок двигался, проверяем, не встал ли он на магму
        if moved:
            self.check_magma_damage(board)

        return moved

    def update_direction_by_angle(self) -> None:
        if self.angle == 0:
            self.direction = 'up'
        elif self.angle == 180:
            self.direction = 'down'
        elif self.angle == 90:
            self.direction = 'left'
        elif self.angle == 270:
            self.direction = 'right'

    def check_magma_damage(self, board) -> None:
        tx = self.rect.x // TILE_SIZE
        ty = self.rect.y // TILE_SIZE
        if 0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]:
            if board.map_data[ty][tx] == 7:  # код магмы
                if self.is_alive():
                    self.health -= 5
                    print(f"Player Health: {self.health}")

    def animate(self) -> None:
        if self.is_moving:
            self.walk_frame_timer += 1
            if self.walk_frame_timer >= self.walk_frame_delay:
                self.walk_frame_timer = 0
                self.walk_frame_index = (self.walk_frame_index + 1) % len(self.walk_frames[self.direction])

            cur_frame = self.walk_frames[self.direction][self.walk_frame_index]
            self.image = pygame.transform.scale(cur_frame, self.size)

            # Прекращаем анимацию после полной "прокрутки"
            if self.walk_frame_index == 7:
                self.is_moving = False
                self.walk_frame_index = 0
        else:
            # Idle
            idle_surface = self.idle_frames[self.direction]
            self.image = pygame.transform.scale(idle_surface, self.size)

        center = self.rect.center
        self.rect = self.image.get_rect(center=center)


class Enemy(Character):
    """Базовый класс врага."""
    def __init__(self, x: int, y: int,
                 *groups: pygame.sprite.Group) -> None:
        super().__init__(x, y, *groups)
        self.health = 50
        self.damage = 10

    def update(self, player, board) -> None:
        if not self.is_alive():
            self.kill()
            return

        ex, ey = (self.rect.x // TILE_SIZE, self.rect.y // TILE_SIZE)
        px, py = (player.rect.x // TILE_SIZE, player.rect.y // TILE_SIZE)

        # Собираем заблокированные клетки
        # 1) Клетка, где стоит игрок (чтобы не сливаться с ним)
        blocked = set()
        if (ex, ey) != (px, py):
            blocked.add((px, py))

        # 2) Клетки, где стоят ДРУГИЕ враги (кроме нас самих)
        for other_enemy in board.enemies:
            if other_enemy is not self and other_enemy.is_alive():
                ox = other_enemy.rect.x // TILE_SIZE
                oy = other_enemy.rect.y // TILE_SIZE
                # Если это не мы сами
                if (ox, oy) != (ex, ey):
                    blocked.add((ox, oy))

        path = bfs((ex, ey), (px, py), board.map_data, blocked)
        if path and len(path) > 1:
            nx, ny = path[1]
            if (nx, ny) != (px, py):
                self.rect.x = nx * TILE_SIZE
                self.rect.y = ny * TILE_SIZE

        # Если вплотную, атакуем
        if abs(ex - px) + abs(ey - py) == 1:
            self.attack(player)

        self.check_magma_damage(board)

    def check_magma_damage(self, board) -> None:
        tx = self.rect.x // TILE_SIZE
        ty = self.rect.y // TILE_SIZE
        if 0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]:
            if board.map_data[ty][tx] == 7:  # магма
                if self.is_alive():
                    self.health -= 5
                    print(f"Enemy Health: {self.health}")

    def attack(self, player) -> None:
        if player.is_alive():
            player.health -= self.damage
            print(f"Player Health: {player.health}")

    def push_back(self, dx: int, dy: int, board) -> None:
        """Отталкиваем врага на 3 клетки."""
        ex = self.rect.x // TILE_SIZE
        ey = self.rect.y // TILE_SIZE
        new_x = ex + dx * 3
        new_y = ey + dy * 3
        if 0 <= new_x < MAP_SIZE[0] and 0 <= new_y < MAP_SIZE[1]:
            if board.map_data[new_y][new_x] in IS_PASSABLE:
                self.rect.x = new_x * TILE_SIZE
                self.rect.y = new_y * TILE_SIZE


class WeakEnemy(Enemy):
    def __init__(self, x: int, y: int,
                 *groups: pygame.sprite.Group) -> None:
        super().__init__(x, y, *groups)
        self.health = WEAK_ENEMY_HEALTH
        self.damage = WEAK_ENEMY_DAMAGE
        self.image.fill(WEAK_ENEMY_COLOR)


class StrongEnemy(Enemy):
    def __init__(self, x: int, y: int,
                 *groups: pygame.sprite.Group) -> None:
        super().__init__(x, y, *groups)
        self.health = STRONG_ENEMY_HEALTH
        self.damage = STRONG_ENEMY_DAMAGE
        self.image.fill(STRONG_ENEMY_COLOR)