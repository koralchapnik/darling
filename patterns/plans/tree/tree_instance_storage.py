from patterns.plans.tree.node.node import Node
from objects.match import Match
import typing


class TreeInstanceStorage:
    """
    This class represents the storage of all the relevant instances
    created during the evaluation of the pattern.
    Creation and deletion of objects is dynamic.
    """

    def __init__(self, root: Node):
        self.root = root
        self.node_to_instances = {}
        for node in self.root.get_subtree_nodes_list():
            self.node_to_instances[node] = []
        self.size = 0
        self.matches_latency_sum = 0

    def add_instance(self, instance):
        self.node_to_instances.get(instance.current_node).append(instance)
        self.size += instance.size

    def get_matches(self) -> typing.List[Match]:
        matches = [i.get_match() for i in self.node_to_instances.get(self.root)]
        self.size -= sum([i.size for i in self.node_to_instances[self.root]])
        self.node_to_instances[self.root] = []
        return matches

    def delete_first_instances(self, peer_node, n):
        self.size -= sum([i.size for i in self.node_to_instances.get(peer_node)[
                                      :n]])
        del self.node_to_instances.get(peer_node)[:n]

    def delete_instances_by_indexes(self, node, array_indexes: typing.List[
        typing.Tuple[int, int]]):
        expired = []
        array = self.node_to_instances.get(node)
        for indexes in reversed(array_indexes):
            # deleting from biggest indexes to smaller ones
            i, j = indexes[0], indexes[1]
            expired.extend(array[i: j+1])
            del self.node_to_instances.get(node)[i: j+1]
        self.size -= sum([i.size for i in expired])

    def remove_old_instances(self, timestamp: float):
        for node in self.node_to_instances.keys():
            node_instances = self.node_to_instances.get(node)
            expired_instances = []
            for instance in node_instances:
                if instance.is_expired(timestamp):
                    expired_instances.append(instance)
            for expired_instance in expired_instances:
                node_instances.remove(expired_instance)

    def clean(self):
        for node in self.node_to_instances.keys():
            self.node_to_instances[node] = []
