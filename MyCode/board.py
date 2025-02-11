import pygame
import random

from pytmx.util_pygame import load_pygame
from characters import *
from constants import *
from spells import Elements


class Tile(pygame.sprite.Sprite):
    """Простой спрайт тайла."""
    def __init__(self, pos: tuple[int, int], surf: pygame.Surface,
                 group: pygame.sprite.Group) -> None:
        super().__init__(group)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)


class Board:
    """
    Класс для загрузки Tiled-карты (TMX), хранения map_data (коды тайлов),
    групп спрайтов (tile_group, entity_group) и функций
    по изменению тайлов (set_tile) и отрисовке (draw).
    """
    def __init__(self, screen: pygame.Surface, camera) -> None:
        self.screen = screen
        self.camera = camera

        # Грузим TMX
        self.tmx_data = load_pygame(MAP)

        # Размер карты в пикселях
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT

        # Группы для спрайтов
        self.tile_group = pygame.sprite.Group()    # все тайлы
        self.entity_group = pygame.sprite.Group()  # игрок, враги, снаряды и т.д.

        # Данные карты (коды тайлов)
        self.map_data = [[0 for _ in range(MAP_SIZE[0])] for _ in range(MAP_SIZE[1])]
        # Спрайты-тайлы
        self.sprite_map = [[None for _ in range(MAP_SIZE[0])] for _ in range(MAP_SIZE[1])]

        # В будущем сохраним игрока и список врагов
        self.player = None
        self.enemies = []

        # Для случайного выбора одного из нескольких тайлов (пример)
        self.random_number = 1

        # Подгрузка изображений для разных тайлов
        self.tile_surfaces = {
            0: pygame.image.load(f"../Images/ground/ground{self.random_number}.png").convert_alpha(),
            1: pygame.image.load("../Images/ground/fire_ground.png").convert_alpha(),
            2: pygame.image.load("../Images/ground/water_ground.png").convert_alpha(),
            3: pygame.image.load("../Images/full_tree/Top_left_tree.png").convert_alpha(),   # дерево (условно)
            4: pygame.image.load("../Images/full_fire_tree/Top_left_fire_tree.png").convert_alpha(),
            5: pygame.image.load(f"../Images/main_pngs/rock{self.random_number}.png").convert_alpha(),
            6: pygame.image.load("../Images/main_pngs/water.png").convert_alpha(),
            7: pygame.image.load("../Images/main_pngs/magma.png").convert_alpha(),
        }

        # Ссылка на класс заклинаний
        self.spell_class = Elements

        # Отрисовываем карту из TMX
        self.draw_map()

    def draw_map(self) -> None:
        """Считываем слои TMX и создаём спрайты тайлов."""
        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, "tiles"):
                for x, y, surf in layer.tiles():
                    pos = (x * TILE_SIZE, y * TILE_SIZE)
                    tile_code = 0  # по умолчанию

                    # Пример, как определять tile_code по имени слоя:
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

                    self.map_data[y][x] = tile_code

                    tile = Tile(pos, surf, self.tile_group)
                    self.sprite_map[y][x] = tile

        # Обработка объектов (спавн игрока, врагов и т.п.)
        '''for obj in self.tmx_data.objects:
            if obj.type == 'Shape':
                if obj.name == 'Spawn_player':
                    self.player = Player(int(obj.x), int(obj.y), self.entity_group)
                elif obj.name == 'Spawn_enemy':
                    enemy = WeakEnemy(int(obj.x), int(obj.y), self.entity_group)
                    self.enemies.append(enemy)
                elif obj.name == 'StrongEnemy':
                    enemy = StrongEnemy(int(obj.x), int(obj.y), self.entity_group)
                    self.enemies.append(enemy)'''

    def draw(self) -> None:
        """Сначала рисуем все тайлы, затем всех персонажей и снаряды."""
        for sprite in self.tile_group:
            self.screen.blit(sprite.image, self.camera.apply(sprite))

        for sprite in self.entity_group:
            self.screen.blit(sprite.image, self.camera.apply(sprite))

    def set_tile(self, tile_x: int, tile_y: int, tile_type: int) -> None:
        """
        Меняет тайл на карте на новый тип.
        Перерисовывает его спрайт.
        """
        if not (0 <= tile_x < MAP_SIZE[0] and 0 <= tile_y < MAP_SIZE[1]):
            return

        old_sprite = self.sprite_map[tile_y][tile_x]
        if old_sprite:
            old_sprite.kill()

        self.map_data[tile_y][tile_x] = tile_type
        pos_px = (tile_x * TILE_SIZE, tile_y * TILE_SIZE)

        new_surf = self.get_tile_surface(tile_type)
        new_sprite = Tile(pos_px, new_surf, self.tile_group)
        self.sprite_map[tile_y][tile_x] = new_sprite

    def get_tile_surface(self, code: int) -> pygame.Surface:
        """
        Возвращает нужный Surface для тайла с кодом code.
        """
        if code == 0:
            self.random_number = random.choice((1, 2))
        elif code == 5:
            self.random_number = random.choice((1, 2, 3, 4))
            # Остальные коды
        return self.tile_surfaces[code]

    def spawn(self, enemy_class, group) -> "Enemy":
        """
        Спавнит врага случайно на проходимом тайле,
        где нет других врагов и нет игрока.
        Возвращает созданного врага.
        """
        while True:
            tx = random.randint(0, MAP_SIZE[0] - 1)
            ty = random.randint(0, MAP_SIZE[1] - 1)
            # Проверяем, что тайл проходим
            if self.map_data[ty][tx] in IS_PASSABLE:
                # Проверяем, не стоит ли там игрок
                if self.player:
                    px = self.player.rect.x // TILE_SIZE
                    py = self.player.rect.y // TILE_SIZE
                    if (px, py) == (tx, ty):
                        continue
                # Проверяем, нет ли там врага
                collision = False
                for e in self.enemies:
                    ex = e.rect.x // TILE_SIZE
                    ey = e.rect.y // TILE_SIZE
                    if (ex, ey) == (tx, ty):
                        collision = True
                        break

                if not collision:
                    # Создаём врага
                    x_px = tx * TILE_SIZE
                    y_px = ty * TILE_SIZE
                    enemy = enemy_class(x_px, y_px, group)
                    self.enemies.append(enemy)
                    return enemy