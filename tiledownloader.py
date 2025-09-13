import xyzservices.providers as xyz
import math
import urllib.request
import os, sys
import time
from tqdm import tqdm, trange

from queue import Queue
from threading import Thread

style = "Mapnik"

def sec(x):
    return 1/math.cos(x)

def arsinh(x):
    return math.log(x + (x**2 + 1)**0.5)

def get_tile_cords(zoom, lat, lon):
    n = 2 ** zoom
    xtile = n * ((lon + 180) / 360)
    lat = math.radians(lat)
    ytile = n * (1 - (math.log(math.tan(lat) + sec(lat)) / math.pi)) /2
    return (int(xtile), int(ytile))

def get_tile_corner(zoom, x, y):
    n = 2 ** zoom
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def download_tile(z, x, y, basepath="tiles"):
    #url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    #style = "Mapnik"
    #url = f"https://a.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
    url = xyz['OpenStreetMap'][style]['url']
    url = url.replace('{s}','a').replace('{z}', f'{z}').replace('{x}', f'{x}').replace('{y}', f'{y}')
    #print(url)
    #exit()
    #print(url)
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Sophie Johnson Intercity Rail Game 0.0.1')]
    urllib.request.install_opener(opener)
    print(url)
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    if not os.path.exists(os.path.join(basepath, style)):
        os.makedirs(os.path.join(basepath, style))
    if not os.path.exists(os.path.join(basepath, style, str(z))):
        os.makedirs(os.path.join(basepath, style, str(z)))

    urllib.request.urlretrieve(url, f"{basepath}\\{style}\\{z}\\{x}_{y}.png")
    time.sleep(0.1)

def get_tile(z, x, y, basepath="tiles", age=(60*60*24*7)):
    filename = f"{basepath}\\{style}\\{z}\\{x}_{y}.png"
    if not os.path.exists(filename):
        download_tile(z, x, y, basepath)
    if (time.time() - os.path.getmtime(filename)) > age:
        download_tile(z, x, y, basepath)

def location_to_tile(lat, lon, zoom):
    n = 2 ** zoom
    xtile = n * ((lon + 180) / 360)
    lat = math.radians(lat)
    ytile = n * (1 - (math.log(math.tan(lat) + sec(lat)) / math.pi)) / 2
    return (int(xtile), int(ytile))


def generate_parent_tiles(z, x, y):
    while z > 0:
        z -= 1
        x = x // 2
        y = y // 2
        yield (z, x, y)

def worker(q):
    while True:
        td = q.get()
        z, x, y = td
        get_tile(z, x, y)
        q.task_done()


if __name__ == '__main__':
    ORIGIN = (50.0327971, 14.3797134)
    ZOOM = 20
    firsttile = location_to_tile(ORIGIN[0], ORIGIN[1], ZOOM)
    all = list(generate_parent_tiles(ZOOM, firsttile[0], firsttile[1]))
    all.reverse()
    print(all)

    q = Queue(maxsize=0)
    for i in range(1):
        t = Thread(target=worker, args=(q,), daemon=True)
        t.start()

    for tile in all:
        q.put(tile)
    q.join()
    print("Fin")


