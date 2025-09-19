import xyzservices.providers as xyz
import math
import urllib.request
import os, sys
import time
from tqdm import tqdm, trange
from PIL import Image
from multiprocessing import Process
from multiprocessing import Queue as MQueue
from multiprocessing import freeze_support

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

def download_tile(z, x, y, basepath="tiles", cachepath="lowres"):
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

    if not os.path.exists(cachepath):
        os.makedirs(cachepath)
    if not os.path.exists(os.path.join(cachepath, style)):
        os.makedirs(os.path.join(cachepath, style))
    if not os.path.exists(os.path.join(cachepath, style, str(z+1))):
        os.makedirs(os.path.join(cachepath, style, str(z+1)))

    filename = f"{basepath}\\{style}\\{z}\\{x}_{y}.png"
    urllib.request.urlretrieve(url, filename)
    time.sleep(0.1)

    hires = Image.open(filename)
    tl = hires.crop((0,0,127,127))
    tr = hires.crop((128,0,255,127))
    bl = hires.crop((0,128,127,255))
    br = hires.crop((128,128,255,255))


    try: tl.save(f"{cachepath}\\{style}\\{z+1}\\{x*2}_{y*2}.png")
    except FileExistsError: pass
    try: tr.save(f"{cachepath}\\{style}\\{z+1}\\{x*2+1}_{y*2}.png")
    except FileExistsError: pass
    try: bl.save(f"{cachepath}\\{style}\\{z+1}\\{x*2}_{y*2+1}.png")
    except FileExistsError: pass
    try: br.save(f"{cachepath}\\{style}\\{z+1}\\{x*2+1}_{y*2+1}.png")
    except FileExistsError: pass

def get_tile(z, x, y, basepath="tiles", age=(60*60*24*7)):
    if x < 0 or y < 0: return
    if x > (2**z)-1 or y > (2**z)-1: return

    filename = f"{basepath}\\{style}\\{z}\\{x}_{y}.png"
    if not os.path.exists(filename):
        download_tile(z, x, y, basepath)
        print(f"Downloaded {filename}, did not exist")
    if (time.time() - os.path.getmtime(filename)) > age:
        download_tile(z, x, y, basepath)
        print(f"Downloaded {filename}, too old")
    else:
        print(f"{filename} exists within cache window")

def location_to_tile(lat, lon, zoom):
    n = 2 ** zoom
    xtile = n * ((lon + 180) / 360)
    lat = math.radians(lat)
    ytile = n * (1 - (math.log(math.tan(lat) + sec(lat)) / math.pi)) / 2
    return (int(xtile), int(ytile))

def point_on_tile(lat, lon, zoom):
    n = 2 ** zoom
    xtile = n * ((lon + 180) / 360)
    lat = math.radians(lat)
    ytile = n * (1 - (math.log(math.tan(lat) + sec(lat)) / math.pi)) / 2
    return xtile % 1, ytile % 1


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
        try:
            q.task_done()
        except AttributeError:
            pass
def setup():
    #q = Queue(maxsize=0)
    q = MQueue(maxsize=0)
    for i in range(1):
        #t = Thread(target=worker, args=(q,), daemon=True)
        t = Process(target=worker, args=(q,))
        t.start()
    return q

if __name__ == '__main__':
    freeze_support()

    q = Queue(maxsize=0)
    for i in range(1):
        t = Thread(target=worker, args=(q,), daemon=True)
        #t = Process(target=worker, args=(q,))
        t.start()

    ORIGIN = (43.04256466450335, -70.93208046028336)
    ZOOM = 20
    firsttile = location_to_tile(ORIGIN[0], ORIGIN[1], ZOOM)
    all = list(generate_parent_tiles(ZOOM, firsttile[0], firsttile[1]))
    all.reverse()
    print(all)

    for tile in all:
        q.put(tile)
    q.join()
    print("Fin")


