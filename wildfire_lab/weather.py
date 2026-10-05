"""Join lagged station-month context without fitting preprocessing."""
import csv
import math
from collections import defaultdict
import numpy as np
from scipy.spatial import cKDTree

MEASUREMENTS = ["mean_temp_c", "total_precip_mm", "snowfall_cm",
                "heating_degree_days", "cooling_degree_days"]


def month_lag(day, months):
    year, month = map(int, day[:7].split("-"))
    offset = year * 12 + month - 1 - months
    return f"{offset // 12}-{offset % 12 + 1:02d}-01"


def sphere(latitudes, longitudes):
    lat, lon = np.radians(latitudes), np.radians(longitudes)
    return np.column_stack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)))


class WeatherIndex:
    def __init__(self, csv_path, latest_year=2018):
        groups = defaultdict(list)
        with csv_path.open(newline="") as stream:
            for row in csv.DictReader(stream):
                if int(row["month"][:4]) > latest_year:
                    continue
                if row["latitude"] and row["longitude"]:
                    groups[row["month"]].append(row)
        self.months = {}
        for month, rows in groups.items():
            rows.sort(key=lambda r: r["climate_id"])
            xyz = sphere([float(r["latitude"]) for r in rows], [float(r["longitude"]) for r in rows])
            self.months[month] = rows, cKDTree(xyz)

    def query(self, incident, lag, max_distance_km=150):
        month = month_lag(incident["date"], lag)
        if month not in self.months:
            return None
        rows, tree = self.months[month]
        distance, index = tree.query(sphere([incident["latitude"]], [incident["longitude"]])[0])
        distance_km = 2 * 6371 * math.asin(min(1., distance / 2))
        if distance_km > max_distance_km:
            return None
        station = rows[index]
        values = {f"lag{lag}_{field}": float(station[field]) if station[field] else np.nan for field in MEASUREMENTS}
        return values, dict(month=month, climate_id=station["climate_id"], distance_km=distance_km)
