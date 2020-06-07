import inspect
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from multiprocessing import RLock
from typing import Any, Tuple, TypeVar, Generic, Union
from uuid import uuid4
from weakref import WeakValueDictionary

from multiprocessing_on_dill.connection import Connection, Pipe

ProxyObjectType = TypeVar("ProxyObjectType")

OriginalObjectReference = str


class ProxyConnection:
    """
    Connection to enable a proxy object to communicate with a receiver on the side of the real object.
    """
    def __init__(self, connection: Connection):
        """
        Constructor.
        :param connection: low level connector
        """
        self.connection = connection
        self._lock = RLock()

    def send(self, to_send: Any):
        """
        Sends the given object to the receiver.
        :param to_send: object to send
        """
        with self._lock:
            self.connection.send(to_send)

    def receive(self) -> Tuple[Any, OriginalObjectReference]:
        """
        Blocks until receives communication from the receiver.
        :return: object returned by the receiver
        """
        with self._lock:
            return self.connection.recv()

    def send_and_receive(self, to_send: Any) -> Tuple[Any, OriginalObjectReference]:
        """
        Send and receive with the same lock.
        :param to_send: object to send
        :return: object returned by the receiver
        """
        with self._lock:
            self.send(to_send)
            return self.receive()


_proxy_object_references = WeakValueDictionary()


class ProxyReceiver:
    """
    TODO
    """
    RUN_POISON = "+kill"

    @property
    def connector(self) -> ProxyConnection:
        return ProxyConnection(self._child_connection)

    def __init__(self, target: Any):
        self._target = target
        self._parent_connection, self._child_connection = Pipe(duplex=True)

    def run(self):
        while True:
            call_string = self._parent_connection.recv()

            if call_string == ProxyReceiver.RUN_POISON:
                return

            call_string, direct_reference, args, kwargs = call_string
            call_prefix = "self._target." if not direct_reference else ""

            # XXX: no support for nested reference placeholders, e.g. args = (1, ReferencePlaceholder())
            args = list(args)
            for i, arg in enumerate(args):
                if isinstance(arg, ReferencePlaceholder):
                    args[i] = eval(arg.reference)
            for key, value in kwargs.items():
                if isinstance(value, ReferencePlaceholder):
                    kwargs[key] = eval(value.reference)

            try:
                value = eval(f"{call_prefix}{call_string}")
                if args is not None:
                    if inspect.ismethod(value):
                        value = value(*args, **kwargs)
                    else:
                        if len(args) == 1:
                            # Property setter
                            exec(f"{call_prefix}{call_string} = {args[0]}")
                            value = None
                        elif len(args) > 1:
                            return ValueError(
                                f"\"{call_string}\" is a property and therefore takes no args: {args}"), True
                        elif len(kwargs) > 0:
                            return ValueError(
                                f"\"{call_string}\" is a property and therefore takes no kwargs: {kwargs}"), True
                result = value, False
            except Exception as e:
                result = e, True

            reference = None
            if not result[1] and result[0] is not None and type(result[0]) not in (str, float, int, bytes, str, tuple, bool):
                identifier = str(uuid4())
                try:
                    _proxy_object_references[identifier] = result[0]
                    reference = f"_proxy_object_references['{identifier}']"
                except TypeError:
                    pass

            self._parent_connection.send((result, reference))
            # Don't hold reference to result
            result = None

    def stop(self):
        """
        TODO
        :return:
        """
        self.connector.send(ProxyReceiver.RUN_POISON)


@dataclass
class ReferencePlaceholder:
    """
    TODO
    """
    reference: OriginalObjectReference


class ProxyObject(Generic[ProxyObjectType], metaclass=ABCMeta):
    """
    TODO
    """
    def __init__(self, connection: ProxyConnection, method_name_prefix: str = "", is_direct_reference: bool = False):
        """
        TODO
        :param connection:
        :param method_name_prefix:
        :param is_direct_reference:
        """
        assert isinstance(method_name_prefix, str)
        super().__init__()
        self.connection = connection
        self.call_string_prefix = method_name_prefix
        self.is_direct_reference = is_direct_reference

    def __eq__(self, other) -> bool:
        return self._communicate("__eq__", other)

    def __str__(self) -> str:
        return self._communicate("__str__")

    def _communicate(self, method_name: str, *args, **kwargs) -> Any:
        """
        TODO
        :param method_name:
        :param args:
        :param kwargs:
        :return:
        """
        return self._communicate_and_get_reference(method_name, *args, *kwargs)[0]

    def _communicate_and_get_reference(self, method_name: str, *args, **kwargs) -> Tuple[Any, OriginalObjectReference]:
        """
        TODO
        :param method_name:
        :param args:
        :param kwargs:
        :return:
        """
        prefix = f"{self.call_string_prefix}." if len(self.call_string_prefix) > 0 else ""
        (value, raised), reference = self.connection.send_and_receive(
            (f"{prefix}{method_name}", self.is_direct_reference, args, kwargs))
        if raised:
            raise value
        return value, reference


def prepare_to_send(obj: Any) -> Union[Any, ReferencePlaceholder]:
    """
    TODO
    :param obj:
    :return:
    """
    if not isinstance(obj, ProxyObject):
        return obj
    if not obj.is_direct_reference:
        raise RuntimeError(f"Cannot convert to non-proxy object copy that can be send to the receiver as does not have "
                           f"direct reference: {obj}")
    return ReferencePlaceholder(obj.call_string_prefix)