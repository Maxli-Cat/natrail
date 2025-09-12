import sys

import pygame

pygame.init()
pygame.font.init()

font = pygame.font.SysFont("Arial", 18)
small = pygame.font.SysFont("Courier New", 15)
FLAGS = pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE
SIZE = WIDTH, LENGTH = (900, 600)

ORIGIN = (41.83, -71.41)
ZOOM = 10

screen = pygame.display.set_mode(SIZE, FLAGS)

if __name__ == "__main__":
    pygame.display.set_caption("Intercity Rail Game")
    screen.fill((255, 255, 255))
    pygame.display.flip()

    while True:
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
