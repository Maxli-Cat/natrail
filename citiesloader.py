import csv

class City:
    def __init__(self, name, lat, lon, population = 0):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.population = population

    def __str__(self):
        return f"{self.name}: {self.population} people, {self.lat}°, {self.lon}°"

def load_file(filename):
    file = open(filename, "r", newline='', encoding='utf-8')
    db = csv.reader(file)
    cities = []
    for row in db:
        name, population, lat, lon = row
        population = int(population)
        lat = float(lat)
        lon = float(lon)
        cities.append(City(name, lat, lon, population))
    return cities


if __name__ == "__main__":
    filename = "datasets\\USA_bordered.csv"
    cities = load_file(filename)
    cities.sort(key=lambda city: city.population)
    for city in cities:
        print(city)