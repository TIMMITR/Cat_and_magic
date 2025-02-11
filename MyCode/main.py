import pygame

from constants import *
from camera import Camera
from board import Board
from characters import Player, WeakEnemy, StrongEnemy
from screens import show_start_screen, show_loss_screen


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Game")
    screen = pygame.display.set_mode(SIZE)

    camera = Camera(MAP_WIDTH, MAP_HEIGHT)
    board = Board(screen, camera)

    # Показать стартовый экран
    show_start_screen(screen)

    if not board.player:
        board.player = Player(0, 0, board.entity_group)

    board.spawn(WeakEnemy, board.entity_group)
    board.spawn(StrongEnemy, board.entity_group)

    player = board.player
    enemies = board.enemies

    clock = pygame.time.Clock()
    set_element = []  # тут будут накапливаться нажатия клавиш f,g,h,j
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYUP:
                # Сброс выбранных элементов
                if event.key == pygame.K_r:
                    set_element = []

                # Добавление элементов при нажатии стрелок (пример)
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
                    # Обновление игрока (движение, заклинания и т.п.)
                    if player and player.is_alive():
                        # Если несколько врагов, можно выбрать ближайшего
                        # или обрабатывать всех, здесь для примера — первый
                        enemy_for_magic = enemies[0] if enemies else None

                        action_done = player.update(event, board, set_element, enemy_for_magic)
                        if action_done:
                            # Ход всех врагов
                            for enemy in enemies:
                                enemy.update(player, board)

                            # Обновление снарядов
                            for proj in player.projectiles:
                                proj.update(board, enemy_for_magic)

        # Проверка, жив ли игрок
        if not player.is_alive():
            show_loss_screen(screen)
            running = False
        else:
            # Камера следует за игроком
            camera.update(player)

        # Отрисовка
        screen.fill(GREEN)
        board.draw()
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == '__main__':
    main()