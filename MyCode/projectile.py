import pygame
from field import Board
from characters import Enemy
from constants import *


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