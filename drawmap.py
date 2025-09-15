import sys
import tiledownloader
import pygame
import functools

pygame.init()
pygame.font.init()

font = pygame.font.SysFont("Arial", 18)
small = pygame.font.SysFont("Courier New", 15)
FLAGS = pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE
SIZE = WIDTH, HEIGHT = (900, 600)

ORIGIN = (22.334496945981964, 91.82751129180363)
ZOOM = 0
REDRAW = True

screen = pygame.display.set_mode(SIZE, FLAGS)

tilecache = {}
lowrescache = {}
downloaded = set()

backup_image = pygame.image.load("tiles\\backup.png")

#@functools.lru_cache(maxsize=None)
def load_image(z, x, y, fail=False):

    if y < 0 or y > (2 ** z) - 1:
        image = backup_image
        return image

    cachekey = f"{z}_{x}_{y}"
    if cachekey in tilecache:
        return tilecache[cachekey]

    while x > ((2**z)-1):
        #print("Wraparound")
        x -= (2**z)
    while x < 0:
        #print("-Wraparound")
        x += (2**z)

    if f"{z}_{x}_{y}" not in downloaded:
        tiledownloader.q.put((z, x, y))
        downloaded.add(f"{z}_{x}_{y}")

    filename = f"tiles\\Mapnik\\{z}\\{x}_{y}.png"
    cachefilename = f"lowres\\Mapnik\\{z}\\{x}_{y}.png"
    #print(filename)
    try:
        image = pygame.image.load(filename)
        tilecache[cachekey] = image
    except FileNotFoundError as ex:
        if fail: raise ex
        if cachekey in lowrescache:
            image = lowrescache[cachekey]
        try:
            image = pygame.image.load(cachefilename)
            image = pygame.transform.scale2x(image)
            lowrescache[cachekey] = image
        except FileNotFoundError as ex:
            image = backup_image
    return image

def draw_tiles(screen):
    global REDRAW
    screen.fill((255, 255, 255))
    center = WIDTH // 2, HEIGHT // 2

    tilecountx = WIDTH // 256 + 2
    tilecounty = HEIGHT // 256 + 2

    basepoint = tiledownloader.point_on_tile(*ORIGIN, ZOOM)
    basepoint = tuple(int(i * 256) for i in basepoint)

    basetile = tiledownloader.location_to_tile(*ORIGIN, ZOOM)
    #print(basepoint)
    offset = tuple(int(j - i) for i, j in zip(basepoint, center))
    #print(offset)
    while offset[0] > 0:
        offset = (offset[0] - 256, offset[1])
        basetile = (basetile[0] - 1, basetile[1])
    while offset[1] > 0:
        offset = (offset[0], offset[1] - 256)
        basetile = (basetile[0], basetile[1] - 1)

    for xtile in range(tilecountx):
        for ytile in range(tilecounty):
            image = load_image(ZOOM, basetile[0] + xtile, basetile[1] + ytile)
            tile_offset = (offset[0] + (xtile * 256), offset[1] + (ytile * 256))
            screen.blit(image, tile_offset)
            pygame.draw.rect(screen, (255,0,0), (tile_offset, (256,256)), 1)





if __name__ == "__main__":
    pygame.display.set_caption("Intercity Rail Game")
    screen.fill((255, 255, 255))
    pygame.display.flip()

    while True:
        if REDRAW:
            draw_tiles(screen)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.VIDEORESIZE:
                SIZE = WIDTH, HEIGHT = event.size

            if event.type == pygame.KEYDOWN:
                REDRAW = True
                keydelta = (1/(2**ZOOM)) * 33
                if event.key == pygame.K_UP:
                    ZOOM -= 1
                    if ZOOM < 0: ZOOM = 0
                elif event.key == pygame.K_DOWN:
                    ZOOM += 1
                    if ZOOM > 19: ZOOM = 19

                elif event.key == pygame.K_w:
                    ORIGIN = (ORIGIN[0] + keydelta, ORIGIN[1])
                elif event.key == pygame.K_s:
                    ORIGIN = (ORIGIN[0] - keydelta, ORIGIN[1])
                elif event.key == pygame.K_a:
                    ORIGIN = (ORIGIN[0], ORIGIN[1] - keydelta)
                elif event.key == pygame.K_d:
                    ORIGIN = (ORIGIN[0], ORIGIN[1] + keydelta)
