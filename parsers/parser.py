import os
import re
import typing

from objects.event import Event
from objects.event_type import EventType
from patterns.conditions.condition import Condition
from patterns.consts import TIME_KEY
from patterns.operator import gen_condition_operator, gen_abs_oprator
from patterns.pattern import Pattern

AllTypes = typing.Dict[str, EventType]


class Parser:

    def __init__(self, event_types_def: typing.Dict):
        self.event_types_def = event_types_def
        self.type_name_to_obj = None

    def parse_pattern(self, pattern_spec: str, conditions_selectivity:
                      typing.Dict[str, float], arrts_dist_params:
    typing.Dict, attrs_types) \
            -> typing.Tuple[AllTypes, Pattern]:
        simple_pattern_spec = r'(\w+)\((.*)\).* WHERE (.*) WITHIN (\d+).*'
        resutls = re.search(simple_pattern_spec, pattern_spec)
        op, events, conds, window = resutls.group(1, 2, 3, 4)
        self.type_name_to_obj = Parser._create_event_types_objects(
            self.event_types_def, arrts_dist_params, attrs_types)

        instance_to_type = self._get_instances_to_types(events)
        conditions = []
        for cond_spec in conds.split(' and '):
            selectivity = 1 if not conditions_selectivity else  \
                conditions_selectivity.get(cond_spec, 1)
            conditions.append(self._convert_spec_to_cond(cond_spec,
                                                         instance_to_type,
                                                         selectivity))
        types = list(instance_to_type.values())
        for i in range(0, len(types)-1): #add the SEQ conds
            if types[i].neg:
                continue
            next_type = types[i+1]
            if types[i+1].neg:
                next_type = types[i+2]
            conditions.append(Condition('SEQ', [types[i], next_type], TIME_KEY,
                                        TIME_KEY, None, '<',
                                        gen_condition_operator('<')
                                        , 1, False))

        return self.type_name_to_obj, \
               Pattern(op, conditions, list(instance_to_type.values()),
                       float(window))

    def _get_instances_to_types(self, events: str) -> \
                                typing.Dict[str, EventType]:
        events_to_types = {}
        events_arr = events.split(',')
        for i, e in enumerate(events_arr):
            kleene, neg = False, False
            type_name, event_instance = e.split(None)
            if '!' in type_name:
                neg = True
                type_name = type_name.replace('!', '')
            if '+' in type_name:
                kleene = True
                type_name = type_name.replace('+', '')
            event_type = self.type_name_to_obj.get(type_name)
            if kleene:
                event_type.kleene = True
            if neg:
                event_type.neg = True
            events_to_types[event_instance] = event_type
            event_type.start_seq = True if i <= (len(events_arr) / 2) else \
                False

        return events_to_types

    def _convert_spec_to_cond(self, spec: str,
                              instance_to_type: typing.Dict[str, EventType],
                              selectivity: float)\
            -> Condition:
        if '|' in spec:
            # it is an abs operator
            regex = r'\|(\w+)\.(\w+) - (\w+)\.(\w+)\| <= (\w+)'
            results = re.search(regex, spec)
            left_event, left_attr, right_event, right_attr, const = \
                results.group(1, 2, 3, 4, 5)
            op_func = gen_abs_oprator(int(const))
            cond = Condition(spec, [instance_to_type.get(left_event),
                                    instance_to_type.get(right_event)],
                             left_attr,
                             right_attr, None, 'abs', op_func, selectivity,
                             free_var=const)
            cond.abs = True
            return cond

        regex = r'(\w+)\.(\w+) ([<>=]) ((\w+)\.(\w+)( (([*]) ([\w.]+))? ?((([+-])) (\w+))?)?|(\w+))'
        spec_search = re.search(regex, spec)
        left_event, left_attr, op = spec_search.group(1, 2, 3)

        cond_unary = True if len(re.findall(r'(\w+)\.(\w+)', spec)) == 1 else\
            False
        if cond_unary:
            op_func = gen_condition_operator(op)
            const = spec_search.group(4)
            cond = Condition(spec, [instance_to_type.get(left_event)],
                             left_attr, None, const, op, op_func, selectivity)
        else:
            right_event, right_attr = spec_search.group(5, 6)
            double_by = spec_search.group(10)
            free_var_op, free_var= spec_search.group(13, 14)
            op_func = gen_condition_operator(op, double_by=double_by,
                                             free_var_op=free_var_op,
                                             free_var=free_var)
            cond = Condition(spec, [instance_to_type.get(left_event),
                              instance_to_type.get(right_event)], left_attr,
                             right_attr, None, op, op_func, selectivity,
                             double_by=double_by, free_var_op=free_var_op,
                             free_var=free_var)

        return cond

    @staticmethod
    def _create_event_types_objects(event_types_spec: typing.Dict,
                                    arrts_dist_params: typing.Dict,
                                    attrs_type) -> \
                                        typing.Dict[str, EventType]:
        # returns event type name to event type object
        event_types = {}
        for event_type_name, event_type_attrs in event_types_spec.items():
            event_type_obj = EventType(event_type_name,
                                       event_type_attrs,
                                       arrts_dist_params.get(
                                           event_type_name), attrs_type)
            event_types[event_type_name] = event_type_obj
        return event_types

    def parse_event_from_str(self, event_str: str) -> Event:
        type_name, *attrs = event_str.split(',')
        event_type = self.type_name_to_obj.get(type_name)
        return Event(event_type, attrs)

    def parse_event(self, events_file: str) -> Event:
        with open(events_file, 'r') as f:
            for line in f:
                type_name, *attrs = line.split(',')
                event_type = self.type_name_to_obj.get(type_name)
                yield Event(event_type, attrs)

    @staticmethod
    def get_data_filename(data_kind: str, pattern: str,
                          with_ws: bool = False) -> \
            typing.Tuple[str, typing.List[str]]:
        pattern = pattern.replace('+', '')
        pattern = pattern.replace('!', '')
        simple_pattern_spec = r'(\w+)\((.*)\).* WHERE (.*) WITHIN (\d+).*'
        resutls = re.search(simple_pattern_spec, pattern)
        op, events, conds, window = resutls.group(1, 2, 3, 4)
        types = [t.split()[0] for t in events.split(',')]
        types = sorted(types)
        filename = os.environ.get('DATA_FILE')
        return filename, types

    @staticmethod
    def get_dist_filename(data_kind, pattern):
        pattern = pattern.replace('+', '')
        pattern = pattern.replace('!', '')
        simple_pattern_spec = r'(\w+)\((.*)\).* WHERE (.*) WITHIN (\d+).*'
        resutls = re.search(simple_pattern_spec, pattern)
        op, events, conds, window = resutls.group(1, 2, 3, 4)
        types = [t.split()[0] for t in events.split(',')]
        types = sorted(types)
        filename = f'{data_kind}_{"_".join(types)}.txt'
        return filename

