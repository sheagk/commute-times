#!/usr/bin/env python3

import os
import pickle
import numpy as np
import argparse
from itertools import product
from collections import OrderedDict

import bokeh.plotting as bk
from bokeh.io import export_png
from bokeh.models import map_plots, Range1d, GMapOptions
from bokeh.models.glyphs import Patches, Line, Circle
from bokeh.models import HoverTool, PanTool, WheelZoomTool, BoxSelectTool, ResetTool, ColorBar
from bokeh.models.mappers import ColorMapper, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.layouts import gridplot

def restructure_key(key):
    name,dest = key.split('_')
    dest = 'to '+dest[2:]
    return name + ' ' + dest

basedir = os.path.realpath(__file__).rsplit('/', 1)[0]
api_file = basedir+'/api_key'
with open(api_file, 'r') as f:
    api_key = f.readline()

parser = argparse.ArgumentParser()
parser.add_argument('pickle_dump')
parser.add_argument('output_file')
args = parser.parse_args()

with open(args.pickle_dump, 'rb') as f:
    print(f"Loading from {args.pickle_dump}")
    data = pickle.load(f)

center_lats = np.array(data.pop('lat'))
center_longs = np.array(data.pop('long'))
names = set(k.split('_')[0] for k in data)

dx = np.max(center_longs[1:] - center_longs[:-1])/2
dy = np.max(center_lats[1:] - center_lats[:-1])/2

xcoords = [[xc-dx, xc-dx, xc+dx, xc+dx] for xc in center_longs]
ycoords = [[yc-dy, yc+dy, yc+dy, yc-dy] for yc in center_lats]
print(f"Plotting {len(xcoords)} squares")

plots = []
bk.output_file(args.output_file, title="Commute times") , #mode="inlne")
moptions = GMapOptions(lat=34.053695, lng=-118.430208, zoom=13, map_type="roadmap")

allkeys = [f'{name}_{destkey}' for name, destkey in product(names, ['towork', 'tohome'])]
dsets = {restructure_key(key): data[key] for key in allkeys}

color_mapper = LinearColorMapper(palette=Viridis256, low=15, high=75)
for name in names:
    for destkey in ['towork', 'tohome']:
        key = f'{name}_{destkey}'
        colors = data[key]

        plot = bk.gmap(api_key, map_options=moptions, title=restructure_key(key))
        plot.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool(), HoverTool(), 
                ResetTool())

        # source_patches = bk.ColumnDataSource(
        #     data=dict(xs=longs, ys=lats,
        #               colors=colors, **dsets))

        # patches_glyph = plot.square('xs', 'ys', 
        #     fill_color={"field": "colors", "transform": color_mapper},
        #     line_color='black', line_width=0.25, source=source_patches)

        source_patches = bk.ColumnDataSource(
            data=dict(xs=xcoords, ys=ycoords,
                      colors=colors))
        patches_glyph = plot.patches('xs', 'ys', fill_alpha=0.5, 
            fill_color={"field": "colors", "transform": color_mapper},
            line_color='black', line_width=0.25, source=source_patches)

        # # patches = Patches(xs="xs", ys="ys", fill_alpha=0.5,
        # #                  fill_color={"field": "colors", "transform": color_mapper},
        # #                  line_color='black', line_width=0.25)
        # # patches_glyph = plot.add_glyph(source_patches, patches)


        hover = plot.select(dict(type=HoverTool))
        hover.tooltips = None
        # hover.tooltips = OrderedDict([
        #     (k, "@"+k) for k in dsets])

        color_bar = ColorBar(color_mapper=color_mapper, border_line_color=None, location=(0,0))
        plot.add_layout(color_bar, 'right')
        plots.append(plot)

grid = gridplot(plots, ncols=2)
bk.show(grid)

