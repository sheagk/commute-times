#!/usr/bin/env python3

import pickle
import numpy as np
import argparse
from itertools import product

import bokeh.plotting as bk
from bokeh.models import map_plots, Range1d
from bokeh.models.glyphs import Patches, Line, Circle
# from bokeh.models import (
#     GMapPlot, Range1d, ColumnDataSource, LinearAxis,
#     HoverTool, PanTool, WheelZoomTool, BoxSelectTool, ResetTool, PreviewSaveTool,
#     BoxSelectionOverlay, GMapOptions,
#     NumeralTickFormatter, PrintfTickFormatter)
from bokeh.layouts import gridplot
from bokeh.resources import CDN
from bokeh.embed import components, autoload_static, autoload_server

basedir = os.path.realpath(__file__).rsplit('/', 1)[0]
api_file = basedir+'/api_key'
with open(api_file, 'r') as f:
    key = f.readline()

parser = argparse.ArgumentParser()
parser.add_argument('pickle_dump')
parser.add_argument('output_file')
args = parser.parse_args()

with open(args.pickle_dump, 'r') as f:
    data = pickle.load(args.pickle_dump)

lats = data.pop('lat')
longs = data.pop('long')
names = set(k.split('_')[0] for k in data)

plots = []
bk.output_file(args.output_file, mode="cdn") # title="Berlin population")
moptions = map_plots.GMapOptions(lat=34.053695, long=-118.430208, zoom=13)
# moptions = map_plots.GMapOptions(map_type=)

def restructure_key(key):
    name,dest = key.split('_')
    dest = 'to '+dest[2:]
    return name + ' ' + dest

allkeys = [f'{name}_{destkey}' for name, destkey in product(names, ['towork', 'tohome'])]
dsets = {restructure_key(key): data[key] for key in allkeys}

for name in names:
    for destkey in ['towork', 'tohome']:
        key = f'{name}_{destkey}'
        colors = data[key]

        plot = map_plots.GMapPlot(api_key=key, map_options=moptions,    
                                  x_range = Range1d(), y_range = Range1d(),
                                  title=restructure_key(key))
        plot.map_options.map_type = "roadmap"

        source_patches = bk.ColumnDataSource(
            data=dict(xs=lats, boroughs_ys=longs,
                      colors=colors, **dsets))

        patches = Patches(xs="xs", ys+"ys", fill_color="colors", 
                          fill_alpha=0.5, line_color='black', line_width=0.25)

        patches_glyph = plot.add_glyph(source_patches, patches)

        plot.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool(), HoverTool(), 
                ResetTool(), PreviewSaveTool())

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
        plots.append(plot)

gridplot(plots, ncols=2)

bk.show(p)

