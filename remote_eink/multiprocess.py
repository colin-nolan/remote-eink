import inspect
import traceback

from abc import ABCMeta
from dataclasses import dataclass
from multiprocessing import RLock, Lock
from typing import Any, TypeVar, Generic, Union, List, Callable
from uuid import uuid4
from weakref import WeakValueDictionary

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

    # TODO: Used separately?
    def send(self, to_send: Any):
        """
        Sends the given object to the receiver.
        :param to_send: object to send
        """
        with self._lock:
            self.connection.send(to_send)

    # TODO: Used separately?
    def receive(self) -> Any:
        """
        Blocks until receives communication from the receiver.
        :return: the first element is the object returned by the receiver and the second is TODO
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


_proxy_object_references = WeakValueDictionary()


class ProxyReceiver:
    """
    TODO
    """
    RUN_POISON = "+kill"

    @property
    def connector(self) -> ProxyConnection:
        return self._proxy_connection

    def __init__(self, target: Any):
        self._target = target
        self._parent_connection, self._child_connection = Pipe(duplex=True)
        self._proxy_connection = ProxyConnection(self._child_connection)

    def run(self):
        while True:
            call_string = self._parent_connection.recv()

            if call_string == ProxyReceiver.RUN_POISON:
                return

            call_string, direct_reference, return_references, args, kwargs = call_string
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
                    # XXX: Detect of "method-wrapper" (such as __str__) is hacky
                    if inspect.ismethod(value) or str(type(value)) == "<class 'method-wrapper'>":
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

            if not result[1] and return_references:
                references = []
                # XXX: Support for other containers, such as nested or dictionaries may be required in the future.
                #      Not adding now as the complexity is already very high.
                if isinstance(result[0], list) or isinstance(result[0], tuple):
                    all_referenced = result[0]
                else:
                    all_referenced = [result[0]]

                for referenced in all_referenced:
                    if type(result[0]) not in (str, float, int, bytes, str, bool):
                        try:
                            if referenced not in references:
                                identifier = str(uuid4())
                                _proxy_object_references[identifier] = referenced
                                reference = f"_proxy_object_references['{identifier}']"
                                references.append(ReferencePlaceholder(reference))
                        except TypeError:
                            pass
                result = references, False

            self._parent_connection.send(result)
            # Don't hold on to references
            result = None
            all_referenced = None
            value = None

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
    reference: str


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
        return self._communicate_with_set_return(method_name, False, *args, *kwargs)

    def _communicate_reference_return(self, method_name: str, *args, **kwargs) -> List[ReferencePlaceholder]:
        """
        TODO
        :param method_name:
        :param args:
        :param kwargs:
        :return:
        """
        return self._communicate_with_set_return(method_name, True, *args, *kwargs)

    def _communicate_with_set_return(self, method_name: str, return_references: bool = False, *args, **kwargs) -> Any:
        """
        TODO
        :param method_name:
        :param return_references:
        :param args:
        :param kwargs:
        :return:
        """
        prefix = f"{self.call_string_prefix}." if len(self.call_string_prefix) > 0 else ""
        value, raised = self.connection.send_and_receive(
            (f"{prefix}{method_name}", self.is_direct_reference, return_references, args, kwargs))
        if raised:
            raise value
        return value


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


class RequestReceiver:
    """
    TODO
    """
    RUN_POISON = "+kill"

    def __init__(self, connection: Connection):
        """
        TODO
        :param connection:
        """
        self._connection = connection

    def run(self):
        """
        TODO
        :return:
        """
        while True:
            received = self._connection.recv()
            if received == RequestReceiver.RUN_POISON:
                return

            callable, args, kwargs = received
            raised = False
            try:
                result = callable(*args, **kwargs)
            except Exception as e:
                result = e
                traceback.print_exc()
                raised = True
            self._connection.send((result, raised))

    # TODO: would need to lock...
    # def stop(self):
    #     """
    #     TODO
    #     :return:
    #     """
    #     self._connection.send(RequestReceiver.RUN_POISON)


class RequestSender:
    """
    TODO
    """
    def __init__(self, connection: Connection):
        """
        TODO
        :param connection:
        """
        self._connection = connection
        self._lock = Lock()

    def communicate(self, callable: Callable, *args, **kwargs) -> Any:
        """
        TODO
        :param callable:
        :param args:
        :param kwargs:
        :return:
        """
        with self._lock:
            self._connection.send((callable, args, kwargs))
            result, raised = self._connection.recv()
            if raised:
                raise result
            return result

    def stop_receiver(self):
        """
        TODO
        :return:
        """
        with self._lock:
            self._connection.send(RequestReceiver.RUN_POISON)


class CommunicationPipe:
    """
    TODO
    """
    @property
    def sender(self) -> RequestSender:
        return self._sender

    @property
    def receiver(self) -> RequestReceiver:
        return self._receiver

    def __init__(self):
        """
        TODO
        """
        parent_connection, child_connection = Pipe(duplex=True)
        self._receiver = RequestReceiver(parent_connection)
        self._sender = RequestSender(child_connection)
