"""Monopoly board topology, tile data, and economic constants."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class PropertyData:
    index: int
    name: str
    group: str
    cost: int
    house_cost: int
    rent: list[int]  # [base, 1h, 2h, 3h, 4h, hotel]

# 40 Tiles of official standard Monopoly
TILES = [
    {"index": 0, "name": "GO", "group": "Special"},
    {"index": 1, "name": "Mediterranean Ave", "group": "Brown", "cost": 60, "house_cost": 50, "rent": [2, 10, 30, 90, 160, 250]},
    {"index": 2, "name": "Community Chest 1", "group": "Special"},
    {"index": 3, "name": "Baltic Ave", "group": "Brown", "cost": 60, "house_cost": 50, "rent": [4, 20, 60, 180, 320, 450]},
    {"index": 4, "name": "Income Tax", "group": "Special"},
    {"index": 5, "name": "Reading Railroad", "group": "Railroad", "cost": 200, "house_cost": 0, "rent": [25, 50, 100, 200, 200, 200]},
    {"index": 6, "name": "Oriental Ave", "group": "Light Blue", "cost": 100, "house_cost": 50, "rent": [6, 30, 90, 270, 400, 550]},
    {"index": 7, "name": "Chance 1", "group": "Special"},
    {"index": 8, "name": "Vermont Ave", "group": "Light Blue", "cost": 100, "house_cost": 50, "rent": [6, 30, 90, 270, 400, 550]},
    {"index": 9, "name": "Connecticut Ave", "group": "Light Blue", "cost": 120, "house_cost": 50, "rent": [8, 40, 100, 300, 450, 600]},
    {"index": 10, "name": "Jail / Just Visiting", "group": "Special"},
    {"index": 11, "name": "St. Charles Place", "group": "Pink", "cost": 140, "house_cost": 100, "rent": [10, 50, 150, 450, 625, 750]},
    {"index": 12, "name": "Electric Company", "group": "Utility", "cost": 150, "house_cost": 0, "rent": [28, 70, 70, 70, 70, 70]}, # avg roll * 4 / 10
    {"index": 13, "name": "States Ave", "group": "Pink", "cost": 140, "house_cost": 100, "rent": [10, 50, 150, 450, 625, 750]},
    {"index": 14, "name": "Virginia Ave", "group": "Pink", "cost": 160, "house_cost": 100, "rent": [12, 60, 180, 500, 700, 900]},
    {"index": 15, "name": "Pennsylvania Railroad", "group": "Railroad", "cost": 200, "house_cost": 0, "rent": [25, 50, 100, 200, 200, 200]},
    {"index": 16, "name": "St. James Place", "group": "Orange", "cost": 180, "house_cost": 100, "rent": [14, 70, 200, 550, 750, 950]},
    {"index": 17, "name": "Community Chest 2", "group": "Special"},
    {"index": 18, "name": "Tennessee Ave", "group": "Orange", "cost": 180, "house_cost": 100, "rent": [14, 70, 200, 550, 750, 950]},
    {"index": 19, "name": "New York Ave", "group": "Orange", "cost": 200, "house_cost": 100, "rent": [16, 80, 220, 600, 800, 1000]},
    {"index": 20, "name": "Free Parking", "group": "Special"},
    {"index": 21, "name": "Kentucky Ave", "group": "Red", "cost": 220, "house_cost": 150, "rent": [18, 90, 250, 700, 875, 1050]},
    {"index": 22, "name": "Chance 2", "group": "Special"},
    {"index": 23, "name": "Indiana Ave", "group": "Red", "cost": 220, "house_cost": 150, "rent": [18, 90, 250, 700, 875, 1050]},
    {"index": 24, "name": "Illinois Ave", "group": "Red", "cost": 240, "house_cost": 150, "rent": [20, 100, 300, 750, 925, 1100]},
    {"index": 25, "name": "B. & O. Railroad", "group": "Railroad", "cost": 200, "house_cost": 0, "rent": [25, 50, 100, 200, 200, 200]},
    {"index": 26, "name": "Atlantic Ave", "group": "Yellow", "cost": 260, "house_cost": 150, "rent": [22, 110, 330, 800, 975, 1150]},
    {"index": 27, "name": "Ventnor Ave", "group": "Yellow", "cost": 260, "house_cost": 150, "rent": [22, 110, 330, 800, 975, 1150]},
    {"index": 28, "name": "Water Works", "group": "Utility", "cost": 150, "house_cost": 0, "rent": [28, 70, 70, 70, 70, 70]},
    {"index": 29, "name": "Marvin Gardens", "group": "Yellow", "cost": 280, "house_cost": 150, "rent": [24, 120, 360, 850, 1025, 1200]},
    {"index": 30, "name": "Go to Jail", "group": "Special"},
    {"index": 31, "name": "Pacific Ave", "group": "Green", "cost": 300, "house_cost": 200, "rent": [26, 130, 390, 900, 1100, 1275]},
    {"index": 32, "name": "North Carolina Ave", "group": "Green", "cost": 300, "house_cost": 200, "rent": [26, 130, 390, 900, 1100, 1275]},
    {"index": 33, "name": "Community Chest 3", "group": "Special"},
    {"index": 34, "name": "Pennsylvania Ave", "group": "Green", "cost": 320, "house_cost": 200, "rent": [28, 150, 450, 1000, 1200, 1400]},
    {"index": 35, "name": "Short Line Railroad", "group": "Railroad", "cost": 200, "house_cost": 0, "rent": [25, 50, 100, 200, 200, 200]},
    {"index": 36, "name": "Chance 3", "group": "Special"},
    {"index": 37, "name": "Park Place", "group": "Dark Blue", "cost": 350, "house_cost": 200, "rent": [35, 175, 500, 1100, 1300, 1500]},
    {"index": 38, "name": "Luxury Tax", "group": "Special"},
    {"index": 39, "name": "Boardwalk", "group": "Dark Blue", "cost": 400, "house_cost": 200, "rent": [50, 200, 600, 1400, 1700, 2000]},
]

COLOR_GROUPS = {
    "Brown": [1, 3],
    "Light Blue": [6, 8, 9],
    "Pink": [11, 13, 14],
    "Orange": [16, 18, 19],
    "Red": [21, 23, 24],
    "Yellow": [26, 27, 29],
    "Green": [31, 32, 34],
    "Dark Blue": [37, 39],
    "Railroad": [5, 15, 25, 35],
    "Utility": [12, 28],
}
