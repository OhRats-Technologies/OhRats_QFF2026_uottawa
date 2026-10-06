"""Render descriptive source maps, never predictions or new model inputs."""
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import rasterio
from rasterio.features import geometry_mask, bounds
from rasterio.warp import transform_geom, transform
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'assets'
PALETTE = {0:'#40545b',20:'#163c50',31:'#c5d5dc',32:'#7f8479',33:'#817b67',
           40:'#8b9470',50:'#a4ad73',80:'#667f67',81:'#4d7761',100:'#b6aa69',
           210:'#245e4b',220:'#97b77a',230:'#57896a',255:'#40545b'}
CITIES = [('Toronto / GTA',-79.3832,43.6532),('Ottawa',-75.6972,45.4215),
          ('Windsor',-83.0364,42.3149),('Thunder Bay',-89.2477,48.3809)]


def annotate(image, geoms, affine, cities):
    """Draw geography independently of classified woodland coverage."""
    drawing = ImageDraw.Draw(image)
    for geom in geoms:
        polygons = geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
        for polygon in polygons:
            for ring in polygon:
                drawing.line([(~affine)*(x,y) for x,y in ring], fill='#bdcfc8', width=2)
    font = ImageFont.load_default(size=24)
    for city in cities:
        x,y = city['x'],city['y']
        drawing.ellipse((x-5,y-5,x+5,y+5), fill='#f4e7c9', outline='#071e24', width=2)
        label_x,label_y = x+10,y-30
        drawing.text((label_x,label_y),city['name'],font=font,fill='#f4e7c9',
                     stroke_width=3,stroke_fill='#071e24')


def main():
    OUT.mkdir(exist_ok=True)
    raster = ROOT / 'data/raw/woodland/woodland-2021.tif'
    boundary = ROOT / 'data/raw/boundaries/ontario-2021.geojson'
    archive = ROOT / 'data/raw/nfdb-audit/source.zip'
    polygons = json.loads(boundary.read_text())['features']
    with rasterio.open(raster) as src:
        height, width = 1200, round(1200 * src.width / src.height)
        pixels = src.read(1, out_shape=(height, width), resampling=rasterio.enums.Resampling.nearest)
        affine = src.transform * src.transform.scale(src.width/width,src.height/height)
        geoms = [transform_geom('EPSG:4326',src.crs,f['geometry']) for f in polygons]
        inside = geometry_mask(geoms,out_shape=pixels.shape,transform=affine,invert=True)
        rgba = np.zeros((*pixels.shape,4),dtype=np.uint8)
        rgba[inside] = [64,84,91,255]
        for code,color in PALETTE.items():
            mask = (pixels==code) & inside
            rgba[mask] = [int(color[i:i+2],16) for i in [1,3,5]]+[255]
        cities=[]
        for name,lon,lat in CITIES:
            x,y=transform('EPSG:4326',src.crs,[lon],[lat])
            col,row=(~affine)*(x[0],y[0])
            control_inside=bool(geometry_mask(geoms,out_shape=(1,1),
                transform=rasterio.Affine.translation(x[0]-1,y[0]+1)*rasterio.Affine.scale(2,-2),
                invert=True)[0,0])
            back_lon,back_lat=transform(src.crs,'EPSG:4326',x,y)
            error=max(abs(back_lon[0]-lon),abs(back_lat[0]-lat))
            assert control_inside and 0<=col<width and 0<=row<height and error<1e-9
            cities.append(dict(name=name,longitude=lon,latitude=lat,x=round(col,2),y=round(row,2),
                inside_official_boundary=control_inside,inside_crop=True,
                raw_class=int(next(src.sample([(x[0],y[0])]))[0]),roundtrip_error_degrees=error))
        cover_image=Image.fromarray(rgba)
        annotate(cover_image,geoms,affine,cities)
        cover_image.save(OUT/'ontario-cover.png')
        with zipfile.ZipFile(archive) as z:
            name, = [n for n in z.namelist() if n.startswith('NFDB_point_') and n.endswith('.txt')]
            with z.open(name) as stream:
                rows = [r for r in csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8-sig'))
                        if r['SRC_AGENCY']=='ON' and r['YEAR']=='2021']
        points=[]
        for r in rows:
            try: lon,lat,size=map(float,[r['LONGITUDE'],r['LATITUDE'],r['SIZE_HA']])
            except ValueError: continue
            if not (-180<=lon<=180 and -90<=lat<=90 and size>=0):continue
            x,y=transform('EPSG:4326',src.crs,[lon],[lat]);col,row=(~affine)*(x[0],y[0])
            if 0<=col<width and 0<=row<height:
                points.append(dict(x=round(col,2),y=round(row,2),ha=size))
        records_image=Image.fromarray(rgba.copy())
        drawing=ImageDraw.Draw(records_image)
        for point in points:
            x,y=point['x'],point['y'];r=2+min(5,np.log1p(point['ha'])/2)
            drawing.ellipse((x-r,y-r,x+r,y+r),fill='#d59d61')
        annotate(records_image,geoms,affine,cities)
        records_image.save(OUT/'ontario-records.png')
        bbox = rasterio.warp.transform_bounds('EPSG:4326',src.crs,-79.3,45.2,-77.2,46.3)
        window=from_bounds(*bbox,src.transform)
        zoom=src.read(1,window=window,out_shape=(620,900),resampling=rasterio.enums.Resampling.nearest)
        rgb=np.zeros((*zoom.shape,3),dtype=np.uint8)
        for code,color in PALETTE.items():rgb[zoom==code]=[int(color[i:i+2],16) for i in [1,3,5]]
        Image.fromarray(rgb).save(OUT/'algonquin-cover.png')
    receipt=dict(year=2021,width=width,height=height,points=points,cities=cities,
                 boundary_wgs84_bounds=bounds(polygons[0]['geometry']),
                 source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [raster,boundary,archive]},
                 legend=PALETTE,region='Ontario; Algonquin-area rectangular detail',
                 method='Nearest-neighbour source pixels; full official Ontario boundary mask/outline; EPSG:3978 projection. City coordinates transformed from WGS84.',
                 coverage_note='Grey = no mapped woodland class (0 or 255), not absence of vegetation. The provincial boundary includes water; this is not a land-only outline.',
                 limitation='Raw recorded coordinate markers, not predicted hotspots, ignition certainty or fire perimeters. Map is context, not final model input; province display is downsampled.')
    (OUT/'map.json').write_text(json.dumps(receipt,separators=(',',':'))+'\n')
    print('Rendered source cover and',len(points),'raw recorded 2021 locations; no fits.')


if __name__=='__main__':main()
