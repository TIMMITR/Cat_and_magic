import pygame
from constants import *


class Projectile(pygame.sprite.Sprite):
    """
    Снаряд (например, фаербол, камень).

    Параметры:
    - x, y: координаты центра снаряда в пикселях
    - angle: угол в градусах (0, 90, 180, 270), задаёт направление полёта
    - projectile_type: строка, идентифицирующая тип ('fj', 'gj' и т.п.)
    - color: цвет снаряда
    - speed: во сколько тайлов (Tile) за раз движется снаряд
    """

    def __init__(self, x: int, y: int, angle: int, projectile_type: str,
                 color = (255, 0, 0), speed: int = 1) -> None:
        super().__init__()

        self.size = (16, 16)
        # Прозрачная поверхностъ
        self.image = pygame.Surface(self.size, pygame.SRCALPHA)
        self.color = color
        self.circle_center = (8, 8)
        self.circle_radius = 8

        # Рисуем круг (например, красный для фаербола)
        pygame.draw.circle(self.image, self.color,
                           self.circle_center,
                           self.circle_radius)

        self.rect = self.image.get_rect(center=(x, y))

        self.angle = angle
        self.speed = speed
        self.projectile_type = projectile_type

    def update(self, board, enemy=None) -> None:
        """
        Обновление позиции снаряда + проверка столкновений.

        Параметры:
        - board: объект карты/поля (в нём хранится map_data и методы set_tile и т.п.)
        - enemy: враг, которого можно зацепить снарядом (для простоты передаём одного).
        """
        # Движение снаряда
        if self.angle == 0:
            self.rect.y -= TILE_SIZE * self.speed
        elif self.angle == 90:
            self.rect.x -= TILE_SIZE * self.speed
        elif self.angle == 180:
            self.rect.y += TILE_SIZE * self.speed
        elif self.angle == 270:
            self.rect.x += TILE_SIZE * self.speed

        # Проверка выхода за границы карты
        if not (0 <= self.rect.x < MAP_WIDTH and 0 <= self.rect.y < MAP_HEIGHT):
            self.kill()
            return

        # Проверка столкновения с врагом
        if enemy and enemy.is_alive():
            if self.rect.colliderect(enemy.rect):
                enemy.health -= ENEMY_DAMAGE
                print(f"Enemy Health: {enemy.health}")
                self.kill()
                return

        # Координаты тайла, в котором сейчас снаряд
        tile_x = self.rect.centerx // TILE_SIZE
        tile_y = self.rect.centery // TILE_SIZE

        if 0 <= tile_x < MAP_SIZE[0] and 0 <= tile_y < MAP_SIZE[1]:
            tile_code = board.map_data[tile_y][tile_x]

            # Логика для конкретных типов снарядов
            if self.projectile_type == "fj":
                # "фаербол"
                # - дерево (3) превращаем в сожжённое дерево (4)
                # - сожжённое дерево (4) превращаем в обычную землю (0)
                # - камень (5) гасит снаряд
                if tile_code == 3:
                    board.set_tile(tile_x, tile_y, 4)
                    self.kill()
                elif tile_code == 4:
                    board.set_tile(tile_x, tile_y, 0)
                    self.kill()
                elif tile_code == 5:
                    self.kill()

            elif self.projectile_type == "gj":
                # "каменный" выстрел
                # - сожжённое дерево (4) превращаем в обычную землю (0)
                # - камень (5) тоже может гасить снаряд (логика на ваше усмотрение)
                if tile_code == 4:
                    board.set_tile(tile_x, tile_y, 0)
                    self.kill()
                elif tile_code == 5:
                    self.kill()


class Elements:
    """
    Обработка набора "стихий" (f, g, h, j) и применение заклинаний.

    Параметры:
    - set_element: список строк (обычно 'f', 'g', 'h', 'j'), где может быть 1 или 2 элемента
    - angle: текущее направление игрока (0, 90, 180, 270)
    - x, y: позиция игрока в пикселях
    - board: объект карты (хранит map_data, set_tile и т.д.)
    - player: сам игрок (для нанесения урона врагам, изменения здоровья и пр.)
    - enemy: враг (если он есть рядом/на линии)
    """

    def __init__(self, set_element, angle, x, y, board, player, enemy) -> None:
        # Сортируем, чтобы 'fg' == 'gf' и т.п.
        self.set_element = sorted(set_element)
        self.angle = angle
        self.player_x = x
        self.player_y = y
        self.board = board
        self.player = player
        self.enemy = enemy

    def set_elements(self) -> None:
        """
        Определяемся, какое заклинание вызвать, исходя из набора (1 или 2 символа).
        """
        combo = "".join(self.set_element)
        if len(self.set_element) == 2:
            # Дву-буквенные заклинания
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
        elif len(self.set_element) == 1:
            # Одно-буквенные заклинания
            e = self.set_element[0]
            if e == 'f':
                self.f()
            elif e == 'g':
                self.g()
            elif e == 'h':
                self.h()
            elif e == 'j':
                self.j()

    # ----------------------------------------------------------------
    # Ниже идут реализации конкретных заклинаний.
    # Для каждого описываем логику, какую именно плитку/объект они меняют.
    # ----------------------------------------------------------------

    # ==== Однобуквенные заклинания ====

    def f(self) -> None:
        """
        f — воздействие огнём на тайл перед игроком или на врага,
        если он стоит в этой клетке.
        """
        dx, dy = self.get_direction()
        tx = (self.player_x + dx) // TILE_SIZE
        ty = (self.player_y + dy) // TILE_SIZE

        if not (0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]):
            return

        tile_code = self.board.map_data[ty][tx]

        # Проверяем, не стоит ли там враг
        if self.enemy and self.enemy.is_alive():
            front_rect = pygame.Rect(self.player_x + dx, self.player_y + dy, TILE_SIZE, TILE_SIZE)
            if front_rect.colliderect(self.enemy.rect):
                self.enemy.health -= ENEMY_DAMAGE
                print(f"Enemy Health: {self.enemy.health}")
                return

        # Логика воздействия на тайл
        if tile_code == 0:
            self.board.set_tile(tx, ty, 1)  # ground -> fire_ground
        elif tile_code in (2, 4):
            self.board.set_tile(tx, ty, 0)  # water_ground или fire_tree -> ground
        elif tile_code == 3:
            self.board.set_tile(tx, ty, 4)  # tree -> fire_tree
        elif tile_code == 6:
            self.board.set_tile(tx, ty, 2)  # water -> water_ground

    def g(self) -> None:
        """
        g — воздействие "землёй" (камень) на ближайший тайл/врага.
        """
        dx, dy = self.get_direction()
        tx = (self.player_x + dx) // TILE_SIZE
        ty = (self.player_y + dy) // TILE_SIZE

        if not (0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]):
            return

        tile_code = self.board.map_data[ty][tx]
        if self.enemy and self.enemy.is_alive():
            front_rect = pygame.Rect(self.player_x + dx, self.player_y + dy, TILE_SIZE, TILE_SIZE)
            if front_rect.colliderect(self.enemy.rect):
                self.enemy.health -= ENEMY_DAMAGE
                print(f"Enemy Health: {self.enemy.health}")
                return

        # Логика воздействия на тайл
        if tile_code == 0:
            self.board.set_tile(tx, ty, 5)  # ground -> rock
        elif tile_code in (1, 2, 4):
            self.board.set_tile(tx, ty, 0)  # fire_ground / water_ground / fire_tree -> ground
        elif tile_code == 6:
            self.board.set_tile(tx, ty, 2)  # water -> water_ground

    def h(self) -> None:
        """
        h — воздействие водой/льдом на тайл перед игроком.
        """
        dx, dy = self.get_direction()
        tx = (self.player_x + dx) // TILE_SIZE
        ty = (self.player_y + dy) // TILE_SIZE

        if not (0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]):
            return

        tile_code = self.board.map_data[ty][tx]

        if self.enemy and self.enemy.is_alive():
            front_rect = pygame.Rect(self.player_x + dx, self.player_y + dy, TILE_SIZE, TILE_SIZE)
            if front_rect.colliderect(self.enemy.rect):
                self.enemy.health -= ENEMY_DAMAGE
                print(f"Enemy Health: {self.enemy.health}")
                return

        # Логика воздействия на тайл
        if tile_code == 0:
            self.board.set_tile(tx, ty, 2)  # ground -> water_ground
        elif tile_code == 1:
            self.board.set_tile(tx, ty, 0)  # fire_ground -> ground
        elif tile_code == 4:
            self.board.set_tile(tx, ty, 3)  # fire_tree -> tree
        elif tile_code == 7:
            self.board.set_tile(tx, ty, 1)  # magma -> fire_ground

    def j(self) -> None:
        """
        j — отталкивание врага, если он стоит перед игроком, на 3 клетки.
        """
        dx_px, dy_px = self.get_direction()
        front_rect = pygame.Rect(self.player_x + dx_px, self.player_y + dy_px, TILE_SIZE, TILE_SIZE)
        if self.enemy and self.enemy.is_alive() and front_rect.colliderect(self.enemy.rect):
            tile_dx = dx_px // TILE_SIZE
            tile_dy = dy_px // TILE_SIZE
            self.enemy.push_back(tile_dx, tile_dy, self.board)

    # ==== Двухбуквенные заклинания ====

    def ff(self) -> None:
        """
        ff — "усиленный огонь": превращает несколько тайлов по направлению игрока.
        Может, например, превращать ground -> fire_ground -> magma,
        water_ground -> fire_ground, дерево -> сжигает и т.д.
        """
        dx, dy = self.get_direction()
        steps = 3  # сколько тайлов пронзает заклинание
        for i in range(1, steps + 1):
            tx = (self.player_x + i * dx) // TILE_SIZE
            ty = (self.player_y + i * dy) // TILE_SIZE

            if not (0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]):
                break

            # Если задели врага — прерываемся
            if self.enemy and self.enemy.is_alive():
                ex = self.enemy.rect.x // TILE_SIZE
                ey = self.enemy.rect.y // TILE_SIZE
                if (ex, ey) == (tx, ty):
                    self.ff_transform(tx, ty)
                    break

            self.ff_transform(tx, ty)

    def ff_transform(self, tx: int, ty: int) -> None:
        """
        Частная функция для ff: как именно меняем каждый тайл.
        """
        tile_code = self.board.map_data[ty][tx]
        if tile_code in (0, 2):
            self.board.set_tile(tx, ty, 1)  # ground/water_ground -> fire_ground
        elif tile_code == 1:
            self.board.set_tile(tx, ty, 7)  # fire_ground -> magma
        elif tile_code in (3, 4, 6):
            # дерево, сожжённое дерево, вода -> ground
            self.board.set_tile(tx, ty, 0)

    def fg(self) -> None:
        """
        fg — пример: превращает воду в огонь или сразу в магму и т.п.
        (возможна любая логика).
        """
        dx, dy = self.get_direction()
        tx = (self.player_x + dx) // TILE_SIZE
        ty = (self.player_y + dy) // TILE_SIZE

        if not (0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]):
            return

        tile_code = self.board.map_data[ty][tx]
        if tile_code == 6:
            # вода -> fire_ground
            self.board.set_tile(tx, ty, 1)
        else:
            # что угодно иное -> magma
            self.board.set_tile(tx, ty, 7)

    def fh(self) -> None:
        """
        fh — удар по площади (конус), например 3 клетки вперёд по ширине 3.
        """
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
                else:  # self.angle == 270
                    cx = (self.player_x // TILE_SIZE) + i
                    cy = (self.player_y // TILE_SIZE) - j

                cell_coords = (cx, cy)
                offsets.append(cell_coords)

        # Если есть враг, проверяем, задели ли его
        if self.enemy and self.enemy.is_alive():
            ex, ey = (self.enemy.rect.x // TILE_SIZE, self.enemy.rect.y // TILE_SIZE)
            for (cx, cy) in offsets:
                if (cx, cy) == (ex, ey):
                    self.enemy.health -= ENEMY_DAMAGE
                    print(f"Enemy Health: {self.enemy.health}")
                    break

    def fj(self) -> None:
        """
        fj — бросок фаербола (снаряд) по направлению игрока.
        """
        px_center = self.player_x + TILE_SIZE // 2
        py_center = self.player_y + TILE_SIZE // 2
        proj = Projectile(px_center, py_center, self.angle, "fj", color=RED, speed=1)
        self.player.projectiles.add(proj)
        self.board.entity_group.add(proj)  # чтобы снаряд тоже рисовался/обновлялся

    def gg(self) -> None:
        """
        gg — создаёт "каменную стену" из 3 тайлов сбоку перед игроком.
        """
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
                self.board.set_tile(cx, cy, 5)

    def gh(self) -> None:
        """
        gh — пример: создаёт дерево (3) перед игроком,
        если там не магма (7). Если была магма, можно оставить как есть или выдумать логику.
        """
        dx, dy = self.get_direction()
        tx = (self.player_x + dx) // TILE_SIZE
        ty = (self.player_y + dy) // TILE_SIZE

        if not (0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]):
            return

        tile_code = self.board.map_data[ty][tx]
        if tile_code != 7:  # не магма
            self.board.set_tile(tx, ty, 3)  # сажаем дерево

    def gj(self) -> None:
        """
        gj — метнуть каменный "снаряд" (Projectile).
        """
        px_center = self.player_x + TILE_SIZE // 2
        py_center = self.player_y + TILE_SIZE // 2
        proj = Projectile(px_center, py_center, self.angle, "gj", color=GREY, speed=1)
        self.player.projectiles.add(proj)
        self.board.entity_group.add(proj)

    def hh(self) -> None:
        """
        hh — мощное водяное заклинание, которое превращает несколько тайлов в воду/убирает огонь и т.д.
        """
        dx, dy = self.get_direction()
        steps = 3
        for i in range(1, steps + 1):
            tx = (self.player_x + i * dx) // TILE_SIZE
            ty = (self.player_y + i * dy) // TILE_SIZE
            if 0 <= tx < MAP_SIZE[0] and 0 <= ty < MAP_SIZE[1]:
                tile_code = self.board.map_data[ty][tx]
                if tile_code == 0:
                    self.board.set_tile(tx, ty, 2)  # ground -> water_ground
                elif tile_code in (1, 7):
                    self.board.set_tile(tx, ty, 0)  # fire_ground/magma -> ground
                elif tile_code == 2:
                    self.board.set_tile(tx, ty, 6)  # water_ground -> water
                elif tile_code == 4:
                    self.board.set_tile(tx, ty, 3)  # fire_tree -> tree

    def hj(self) -> None:
        """
        hj — восполняет здоровье игрока.
        """
        heal_amount = 30
        old_health = self.player.health
        self.player.health = min(HEALTH, self.player.health + heal_amount)
        print(f"Healed player from {old_health} to {self.player.health}")

    def jj(self) -> None:
        """
        jj — "рывок" игрока на 2 тайла вперёд, если это возможно; иначе на 1.
        """
        dx, dy = self.get_direction()
        tx2 = (self.player_x + 2 * dx) // TILE_SIZE
        ty2 = (self.player_y + 2 * dy) // TILE_SIZE
        tx1 = (self.player_x + dx) // TILE_SIZE
        ty1 = (self.player_y + dy) // TILE_SIZE

        # Проверяем 2 клетки вперёд
        if 0 <= tx2 < MAP_SIZE[0] and 0 <= ty2 < MAP_SIZE[1]:
            if self.board.map_data[ty2][tx2] in IS_PASSABLE:
                self.player.rect.x = tx2 * TILE_SIZE
                self.player.rect.y = ty2 * TILE_SIZE
                return

        # Иначе проверяем хотя бы 1 клетку
        if 0 <= tx1 < MAP_SIZE[0] and 0 <= ty1 < MAP_SIZE[1]:
            if self.board.map_data[ty1][tx1] in IS_PASSABLE:
                self.player.rect.x = tx1 * TILE_SIZE
                self.player.rect.y = ty1 * TILE_SIZE


    def get_direction(self) -> tuple[int, int]:
        """
        Возвращает смещение (dx, dy) в пикселях (кратно TILE_SIZE)
        в зависимости от угла (0, 90, 180, 270).
        """
        if self.angle == 0:
            return 0, -TILE_SIZE
        elif self.angle == 90:
            return -TILE_SIZE, 0
        elif self.angle == 180:
            return 0, TILE_SIZE
        elif self.angle == 270:
            return TILE_SIZE, 0
        return 0, 0