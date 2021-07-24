from enum import IntEnum
from functools import wraps, partial
from typing import Type, TypeVar, Optional

import enum_tools

from .inner import _InnerProcessor
from .left import _LeftProcessor
from .outer import _OuterProcessor
from .strict import _StrictProcessor
from ..common import raw
from ..tree.tree import TreeValue
from ...utils import int_enum_loads, SingletonMark


@enum_tools.documentation.document_enum
@int_enum_loads(name_preprocess=str.upper)
class TreeMode(IntEnum):
    """
    Overview:
        Four mode of the tree calculation
    """
    STRICT = 1  # doc: Strict mode, which means the keys should be one to one in every trees.
    LEFT = 2  # doc: Left mode, the keys of the result is relied on the left value.
    INNER = 3  # doc: Inner mode, the keys of the result is relied on the intersection of the trees' key set.
    OUTER = 4  # doc: Outer mode, the keys of the result is relied on the union of the trees' key set.


_MODE_PROCESSORS = {
    TreeMode.STRICT: _StrictProcessor(),
    TreeMode.LEFT: _LeftProcessor(),
    TreeMode.INNER: _InnerProcessor(),
    TreeMode.OUTER: _OuterProcessor(),
}


def _any_getattr(value):
    class _AnyClass:
        def __getattr__(self, item):
            return value

    return _AnyClass()


_ClassType = TypeVar("_ClassType", bound=TreeValue)
MISSING_NOT_ALLOW = SingletonMark("missing_not_allow")


def func_treelize(mode='strict', return_type: Optional[Type[_ClassType]] = TreeValue,
                  inherit: bool = False, missing=MISSING_NOT_ALLOW):
    """
    Overview:
        Wrap a common function to tree-supported function.

    Arguments:
        - mode (:obj:): Mode of the wrapping (string or TreeMode both okay), default is `strict`.
        - return_type (:obj:`Optional[Type[_ClassType]]`): Return type of the wrapped function, default is `TreeValue`.
        - inherit (:obj:`bool`): Allow inherit in wrapped function, default is `False`.
        - missing (:obj:): Missing value or lambda generator of when missing, default is `MISSING_NOT_ALLOW`, which \
            means raise `KeyError` when missing detected.

    Returns:
        - new_func (:obj:): Wrapped tree-supported function.

    Example:
        >>> @func_treelize(inherit=True)
        >>> def ssum(a, b):
        >>>     return a + b  # the a and b will be integers, not TreeValue
        >>>
        >>> t1 = TreeValue({'a': 1, 'b': 2, 'x': {'c': 3, 'd': 4}})
        >>> t2 = TreeValue({'a': 11, 'b': 22, 'x': {'c': 33, 'd': 5}})
        >>> ssum(1, 2)    # 3
        >>> ssum(t1, t2)  # TreeValue({'a': 12, 'b': 24, 'x': {'c': 36, 'd': 9}})
    """
    mode = TreeMode.loads(mode)
    if missing is MISSING_NOT_ALLOW:
        allow_missing = False
        missing_func = None
    else:
        allow_missing = True
        missing_func = missing if hasattr(missing, '__call__') else (lambda: missing)

    _MODE_PROCESSORS[mode].check_arguments(mode, return_type, inherit, allow_missing, missing_func)

    def _value_wrap(item, index):
        if isinstance(item, TreeValue):
            def _get_from_key(key):
                if key in item:
                    return item.__getattr__(key)
                elif allow_missing:
                    return missing_func()
                else:
                    raise KeyError("Missing is off, key {key} not found in {item}.".format(
                        key=repr(key), item=repr(item),
                    ))

            return _get_from_key
        elif inherit:
            return _any_getattr(item).__getattr__
        else:
            raise TypeError("Inherit is off, tree value expected but {type} found in args {index}.".format(
                type=repr(type(item).__name__), index=repr(index),
            ))

    def _decorator(func):
        @wraps(func)
        def _new_func(*args, **kwargs) -> Optional[_ClassType]:
            if all([not isinstance(item, TreeValue) for item in args]) \
                    and all([not isinstance(value, TreeValue) for value in kwargs.values()]):
                return func(*args, **kwargs)

            pargs = [_value_wrap(item, index) for index, item in enumerate(args)]
            pkwargs = {key: _value_wrap(value, key) for key, value in kwargs.items()}

            _data = {
                key: raw(_new_func(
                    *(item(key) for item in pargs),
                    **{key_: value(key) for key_, value in pkwargs.items()}
                )) for key in sorted(_MODE_PROCESSORS[mode].get_key_set(*args, **kwargs))
            }
            return return_type(_data) if return_type is not None else None

        return _new_func

    return _decorator


AUTO_DETECT_RETURN_TYPE = SingletonMark("auto_detect_return_type")


def method_treelize(mode='strict', return_type: Optional[Type[_ClassType]] = AUTO_DETECT_RETURN_TYPE,
                    inherit: bool = False, missing=MISSING_NOT_ALLOW):
    """
    Overview:
        Wrap a common instance method to tree-supported method.

    Attention:
        - This decorator can only used to instance method, usage with class method may cause unconditional fatal.
        - When decorated instance method is called, the `self` argument will be no longer the class instance, \
            but the single element of the tree instead.

    Arguments:
        - mode (:obj:): Mode of the wrapping (string or TreeMode both okay), default is `strict`.
        - return_type (:obj:`Optional[Type[_ClassType]]`): Return type of the wrapped function, \
            default is `AUTO_DETECT_RETURN_VALUE`, which means automatically use the decorated method's class.
        - inherit (:obj:`bool`): Allow inherit in wrapped function, default is `False`.
        - missing (:obj:): Missing value or lambda generator of when missing, default is `MISSING_NOT_ALLOW`, which \
            means raise `KeyError` when missing detected.

    Returns:
        - new_method (:obj:): Wrapped tree-supported method.

    Example:
        >>> class MyTreeValue(TreeValue):
        >>>     @method_treelize(inherit=True)
        >>>     def append(self, *args):
        >>>         return sum([self, *args])  # the self will be the integers, not MyTreeValue
        >>>
        >>> t1 = MyTreeValue({'a': 1, 'b': 2, 'x': {'c': 3, 'd': 4}})
        >>> t2 = MyTreeValue({'a': 11, 'b': 22, 'x': {'c': 33, 'd': 5}})
        >>> t1.append(2)   # MyTreeValue({'a': 3, 'b': 4, 'x': {'c': 5, 'd': 6}})
        >>> t1.append(t2)  # MyTreeValue({'a': 12, 'b': 24, 'x': {'c': 36, 'd': 9}})
    """

    def _decorator(method):
        @wraps(method)
        def _new_method(self, *args, **kwargs):
            rt = self.__class__ if return_type is AUTO_DETECT_RETURN_TYPE else return_type
            return func_treelize(mode, rt, inherit, missing)(method)(self, *args, **kwargs)

        return _new_method

    return _decorator


def classmethod_treelize(mode='strict', return_type: Optional[Type[_ClassType]] = AUTO_DETECT_RETURN_TYPE,
                         inherit: bool = False, missing=MISSING_NOT_ALLOW):
    """
    Overview:
        Wrap a common class method to tree-supported method.

    Attention:
        - This decorator can only used to class method, usage with instance method may cause unconditional fatal.
        - When decorated instance method is called, the `cls` argument will still be the calling class.

    Arguments:
        - mode (:obj:): Mode of the wrapping (string or TreeMode both okay), default is `strict`.
        - return_type (:obj:`Optional[Type[_ClassType]]`): Return type of the wrapped function, \
            default is `AUTO_DETECT_RETURN_VALUE`, which means automatically use the decorated method's class.
        - inherit (:obj:`bool`): Allow inherit in wrapped function, default is `False`.
        - missing (:obj:): Missing value or lambda generator of when missing, default is `MISSING_NOT_ALLOW`, which \
            means raise `KeyError` when missing detected.

    Returns:
        - new_method (:obj:): Wrapped tree-supported method.

    Example:
        >>> class TestUtils:
        >>>     @classmethod
        >>>     @classmethod_treelize(return_type=TreeValue)
        >>>     def add(cls, a, b):
        >>>         return cls, a + b
        >>>
        >>> TestUtils.add(
        >>>     TreeValue({'a': 1, 'b': 2}),
        >>>     TreeValue({'a': 11, 'b': 23}),
        >>> )  # TreeValue({'a': (TestUtils, 12), 'b': (TestUtils, 25)})
    """

    def _decorator(method):
        @wraps(method)
        def _new_method(cls, *args, **kwargs):
            rt = cls if return_type is AUTO_DETECT_RETURN_TYPE else return_type
            return func_treelize(mode, rt, inherit, missing)(partial(method, cls))(*args, **kwargs)

        return _new_method

    return _decorator
