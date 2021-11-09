import math
import os
import typing

from objects.event import Event
from objects.event_buffer import EventBuffer
from objects.event_type import EventType
from patterns.conditions.condition import Condition
from patterns.plans.tree.node.node import Node


class LeafNode(Node):
    def __init__(self, parent: Node, conditions: typing.List[Condition],
                 event_type: EventType, window: float):
        super().__init__(None, None, parent, conditions)
        self.event_type = event_type
        self.max_size = None
        self.total_events = 0
        self.last_ts = None
        self.psi = int(os.environ.get('PSI', '100'))
        self.event_buffer = EventBuffer(None, self.max_size, window, self.psi)
        self.event_buffer.start_seq = self.event_type.start_seq
        self.height_selectivity = 1
        self.last_evaluated_ts = None
        self.processed_conditions = []
        self.sum_buffer_sizes = 0
        self.number_insertions = 0
        self.peer_neg = False

    def get_event_types(self) -> typing.List[EventType]:
        return [self.event_type]

    def get_subtree_leaves(self) -> typing.List['LeafNode']:
        return [self]

    def __str__(self):
        return f'{self.event_type.name}'

    def is_leaf(self) -> bool:
        return True

    def add_event(self, event: Event, limit: bool) -> bool:
        success = self.event_buffer.add_event(event, limit)
        if success:
            self.sum_buffer_sizes += self.event_buffer.size
            self.number_insertions += 1
        return success

    def get_next_event(self) -> Event:
        event = self.event_buffer.get_next_event()
        return event

    def show_next_event(self) -> Event:
        return self.event_buffer.show_next_event()

    def get_min_ts(self) -> float:
        return self.event_buffer.earliest_timestamp

    def get_max_ts(self) -> float:
        return self.event_buffer.latest_timestamp

    def update_max_size(self, rate: float):
        self.max_size = rate
        self.event_buffer.max_size = math.ceil(self.max_size)

    def calc_height_selectivity(self):
        current_node = self
        while current_node is not None:
            self.height_selectivity *= current_node.selectivity
            current_node = current_node.parent

    def turn_sort_on(self):
        self.event_buffer.turn_sort_on()

    def turn_sort_off(self):
        self.event_buffer.turn_sort_off()

    def sort_activated(self) -> bool:
        return self.event_buffer.sort_activated()

    def size(self) -> int:
        return self.event_type.size

    def utility_func(self, event: Event) -> float:
        prob = 1
        for cond in self.processed_conditions:
            if len(cond) == 1:
                if not cond.verify(event):
                    return 0  # the event has no chance to be a part of a match
                else:
                    continue
            prob *= cond.custom_verifiers_by_type.get(event.type)(event)
        return math.floor(prob * self.psi)
