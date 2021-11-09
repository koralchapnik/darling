import typing
from abc import ABC

import scipy.stats

from objects.event import Event
from objects.event_type import EventType
from patterns.exceptions import InvalidConditionParams


class Condition(ABC):
    def __init__(self, desc: str, event_types: typing.List[EventType],
                 attr_1: str, attr_2: str, const: str, op_name: str, op_func:
            typing.Callable, selectivity: float = None, user_input: bool =
                 True, double_by=None, free_var_op=None, free_var=None):
        self.desc = desc
        self.event_types = event_types
        self.contains_kleene = any([event_type.kleene for event_type in self.event_types])
        self.attr_1 = attr_1
        self.attr_2 = attr_2
        self.const = const
        self.op_name = op_name
        self.op_func = op_func
        self.selectivity = selectivity
        self.func = self._gen_func()
        self.double_by = None if double_by is None else float(double_by)
        if free_var_op is None and free_var is None:
            self.free_var = None
        elif free_var_op == '-':
            self.free_var = float(free_var) * (-1)
        elif free_var_op == '+':
            self.free_var = float(free_var)
        else:
            self.free_var = float(free_var)
        self.user_input = user_input
        self.abs = False
        if user_input:
            self.custom_verifiers_by_type = self._gen_custom_verifiers_by_attr()

    def __len__(self):
        return len(self.event_types)

    def get_other_type(self, event_type) -> EventType:
        for type_ in self.event_types:
            if type_ != event_type:
                return type_
        return None

    def _gen_func(self):
        if self.attr_2 is None:
            return lambda e: self.op_func(e.attrs[self.attr_1], self.const)
        else:
            return lambda e_1, e_2: self.op_func(e_1.attrs[self.attr_1],
                                            e_2.attrs[self.attr_2])

    def _gen_custom_verifiers_by_attr(self):
        if '|' in self.desc:
            # it is an abs cond
            mu1, sigma1 = self.event_types[0].attrs_dist_params.get(self.attr_1)
            mu2, sigma2 = self.event_types[1].attrs_dist_params.get(self.attr_2)
            attr_1_norm = scipy.stats.norm(mu1, sigma1)
            attr_2_norm = scipy.stats.norm(mu2, sigma2)

            def f1_(e_1):
                attr = e_1.attrs[self.attr_1]
                norm = scipy.stats.norm(mu2 - attr, sigma2)
                return norm.cdf(self.free_var) - norm.cdf((-1) * self.free_var)

            def f2_(e_2):
                attr = e_2.attrs[self.attr_2]
                norm = scipy.stats.norm(mu1 - attr, sigma1)
                return norm.cdf(self.free_var) - norm.cdf((-1) * self.free_var)

            return {
                self.event_types[0]: f1_,
                self.event_types[1]: f2_
            }

        if len(self.event_types) == 1:
            return None
        attr_1_norm = scipy.stats.norm(*self.event_types[0].
                                       attrs_dist_params.get(self.attr_1))
        mu2, sigma2 = self.event_types[1].attrs_dist_params.get(self.attr_2)
        if self.double_by is not None:
            mu2 *= self.double_by
            sigma2 *= self.double_by

        if self.free_var is not None:
            mu2 += self.free_var

        double_by = 1 if self.double_by is None else self.double_by
        free_var = 0 if self.free_var is None else self.free_var

        attr_2_norm = scipy.stats.norm(mu2, sigma2)
        if self.op_name == '<':
            f1 = lambda e_1: 1 - attr_2_norm.cdf(e_1.attrs[self.attr_1])
            f2 = lambda e_2: attr_1_norm.cdf(e_2.attrs[self.attr_2] *
                                             double_by + free_var)
        elif self.op_name == '>':
            f1 = lambda e_1: attr_2_norm.cdf(e_1.attrs[self.attr_1])
            f2 = lambda e_2: 1 - attr_1_norm.cdf(e_2.attrs[self.attr_2] *
                                                 double_by + free_var)
        elif self.op_name == '=':
            f1 = lambda e_1: attr_2_norm.pdf(e_1.attrs[self.attr_1])
            f2 = lambda e_2: attr_1_norm.pdf(e_2.attrs[self.attr_2] *
                                             double_by + free_var)

        return {
            self.event_types[0]: f1,
            self.event_types[1]: f2
        }

    def verify(self, *events: Event) -> bool:
        if not self.contains_kleene:
            self._check_arguments(events)
            ordered_events = self._order_events(events)
            return self.func(*ordered_events)
        elif len(self.event_types) == 1:
            for event in events:
                if not self.func(event):
                    return False
            return True
        else:
            first_arg_events = [event for event in events if self.event_types[
                0].name == event.type.name]
            second_arg_events = [event for event in events if self.event_types[
                1].name == event.type.name]
            if len(first_arg_events) > len(second_arg_events):
                e2 = second_arg_events[0]
                for e1 in first_arg_events:
                    if not self.func(e1, e2):
                        return False
            else:
                e1 = first_arg_events[0]
                for e2 in second_arg_events:
                    if not self.func(e1, e2):
                        return False
            return True

    def _order_events(self, events: typing.Tuple[Event]) -> typing.Iterable[Event]:
        return events if self.event_types[0].name == events[0].type.name else\
            reversed(events)

    def _check_arguments(self, events: typing.Tuple[Event]):
        if len(events) != len(self.event_types):
            raise InvalidConditionParams('Not enough or too much events')
