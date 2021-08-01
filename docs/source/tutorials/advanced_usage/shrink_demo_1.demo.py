from functools import reduce
from operator import __mul__

from treevalue import shrink, FastTreeValue


def multi(items):
    return reduce(__mul__, items, 1)


if __name__ == '__main__':
    t = FastTreeValue({'a': 1, 'b': 2, 'x': {'c': 3, 'd': 4}, 'y': {'e': 6, 'f': 8}})

    print("Sum of t:", shrink(t, lambda **kwargs: sum(kwargs.values())))
    print("Multiply of t:", shrink(t, lambda **kwargs: multi(kwargs.values())))
