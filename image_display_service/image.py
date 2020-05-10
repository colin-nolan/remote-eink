from typing import Any, Callable


class Image:
    """
    TODO
    """
    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def cache_data(self) -> bool:
        return self._cache_data

    @cache_data.setter
    def cache_data(self, cache_on: bool):
        if not cache_on:
            self._cached = None
        self._cache_data = cache_on

    @property
    def data(self) -> bytes:
        if self._cached:
            return self._cached
        data = self._data_reader()
        if self.cache_data:
            self._cached = data
        return data

    def __init__(self, identifier: str, data_reader: Callable[[], bytes], cache_data: bool = True):
        self._identifier = identifier
        self._data_reader = data_reader
        self._cache_data = cache_data
        self._cached = None

    def __repr__(self) -> str:
        return repr(dict(identifier=self.identifier, data=self.data))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        if other.identifier != self.identifier:
            return False
        return other.data == self.data

    def __hash__(self) -> int:
        return hash(self.identifier)
