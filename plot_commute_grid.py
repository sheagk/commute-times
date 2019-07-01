#!/usr/bin/env python3

import os
import pickle
import numpy as np
import argparse
from itertools import product
from collections import OrderedDict

import bokeh.plotting as bk
from bokeh.models import map_plots, Range1d, GMapOptions
from bokeh.models.glyphs import Patches, Line, Circle
from bokeh.models import HoverTool, PanTool, WheelZoomTool, BoxSelectTool, ResetTool, ColorBar
from bokeh.models.mappers import ColorMapper, LinearColorMapper
from bokeh.palettes import Viridis5
from bokeh.layouts import gridplot

basedir = os.path.realpath(__file__).rsplit('/', 1)[0]
api_file = basedir+'/api_key'
with open(api_file, 'r') as f:
    key = f.readline()

parser = argparse.ArgumentParser()
parser.add_argument('pickle_dump')
parser.add_argument('output_file')
args = parser.parse_args()

with open(args.pickle_dump, 'rb') as f:
    print(f"Loading from {args.pickle_dump}")
    data = pickle.load(f)

lats = data.pop('lat')
longs = data.pop('long')
names = set(k.split('_')[0] for k in data)

plots = []
bk.output_file(args.output_file, mode="cdn") # title="Berlin population")
moptions = GMapOptions(lat=34.053695, lng=-118.430208, zoom=13, map_type="roadmap")
# moptions = map_plots.GMapOptions(map_type=)

def restructure_key(key):
    name,dest = key.split('_')
    dest = 'to '+dest[2:]
    return name + ' ' + dest

allkeys = [f'{name}_{destkey}' for name, destkey in product(names, ['towork', 'tohome'])]
dsets = {restructure_key(key): data[key] for key in allkeys}

color_mapper = LinearColorMapper(palette=Viridis5, low=15, high=75)
for name in names:
    for destkey in ['towork', 'tohome']:
        key = f'{name}_{destkey}'
        colors = data[key]

        plot = bk.gmap(google_api_key=key, map_options=moptions, title=restructure_key(key))

        source_patches = bk.ColumnDataSource(
            data=dict(xs=lats, ys=longs,
                      colors=colors, **dsets))

        patches = Patches(xs="xs", ys="ys", fill_alpha=0.5,
                         fill_color={"field": "colors", "transform": color_mapper},
                         line_color='black', line_width=0.25)

        patches_glyph = plot.add_glyph(source_patches, patches)

        plot.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool(), HoverTool(), 
                ResetTool())

        hover = plot.select(dict(type=HoverTool))
        #hover.snap_to_data = False # not supported in new bokeh versions
        hover.tooltips = OrderedDict([
            (k, "@"+k) for k in dsets])
        #     ("Borough", "@boroughsnames"),
        #     ("Density (pop/km2)", "@density"),
        # #    ("Population", "@population"),
        #     ("Area (km2)", "@area"),
        # #    ("(long,lat)", "($x, $y)"),
        # ])
        color_bar = ColorBar(color_mapper=color_mapper, border_line_color=None, location=(0,0))
        plot.add_layout(color_bar, 'right')

        plots.append(plot)

grid = gridplot(plots, ncols=2)
bk.show(grid)

