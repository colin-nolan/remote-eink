import inspect
from abc import ABCMeta
from multiprocessing import RLock
from typing import Any, Optional, Tuple, TypeVar, Generic

from multiprocessing_on_dill.connection import Connection, Pipe

ProxyObjectType = TypeVar("ProxyObjectType")


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

    def receive(self) -> Any:
        """
        Blocks until receives communication from the receiver.
        :return: object returned by the receiver
        """
        with self._lock:
            return self.connection.recv()

    def send_and_receive(self, to_send: Any) -> Any:
        """
        Send and receive with the same lock.
        :param to_send: object to send
        :return: object returned by the receiver
        """
        with self._lock:
            self.send(to_send)
            return self.receive()


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

            args, kwargs = None, None
            if isinstance(call_string, Tuple):
                call_string, args, kwargs = call_string

            try:
                value = eval(f"self._target.{call_string}")
                if args is not None:
                    if inspect.ismethod(value):
                        value = value(*args, **kwargs)
                    else:
                        if len(args) == 1:
                            # Property setter
                            exec(f"self._target.{call_string} = {args[0]}")
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
            self._parent_connection.send(result)

    def stop(self):
        """
        TODO
        :return:
        """
        self.connector.send(ProxyReceiver.RUN_POISON)



class ProxyObject(Generic[ProxyObjectType], metaclass=ABCMeta):
    """
    TODO
    """
    def __init__(self, connection: ProxyConnection, method_name_prefix: str = "",
                 local_copy: Optional[ProxyObjectType] = None):
        """
        TODO
        :param connection:
        :param method_name_prefix:
        :param local_copy:
        """
        assert isinstance(method_name_prefix, str)
        super().__init__()
        self.connection = connection
        self.method_name_prefix = method_name_prefix
        self.local_copy = local_copy

    def __eq__(self, other) -> bool:
        return self._communicate("__eq__", other)

    def __str__(self) -> str:
        return self._communicate("__str__")

    def _communicate_call(self, call_string: str) -> Any:
        """
        TODO
        :param call_string:
        :return:
        """
        value, raised = self.connection.send_and_receive(call_string)
        if raised:
            raise value
        return value

    def _communicate(self, method_name: str, *args, **kwargs) -> Any:
        """
        TODO
        :param method_name:
        :param args:
        :param kwargs:
        :return:
        """
        prefix = f"{self.method_name_prefix}." if len(self.method_name_prefix) > 0 else ""
        value, raised = self.connection.send_and_receive((f"{prefix}{method_name}", args, kwargs))
        if raised:
            raise value
        return value

