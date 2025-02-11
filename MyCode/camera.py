import pygame
from constants import WIDTH, HEIGHT


class Camera:
    def __init__(self, width: int, height: int) -> None:
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.camera_rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def apply(self, entity: pygame.sprite.Sprite) -> pygame.Rect:
        """Сдвигает спрайт на смещение камеры."""
        return entity.rect.move(self.camera_rect.topleft)

    def update(self, target: pygame.sprite.Sprite) -> None:
        """Следит за целевым спрайтом (обычно игроком)."""
        self.x = -target.rect.centerx + WIDTH // 2
        self.y = -target.rect.centery + HEIGHT // 2

        # Ограничения, чтобы камера не выходила за границы карты
        self.x = min(0, self.x)  # слева
        self.y = min(0, self.y)  # сверху
        self.x = max(-(self.width - WIDTH), self.x)   # справа
        self.y = max(-(self.height - HEIGHT), self.y) # снизу

        self.camera_rect = pygame.Rect(self.x, self.y, self.width, self.height)