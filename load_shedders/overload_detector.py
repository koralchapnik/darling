import math
import time

from experiments.consts import *
from objects.event_type import EventType
from patterns.plans.tree.node.leaf_node import LeafNode


class Stats:
    stop_calc = False
    f = float(os.environ.get('BETA'))

    def __init__(self, event_type: EventType, leaf: LeafNode, latency_bound:
                 float):
        self.event_type = event_type
        self.leaf = leaf
        self.arrival_rate = 0
        self.arrived = 0
        self.arrived_start_ts, self.arrived_end_ts = 0, 0  # seconds
        self.latency_bound = latency_bound
        self.buffer_len = None
        self.stop_calc = False
        self.processed = 0
        self.processed_start_ts = None
        self.processed_end_ts = None

    def restart_vals(self):
        self.arrival_rate = 0
        self.arrived = 0
        self.arrived_start_ts, self.arrived_end_ts = 0, 0

    def event_arrived(self):
        if self.arrived_start_ts == 0:
            self.arrived_start_ts = time.time()
        self.arrived += 1

    def set_arrival_rate(self) -> float:
        self.arrived_end_ts = time.time()
        processing_latency = (self.processed_end_ts - self.processed_start_ts) / self.processed
        self.arrival_rate = self.arrived / (self.arrived_end_ts -
                                            self.arrived_start_ts)
        self.arrival_rate *= processing_latency
        return self.arrival_rate

    def set_buffers_len(self, q_size, sum_arrival_rates) -> int:
        partial_arrival_rate = self.arrival_rate / sum_arrival_rates
        buffer_len = math.ceil(q_size * partial_arrival_rate)
        print(f'Local constraint for event type {self.leaf.event_type.name} is:'
              f' {buffer_len}')
        self.leaf.update_max_size(buffer_len)
        self.buffer_len = buffer_len
        return buffer_len


class OverloadDetector:
    def __init__(self, evaluation_mechanism, latency_bound: float):
        self.evaluation_mechanism = evaluation_mechanism
        self.event_type_to_stats = {event_type: Stats(event_type, leaf, latency_bound)
                                    for (event_type, leaf) in
                                    self.evaluation_mechanism.event_types_to_leaves.items()}
        self.counter_max = STATS_COUNT
        self.set_buffers = False
        self.throughput = 0
        self.processed = 0
        self.processed_start_ts, self.processed_end_ts = 0, 0  # seconds
        self.latency_bound = latency_bound
        self.first_event_arrived = False
        self.warm_up_finished = False

    def event_processed(self, event_type):
        if self.set_buffers:
            return
        if self.processed_start_ts == 0:
            self.processed_start_ts = time.time()
        self.processed += 1
        if self.processed <= self.counter_max:
            stats = self.event_type_to_stats.get(event_type)
            if stats.processed_start_ts is None:
                stats.processed_start_ts = time.time()
            stats.processed_end_ts = time.time()
            stats.processed += 1
        if self.processed == self.counter_max:
            self.processed_end_ts = time.time()
            self.throughput = self.processed / (self.processed_end_ts -
                                                self.processed_start_ts)
            processing_latency = 1 / self.throughput
            self.evaluation_mechanism.processing_latency = processing_latency
            self.N_in = math.ceil((self.latency_bound / processing_latency) *
                                  Stats.f)
            self.evaluation_mechanism.N_in = self.N_in
            self.set_arrival_rates()

        if self.processed == WARM_UP:
            self.set_buffers = True
            all_constraints = self.set_buffers_len(self.N_in)
            print(f'N_in size is: {all_constraints}')

    def set_arrival_rates(self):
        self.sum_arrival_rates = 0
        for stat in self.event_type_to_stats.values():
            self.sum_arrival_rates += stat.set_arrival_rate()

    def set_buffers_len(self, q_max: int) -> int:
        all_constraints = 0
        for stat in self.event_type_to_stats.values():
            all_constraints += stat.set_buffers_len(q_max, self.sum_arrival_rates)
        return all_constraints

    def event_arrived(self, event_type):
        if self.set_buffers:
            return
        if not self.first_event_arrived:
            self.first_event_arrived = True
            ts = time.time()
            for stat in self.event_type_to_stats.values():
                stat.arrived_start_ts = ts
        self.event_type_to_stats.get(event_type).event_arrived()
