from typing import Dict, Any, Union

from ...utils import init_magic


def _to_tree_decorator(init_func):
    def _new_init_func(data):
        if isinstance(data, Tree):
            _new_init_func(data.to_json())
        elif isinstance(data, dict):
            init_func({
                str(key): Tree(value) if isinstance(value, dict) else value
                for key, value in data.items()
            })
        else:
            raise TypeError(
                "Dict value expected for dispatch value but {type} actually.".format(type=repr(type(data).__name__)))

    return _new_init_func


@init_magic(_to_tree_decorator)
class Tree:
    def __init__(self, mapping: Union[Dict[str, Union['Tree', Any]], 'Tree']):
        self.__dict = mapping

    def __check_key_exist(self, key):
        if key not in self.__dict.keys():
            raise KeyError("Key {key} not found.".format(key=repr(key)))

    def __getitem__(self, key):
        self.__check_key_exist(key)
        return self.__dict[key]

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            value = Tree(value)
        self.__dict[key] = value

    def __delitem__(self, key):
        self.__check_key_exist(key)
        del self.__dict[key]

    def to_json(self):
        return {
            key: value.to_json() if isinstance(value, Tree) else value
            for key, value in self.__dict.items()
        }

    def clone(self):
        return self.__class__(self)

    def __repr__(self):
        return '<{cls} keys: {keys}>'.format(
            cls=self.__class__.__name__,
            keys=repr(sorted(self.__dict.keys()))
        )

    def items(self):
        return self.__dict.items()

    def keys(self):
        return self.__dict.keys()

    def values(self):
        return self.__dict.values()

    def __len__(self):
        return len(self.__dict)

    def __hash__(self):
        return hash(((key, value) for key, value in sorted(self.__dict.items())))

    def __eq__(self, other):
        if other is self:
            return True
        elif isinstance(other, Tree):
            return self.__dict == other.__dict
        else:
            return False
