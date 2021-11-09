import typing


class TreeMetadata:
    def __init__(self, expected_rate: typing.Dict[str, float],
                 epsilon: float, sort_delta: float):
        self.current_load = None
        self.expected_rate = expected_rate
        self.sort_delta = sort_delta

    def get_expected_rate(self, event_type_name: str) -> float:
        return self.expected_rate.get(event_type_name)

