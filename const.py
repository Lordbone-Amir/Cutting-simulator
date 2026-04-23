# constants.py

# большие простые числа
PRIME_F = 10**9 + 7
PRIME_S = 10**9 + 3

# Размеры сетки (в клетках)
GRID_WIDTH = 30
GRID_HEIGHT = 30
# Цвета (RGB, Alpha)
COLOR_BACKGROUND = (0.95, 0.95, 0.95, 1)
COLOR_BACK_LINE = (0, 0, 0, 1)
COLOR_GRID = (0.7, 0.7, 0.7, 1)
COLOR_ANS = (1,0,0,1)
COLOR_VERTEX = (0, 0, 1, 1)
COLOR_EDGE = (0, 0.8, 1, 1)
COLOR_FILL = (0.2, 0.6, 0.9, 0.4)
COLOR_CUT_LINE = (1, 0.5, 0, 1)      # оранжевый
COLOR_CUT_LINE_INVALID = (1, 0, 0, 1) # красный при ошибке
COLOR_SUCCESS = (0, 1, 0, 1)
COLOR_ERROR = (0, 0, 1, 1)

# Отступы и размеры
MARGIN_FRACTION = 0.05
VERTEX_RADIUS_FRACTION = 0.15

BUTTON_SPACING = 10
BUTTON_PADDING = 10