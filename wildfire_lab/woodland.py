"""Native categorical proportions around approximate reported fire locations."""
import math
import numpy as np
import rasterio
from rasterio.warp import transform
from rasterio.windows import Window


class WoodlandIndex:
    def __init__(self, path, year=1988, radius_m=1000):
        self.path, self.year, self.radius = path, year, radius_m

    def features(self, incidents):
        result = []
        with rasterio.open(self.path) as src:
            if src.crs!=rasterio.crs.CRS.from_epsg(3978) or src.count!=1 or src.res!=(30.,30.):
                raise ValueError("Expected native one-band 30 m EPSG:3978 map")
            xs, ys = transform("EPSG:4326", src.crs, [r["longitude"] for r in incidents], [r["latitude"] for r in incidents])
            radius = math.ceil(self.radius / src.res[0])
            yy, xx = np.mgrid[-radius:radius+1, -radius:radius+1]
            disk = xx**2 + yy**2 <= (self.radius / src.res[0])**2
            for row, x, y in zip(incidents, xs, ys):
                if row["year"] < self.year:
                    result.append(None)
                    continue
                i, j = src.index(x, y)
                inside = radius <= i < src.height-radius and radius <= j < src.width-radius
                raw = src.read(1, window=Window(j-radius, i-radius, 2*radius+1, 2*radius+1), boundless=not inside, fill_value=255)
                known = disk & (raw != 0) & (raw != 255)
                if known.sum() < .5 * disk.sum():
                    result.append(None)
                    continue
                fields = dict(cover_conifer=float(((raw == 210) & known).sum()/known.sum()),
                              cover_broadleaf=float(((raw == 220) & known).sum()/known.sum()),
                              cover_mixed=float(((raw == 230) & known).sum()/known.sum()),
                              cover_water=float(((raw == 20) & known).sum()/known.sum()),
                              cover_valid_fraction=float(known.sum()/disk.sum()))
                fields.update(cover_center_class=int(raw[radius,radius]),cover_center_water=int(raw[radius,radius]==20))
                result.append(fields)
        return result
