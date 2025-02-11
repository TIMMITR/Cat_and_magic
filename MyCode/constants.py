import random

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
MAPS = ['../Maps/name_tmx/map1.tmx',
        '../Maps/name_tmx/map3.tmx',
        '../Maps/name_tmx/map4.tmx',
        '../Maps/name_tmx/map5.tmx']

MAP = random.choice(MAPS)

if '1' in MAP or '3' in MAP:
    MAP_SIZE = (30, 25)
elif '4' in MAP or '5' in MAP:
    MAP_SIZE = (50, 35)
else:
    MAP_SIZE = (100, 100)

MAP_WIDTH = MAP_SIZE[0] * TILE_SIZE
MAP_HEIGHT = MAP_SIZE[1] * TILE_SIZE

# Какие коды считаются проходимыми
IS_PASSABLE = [0, 1, 2, 7]