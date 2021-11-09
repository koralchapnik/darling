import typing
from enum import Enum


class Operator(Enum):
    SEQ = 'SEQ'
    NEG = 'NEG'
    AND = 'AND'
    OR = 'OR'
    KLEENE = 'KLEENE'


OPERATORS = {
    'SEQ': (Operator.SEQ, lambda x, y: x < y),
    'NEG': (Operator.NEG, lambda x: not x),
    'AND': (Operator.AND, lambda x, y: x and y),
    'OR': (Operator.OR, lambda x, y: x or y),
    'KLEENE': (Operator.KLEENE, None)
}


def gen_abs_oprator(c: int) -> typing.Callable:
    return lambda x, y: abs(x - y) <= c


def gen_condition_operator(op: str, double_by=None, free_var_op=None,
                           free_var=None) -> \
        typing.Callable:
        if op == '=':
            op = '=='
        if double_by is None and free_var_op is None:
            return lambda x,y: eval(f'{x} {op} {y}')
        elif double_by is not None and free_var_op is None:
            return lambda x,y: eval(f'{x} {op} ({y} * {double_by})')
        elif double_by is not None and free_var_op is not None:
            return lambda x,y: eval(f'{x} {op} ({y} * {double_by} '
                                    f'{free_var_op} {free_var})')
        elif double_by is None and free_var_op is not None:
            return lambda x, y: eval(f'{x} {op} {y} '
                                     f'{free_var_op} {free_var}')