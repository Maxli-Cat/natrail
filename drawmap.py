import sys
import tiledownloader
import functools
import multiprocessing
import queue
import threading
import citiesloader
import math

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
        q.put((z, x, y))
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
            return lowrescache[cachekey]
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
            #pygame.draw.rect(screen, (255,0,0), (tile_offset, (256,256)), 1)

def draw_cities(screen):
    center = WIDTH // 2, HEIGHT // 2

    tilecountx = WIDTH // 256 + 2
    tilecounty = HEIGHT // 256 + 2

    basepoint = tiledownloader.point_on_tile(*ORIGIN, ZOOM)
    basepoint = tuple(int(i * 256) for i in basepoint)

    basetile = tiledownloader.location_to_tile(*ORIGIN, ZOOM)


    for city in cities:
        citytile = tiledownloader.location_to_tile(city.lat, city.lon, ZOOM)
        cityoffset = tiledownloader.point_on_tile(city.lat, city.lon, ZOOM)
        cityoffset = tuple(int(i*256) for i in cityoffset)
        posx = center[0] - basepoint[0] - (basetile[0] * 256) + (citytile[0] * 256) + cityoffset[0]
        posy = center[1] - basepoint[1] - (basetile[1] * 256) + (citytile[1] * 256) + cityoffset[1]


        pygame.draw.circle(screen, (255,0,0), (posx, posy), 10)


def render(screen):
    draw_tiles(screen)
    draw_cities(screen)

def clickpos_to_realpos(x, y):
    center = WIDTH // 2, HEIGHT // 2

    tilecountx = WIDTH // 256 + 2
    tilecounty = HEIGHT // 256 + 2

    basepoint = tiledownloader.point_on_tile(*ORIGIN, ZOOM)
    #basepoint = tuple(int(i * 256) for i in basepoint)

    basetile = tiledownloader.location_to_tile(*ORIGIN, ZOOM)

    xpos = (x - center[0]) / 256
    ypos = (y - center[1]) / 256

    click_tile_x = basetile[0] + basepoint[0] + xpos
    click_tile_y = basetile[1] + basepoint[1] + ypos

    n = 1 << ZOOM

    lon_d = click_tile_x / n * 360 - 180
    lat_r = math.atan(math.sinh(math.pi * (1 - 2 * click_tile_y / n)))
    lat_d = math.degrees(lat_r)
    return lat_d, lon_d

def zoom_in(mousepos = None):
    global ZOOM, ORIGIN
    if mousepos is not None:
        ORIGIN = clickpos_to_realpos(mousepos[0], mousepos[1])
    ZOOM += 1
    if ZOOM > 19: ZOOM = 19
    if mousepos is not None:
        oldreal = clickpos_to_realpos(WIDTH // 2, HEIGHT // 2)
        newreal = clickpos_to_realpos(*mousepos)
        deltax = newreal[0] - oldreal[0]
        deltay = newreal[1] - oldreal[1]
        move(deltax, deltay)

def zoom_out(bounded=True, mousepos = None):
    global ZOOM, ORIGIN
    if mousepos is not None:
        ORIGIN = clickpos_to_realpos(mousepos[0], mousepos[1])

    ZOOM -= 1
    if ZOOM < 0: ZOOM = 0
    if bounded:
        tiles = math.ceil(min(SIZE) / 256)
        maxzoom = math.ceil(math.log(tiles, 2))
        print(f"{SIZE=}, {tiles=}, {maxzoom=}")
        if ZOOM < maxzoom:
            ZOOM = maxzoom
    if mousepos is not None:
        oldreal = clickpos_to_realpos(WIDTH // 2, HEIGHT // 2)
        newreal = clickpos_to_realpos(*mousepos)
        deltax = newreal[0] - oldreal[0]
        deltay = newreal[1] - oldreal[1]
        move(deltax, deltay)
def move(deltax, deltay):
    global ORIGIN
    ORIGIN = (ORIGIN[0] - deltax, ORIGIN[1] - deltay)
    print(f"{ORIGIN=}")
    while ORIGIN[1] < -180:
        ORIGIN = (ORIGIN[0], ORIGIN[1] + 360)
    while ORIGIN[1] > 180:
        ORIGIN = (ORIGIN[0], ORIGIN[1] - 360)


if __name__ == "__main__":
    import pygame
    cities = []
    filenames = ["datasets\\USA_bordered.csv", "datasets\\US_CAN_BORDER.csv", "datasets\\US_MEX_Border.csv",]# "datasets\\msa_canada.csv"]
    for filename in filenames:
        cities += citiesloader.load_file(filename)
    cities.sort(key=lambda city: city.population, reverse=True)
    for city in cities:
        print(city.lat, city.lon)

    pygame.init()
    pygame.font.init()

    font = pygame.font.SysFont("Arial", 18)
    small = pygame.font.SysFont("Courier New", 15)
    FLAGS = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE
    SIZE = WIDTH, HEIGHT = (900, 600)

    ORIGIN = (42.36661312067483, -71.06257793936203)
    ZOOM = 5
    REDRAW = True

    screen = pygame.display.set_mode(SIZE, FLAGS)

    tilecache = {}
    lowrescache = {}
    downloaded = set()

    backup_image = pygame.image.load("tiles\\backup.png")

    pygame.display.set_caption("Intercity Rail Game")
    screen.fill((255, 255, 255))
    pygame.display.flip()

    #q = queue.Queue(maxsize=0)
    q = multiprocessing.Queue(maxsize=0)
    for i in range(10):
        #t = threading.Thread(target=tiledownloader.worker, args=(q,), daemon=True)
        t = multiprocessing.Process(target=tiledownloader.worker, args=(q,), daemon=True)
        t.start()

    CLICKED = False
    oldpos = (0,0)

    while True:
        if REDRAW:
            render(screen)
        if CLICKED:
            newpos = pygame.mouse.get_pos()
            oldreal = clickpos_to_realpos(*oldpos)
            newreal = clickpos_to_realpos(*newpos)
            deltax = newreal[0] - oldreal[0]
            deltay = newreal[1] - oldreal[1]
            move(deltax, deltay)
            oldpos = newpos

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
                    zoom_out()
                elif event.key == pygame.K_DOWN:
                    zoom_in()

                elif event.key == pygame.K_w:
                    move(keydelta, 0)
                elif event.key == pygame.K_s:
                    move(-keydelta, 0)
                elif event.key == pygame.K_a:
                    move(0, -keydelta)
                elif event.key == pygame.K_d:
                    move(0, keydelta)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    oldpos = pygame.mouse.get_pos()
                    CLICKED = True
                elif event.button == 4:
                    zoom_in(mousepos=pygame.mouse.get_pos())
                elif event.button == 5:
                    zoom_out(True, mousepos=pygame.mouse.get_pos())
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    CLICKED = False