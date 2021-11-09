import typing

from objects.event import Event


class Match:
    def __init__(self, primitive_events: typing.List[Event]):
        self.primitive_events = primitive_events

    def __str__(self):
        match_str = ', '.join(str(e) for e in self.primitive_events)
        return f'[{match_str}]'

    def clone(self) -> 'Match':
        primitive_events = [event for event in self.primitive_events]
        return Match(primitive_events)

    def size(self):
        return sum(map(lambda e: e.size(), self.primitive_events))
