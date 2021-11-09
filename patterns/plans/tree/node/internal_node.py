import typing

from objects.event_type import EventType
from patterns.conditions.condition import Condition
from patterns.operator import Operator
from patterns.plans.tree.node.leaf_node import LeafNode
from patterns.plans.tree.node.node import Node


class InternalNode(Node):
    def __init__(self, left_son: Node, right_son: Node, parent: Node,
                 conditions: typing.List[Condition],
                 operator: Operator):
        super().__init__(left_son, right_son, parent, conditions)
        self.operator = operator
        self.event_types = self.get_event_types()

    def get_event_types(self) -> typing.List[EventType]:
        return self.left_son.get_event_types() + self.right_son.get_event_types()

    def get_subtree_leaves(self) -> typing.List[LeafNode]:
        return self.left_son.get_subtree_leaves() + \
               self.right_son.get_subtree_leaves()

    def __str__(self):
        return f'{self.operator}'

    def is_leaf(self) -> bool:
        return False

    def size(self) -> int:
        return sum([event_type.size for event_type in self.event_types])