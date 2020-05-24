from collections import defaultdict
from functools import partial
from types import MappingProxyType
from typing import Any, TypeVar, Generic, Callable, Set, Sequence, Dict

EventType = TypeVar("EventType")
Listener = Callable[..., Any]
ListenerReturn = Callable[[], Any]


def _raiser(exception: Exception):
    raise exception


class EventListenerController(Generic[EventType]):
    """
    Controller that links events to listeners.
    """
    def __init__(self):
        self._event_listeners = defaultdict(set)

    def get_listeners(self, event: EventType) -> Set[Listener]:
        return self._event_listeners[event]

    def get_events(self) -> Set[EventType]:
        return set(self._event_listeners.keys())

    def add(self, listener: Listener, event: EventType):
        return self.add_listener(listener, event)

    def add_listener(self, listener: Listener, event: EventType):
        if listener in self._event_listeners[event]:
            raise ValueError("Listener already listening to event")
        self._event_listeners[event].add(listener)

    def remove(self, listener: Listener, event: EventType):
        return self.remove_listener(listener, event)

    def remove_listener(self, listener: Listener, event: EventType):
        try:
            self._event_listeners[event].remove(listener)
        except KeyError:
            pass

    def call(self, event: EventType, event_args: Sequence[Any] = (),
             event_kwargs: Dict[str, Any] = MappingProxyType({})) -> Dict[Listener, ListenerReturn]:
        return self.call_listeners(event, event_args, event_kwargs)

    def call_listeners(self, event: EventType, event_args: Sequence[Any] = (),
                       event_kwargs: Dict[str, Any] = MappingProxyType({})) -> Dict[Listener, ListenerReturn]:
        listener_return_map: Dict[Listener, Any] = {}
        for listener in self._event_listeners[event]:
            assert listener not in listener_return_map.keys()
            try:
                listener_return = listener(*event_args, **event_kwargs)
                listener_return_map[listener] = partial(lambda x: x, listener_return)
            except Exception as e:
                # TODO: log error
                listener_return_map[listener] = partial(_raiser, e)
        return listener_return_map
