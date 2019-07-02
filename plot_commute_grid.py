#!/usr/bin/env python3

import os
import pickle
import numpy as np
from itertools import product

import bokeh.plotting as bk
from bokeh.io import export_png
from bokeh.models import map_plots, Range1d, GMapOptions
from bokeh.models.glyphs import Patches, Line, Circle
from bokeh.models import HoverTool, PanTool, WheelZoomTool, BoxSelectTool, ResetTool, ColorBar
from bokeh.models.mappers import ColorMapper, LinearColorMapper
from bokeh.palettes import all_palettes
from bokeh.layouts import gridplot

from load_config import load_config

def restructure_key(key):
    name,dest = key.split('_')
    dest = 'to '+dest[2:]
    return name + ' ' + dest

def plot_patches_on_gmap(vertex_xcoords, vertex_ycoords, api_key,
        solid_fill=None, values=None, color_mapper=None, 
        map_options=None, title=None, alpha=0.25):

    if values is not None:
        assert color_mapper is not None, "must provide a color_mapper if providing a list of colors"
    else:
        assert solid_fill is not None, "must provide a solid fill color if not providing a list of colors"

    plot = bk.gmap(api_key, map_options=map_options, title=title)
    plot.add_tools(PanTool(), WheelZoomTool(), ResetTool())

    data = dict(xs=vertex_xcoords, ys=vertex_ycoords)
    if values is not None:
        data['colors'] = values

    source_patches = bk.ColumnDataSource(data=data)

    if values is not None:
        patches_glyph = plot.patches('xs', 'ys', fill_alpha=alpha, 
            fill_color={"field": "colors", "transform": color_mapper},
            source=source_patches, line_width=0)

        color_bar = ColorBar(color_mapper=color_mapper, 
            border_line_color=None, location=(0,0), scale_alpha=alpha,
            title="minutes")
        plot.add_layout(color_bar, 'right')
    else:
        patches_glyph = plot.patches('xs', 'ys', fill_alpha=alpha, 
            fill_color=solid_fill, source=source_patches, line_width=0)

    return plot

def main():
    import argparse
    from load_config import load_config

    parser = argparse.ArgumentParser()
    parser.add_argument('pickle_dump')
    parser.add_argument('output_file')
    parser.add_argument('-c', '--config_filename', dest='config_filename', help="Config file with private info", default=None)
    parser.add_argument('--max_happy_commute', default=45, type=float, help="For plot that overlays all the commutes, what's the longest not colored red?")
    parser.add_argument('--center_lat', default=34.053695, help="latitude to center on")
    parser.add_argument('--center_lng', default=-118.430208, help="longitutde to center on")
    parser.add_argument('--zoom', default=11, type=int, help="initial zoom of maps.  goes 1 (least zoomed) to 20 (most zoomed)")
    parser.add_argument('--map_type', default='roadmap', help="initial zoom of maps.  goes 1 (least zoomed) to 20 (most zoomed)")    
    parser.add_argument('--palette', default='Viridis', help="Palette to use.  Must be in bokeh.palettes.all_palettes")
    parser.add_argument('--ncolors', type=int, default=256, 
        help="Number of colors to use.  Must be able to access bokeh.palettes.all_palettes[<palette>][<ncolors>]")
    parser.add_argument('--cbar_min', default=15, type=float)
    parser.add_argument('--cbar_max', default=75, type=float)
    
    args = parser.parse_args()
    
    config, timezome = load_config(args.config_filename)
    api_key = config['api_key']

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

    try:
        args.center_lat = float(args.center_lat)
    except ValueError:
        args.center_lat = (min([yc[0] for yc in ycoords]) + max([yc[1] for yc in ycoords]))/2

    try:
        args.center_lng = float(args.center_lng)
    except ValueError:
        args.center_lng = (min([xc[0] for xc in ycoords]) + max([xc[2] for xc in ycoords]))/2        

    plots = []
    bk.output_file(args.output_file, title="Commute times") , #mode="inlne")
    moptions = GMapOptions(lat=args.center_lat, lng=args.center_lng, 
        zoom=args.zoom, map_type=args.map_type)

    allkeys = [f'{name}_{destkey}' for name, destkey in product(names, ['towork', 'tohome'])]
    dsets = {restructure_key(key): data[key] for key in allkeys}

    color_mapper = LinearColorMapper(palette=all_palettes[args.palette][args.ncolors], 
        low=args.cbar_min, high=args.cbar_max)

    nhappy = np.zeros(len(xcoords), dtype=int)
    for name in names:
        for destkey in ['towork', 'tohome']:
            key = f'{name}_{destkey}'
            colors = data[key]
            plots.append(plot_patches_on_gmap(xcoords, ycoords, api_key, 
                values=colors, map_options=moptions, title=restructure_key(key),
                color_mapper=color_mapper))

            msk = np.array(colors) <= args.max_happy_commute
            nhappy[msk] += 1

    ## now overlap all the commutes:
    title = f'Areas where all commutes are < {args.max_happy_commute} minutes'
    plot = plot_patches_on_gmap(
        list(np.array(xcoords)[nhappy<len(allkeys)-1]), 
        list(np.array(ycoords)[nhappy<len(allkeys)-1]), 
        api_key, map_options=moptions, title=title, solid_fill='red')

    data = dict(
        xs=list(np.array(xcoords)[nhappy==len(allkeys)-1]), 
        ys=list(np.array(ycoords)[nhappy==len(allkeys)-1]))

    source_patches = bk.ColumnDataSource(data=data)
    patches_glyph = plot.patches('xs', 'ys', fill_alpha=0.25, 
        fill_color='orange', source=source_patches, line_width=0)

    plots.append(plot)


    ## now show
    grid = gridplot(plots, ncols=2)
    bk.show(grid)

if __name__ == "__main__":
    main()

