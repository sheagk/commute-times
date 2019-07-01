# addresses = ['Brentwood', 'Brentwood Park', 'North of Montana', 'Sawtell', 
#              'Mid-city Santa Monica', 'Mar Vista', 'Mar Vista Houses', 'Oakwood',
#              '' ]
# Sherman Oaks off Ventura
# Studio City off Ventura
# Los Feliz off Vermont
# Crenshaw & Slawson      

import numpy as np
from collections import defaultdict
import os, yaml, pytz, pickle
from tqdm import tqdm

basedir = os.path.realpath(__file__).rsplit('/', 1)[0]
api_file = basedir+'/api_key'
pifile = basedir+'/private_info.txt'

with open(api_file, 'r') as f:
    key = f.readline()

with open(pifile, 'r') as f:
    local_info = yaml.load(f)

if 'timezone' in local_info:
    timezone = pytz.timezone(local_info.pop('timezone'))
else:
    import tzlocal
    timezone = tzlocal.get_localzone()

from query_commute_times import CommuteTimesClass
CommuteTimes = CommuteTimesClass(key=key)

## western LA:
northern_limit = 34.219498
western_limit = -118.606110
southern_limit = 33.816168
eastern_limit = -118.254013

## all of CA:
# northern_limit, western_limit = [42.263522, -125.653625]
# southern_limit, eastern_limit = [32.543199, -114.048381]

import shapely.vectorized
import shapely.geometry as sgeom
import cartopy.io.shapereader as shpreader


shpfilename = shpreader.natural_earth(resolution='10m',
                                      category='cultural',
                                      name='admin_1_states_provinces')
reader = shpreader.Reader(shpfilename)
states = list(reader.records())

CA, = [state for state in states if state.attributes['name'] == 'California']
geom = CA.geometry

npts = 3

xv = np.linspace(western_limit, eastern_limit, npts)
yv = np.linspace(southern_limit, northern_limit, npts)
pairs = np.array(np.meshgrid(xv, yv)).T.reshape(-1, 2)
xvals, yvals = pairs.T
mask = shapely.vectorized.contains(geom, xvals, yvals)

result = defaultdict(list)
names = local_info.keys()

keys = [n+'_towork' for n in names] + [n+'_tohome' for n in names] + ['lat', 'long']
for ii, (ll, la) in enumerate(tqdm(pairs)):
    # if bm.is_land(ll, la):
    if mask[ii]:
        result['lat'].append(la)
        result['long'].append(ll)
        try:
            address = f'{la},{ll}'
            res = CommuteTimes.get_commute_times(address, local_info, 
                2019, 8, 7, 2, timezone, models=['best_guess'], 
                do_print=False, do_pbar=False)

            for key in res:
                result[key].append(res[key])
        except ValueError:
            for key in filter(lambda x: x not in ['lat', 'long'], keys):
                result[key].append(np.nan)
    else:
        for key in keys:
            if key == 'lat':
                result[key].append(la)
            elif key == 'long':
                result[key].append(ll)
            else:
                result[key].append(np.nan)
    # print(result)
        
print("Writing output...")
with open('commute_times.pkl', 'wb') as out:
    pickle.dump(result, out)
print("Done!")