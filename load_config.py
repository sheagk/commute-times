#!/usr/bin/env python3

import yaml
import pytz

def validate_config(config):
    if 'commutes' not in config or not len(config['commutes']):
        raise KeyError("Must supply a list of commutes in the config file")
    if 'api_key' not in config or not len(config['api_key']):
        raise KeyError("Must supply a Google API Key (w/ Directions and JavaScript Maps activated)")

def load_config(config_filename=None):
    if config_filename is None:
        import os
        basedir = os.path.realpath(__file__).rsplit('/', 1)[0]
        config_filename = basedir+'/private_info.txt'

    with open(config_filename, 'r') as f:
        config = yaml.load(f)

    if 'timezone' in config and len(config['timezone']):
        timezone = pytz.timezone(config.pop('timezone'))
    else:
        import tzlocal
        timezone = tzlocal.get_localzone()

    validate_config(config)

    return config, timezone