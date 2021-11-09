from abc import ABC, abstractmethod

from objects.event import Event
from patterns.plans.tree.node.leaf_node import LeafNode


class LoadShedder(ABC):
    @abstractmethod
    def shed(self, event: Event, leaf_node: LeafNode, mechanism) -> bool:
        pass
