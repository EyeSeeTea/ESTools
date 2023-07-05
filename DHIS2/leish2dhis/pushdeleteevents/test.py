import pygame
import random

# Configuración inicial
pygame.init()
clock = pygame.time.Clock()

# Dimensiones de la ventana
WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetris")

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Parámetros del juego
BLOCK_SIZE = 30
ROWS, COLS = HEIGHT // BLOCK_SIZE, WIDTH // BLOCK_SIZE
shapes = [
    [['.....',
      '.....',
      '..O..',
      '.OOO.',
      '.....'],
     ['.....',
      '.O...',
      '.OO..',
      '..O..',
      '.....']],
    [['.....',
      '.....',
      '.OOO.',
      '..O..',
      '.....'],
     ['.....',
      '..O..',
      '.OO..',
      '..O..',
      '.....']],
    [['.....',
      '.....',
      '.OOO.',
      '.O...',
      '.....'],
     ['.....',
      '.OO..',
      '.O...',
      '.O...',
      '.....']],
    [['.....',
      '.....',
      '.OOO.',
      '...O.',
      '.....'],
     ['.....',
      '...O.',
      '...O.',
      '..OO.',
      '.....']]
]

def new_piece():
    shape = random.choice(shapes)
    color = (random.randint(20, 255), random.randint(20, 255), random.randint(20, 255))
    return [pygame.Surface((BLOCK_SIZE, BLOCK_SIZE)) for _ in shape], color

def draw_piece(surface, pos, color):
    for y, row in enumerate(surface):
        for x, col in enumerate(row):
            if col == 'O':
                pygame.draw.rect(win, color, (pos[0] + x * BLOCK_SIZE, pos[1] + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

def main():
    piece = new_piece()
    pos = [WIDTH // 2 - BLOCK_SIZE * 2, 0]
    speed = 500
    timer = 0
    running = True

    while running:
        win.fill(BLACK)
        dt = clock.tick(60)
        timer += dt

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            pos[0] -= BLOCK_SIZE
        if keys[pygame.K_RIGHT]:
            pos[0] += BLOCK_SIZE
        if keys[pygame.K_DOWN]:
            pos[1] += BLOCK_SIZE

        if timer > speed:
            pos[1] += BLOCK_SIZE
            timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        draw_piece(piece[0][0], pos, piece[1])

        pygame.display.update()

    pygame.quit()

if __name__ == '__main__':
    main()