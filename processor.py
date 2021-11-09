import signal
import socket
import threading
import time
import typing
from datetime import datetime

import experiments.results_consts as rc
from experiments.configurations_map import config, boost_size, boost_peaks
from experiments.consts import *
from objects.match import Match
from parsers.parser import Parser
from patterns.plans.tree.left_deep_tree_evaluation_plan import \
    LeftDeepTreeEvaluationPlan
from patterns.plans.tree.tree_evaluation_mechanism import EvaluationMechanism


class Processor:
    def __init__(self):

        self.config = config
        self.num_events = config[TOTAL_EVENTS]
        self.last_tp_time = None # for updating throughput
        self.tp_events_sum, self.num_processed, self.new_shedded, \
        self.buffer_shedded, self.not_related, self.num_overloaded = [0] * 6
        self.num_reset = 0
        self.throughputs = []
        self._lock = threading.Lock()
        self.boost = config[BOOST] # dict mapping index -> boost
        self.allow_sleeping = config[ALLOW_SLEEPING]
        self.parser = Parser(config[EVENT_TYPES])
        self.types, self.pattern = self.parser.parse_pattern(config[PATTERN],
                                                           config.get(SELECTIVITY),
                                                           config[
                                                                 ATTRS_DIST_PARAMS], config[ATTRS_TYPES])

        self.evaluation_mechanism = EvaluationMechanism(self.pattern,
                                                        LeftDeepTreeEvaluationPlan())
        self.matches = 0
        self.start_time, self.end_time, self.time_warm_up = 0, 0, 0

    def _update_throughput(self, start_ts: float, end_ts: float):
        self.tp_events_sum += 1
        if self.last_tp_time is None:
            self.last_tp_time = end_ts
        timediff = end_ts - start_ts
        if timediff >= self.throughput_delta:
            throughput = self.tp_events_sum / timediff
            self.throughputs.append(throughput)
            self.last_tp_time = end_ts
            self.tp_events_sum = 0

    def _calc_selectivity(self):
        events, result = {}, {}
        for event_type in self.types:
            events[event_type] = []
        for event in self.parser.parse_event(self.data_file):
            events.get(event.type.name).append(event)
        for cond in self.pattern.conditions:
            if not cond.user_input:
                continue
            print(cond.attr_1)
            passed_cond = 0
            if len(cond.event_types) == 1:
                type_1, type_2 = cond.event_types[0].name, None
                sum = len(events.get(type_1))
                for event in events.get(type_1):
                    if cond.verify(event):
                        passed_cond += 1
            else:
                type_1, type_2 = cond.event_types[0].name, cond.event_types[1].name
                sum = len(events.get(type_1)) * \
                      len(events.get(type_2))
                for event1 in events.get(type_1):
                    for event2 in events.get(type_2):
                        if cond.verify(event1, event2):
                            passed_cond += 1
            cond.selectivity = passed_cond / sum
            print(f'selectivity for condition {cond.desc} is {cond.selectivity}')
            print(f'selectivity for condition {cond.desc} is {cond.selectivity}')

    def add_event(self, event_str: str, event_ws: int):
        event = self.parser.parse_event_from_str(event_str)
        self.evaluation_mechanism.add_event(event)

    def add_events_route(self, msg):
        event_str, event_ws = msg.split(SEPARATOR)
        event_ws = int(event_ws)
        self.add_event(event_str, event_ws)

    def add_events(self):
        server_address = ('0.0.0.0', 80)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(server_address)
        sock.listen(1)

        conn, address = sock.accept()
        x = conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        print(f'got connection from {str(address)}')
        # try:
        while True:
            data = conn.recv(2048).decode()

            if data:
                if data == FINISH:
                    conn.close()
                    break
                elif data == CHECK_FINISHED_WARM_UP:
                    if self.evaluation_mechanism.num_processed == WARM_UP:
                        conn.send(FINISHED_WARM_UP.encode())
                        self.evaluation_mechanism.overload_detector \
                            .warm_up_finished = True
                        print(f'finished warm up!, matches: {self.matches}')
                        self.time_warm_up = datetime.utcnow().timestamp()
                    else:
                        conn.send(NOT_FINISHED_WARM_UP.encode())
                else:
                    conn.send(GOT_MESSAGE.encode())
                    self.add_events_route(data)


    def update_results(self, result):
        result.update({
            rc.NEW_SHEDDED: self.new_shedded,
            rc.BUFFER_SHEDDED: self.buffer_shedded,
            rc.NOT_RELATED: self.not_related
        })

    def process_events(self, matches: typing.List[Match], result: typing.Dict):
        time.sleep(5)  # waiting for starting getting events

        while self.evaluation_mechanism.num_processed != self.num_events:
            new_matches = self.evaluation_mechanism.process()
            if new_matches is None:
                continue  # there is no available event
            self.matches += new_matches

    def write_results(self, signum=None, frame=None):
        if signum is not None:
            stopped = 1
            signum = signum
            self.end_time = datetime.utcnow().timestamp()
        else:
            stopped = 0
            signum = -1
        results = {
            'queue_size': self.evaluation_mechanism.N_in,
            'processing_latency': self.evaluation_mechanism.processing_latency,
            'num_shedded': self.evaluation_mechanism.num_shedded,
            'found_matches': self.matches,
            'matches_latency':
                self.evaluation_mechanism.storage.matches_latency_sum
                / self.matches if self.matches else 0,
            'pattern': os.environ.get('PATTERN'),
            'lb': float(os.environ.get('L_MAX')),
            'data': DATASET_KIND,
            'time': self.end_time - self.start_time,
            'time_warm_up': self.time_warm_up - self.start_time,
            'warm_up': WARM_UP,
            'stopped': stopped,
            'signum': signum,
            'pattern_len': len(self.pattern.event_types),
            'window_time': self.pattern.time_window,
            'sleep_reg': float(os.environ.get('SLEEP_REG')),
            'sleep_load': float(os.environ.get('SLEEP_LOAD')),
            'port': os.environ.get('PORT'),
            'boost_size': boost_size,
            'boost_peaks': boost_peaks,
            'throughput': DATA_SIZE / (self.end_time - self.start_time),
            'data_size': DATA_SIZE,
            'num_processed': self.evaluation_mechanism.num_processed,
            'storage_size': self.evaluation_mechanism.storage_size,
            'storage_size_avg': self.evaluation_mechanism.total_storage_size
                                / float(self.evaluation_mechanism.num_processed)
        }

        print(results)

        # out_file = f'results_final/{port}.json'
        # with open(out_file, 'w', encoding='utf-8') as f:
        #     json.dump(results, f, ensure_ascii=False, indent=4)

    def run(self) -> None:
        print(config[PATTERN])
        result = dict()
        self.start_time = datetime.utcnow().timestamp()
        matches = []
        t2 = threading.Thread(target=self.process_events,
                              args=(matches, result,))
        t2.start()
        self.add_events()
        t2.join()

        self.end_time = datetime.utcnow().timestamp()

        print(f'num of matches {self.matches}')
        self.write_results()
        # if self.evaluation_mechanism.has_neg:
        #     port = int(os.environ.get('PORT'))
        #     out_file = f'results/{port}-matches.txt'
        #     with open(out_file, 'w') as f:
        #         f.writelines(self.evaluation_mechanism.total_matches)


if __name__ == '__main__':
    processor = Processor()
    signal.signal(signal.SIGTERM, processor.write_results)
    processor.run()
