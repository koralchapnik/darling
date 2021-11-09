import os

DATA_SIZE = int(os.getenv('DATA_SIZE', '1000000'))
EVENT_TYPES = 'event_types'
PATTERN = 'pattern'
PATTERN_LEN = 'pattern_len'
DEFAULT_PATTERN_LEN = 'default_pattern_len'
DEFAULT_COND_LEN = 'default_cond_len'
SELECTIVITY = 'conditions_selectivity'
EXPECTED_RATE = 'event_types_expected_rate'
ATTRS_DIST_PARAMS = 'attrs_dist_params'
SORT_DELTA = 'sort_delta'
MAX_LOAD = 'max_load'
PORT = int(os.getenv('PORT', '80'))
IP = os.getenv('IP', 'localhost')
MAX_LOAD_ARR = 'max_load_arr'
TIME_ARR = 'time_arr'
MATCHES_ARR = 'matches_arr'
SHEDDED_ARR = 'shedded_arr'
REMOVED_ARR = 'removed_arr'
PENALIZED_ARR = 'penalized_arr'
THROUGHPUT_ARR = 'throughput_arr'
LOAD_SHEDDING_ARR = 'is_load_shedding'
OVERLOADED_ARR = 'overloaded'
STATS = [LOAD_SHEDDING_ARR, MAX_LOAD_ARR, TIME_ARR, MATCHES_ARR, SHEDDED_ARR,
         REMOVED_ARR, PENALIZED_ARR, OVERLOADED_ARR, THROUGHPUT_ARR]
WITH_LS = 'with load shedding'
WITHOUT_LS = 'without load shedding'
THROUGHPUT_DELTA = 'throughput_delta'
MAX_MATCHES = 'max_matches'
BOOST = 'boost'  # the peak size
ALLOW_SLEEPING = 'allow_sleeping'  # for not sleeping when calc #matches
RAND_INDEX = 'rand_index'  # the index where the peak starts
BUFFER_SIZES = 'buffer_size'
VESSLE_A = 'A'
VESSLE_B = 'B'
VESSLE_C = 'C'
STATUS = 'status'
TURN = 'turn'
SPEED = 'speed'
COURSE = 'course'
HEADING = 'heading'
LON = 'lon'
LAT = 'lat'


EXPERIMENT_INDEXES = 'experiment_indexes'
PATTERN_INDEXES = 'pattern_indexes'
COND_INDEXES = 'condition_indexes'

GOOGLE = 'Google'
MICROSOFT = 'Microsoft'
APPLE = 'Apple'
TIME = 'time'
SCORE = 'score'
PRICE = 'price'

MEAN_MAX_LOAD = 'mean_max_load'
TOTAL_MATCHES = 'total_matches'
TOTAL_EVENTS = 'total_events'
COND_LEN = 'condition_len'

NEXT_EVENT_URI = '/next_event'
NUM_MATCHES_URI = '/num_matches'
TO_FINISH_URI = '/to_finish'
START_URI = '/start'

UPDATE_RATE = 2

GOT_MESSAGE = 'OK'
FINISH = 'FINISH'
CHECK_FINISHED_WARM_UP = 'CHECK_FINISHED_WARM_UP'
FINISHED_WARM_UP = 'FINISHED_WARM_UP'
NOT_FINISHED_WARM_UP = 'NOT_FINISHED_WARM_UP'
SLEEP_WARM_UP_SEC = 10

SEPARATOR = '|'
WARM_UP = int(os.environ.get('WARM_UP'))
STATS_COUNT = min([int(os.environ.get('STATS_COUNT')), WARM_UP - 1])
ATTRS_TYPES = 'attrs_types'
ORIGIN_DATA_DIR = 'experiments/datasets'
DATASET_KIND = os.environ.get('DATASET_KIND')