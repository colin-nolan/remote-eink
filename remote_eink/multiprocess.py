import traceback

from multiprocessing import Lock
from typing import Any, Callable

from multiprocessing_on_dill.connection import Connection, Pipe


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
