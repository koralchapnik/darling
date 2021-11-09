import typing
from abc import ABC, abstractmethod

from objects.event import Event
from objects.event_type import EventType
from patterns.conditions.condition import Condition


class Node(ABC):
    def __init__(self, left_son, right_son, parent,
                 conditions: typing.List[Condition]):
        self.left_son = left_son
        self.right_son = right_son
        self.parent = parent
        self.conditions = conditions if conditions is not None else []
        self.selectivity = 1
        self.cost = 1
        self.load = 0
        self.subtree_load = 0
        self.subtree_leaves = None

    def gen_selectivity(self):
        for cond in self.conditions:
            self.selectivity *= cond.selectivity
        if not self.is_leaf():
            self.selectivity *= self.right_son.selectivity
            self.selectivity *= self.left_son.selectivity

    def update_selectivity(self, n: float):
        current_node = self
        while current_node is not None:
            current_node.selectivity *= n
            current_node = current_node.parent

    @abstractmethod
    def get_event_types(self) -> typing.List[EventType]:
        pass

    def get_subtree_nodes_list(self) -> typing.List:
        if self.subtree_leaves is not None:
            return self.subtree_leaves
        if self.left_son is None and self.right_son is None:
            return [self]
        self.subtree_leaves =  self.left_son.get_subtree_nodes_list() + \
               self.right_son.get_subtree_nodes_list() + [self]
        return self.subtree_leaves

    @abstractmethod
    def get_subtree_leaves(self) -> typing.List['Node']:
        pass

    def validate_conditions(self, events: typing.List[Event]) -> bool:
        for condition in self.conditions:
            # assuming events are ordered as tree leaves
            relevant_events = list(filter(lambda e: e.type in condition.event_types,
                                          events))

            if not condition.verify(*relevant_events):
                return False
        return True

    def get_peer(self) -> 'Node':
        if self.parent is None:
            return None
        if self == self.parent.right_son:
            return self.parent.left_son
        if self == self.parent.left_son:
            return self.parent.right_son
        return None

    @abstractmethod
    def size(self) -> int:
        pass

    @abstractmethod
    def is_leaf(self) -> bool:
        pass
