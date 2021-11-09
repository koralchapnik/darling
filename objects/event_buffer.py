import typing

from objects.event import Event


class EventBuffer:
    def __init__(self, events: typing.List[Event] = None,
                 max_size: float = None, window: float = None, psi: int = 100):
        self.events = events if events is not None else []
        self.sorted_events = None # auxiliary data structures
        self.utility_func = None
        self.earliest_timestamp = None
        self.latest_timestamp = None
        self.max_size = int(max_size) if max_size is not None else None
        self.window = window
        self.psi = psi
        self.size = 0
        self.start_seq = None
        self.min_utility = None

    def is_full(self):
        if self.max_size is None:
            return False
        return self.size >= self.max_size

    def init_sorted_events(self):
        self.sorted_events = {i: [] for i in range(0, self.psi + 1)}

    def add_event(self, event: Event, limit: bool = False) -> bool:
        if limit and self.is_full():
            return False
        self.events.append(event)
        if self.sorted_events is not None:
            self._insert_to_sorted_events_list(event)
        self.update_timestamp(event)
        self.size += 1
        return True

    def _insert_to_sorted_events_list(self, event: Event):
        relevant_array = self.sorted_events.get(event.utility)
        if self.min_utility is None:
            self.min_utility = event.utility
        elif event.utility < self.min_utility:
            self.min_utility = event.utility
        relevant_array.append(event)

    def update_min_timestamp(self):
        self.earliest_timestamp = self.events[0].get_timestamp() if \
            self.events else None

    def get_next_event(self, from_sorted: bool = False) -> Event:
        if not self.events:
            return None
        if from_sorted:
            (array_to_remove_from, to_remove_index) = \
                self._get_arr_idx_next_sorted()
            element = array_to_remove_from.pop(
                to_remove_index)
            if not array_to_remove_from:
                # the array is empty
                self.min_utility = self._find_min_utility_index()
            res = element
            element.deleted = True
        else:
            res = self.events.pop(0)
            while res.deleted:
                res = self.events.pop(0)
            if self.sorted_events:
                del self.sorted_events.get(res.utility)[0]
                if self.min_utility == res.utility and not \
                        self.sorted_events.get(res.utility):
                    # the array is empty
                    self.min_utility = self._find_min_utility_index()
        self.size -= 1
        self.update_min_timestamp()
        return res

    def show_next_event(self) -> Event:
        if not self.events:
            return None
        res = self.events[0]
        while res.deleted:
            del self.events[0]
            if not self.events:
                return None
            res = self.events[0]
        return res

    def _find_min_utility_index(self, start=0) -> int:
        for util in range(self.min_utility, self.psi + 1):
            if self.sorted_events[util]:
                self.min_utility = util
                return util
        return None

    def _get_arr_idx_next_sorted(self):
        array_to_remove_from = self.sorted_events[self.min_utility] if \
            self.min_utility is not None else \
            self.sorted_events[self._find_min_utility_index()]
        if not array_to_remove_from:
            return None, None
        to_remove_index = 0 if self.start_seq else -1
        return array_to_remove_from, to_remove_index

    def show_sorted_next_event(self) -> Event:
        if not self.sorted_events:
            return None
        indexes = self._get_arr_idx_next_sorted()
        if indexes is None:
            return None
        (array_to_remove_from, to_remove_index) = indexes
        try:
            array_to_remove_from[to_remove_index]
        except Exception as e:
            print(f'Error!!! {e}')
        return array_to_remove_from[to_remove_index]

    def update_timestamp(self, event: Event):
        timestamp = event.get_timestamp()
        if self.earliest_timestamp is None or timestamp < \
                self.earliest_timestamp:
            self.earliest_timestamp = timestamp
        if self.latest_timestamp is None or timestamp > self.latest_timestamp:
            self.latest_timestamp = timestamp

    def is_expired(self) -> bool:
        return self.latest_timestamp - self.earliest_timestamp > self.window

    def clone(self) -> 'EventBuffer':
        events = [event for event in self.events]
        new_event_buffer = EventBuffer(events, self.max_size, self.window)
        if self.sorted_events:
            new_event_buffer.sorted_events = self.sorted_events
        new_event_buffer.earliest_timestamp = self.earliest_timestamp
        new_event_buffer.latest_timestamp = self.latest_timestamp
        return new_event_buffer

    def sort_activated(self) -> bool:
        return self.sorted_events is not None

    def left_size(self) -> int:
        return self.max_size - self.size

    def __str__(self):
        return f'{self.events}'
