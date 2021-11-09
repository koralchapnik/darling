from patterns.plans.tree.node.node import Node
from objects.event_buffer import EventBuffer
from objects.event import Event
from objects.match import Match
from patterns.exceptions import NonMatchParents
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from patterns.plans.tree.tree_evaluation_mechanism import EvaluationMechanism


class TreeInstance:
    """
    This class represents an instance of a tree created during
    evaluation.
    """
    def __init__(self, tree: 'EventsProcessor', node: Node,
                 match_buffer: EventBuffer = None, kleene = None):
        self.tree = tree
        self.current_node = node
        self.match_buffer = EventBuffer(window=self.tree.time_window)\
            if match_buffer is None else match_buffer
        self.size = sum([e.size() for e in self.match_buffer.events])
        self.kleene = kleene is not None

    def has_match(self):
        return self.current_node == self.tree.root

    def get_latency(self) -> float:
        now = datetime.utcnow().timestamp()
        ts_last_event_inserted = max(map(lambda e: e.system_ts_in_adding,
                                         self.match_buffer.events))
        return now - ts_last_event_inserted

    def add_event(self, event: Event):
        self.match_buffer.add_event(event)
        self.size += event.size()

    def get_min_timestamp(self):
        return self.match_buffer.earliest_timestamp

    def get_max_timestamp(self):
        return self.match_buffer.latest_timestamp

    def validate_conditions(self) -> bool:
        events = self.match_buffer.events
        return self.current_node.validate_conditions(events)

    def get_match(self) -> Match:
        if not self.has_match() or self.match_buffer.is_expired():
            return None
        return ','.join([event.name for event in self.match_buffer.events]) +\
               '\n'

    def is_expired(self, timestamp: float) -> bool:
        """
        checks if the current time window has not passed yet
        """
        return self.match_buffer.is_expired() or (timestamp and timestamp - \
               self.match_buffer.earliest_timestamp > self.match_buffer.window)

    def create_parent_instance(self, peer_instance: 'TreeInstance'
                               ) -> 'TreeInstance':
        if self.current_node.parent != peer_instance.current_node.parent:
            raise NonMatchParents()
        common_parent = self.current_node.parent
        new_event_buffer = self.match_buffer.clone()
        for event in peer_instance.match_buffer.events:
            new_event_buffer.add_event(event)
        return TreeInstance(self.tree, common_parent, new_event_buffer)

    def create_kleene_instance(self, event: Event) -> 'TreeInstance':
        node = self.current_node
        new_event_buffer = self.match_buffer.clone()
        new_event_buffer.add_event(event)
        return TreeInstance(self.tree, node, new_event_buffer, True)

    def __str__(self):
        return f'node: {self.current_node}, buffer: {self.match_buffer}'
