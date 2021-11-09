from load_shedders.load_shedder import LoadShedder
from objects.event import Event
from patterns.plans.tree.node.leaf_node import LeafNode


class SelectivityLoadShedder(LoadShedder):
    def __init__(self):
        self.utility_functions = {}

    def shed(self, event: Event, leaf_node: LeafNode, mechanism:
                'EvaluationMechanism') -> bool:

        event_utility = event.utility
        buffer_event = leaf_node.event_buffer.show_sorted_next_event()
        buffer_utility = buffer_event.utility if buffer_event else None

        if not buffer_event:
            print('Error')

        if buffer_event and event < buffer_event:
            # removing the new event
            return True
        # remove the buffer event
        buffer_event_removed = leaf_node.event_buffer.get_next_event(True)
        if buffer_event != buffer_event_removed:
            print('Error! buffer event differs from removed event when '
                  'should be equal')
        success = leaf_node.add_event(event, True)
        if not success:
            print(f'Unsuccessful insertion to buffer')
        return False
