import json
from experiments.consts import *
from parsers.parser import Parser
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
dist_path = os.path.join(dir_path, 'datasets', 'data_distributions.json')

boost_env = os.environ.get('BOOST', None)
if boost_env is not None:
    general_boost = dict()
    for item in boost_env.split(','):
        key, val = item.split(':')
        key = int(key)
        val = int(val)
        general_boost[key] = val
else:
    general_boost = {
            3: 30,
            40: 10,
            60: 20,
            90: 10
    }

boost_peaks = len(general_boost)
boost_size = sum(general_boost.values())

pattern = os.environ.get('PATTERN')
filename, types = Parser.get_data_filename(DATASET_KIND, pattern)
dist_filename = Parser.get_dist_filename(DATASET_KIND, pattern)
with open(dist_path) as j:
    files_dist = json.load(j)
attrs_dist = files_dist.get(dist_filename)


data_dist_new_path = f'datasets/data_distributions.json'

data_to_col_names = {
 'soccer': ['time', 'x', 'y', 'z','v', 'a', 'vx', 'vy', 'vz', 'ax',
                     'ay', 'az'],
 'bus': ['time', 'direction', 'journey_pattern_id', 'time_frame',
                  'vehicle_journey_id', 'operator', 'congestion', 'lon', 'lat',
                  'delay', 'block_id', 'vehicle_id', 'stop_id', 'at_stop',
                  'dist'],
 'stock': ['time', 'open', 'high', 'low', 'close', 'volume'],
 'synthetic': ['time', 'x'],
 'synthetic2': ['time', 'x']
}

data_to_col_types = {
 'soccer': [int, float, float, float, float, float, float, float, float,
                  float, float, float],
 'bus': [int, int, int, int,
                  int, int, int, float, float, int,
                  int, int, int, int, float],
 'stock': [int, float, float, float, float, int],
}

event_types = {type_: data_to_col_names.get(DATASET_KIND) for type_ in types}

config = {
    EVENT_TYPES: event_types,
    PATTERN: pattern,
    ATTRS_DIST_PARAMS: attrs_dist,
    TOTAL_EVENTS: DATA_SIZE,
    BOOST: general_boost,
    ALLOW_SLEEPING: True,
    ATTRS_TYPES: data_to_col_types.get(DATASET_KIND)
}
