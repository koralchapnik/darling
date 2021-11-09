from abc import ABC, abstractmethod

from objects.event_type import EventType
from patterns.conditions.condition import Condition
from patterns.pattern import Pattern
from patterns.plans.tree.node.leaf_node import LeafNode
from patterns.plans.tree.node.node import Node


class TreeEvaluationPlan(ABC):
    def __init__(self):
        self.root = None

    @abstractmethod
    def build_tree_plan(self, pattern: Pattern) \
            -> Node:
        pass

    def put_conditions(self, pattern: Pattern):
        for cond in pattern.conditions:
            if cond.user_input:
                for node in [self.get_leaf_by_event_type(event_type) for
                             event_type in cond.event_types]:
                    node.processed_conditions.append(cond)
            common_parent = self.get_common_parent(cond)
            common_parent.conditions.append(cond)
            common_parent.selectivity *= cond.selectivity

    @abstractmethod
    def get_common_parent(self, condition: Condition) -> Node:
        pass

    def get_leaf_by_event_type(self, event_type: EventType) -> LeafNode:
        nodes = self.root.get_subtree_leaves()
        for leaf_node in nodes:
            if leaf_node.event_type == event_type:
                return leaf_node

    def update_height_selectivities(self):
        for leaf_node in self.root.get_subtree_leaves():
            leaf_node.calc_height_selectivity()