import typing
import sys
from objects.exceptions import InvalidAttribute
from patterns.consts import *
from datetime import datetime


class Event:
    def __init__(self, event_type: 'EventType', attrs_values: typing.List,
                 name=None):
        self.type = event_type
        self.name = next(self.type.event_name_generator) if name is None else\
            name
        if not self.type.is_valid_attrs(attrs_values):
            raise InvalidAttribute()
        attrs_values = [t(i) if i else 0.0 for i, t in zip(attrs_values,
                                                           self.type.attrs_types)]
        self.attrs = dict(zip(self.type.attrs_names, attrs_values))
        if TIME_KEY not in self.type.attrs_names:
            self.attrs[TIME_KEY] = datetime.utcnow().timestamp()
        self.utility = None
        self.deleted = False

    def __str__(self):
        attrs = ','.join([f'{key}={val}' for key, val in self.attrs.items()])
        return f'{self.name}({attrs})'

    def get_timestamp(self):
        return self.attrs[TIME_KEY]

    def size(self):
        return sys.getsizeof(self.attrs)

    def __lt__(self, other):
        if self.utility == other.utility:
            return self.get_timestamp() >= other.get_timestamp() if \
                self.type.start_seq else self.get_timestamp() < \
                                         other.get_timestamp()

        return self.utility < other.utility

    def to_json(self) -> typing.Dict:
        return {
            'type': self.type.name,
            'attrs_values': list(self.attrs.values()),
            'name': self.name
        }

    @staticmethod
    def from_json(event_json, event_type: 'EventType') -> 'Event':
        attrs_values = event_json.get('attrs_values')
        name = event_json.get('name')
        return Event(event_type, attrs_values, name)

