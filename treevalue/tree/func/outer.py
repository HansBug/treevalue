from functools import reduce

from .base import _BaseProcessor


class _OuterProcessor(_BaseProcessor):
    def get_key_set(self, *args, **kwargs):
        return reduce(lambda x, y: x | y, [set(keyset) for index, keyset in self._get_key_entries(*args, **kwargs)])
