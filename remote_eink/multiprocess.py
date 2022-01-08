import traceback
from multiprocessing import Lock
from typing import Any, Callable

from multiprocessing_on_dill.connection import Connection, Pipe


class RequestReceiver:
    """
    Receiver used to get requests over a multiprocessor pipe.
    """

    RUN_POISON = "+kill"

    def __init__(self, connection: Connection):
        """
        Constructor.
        :param connection: multiprocessor connection
        """
        self._connection = connection

    def run(self):
        """
        Runs the receiver. Will exit when `RUN_POISON` is received as a message.
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


class RequestSender:
    """
    Sender of requests over a multiprocessor pipe.
    """

    def __init__(self, connection: Connection):
        """
        Constructor.
        :param connection: multiprocessor connection
        """
        self._connection = connection
        self._lock = Lock()

    def communicate(self, callable: Callable, *args, **kwargs) -> Any:
        """
        Communicates a callable via the connection.
        :param callable: the callable
        :param args: args for the callable
        :param kwargs: kwargs for the callable
        :return: the result received in response
        """
        with self._lock:
            self._connection.send((callable, args, kwargs))
            result, raised = self._connection.recv()
            if raised:
                raise result
            return result

    def stop_receiver(self):
        """
        Stop the connected receiver.
        """
        with self._lock:
            self._connection.send(RequestReceiver.RUN_POISON)


class CommunicationPipe:
    """
    Communication pipe that can be used to connect two multiprocessor processes.

    The forked process is expected to be the sender, and the original process is the receiver.
    """

    @property
    def sender(self) -> RequestSender:
        return self._sender

    @property
    def receiver(self) -> RequestReceiver:
        return self._receiver

    def __init__(self):
        """
        Constructor.
        """
        parent_connection, child_connection = Pipe(duplex=True)
        self._receiver = RequestReceiver(parent_connection)
        self._sender = RequestSender(child_connection)
