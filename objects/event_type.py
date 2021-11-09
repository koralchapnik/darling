import typing


class EventType:
    def __init__(self, name: str, attrs_names: typing.List[str],
                 attrs_dist_params: typing.Dict[str, typing.List[float]],
                 attrs_types: typing.Dict):
        self.name = name
        self.attrs_names = attrs_names
        self.attrs_types = attrs_types
        self.attrs_sum = [0] * (len(attrs_names) - 1) # without time
        self.curr_num = 0
        self.event_name_generator = self.gen_event_name()
        self.size = len(self.attrs_names)
        self.attrs_dist_params = attrs_dist_params
        self.kleene = False
        self.neg = False

    def is_valid_attrs(self, attrs: typing.List[str]) -> int:
        return len(self.attrs_names) == len(attrs)

    def gen_event_name(self) -> str:
        i = 1
        while True:
            yield f'{self.name}_{i}'
            i += 1

    def __str__(self):
        return f'{self.name}{self.attrs_names}'
