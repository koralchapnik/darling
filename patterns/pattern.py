import typing
from abc import ABC

from objects.event_type import EventType
from patterns.conditions.condition import Condition


class Pattern(ABC):

    def __init__(self, op: str, conditions: typing.List[Condition],
                 event_types: typing.List[EventType], time_window: float):
        self.op = op
        self.conditions = conditions
        self.time_window = time_window
        self.event_types = event_types

    def evaluate(self):
        pass
