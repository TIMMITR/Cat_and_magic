import pygame
from constants import WHITE, BLACK, WIDTH, HEIGHT


def show_start_screen(screen: pygame.Surface) -> None:
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
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False


def show_loss_screen(screen: pygame.Surface) -> None:
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
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False