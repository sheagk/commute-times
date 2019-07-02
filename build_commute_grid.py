from collections import defaultdict
import os
import yaml
import pytz
import pickle
import argparse
from tqdm import tqdm

import numpy as np
import shapely.vectorized
import shapely.geometry as sgeom
import cartopy.io.shapereader as shpreader

from query_commute_times import CommuteTimesClass
from load_config import load_config

## all of CA:
# northern_limit, western_limit = [42.263522, -125.653625]
# southern_limit, eastern_limit = [32.543199, -114.048381]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('outname')
    parser.add_argument('--config_filename', default=None, help="File with api key, commutes, and optionally timezone")
    parser.add_argument('--state_name', default="California", help="State to use for the boundary to distinguish land from water")
    parser.add_argument('--npts', default=10, type=int)
    parser.add_argument('--northern_limit', default=34.219498, type=float)
    parser.add_argument('--southern_limit', default=33.816168, type=float)
    parser.add_argument('--eastern_limit', default=-118.254013, type=float)
    parser.add_argument('--western_limit', default=-118.606110, type=float)

    args = parser.parse_args()

    config, timezome = load_config(args.config_filename)
    CommuteTimes = CommuteTimesClass(key=config['api_key'])
    commutes = config['commutes']

    shpfilename = shpreader.natural_earth(resolution='10m',
                                          category='cultural',
                                          name='admin_1_states_provinces')
    reader = shpreader.Reader(shpfilename)
    states = list(reader.records())

    state, = [state for state in states if state.attributes['name'] == args.state_name]
    geom = state.geometry

    xv = np.linspace(args.western_limit, args.eastern_limit, args.npts)
    yv = np.linspace(args.southern_limit, args.northern_limit, args.npts)
    pairs = np.array(np.meshgrid(xv, yv)).T.reshape(-1, 2)
    xvals, yvals = pairs.T
    mask = shapely.vectorized.contains(geom, xvals, yvals)

    result = defaultdict(list)
    names = commutes.keys()

    for ii, (ll, la) in enumerate(tqdm(pairs)):
        if mask[ii]:
            try:
                address = f'{la},{ll}'

                res = CommuteTimes.get_commute_times(address, commutes, 
                    2019, 8, 7, 2, timezone, models=['best_guess'], 

                    do_print=False, do_pbar=False)

                result['lat'].append(la)
                result['long'].append(ll)
                for key in res:
                    result[key].append(res[key])
            except ValueError:
                pass

    print(f"Writing output to {args.outname}...")
    with open(args.outname, 'wb') as out:
        pickle.dump(result, out)
    print("Done!")

if __name__ == "__main__":
    main()