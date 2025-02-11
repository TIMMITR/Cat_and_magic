import pygame
import random
from pytmx.util_pygame import load_pygame
from collections import deque

# Параметры экрана
FPS = 60
SIZE = WIDTH, HEIGHT = (720, 480)

# Цвета (могут понадобиться для отдельных операций)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
BROWN = (70, 40, 0)
ORANGE = (255, 165, 0)
GREY = (128, 128, 128)
CYAN = (0, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Здоровье игрока и урон
HEALTH = 100
ENEMY_DAMAGE = 10

# Параметры врагов
WEAK_ENEMY_HEALTH = 100
WEAK_ENEMY_DAMAGE = 10
WEAK_ENEMY_COLOR = (0, 100, 255)

STRONG_ENEMY_HEALTH = 150
STRONG_ENEMY_DAMAGE = 15
STRONG_ENEMY_COLOR = (255, 50, 50)

# Размер карты в тайлах
TILE_SIZE = 32
MAPS = ['../Maps/name_tmx/map1.tmx', '../Maps/name_tmx/map3.tmx',
             '../Maps/name_tmx/map4.tmx', '../Maps/name_tmx/map5.tmx']
MAP = random.choice(MAPS)
if MAP == '../Maps/name_tmx/map1.tmx' or MAP == '../Maps/name_tmx/map3.tmx':
    MAP_SIZE = (30, 25)
elif MAP == '../Maps/name_tmx/map4.tmx' or MAP == '../Maps/name_tmx/map5.tmx':
    MAP_SIZE = (50, 35)
else:
    MAP_SIZE = (100, 100)
MAP_WIDTH = MAP_SIZE[0] * TILE_SIZE
MAP_HEIGHT = MAP_SIZE[1] * TILE_SIZE

# Какие коды считаются проходимыми
IS_PASSABLE = [0, 1, 2, 7]

# -----

class Camera:
    def __init__(self, width: int, height: int) -> None:
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.camera_rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def apply(self, entity: pygame.sprite.Sprite) -> pygame.Rect:
        return entity.rect.move(self.camera_rect.topleft)

    def update(self, target: pygame.sprite.Sprite) -> None:
        self.x = -target.rect.centerx + WIDTH // 2
        self.y = -target.rect.centery + HEIGHT // 2

        # Границы
        self.x = min(0, self.x)  # слева
        self.y = min(0, self.y)  # сверху
        self.x = max(-(self.width - WIDTH), self.x)   # справа
        self.y = max(-(self.height - HEIGHT), self.y) # снизу

        self.camera_rect = pygame.Rect(self.x, self.y, self.width, self.height)

# -----

class Tile(pygame.sprite.Sprite):
    """Простой спрайт тайла."""
    def __init__(self, pos: tuple[int, int], surf: pygame.Surface,
                 group: pygame.sprite.Group) -> None:
        super().__init__(group)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

# -----

class Board:
    def __init__(self, screen: pygame.Surface, camera: Camera) -> None:
        self.screen = screen
        self.camera = camera

        self.tmx_data = load_pygame(MAP)

        # Размер карты в пикселях
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT

        # Группы для отрисовки
        self.tile_group = pygame.sprite.Group()    # все тайлы
        self.entity_group = pygame.sprite.Group()  # игрок, враги, снаряды

        # Данные карты (коды тайлов)
        self.map_data = [[0 for _ in range(MAP_SIZE[0])] for _ in range(MAP_SIZE[1])]
        # Спрайты-тайлы
        self.sprite_map = [[None for _ in range(MAP_SIZE[0])] for _ in range(MAP_SIZE[1])]

        # В будущем сохраним игрока и список врагов
        self.player = None
        self.enemies = []

        # Для случайного выбора одного из нескольких тайлов
        self.random_number = 1

        # Для разных фрагментов сожжённого дерева
        self.tree_images = {
            ('top', 'left'):   pygame.image.load("../Images/full_tree/Top_left_tree.png").convert_alpha(),
            ('top', 'right'):  pygame.image.load("../Images/full_tree/Top_right_tree.png").convert_alpha(),
            ('mid', 'left'):   pygame.image.load("../Images/full_tree/Middle_left_tree.png").convert_alpha(),
            ('mid', 'right'):  pygame.image.load("../Images/full_tree/Middle_right_tree.png").convert_alpha(),
            ('btm', 'left'):   pygame.image.load("../Images/full_tree/Bottom_left_tree.png").convert_alpha(),
            ('btm', 'right'):  pygame.image.load("../Images/full_tree/Bottom_right_tree.png").convert_alpha(),
        }

        # Для разных фрагментов сожжённого дерева
        self.fire_tree_images = {
            ('top', 'left'):   pygame.image.load("../Images/full_fire_tree/Top_left_fire_tree.png").convert_alpha(),
            ('top', 'right'):  pygame.image.load("../Images/full_fire_tree/Top_right_fire_tree.png").convert_alpha(),
            ('mid', 'left'):   pygame.image.load("../Images/full_fire_tree/Middle_left_fire_tree.png").convert_alpha(),
            ('mid', 'right'):  pygame.image.load("../Images/full_fire_tree/Middle_right_fire_tree.png").convert_alpha(),
            ('btm', 'left'):   pygame.image.load("../Images/full_fire_tree/Bottom_left_fire_tree.png").convert_alpha(),
            ('btm', 'right'):  pygame.image.load("../Images/full_fire_tree/Bottom_right_fire_tree.png").convert_alpha(),
        }

        # Для остальных тайлов
        self.tile_surfaces = {
            0: pygame.image.load(f"../Images/ground/ground{self.random_number}.png").convert_alpha(),
            1: pygame.image.load("../Images/ground/fire_ground.png").convert_alpha(),
            2: pygame.image.load("../Images/ground/water_ground.png").convert_alpha(),
            5: pygame.image.load(f"../Images/main_pngs/rock{self.random_number}.png").convert_alpha(),
            6: pygame.image.load("../Images/main_pngs/water.png").convert_alpha(),
            7: pygame.image.load("../Images/main_pngs/magma.png").convert_alpha(),
            # 3 и 4 будут подставляться динамически
        }

        self.draw_map()

    def draw_map(self) -> None:
        # Задаём порядок слоёв

        for layer in self.tmx_data.visible_layers:
            for x, y, surf in layer.tiles():
                pos = (x * TILE_SIZE, y * TILE_SIZE)

                # Определим код тайла
                if layer.name == 'Ground':
                    tile_code = 0
                elif layer.name == 'Fire_ground':
                    tile_code = 1
                elif layer.name == 'Water_ground':
                    tile_code = 2
                elif layer.name == 'Tree':
                    tile_code = 3
                elif layer.name == 'Fire_tree':
                    tile_code = 4
                elif layer.name == 'Rock':
                    tile_code = 5
                elif layer.name == 'Water':
                    tile_code = 6
                elif layer.name == 'Magma':
                    tile_code = 7
                else:
                    tile_code = 0

                self.map_data[y][x] = tile_code

                tile = Tile(pos, surf, self.tile_group)
                self.sprite_map[y][x] = tile

        # Обработка объектов для спавна игрока и врагов
        for obj in self.tmx_data.objects:
            if obj.type == 'Shape':
                if obj.name == 'Spawn_player':
                    self.player = Player(int(obj.x), int(obj.y), self.entity_group)
                elif obj.name == 'Spawn_enemy':
                    enemy = WeakEnemy(int(obj.x), int(obj.y), self.entity_group)
                    self.enemies.append(enemy)
                elif obj.name == 'StrongEnemy':
                    enemy = StrongEnemy(int(obj.x), int(obj.y), self.entity_group)
                    self.enemies.append(enemy)

    def change_tree_part(self, tx: int, ty: int, part: str, to_fire: bool) -> None:
        # Меняет одну часть дерева на сожжённое или обратно в зависимости от to_fire.
        # Возможные части дерева: 'top', 'mid', 'btm'
        parts = ['left', 'right']  # Каждая часть дерева имеет левую и правую сторону
        parts2 = ['top', 'mid', 'btm']

        # Выбираем нужные изображения для сожжённого или обычного дерева
        image_dict = self.fire_tree_images if to_fire else self.tree_images

        for side in parts:
            for part1 in parts2:
                # Берём правильный спрайт
                part_image = image_dict.get((part, side, part1))

                if part_image is not None:
                    # Устанавливаем новое изображение на соответствующий тайл
                    self.set_tile(tx, ty, 4 if to_fire else 3)

                    # Применяем новый спрайт
                    tile_surf = part_image
                    self.sprite_map[ty][tx] = Tile((tx * TILE_SIZE, ty * TILE_SIZE), tile_surf, self.tile_group)

    def get_tile_surface(self, code: int) -> pygame.Surface:
        """
        Возвращает нужный Surface для тайла с кодом code.
        Если это дерево (3) или сожжённое дерево (4), выбираем кусок
        (top/mid/bottom; left/right) исходя из координат.
        """
        if code == 0:
            self.random_number = random.choice((1, 2))
        elif code == 5:
            self.random_number = random.choice((1, 2, 3, 4))
            # Остальные коды
        if code == 3:
            return self.tree_images[('top', 'left')]  # Поставьте нужный tile в зависимости от позиции
        elif code == 4:
            return self.fire_tree_images[('top', 'left')]
        return self.tile_surfaces[code]

    def set_tile(self, tile_x: int, tile_y: int, tile_type: int) -> None:
        """
        Меняет тайл на карте в (tile_x, tile_y) на тип tile_type
        и перерисовывает его спрайт. (Если нужно заменить одиночный тайл.)
        """
        if not (0 <= tile_x < MAP_SIZE[0] and 0 <= tile_y < MAP_SIZE[1]):
            return

        old_sprite = self.sprite_map[tile_y][tile_x]
        if self.map_data[tile_y][tile_x] in (0, 1, 2):
            pass
        else:
            old_sprite.kill()

        self.map_data[tile_y][tile_x] = tile_type

        pos_px = (tile_x * TILE_SIZE, tile_y * TILE_SIZE)
        new_surf = self.get_tile_surface(tile_type)

        new_sprite = Tile(pos_px, new_surf, self.tile_group)
        self.sprite_map[tile_y][tile_x] = new_sprite

    def draw(self) -> None:
        # Сначала рисуем все тайлы
        for sprite in self.tile_group:
            self.screen.blit(sprite.image,
                             self.camera.apply(sprite))

        # Затем рисуем все объекты (игрок, враги, снаряды и т.д.)
        for sprite in self.entity_group:
            self.screen.blit(sprite.image,
                             self.camera.apply(sprite))

# -----

class Character(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int,
                 *groups: pygame.sprite.Group) -> None:
        super().__init__(*groups)
        self.image_size = (TILE_SIZE, TILE_SIZE)
        self.image = pygame.Surface(self.image_size)
        self.rect = self.image.get_rect(topleft=(x, y))

    def is_alive(self) -> bool:
        return getattr(self, "health", 0) > 0

# -----

class Player(Character):
    def __init__(self, x: int, y: int,
                 *groups: pygame.sprite.Group) -> None:
        super().__init__(x, y, *groups)

        # Idle-кадры (когда игрок стоит)
        self.idle_frames = {
            'down': pygame.image.load('../Images/Player/Player_d1.png').convert_alpha(),
            'up':   pygame.image.load('../Images/Player/Player_u1.png').convert_alpha(),
            'left': pygame.image.load('../Images/Player/Player_l1.png').convert_alpha(),
            'right':pygame.image.load('../Images/Player/Player_r1.png').convert_alpha()
        }

        # Ходьба: по 8 кадров на направление
        self.walk_frames = {
            'down':   [pygame.image.load(f'../Images/Player/Player_rd/Player_rd_0{str(i)}.png').convert_alpha()
                      for i in range(8)],
            'up':     [pygame.image.load(f'../Images/Player/Player_ru/Player_ru_0{str(i)}.png').convert_alpha()
                      for i in range(8)],
            'left':   [pygame.image.load(f'../Images/Player/Player_rl/Player_rl_0{str(i)}.png').convert_alpha()
                      for i in range(8)],
            'right':  [pygame.image.load(f'../Images/Player/Player_rr/Player_rr_0{str(i)}.png').convert_alpha()
                      for i in range(8)],
        }

        self.size = (TILE_SIZE, TILE_SIZE)

        # Текущее состояние анимации
        self.direction = 'down'  # down / up / left / right
        self.is_moving = False   # движется ли сейчас
        self.walk_frame_index = 0
        self.walk_frame_timer = 0
        self.walk_frame_delay = 1  # скорость пролистывания кадров
                                   # (чем больше, тем медленней анимация)

        # Текущее изображение (сразу idle)
        self.image = pygame.transform.scale(self.idle_frames[self.direction],
                                            self.size)
        self.rect = self.image.get_rect(topleft=(x, y))

        self.projectiles = pygame.sprite.Group()
        self.health = HEALTH
        self.angle = 180  # по умолчанию смотрит вниз

    def update(self, event: pygame.event.Event, board: Board,
               set_element: list[str], enemy: "Enemy" = None) -> bool:
        if not self.is_alive():
            self.kill()
            return False

        moved = False
        if event.type == pygame.KEYUP:
            # При отпускании WASD – делаем шаг
            moved = self.handle_keys(event, board,
                                     set_element, enemy)

        # Обновляем анимацию (даже если не было новых событий)
        self.animate()

        return moved

    def handle_keys(self, event: "key", board: Board,
                    set_element: list[str,], enemy: "Enemy") -> bool:
        """
        Обработка нажатых клавиш, сама логика движения, применения заклинаний.
        Выделена, чтобы не перегружать update().
        """
        moved = False
        # Координаты врага (если есть)
        e_x, e_y = (-1, -1)
        if enemy and enemy.is_alive():
            e_x, e_y = (enemy.rect.x // TILE_SIZE, enemy.rect.y // TILE_SIZE)

        if event.key == pygame.K_w:
            nx = self.rect.x // TILE_SIZE
            ny = (self.rect.y - TILE_SIZE) // TILE_SIZE
            if (nx, ny) != (e_x, e_y):
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
            if (nx, ny) != (e_x, e_y):
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
            if (nx, ny) != (e_x, e_y):
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
            if (nx, ny) != (e_x, e_y):
                if 0 <= nx < MAP_SIZE[0] and 0 <= ny < MAP_SIZE[1]:
                    if board.map_data[ny][nx] in IS_PASSABLE:
                        self.rect.x += TILE_SIZE
                        self.angle = 270
                        self.direction = 'right'
                        self.is_moving = True
                        moved = True

        elif event.key == pygame.K_SPACE:
            # Применяем стихию
            elements = Elements(set_element, self.angle, self.rect.x, self.rect.y,
                                board, self, enemy)
            elements.set_elements()
            moved = True

        elif event.key == pygame.K_q:
            # Поворот на 90° влево (без движения)
            self.angle = (self.angle + 90) % 360
            self.update_direction_by_angle()

        elif event.key == pygame.K_e:
            # Поворот на 90° вправо (без движения)
            self.angle = (self.angle + 270) % 360
            self.update_direction_by_angle()

        # Если сходили/сделали действие, проверяем урон от магмы
        if moved:
            self.check_magma_damage(board)

        return moved

    def update_direction_by_angle(self):
    # Нужно просто синхронизовать angle с self.direction
        if self.angle == 0:
            self.direction = 'up'
        elif self.angle == 180:
            self.direction = 'down'
        elif self.angle == 90:
            self.direction = 'left'
        elif self.angle == 270:
            self.direction = 'right'

    def check_magma_damage(self, board: Board) -> None:
        tx = self.rect.x // TILE_SIZE
        ty = self.rect.y // TILE_SIZE
        if 0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]:
            if board.map_data[ty][tx] == 7:  # magma
                if self.is_alive():
                    self.health -= 5
                    print(f"Player Health: {self.health}")

    def animate(self):
        """
        Вызывается каждый кадр (FPS раз в секунду).
        Крутит анимацию, если self.is_moving == True,
        иначе показывает idle-кадр.
        """
        if self.is_moving:
            self.walk_frame_timer += 1
            if self.walk_frame_timer >= self.walk_frame_delay:
                self.walk_frame_timer = 0
                self.walk_frame_index = (self.walk_frame_index + 1) % len(self.walk_frames[self.direction])

            # Берём текущий кадр анимации
            cur_frame = self.walk_frames[self.direction][self.walk_frame_index]
            self.image = pygame.transform.scale(cur_frame, self.size)

            # анимацию закончим и вернёмся в idle
            if self.walk_frame_index == 7:  # последний кадр цикла
                # Можно либо зациклить дальше, либо остановиться
                self.is_moving = False
                self.walk_frame_index = 0

        else:
            # Idle-спрайт
            idle_surface = self.idle_frames[self.direction]
            self.image = pygame.transform.scale(idle_surface, self.size)

        # Чтобы прямоугольник не "скакал", фиксим центр
        center = self.rect.center
        self.rect = self.image.get_rect(center=center)
# -----

def bfs(start: tuple[int, int], goal: tuple[int, int],
        map_data: list[list[int]], blocked = None) -> list[tuple[int, int]]|None:
    if blocked is None:
        blocked = set()

    if start == goal:
        return [start]

    queue = deque([start])
    visited = {start}
    parents = {start: None}

    width = len(map_data[0])
    height = len(map_data)

    while queue:
        cx, cy = queue.popleft()

        for dx, dy in [(0, 1), (0, -1),
                       (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) == goal:
                    parents[(nx, ny)] = (cx, cy)
                    path = []
                    cur = goal
                    while cur is not None:
                        path.append(cur)
                        cur = parents[cur]
                    path.reverse()
                    return path
                if map_data[ny][nx] in IS_PASSABLE and (nx, ny) not in blocked:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        parents[(nx, ny)] = (cx, cy)
                        queue.append((nx, ny))
    return None

# -----

class Enemy(Character):
    """Базовый класс. Слабый/Сильный враг унаследуют от него."""
    def __init__(self, x: int, y: int,
                 *groups: pygame.sprite.Group) -> None:
        super().__init__(x, y, *groups)
        # По умолчанию
        self.health = 50
        self.damage = 10
        self.image.fill(BLUE)

    def update(self, player: Player, board: Board) -> None:
        # Если мёртв — убираем
        if not self.is_alive():
            self.kill()
            return

        ex, ey = (self.rect.x // TILE_SIZE, self.rect.y // TILE_SIZE)
        px, py = (player.rect.x // TILE_SIZE, player.rect.y // TILE_SIZE)

        # Не идём в клетку игрока, чтобы не сливаться с ним;
        blocked = set()
        if (ex, ey) != (px, py):
            blocked.add((px, py))

        path = bfs((ex, ey), (px, py), board.map_data, blocked)

        if path and len(path) > 1:
            nx, ny = path[1]
            # Если не совпадает с позицией игрока
            if (nx, ny) != (px, py):
                self.rect.x = nx * TILE_SIZE
                self.rect.y = ny * TILE_SIZE

        # Если рядом — бьём
        if abs(ex - px) + abs(ey - py) == 1:
            self.attack(player)

        self.check_magma_damage(board)

    def check_magma_damage(self, board: Board) -> None:
        tx = self.rect.x // TILE_SIZE
        ty = self.rect.y // TILE_SIZE
        if 0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]:
            if board.map_data[ty][tx] == 7:
                if self.is_alive():
                    self.health -= 5
                    print(f"Enemy Health: {self.health}")

    def attack(self, player: Player) -> None:
        if player.is_alive():
            player.health -= self.damage
            print(f"Player Health: {player.health}")

    def push_back(self, dx: int, dy: int, board: Board) -> None:
        """Отталкивание на 3 клетки."""
        ex = self.rect.x // TILE_SIZE
        ey = self.rect.y // TILE_SIZE
        new_x = ex + dx * 3
        new_y = ey + dy * 3
        if 0 <= new_x < MAP_SIZE[0] and 0 <= new_y < MAP_SIZE[1]:
            if board.map_data[new_y][new_x] in IS_PASSABLE:
                self.rect.x = new_x * TILE_SIZE
                self.rect.y = new_y * TILE_SIZE


class WeakEnemy(Enemy):
    # Слабый враг
    def __init__(self, x: int, y: int, *groups: pygame.sprite.Group) -> None:
        super().__init__(x, y, *groups)
        self.health = WEAK_ENEMY_HEALTH
        self.damage = WEAK_ENEMY_DAMAGE
        # Для наглядности – другой цвет (или можно загрузить картинку)
        self.image.fill(WEAK_ENEMY_COLOR)


class StrongEnemy(Enemy):
    # Сильный враг
    def __init__(self, x: int, y: int, *groups: pygame.sprite.Group) -> None:
        super().__init__(x, y, *groups)
        self.health = STRONG_ENEMY_HEALTH
        self.damage = STRONG_ENEMY_DAMAGE
        self.image.fill(STRONG_ENEMY_COLOR)


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, angle: int, projectile_type: str,
                 color: tuple[int, int, int] = (255, 0, 0), speed: int = 1) -> None:
        super().__init__()

        self.size = (16, 16)
        self.image = pygame.Surface(self.size, pygame.SRCALPHA)
        self.color = color
        self.circle_center = (8, 8)
        self.circle_radius = 8

        pygame.draw.circle(self.image, self.color,
                           self.circle_center,
                           self.circle_radius)

        self.rect = self.image.get_rect(center=(x, y))
        self.angle = angle
        self.speed = speed
        self.projectile_type = projectile_type

    def update(self, board: Board, enemy: Enemy = None) -> None:
        # Движение
        if self.angle == 0:
            self.rect.y -= TILE_SIZE * self.speed
        elif self.angle == 90:
            self.rect.x -= TILE_SIZE * self.speed
        elif self.angle == 180:
            self.rect.y += TILE_SIZE * self.speed
        elif self.angle == 270:
            self.rect.x += TILE_SIZE * self.speed

        # Проверка выхода за границы
        if not (0 <= self.rect.x < MAP_WIDTH and 0 <= self.rect.y < MAP_HEIGHT):
            self.kill()
            return

        # Столкновение с врагом
        if enemy and enemy.is_alive():
            if self.rect.colliderect(enemy.rect):
                enemy.health -= ENEMY_DAMAGE
                print(f"Enemy Health: {enemy.health}")
                self.kill()
                return

        # Столкновение с тайлами
        tile_x = self.rect.centerx // TILE_SIZE
        tile_y = self.rect.centery // TILE_SIZE
        if 0 <= tile_x < MAP_SIZE[0] and 0 <= tile_y < MAP_SIZE[1]:
            tile_code = board.map_data[tile_y][tile_x]
            if self.projectile_type == "fj":
                # фаерболл
                if tile_code == 3:
                    board.set_tile(tile_x, tile_y, 4)  # дерево -> сожжённое
                    self.kill()
                elif tile_code == 4:
                    board.set_tile(tile_x, tile_y, 0)  # fire_tree -> ground
                    self.kill()
                elif tile_code == 5:
                    self.kill()

            elif self.projectile_type == "gj":
                # кинуть кирпич
                if tile_code == 4:
                    board.set_tile(tile_x, tile_y, 0)  # fire_tree -> ground
                    self.kill()


class Elements:
    """
    Обработка набора "стихий" (f, g, h, j) и применение заклинаний.
    """
    def __init__(self, set_element: list[str], angle: int, x: int, y: int,
                 board: Board, player: Player, enemy: Enemy) -> None:
        # Сортируем, чтобы 'fg' == 'gf' и т.п.
        self.set_element = sorted(set_element)
        self.angle = angle
        self.player_x = x
        self.player_y = y
        self.board = board
        self.player = player
        self.enemy = enemy

    def set_elements(self) -> None:
        combo = "".join(self.set_element)
        # Две буквы
        if len(self.set_element) == 2:
            if combo == "ff":
                self.ff()
            elif combo == "fg":
                self.fg()
            elif combo == "fh":
                self.fh()
            elif combo == "fj":
                self.fj()
            elif combo == "gg":
                self.gg()
            elif combo == "gh":
                self.gh()
            elif combo == "gj":
                self.gj()
            elif combo == "hh":
                self.hh()
            elif combo == "hj":
                self.hj()
            elif combo == "jj":
                self.jj()
        # Одна буква
        elif len(self.set_element) == 1:
            e = self.set_element[0]
            if e == 'f':
                self.f()
            elif e == 'g':
                self.g()
            elif e == 'h':
                self.h()
            elif e == 'j':
                self.j()

    # --- Single letter effects ---
    def f(self) -> None:
        dx, dy = self.get_direction()
        tx = (self.player_x + dx) // TILE_SIZE
        ty = (self.player_y + dy) // TILE_SIZE
        if 0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]:
            tile_code = self.board.map_data[ty][tx]
            # Проверяем, нет ли там врага
            front_rect = pygame.Rect(self.player_x + dx, self.player_y + dy,
                                     TILE_SIZE, TILE_SIZE)
            if self.enemy and self.enemy.rect.colliderect(front_rect):
                self.enemy.health -= ENEMY_DAMAGE
                print(f"Enemy Health: {self.enemy.health}")
            else:
                if tile_code == 0:
                    self.board.set_tile(tx, ty, 1)
                elif tile_code in (2, 4):
                    self.board.set_tile(tx, ty, 0)
                elif tile_code == 3:
                    self.board.set_tile(tx, ty, 4)
                elif tile_code == 6:
                    self.board.set_tile(tx, ty, 2)

    def g(self) -> None:
        dx, dy = self.get_direction()
        tx = (self.player_x + dx) // TILE_SIZE
        ty = (self.player_y + dy) // TILE_SIZE
        if 0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]:
            tile_code = self.board.map_data[ty][tx]
            front_rect = pygame.Rect(self.player_x + dx, self.player_y + dy,
                                     TILE_SIZE, TILE_SIZE)
            if self.enemy and self.enemy.rect.colliderect(front_rect):
                self.enemy.health -= ENEMY_DAMAGE
                print(f"Enemy Health: {self.enemy.health}")
            else:
                if tile_code == 0:
                    self.board.set_tile(tx, ty, 5)
                elif tile_code in (1, 2, 4):
                    self.board.set_tile(tx, ty, 0)
                elif tile_code == 6:
                    self.board.set_tile(tx, ty, 2)

    def h(self) -> None:
        dx, dy = self.get_direction()
        tx = (self.player_x + dx) // TILE_SIZE
        ty = (self.player_y + dy) // TILE_SIZE
        if 0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]:
            tile_code = self.board.map_data[ty][tx]
            front_rect = pygame.Rect(self.player_x + dx, self.player_y + dy,
                                     TILE_SIZE, TILE_SIZE)
            if self.enemy and self.enemy.rect.colliderect(front_rect):
                self.enemy.health -= ENEMY_DAMAGE
                print(f"Enemy Health: {self.enemy.health}")
            else:
                if tile_code == 0:
                    self.board.set_tile(tx, ty, 2)
                elif tile_code == 1:
                    self.board.set_tile(tx, ty, 0)
                elif tile_code == 4:
                    self.board.set_tile(tx, ty, 3)
                elif tile_code == 7:
                    self.board.set_tile(tx, ty, 1)

    def j(self) -> None:
        # отталкивание врага на 3 клетки
        dx_px, dy_px = self.get_direction()
        front_rect = pygame.Rect(self.player_x + dx_px, self.player_y + dy_px,
                                 TILE_SIZE, TILE_SIZE)
        if self.enemy and self.enemy.is_alive():
            if front_rect.colliderect(self.enemy.rect):
                tile_dx = dx_px // TILE_SIZE
                tile_dy = dy_px // TILE_SIZE
                self.enemy.push_back(tile_dx, tile_dy, self.board)

    # --- Two-letter combos ---
    def ff_trans(self, tx: int, ty: int) -> None:
        tile_code = self.board.map_data[ty][tx]
        if tile_code in (0, 2):
            self.board.set_tile(tx, ty, 1)
        elif tile_code == 1:
            self.board.set_tile(tx, ty, 7)
        elif tile_code in (3, 4, 6):
            self.board.set_tile(tx, ty, 0)

    def ff(self) -> None:
        dx, dy = self.get_direction()
        for i in range(1, 4):
            tx = (self.player_x + i*dx)//TILE_SIZE
            ty = (self.player_y + i*dy)//TILE_SIZE
            if not (0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]):
                break
            if self.enemy and self.enemy.is_alive():
                ex = self.enemy.rect.x // TILE_SIZE
                ey = self.enemy.rect.y // TILE_SIZE
                if (ex, ey) == (tx, ty):
                    self.ff_trans(tx, ty)
                    break
            self.ff_trans(tx, ty)

    def fg(self) -> None:
        dx, dy = self.get_direction()
        tx = (self.player_x + dx)//TILE_SIZE
        ty = (self.player_y + dy)//TILE_SIZE
        if 0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]:
            tile_code = self.board.map_data[ty][tx]
            if tile_code == 6:
                self.board.set_tile(tx, ty, 1)
            else:
                self.board.set_tile(tx, ty, 7)

    def fh(self) -> None:
        offsets = []
        for i in range(1, 4):
            for j in [-1, 0, 1]:
                if self.angle == 0:
                    cx = (self.player_x // TILE_SIZE) + j
                    cy = (self.player_y // TILE_SIZE) - i
                elif self.angle == 90:
                    cx = (self.player_x // TILE_SIZE) - i
                    cy = (self.player_y // TILE_SIZE) + j
                elif self.angle == 180:
                    cx = (self.player_x // TILE_SIZE) - j
                    cy = (self.player_y // TILE_SIZE) + i
                elif self.angle == 270:
                    cx = (self.player_x // TILE_SIZE) + i
                    cy = (self.player_y // TILE_SIZE) - j

                cell_coords = (cx, cy)
                offsets.append(cell_coords)

        if self.enemy and self.enemy.is_alive():
            ex, ey = (self.enemy.rect.x//TILE_SIZE, self.enemy.rect.y//TILE_SIZE)
            for (cx, cy) in offsets:
                if (cx, cy) == (ex, ey):
                    self.enemy.health -= ENEMY_DAMAGE
                    print(f"Enemy Health: {self.enemy.health}")
                    break

    def fj(self) -> None:
        px_center = self.player_x + TILE_SIZE//2
        py_center = self.player_y + TILE_SIZE//2
        proj = Projectile(px_center, py_center, self.angle, "fj", RED, speed=1)
        self.player.projectiles.add(proj)
        self.board.entity_group.add(proj)

    def gg(self) -> None:
        px = self.player_x // TILE_SIZE
        py = self.player_y // TILE_SIZE

        if self.angle == 0:
            coords = [(px - 1, py - 1),
                      (px, py - 1),
                      (px + 1, py - 1)]
        elif self.angle == 90:
            coords = [(px - 1, py + 1),
                      (px - 1, py),
                      (px - 1, py - 1)]
        elif self.angle == 180:
            coords = [(px + 1, py + 1),
                      (px, py + 1),
                      (px - 1, py + 1)]
        elif self.angle == 270:
            coords = [(px + 1, py - 1),
                      (px + 1, py),
                      (px + 1, py + 1)]

        for (cx, cy) in coords:
            if 0 <= cx < MAP_SIZE[0] and 0 <= cy < MAP_SIZE[1]:
                self.board.set_tile(cx, cy,5)

    def gh(self) -> None:
        dx, dy = self.get_direction()
        tx = (self.player_x+dx) // TILE_SIZE
        ty = (self.player_y+dy) // TILE_SIZE
        if 0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]:
            tile_code = self.board.map_data[ty][tx]
            if tile_code != 7:
                self.board.set_tile(tx, ty, 3)

    def gj(self) -> None:
        px_center = self.player_x + TILE_SIZE // 2
        py_center = self.player_y + TILE_SIZE // 2
        proj = Projectile(px_center, py_center,
                          self.angle, "gj",
                          GREY, speed=1)
        self.player.projectiles.add(proj)
        self.board.entity_group.add(proj)

    def hh(self) -> None:
        dx, dy = self.get_direction()
        for i in range(1, 4):
            tx = (self.player_x + i * dx) // TILE_SIZE
            ty = (self.player_y + i * dy) // TILE_SIZE
            if 0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]:
                tile_code = self.board.map_data[ty][tx]
                if tile_code == 0:
                    self.board.set_tile(tx, ty, 2)
                elif tile_code in (1, 7):
                    self.board.set_tile(tx, ty, 0)
                elif tile_code == 2:
                    self.board.set_tile(tx, ty, 6)
                elif tile_code == 4:
                    self.board.set_tile(tx, ty, 3)

    def hj(self) -> None:
        heal_amount = 30
        old_health = self.player.health
        self.player.health = min(HEALTH, self.player.health + heal_amount)
        print(f"Healed player from {old_health} to {self.player.health}")

    def jj(self) -> None:
        dx, dy = self.get_direction()
        tx2 = (self.player_x + 2 * dx) // TILE_SIZE
        ty2 = (self.player_y + 2 * dy) // TILE_SIZE
        tx1 = (self.player_x + dx) // TILE_SIZE
        ty1 = (self.player_y + dy) // TILE_SIZE
        # Двигаемся на 2 клетки, если можно, иначе на 1
        if 0 <= tx2 < MAP_SIZE[0] and 0 <= ty2 < MAP_SIZE[1]:
            if self.board.map_data[ty2][tx2] in IS_PASSABLE:
                self.player.rect.x = tx2 * TILE_SIZE
                self.player.rect.y = ty2 * TILE_SIZE
                return

        if 0 <= tx1 < MAP_SIZE[0] and 0 <= ty1 < MAP_SIZE[1]:
            if self.board.map_data[ty1][tx1] in IS_PASSABLE:
                self.player.rect.x = tx1 * TILE_SIZE
                self.player.rect.y = ty1 * TILE_SIZE

    def get_direction(self) -> tuple[int, int]:
        if self.angle == 0:
            return 0, -TILE_SIZE
        elif self.angle == 90:
            return -TILE_SIZE, 0
        elif self.angle == 180:
            return 0, TILE_SIZE
        elif self.angle == 270:
            return TILE_SIZE, 0
        return 0, 0


def show_start_screen(screen: pygame.Surface) -> None:
    """Displays the start screen with game title and instructions."""
    font = pygame.font.Font(None, 74)
    title_text = font.render("Cat and magic", True, WHITE)

    instruction_font = pygame.font.Font(None, 36)
    instruction_text = instruction_font.render("Нажмите Enter", True, WHITE)

    screen.fill(BLACK)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))
    screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT // 2))

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False

def show_loss_screen(screen: pygame.Surface) -> None:
    """Displays the loss screen with a message and instructions to return to the start screen."""
    font = pygame.font.Font(None, 74)
    loss_text = font.render("Вы проиграли", True, WHITE)

    instruction_font = pygame.font.Font(None, 36)
    instruction_text = instruction_font.render("Нажмите Enter, чтобы вернуться", True, WHITE)

    screen.fill(BLACK)
    screen.blit(loss_text, (WIDTH // 2 - loss_text.get_width() // 2, HEIGHT // 4))
    screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT // 2))

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False

def main() -> None:
    pygame.init()
    pygame.display.set_caption("Game")
    screen = pygame.display.set_mode(SIZE)
    camera = Camera(MAP_WIDTH, MAP_HEIGHT)
    board = Board(screen, camera)

    # Забираем ссылки на созданные из TMX объекты:
    show_start_screen(screen)
    player = Player(0, 0,
                    board.entity_group)
    enemy1 = WeakEnemy(640, 0,
                      board.entity_group)
    enemy2 = StrongEnemy(320, 64,
                      board.entity_group)
    enemies = [enemy1, enemy2]

    clock = pygame.time.Clock()
    set_element = []
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_r:
                    set_element = []
                elif event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_UP]:
                    if len(set_element) < 2:
                        if event.key == pygame.K_LEFT:
                            set_element.append('f')
                        elif event.key == pygame.K_RIGHT:
                            set_element.append('h')
                        elif event.key == pygame.K_DOWN:
                            set_element.append('g')
                        elif event.key == pygame.K_UP:
                            set_element.append('j')
                else:
                    if player and player.is_alive():
                        # Если несколько врагов, можно выбрать ближайшего или обрабатывать всех.
                        enemy_for_magic = enemies[0] if enemies else None

                        action_done = player.update(event, board, set_element, enemy_for_magic)
                        if action_done:
                            for enemy in enemies:
                                enemy.update(player, board)

                            for proj in player.projectiles:
                                proj.update(board, enemy_for_magic)
        if not player.is_alive():
            show_loss_screen(screen)
            running = False
        elif player and player.is_alive():
            camera.update(player)

        screen.fill(GREEN)

        board.draw()
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == '__main__':
    main()