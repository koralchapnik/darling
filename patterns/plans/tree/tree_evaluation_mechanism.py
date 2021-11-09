import os
import sys
import threading
import typing
from collections import deque
from datetime import datetime

from load_shedders.overload_detector import OverloadDetector
from load_shedders.selectivity_load_shedder import SelectivityLoadShedder
from objects.event import Event
from objects.event_type import EventType
from objects.match import Match
from patterns.pattern import Pattern
from patterns.plans.tree.node.leaf_node import LeafNode
from patterns.plans.tree.node.node import Node
from patterns.plans.tree.tree_evaluation_plan import TreeEvaluationPlan
from patterns.plans.tree.tree_instance import TreeInstance
from patterns.plans.tree.tree_instance_storage import TreeInstanceStorage

NEW_SHEDDED, NOT_RELATED, BUFFER_SHEDDED = int, int, int


class EvaluationMechanism:
    def __init__(self, pattern: Pattern, evaluation_plan: TreeEvaluationPlan):
        self.root = evaluation_plan.build_tree_plan(pattern)
        self.event_types_to_leaves = self._init_event_types_to_leaves()
        self.has_neg = any([event_type.neg
                            for event_type in
                            self.event_types_to_leaves.keys()])
        self.storage = TreeInstanceStorage(self.root)
        self.storage_size = -1
        self.total_storage_size = 0
        self.time_window = pattern.time_window
        self.init_buffer_sizes()
        self._lock = threading.Lock()
        self.min_event_timestamp, self.max_event_timestamp = None, None
        self.load_shedder = SelectivityLoadShedder()
        self.num_shedded = 0
        self.num_processed = 0
        self.num_matches = 0
        latency_bound = float(os.environ.get('L_MAX', 1))
        self.overload_detector = OverloadDetector(self, latency_bound)
        self.num_added = 0
        self.set_final_buffer_sizes = False
        self.max_latency = int(os.environ.get('MAX_LATENCY'))
        self.total_matches = []
        self.events = []
        self.curr_active = 0

    def init_buffer_sizes(self):
        for leaf in self.event_types_to_leaves.values():
            max_size = sys.maxsize
            leaf.update_max_size(max_size)

    def _init_event_types_to_leaves(self) -> typing.Dict[EventType, LeafNode]:
        leaves = self.root.get_subtree_leaves()
        for leaf_node in leaves:
            leaf_node.event_buffer.init_sorted_events()

        return {node.event_type: node for node in leaves}

    def get_next_event(self) -> Event:
        with self._lock:
            available_events = []
            min_ts = None
            min_ts_leaf = None
            min_event = None
            for leaf in self.event_types_to_leaves.values():
                next_event = leaf.show_next_event()
                if next_event is None:
                    continue
                available_events.append(next_event)
                ts = next_event.get_timestamp()
                if min_ts is None:
                    min_ts = ts
                    min_ts_leaf = leaf
                    min_event = next_event
                elif ts < min_ts:
                    min_ts = ts
                    min_ts_leaf = leaf
                    min_event = next_event
                elif ts == min_ts and next_event.system_ts_in_adding < \
                        min_event.system_ts_in_adding:
                    min_ts = ts
                    min_ts_leaf = leaf
                    min_event = next_event

            if not available_events:
                return None
            next = min_ts_leaf.get_next_event()
            return next

    def process(self) -> typing.List[Match]:
        self.move_to_buffers()
        next_event = self.get_next_event()
        if next_event is None:
            return None
        new_matches = self.process_new_event(next_event)
        if self.has_neg:
            self.total_matches.extend(new_matches)
        matches_len = len(new_matches)
        self.num_matches += matches_len
        with self._lock:
            self.num_processed += 1
        self.overload_detector.event_processed(next_event.type)
        return matches_len

    def process_new_event(self, event: Event) -> \
            typing.List[Match]:
        if event is None:
            return []
        if self.num_processed % 1000 == 0:
            print(f'Processed {self.num_processed} events, matches:'
                  f' {self.num_matches}')
        self.min_event_timestamp = event.get_timestamp()
        leaf = self.event_types_to_leaves.get(event.type)
        if not leaf.validate_conditions([event]):
            return []
        node = leaf if not leaf.peer_neg else leaf.parent
        leaf_instance = TreeInstance(self, node)
        leaf_instance.add_event(event)
        if leaf.peer_neg:
            self.storage.add_instance(leaf_instance)
        else:
            self.activate_tree_processing(leaf_instance)
        leaf.last_evaluated_ts = event.get_timestamp()
        storage_size_temp = self.storage.size
        self.total_storage_size += (storage_size_temp / float(10 ** 6))
        if self.overload_detector.warm_up_finished:
            self.storage_size = storage_size_temp if storage_size_temp > \
                                                     self.storage_size else self.storage_size
        return self.storage.get_matches()

    def __activate_kleene_instance(self, leaf_instance: TreeInstance,
                                   instance_queue):
        event = leaf_instance.match_buffer.events[0]
        kleene_node = leaf_instance.current_node
        kleene_instances = self.storage.node_to_instances.get(kleene_node)
        new_instances = []
        for instance in kleene_instances:
            if instance == leaf_instance:
                continue
            if not instance.is_expired(event.get_timestamp()):
                # if this instance is not expired we add it the event
                new_instance = instance.create_kleene_instance((event))
                new_instances.append(new_instance)
                instance_queue.append(new_instance)
        if new_instances:
            kleene_instances.extend(new_instances)

    def activate_tree_processing(self, leaf_instance: TreeInstance):
        instance_queue = deque()
        instance_queue.append(leaf_instance)
        self.storage.add_instance(leaf_instance)
        if leaf_instance.current_node.event_type.kleene:
            self.__activate_kleene_instance(leaf_instance, instance_queue)
        if leaf_instance.current_node.event_type.neg:
            self.storage.node_to_instances[leaf_instance.current_node.parent] = []
            return

        while instance_queue:
            current_instance = instance_queue.popleft()
            if current_instance != leaf_instance and (not \
                    current_instance.kleene):
                self.storage.add_instance(current_instance)
            peer_node = self.get_peer(current_instance)
            if not peer_node:
                continue

            self.process_event_on_peer_instance_set(current_instance,
                                                        peer_node,
                                                        instance_queue)

    def get_peer(self, current_instance: TreeInstance) -> Node:
        return current_instance.current_node.get_peer()

    def process_event_on_peer_instance_set(self, current_instance: TreeInstance,
                                           peer_node: Node,
                                           instance_queue: deque):
        peer_instances = self.storage.node_to_instances.get(peer_node, None)
        if not peer_instances:
            return
        sequence_delete, first_idx = None, None
        delete_indxes = []
        for i, peer_instance in enumerate(peer_instances):
            if peer_instance.is_expired(self.min_event_timestamp):
                if first_idx is None:
                    first_idx = i
                continue
            if first_idx is not None:
                max_idx = i - 1
                delete_indxes.append((first_idx, max_idx))
                first_idx = None
            parent_instance = current_instance.create_parent_instance(peer_instance)
            if parent_instance.validate_conditions() and not \
                    parent_instance.is_expired(self.min_event_timestamp):
                if parent_instance.current_node == self.root:
                    # its a match
                    match_latency = parent_instance.get_latency()
                    if match_latency <= self.max_latency:
                        self.storage.matches_latency_sum += match_latency
                        instance_queue.append(parent_instance)
                else:
                    instance_queue.append(parent_instance)
        self.storage.delete_instances_by_indexes(peer_node, delete_indxes)

    def to_shed(self, leaf_node: LeafNode) -> bool:
        return leaf_node.event_buffer.is_full()

    def add_event(self, event: Event):
        event.system_ts_in_adding = datetime.utcnow().timestamp()
        self.overload_detector.event_arrived(event.type)
        with self._lock:
            self.events.append(event)
            self.num_added += 1

    def move_to_buffers(self):
        with self._lock:
            i = len(self.events)
            events = self.events[:i]
        for event in events:
            leaf_node = self.get_node(event)
            event.utility = leaf_node.utility_func(event)
            if self.overload_detector.warm_up_finished and \
                    self.to_shed(leaf_node):
                self.num_shedded += 1
                if self.num_shedded % 1000 == 0:
                    print(f'Total shedded: {self.num_shedded}')
                new_shedded = int(self.load_shedder.shed(event, leaf_node, self))
                with self._lock:
                    self.num_processed += 1
            else:
                to_limit = self.set_final_buffer_sizes
                success = leaf_node.add_event(event, to_limit)
                if not success:
                    print(f'problem! not success on event {event.name}')
        with self._lock:
            del self.events[:i]

    def get_node(self, event: Event) -> LeafNode:
        return self.event_types_to_leaves.get(event.type, None)
