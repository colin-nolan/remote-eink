import inspect
from abc import ABCMeta
from multiprocessing import RLock

from multiprocessing_on_dill.connection import Connection, Pipe
from types import MappingProxyType
from typing import Any, Optional, List, Iterator, Dict, Sequence, Union, Tuple, Callable

from remote_eink.controllers import DisplayController
from remote_eink.drivers.base import DisplayDriver
from remote_eink.models import Image
from remote_eink.storage.images import ImageStore
from remote_eink.transformers import ImageTransformerSequence, ImageTransformer


# FIXME: pipe locking!


class MultiprocessConnection:
    """
    TODO
    """
    def __init__(self, connection: Connection):
        self.connection = connection

        self._lock = RLock()

    def send(self, to_send: Any):
        with self._lock:
            self.connection.send(to_send)

    def receive(self) -> Any:
        with self._lock:
            return self.connection.recv()

    def send_and_receive(self, to_send: Any) -> Any:
        with self._lock:
            self.send(to_send)
            return self.receive()


class _MultiprocessCaller(metaclass=ABCMeta):
    """
    TODO
    """
    def __init__(self, connection: MultiprocessConnection, method_name_prefix: str = ""):
        """
        TODO
        :param connection:
        """
        self.connection = connection
        self.method_name_prefix = method_name_prefix

    def _communicate_call(self, call_string: str) -> Any:
        """
        TODO
        :param method_name:
        :param args:
        :param kwargs:
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


class MultiprocessImageTransformer(ImageTransformer, _MultiprocessCaller):
    """
    TODO
    """
    @property
    def active(self) -> bool:
        return self._communicate("active")

    @property
    def configuration(self) -> Dict[str, Any]:
        return self._communicate("configuration")

    @property
    def description(self) -> str:
        return self._communicate("description")

    @property
    def identifier(self) -> str:
        return self._communicate("identifier")

    def __init__(self, image_transformer: ImageTransformer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image_transformer = image_transformer

    def modify_configuration(self, configuration: Dict[str, Any]):
        self._communicate("modify_configuration", configuration)

    def _transform(self, image: Image) -> Image:
        return self._communicate("_transform", image)


def to_native_image_transformer(wrappable: Callable) -> Callable:
    """
    TODO
    :param image_transformer:
    :return:
    """
    def wrapped(self, image_transformer, *args, **kwargs) -> Callable:
        if isinstance(image_transformer, MultiprocessImageTransformer):
            image_transformer = image_transformer.image_transformer
        return wrappable(self, image_transformer, *args, **kwargs)

    return wrapped


class MultiprocessImageTransformerSequence(ImageTransformerSequence, _MultiprocessCaller):
    """
    TODO
    """
    def __getitem__(self, i: int) -> ImageTransformer:
        image_transformer = self._communicate("__getitem__", i)
        prefix = f"{self.method_name_prefix}.get_by_id('{image_transformer.identifier}')"
        return MultiprocessImageTransformer(image_transformer, self.connection, prefix)

    def __len__(self) -> int:
        return self._communicate("__len__")

    def get_by_id(self, image_transformer_id: str) -> Optional[ImageTransformer]:
        image_transformer = self._communicate("get_by_id", image_transformer_id)
        if image_transformer is None:
            return None
        prefix = f"{self.method_name_prefix}.get_by_id('{image_transformer_id}')"
        return MultiprocessImageTransformer(image_transformer, self.connection, prefix)

    @to_native_image_transformer
    def get_position(self, image_transformer: Union[ImageTransformer, str]) -> int:
        return self._communicate("get_position", image_transformer)

    @to_native_image_transformer
    def set_position(self, image_transformer: ImageTransformer, position: int):
        self._communicate("set_position", image_transformer, position)

    @to_native_image_transformer
    def add(self, image_transformer: ImageTransformer, position: Optional[int] = None):
        self._communicate("add", image_transformer, position)

    @to_native_image_transformer
    def remove(self, image_transformer: ImageTransformer) -> bool:
        return self._communicate("remove", image_transformer)


class MultiprocessImageStore(ImageStore, _MultiprocessCaller):
    """
    TODO
    """
    def __len__(self) -> int:
        return self._communicate("__len__")

    def __iter__(self) -> Iterator[Image]:
        return iter(self.list())

    def __contains__(self, x: Any) -> bool:
        return self._communicate("__contains__", x)

    def get(self, image_id: str) -> Optional[Image]:
        return self._communicate("get", image_id)

    def list(self) -> List[Image]:
        return self._communicate("list")

    def add(self, image: Image):
        self._communicate("add", image)

    def remove(self, image_id: str) -> bool:
        return self._communicate("remove", image_id)


# FIXME: DisplayDriver + listenable
class MultiprocessDisplayDriver(DisplayDriver, _MultiprocessCaller):
    """
    TODO
    """
    @property
    def sleeping(self) -> bool:
        return self._communicate("sleeping")

    @property
    def image(self) -> Optional[Image]:
        return self._communicate("image")

    def display(self, image_data: bytes):
        self._communicate("display", image_data)

    def clear(self):
        self._communicate("clear")

    def sleep(self):
        self._communicate("sleep")

    def wake(self):
        self._communicate("wake")


class MultiprocessDisplayController(DisplayController, _MultiprocessCaller):
    """
    TODO
    """
    @property
    def identifier(self) -> str:
        return self._communicate("identifier")

    @property
    def current_image(self) -> Image:
        return self._communicate("current_image")

    @property
    def driver(self) -> DisplayDriver:
        return MultiprocessDisplayDriver(self.connection, "driver")

    @property
    def image_store(self) -> ImageStore:
        return MultiprocessImageStore(self.connection, "image_store")

    @property
    def image_transformers(self) -> ImageTransformerSequence:
        return MultiprocessImageTransformerSequence(self.connection, "image_transformers")

    def display(self, image_id: str):
        self._communicate("display", image_id)

    def clear(self):
        self._communicate("clear")

    def apply_image_transforms(self, image: Image) -> Image:
        return self._communicate("apply_image_transforms", image)


class MultiprocessDisplayControllerReceiver:
    """
    TODO
    """
    RUN_POISON = "+kill"

    @property
    def connector(self) -> MultiprocessConnection:
        return MultiprocessConnection(self._child_connection)

    @property
    def display_controller(self):
        return self._display_controller

    def __init__(self, display_controller: DisplayController):
        self._display_controller = display_controller
        self._parent_connection, self._child_connection = Pipe(duplex=True)

    def run(self):
        while True:
            call_string = self._parent_connection.recv()

            if call_string == MultiprocessDisplayControllerReceiver.RUN_POISON:
                return

            args, kwargs = None, None
            if isinstance(call_string, Tuple):
                call_string, args, kwargs = call_string

            try:
                value = eval(f"self._display_controller.{call_string}")
                if args is not None:
                    if inspect.ismethod(value):
                        value = value(*args, **kwargs)
                    else:
                        if len(args) > 0:
                            return ValueError(f"\"{call_string}\" is a property and therefore takes no args: {args}"), True
                        if len(kwargs) > 0:
                            return ValueError(f"\"{call_string}\" is a property and therefore takes no kwargs: {kwargs}"), True
                result = value, False
            except Exception as e:
                result = e, True
            self._parent_connection.send(result)


            # obj = self._display_controller
            # raised = False
            # call_stack = call_string.split(".")
            # for i, method_name in enumerate(call_stack):
            #     if "(" in method_name:
            #         method_name, other = method_name.split("(")
            #         if other[-1] != ")":
            #             value, raised = ValueError(f"Expected to parse (*args, **kwargs) in call string: {other}"), True
            #             break
            #         print(other)
            #         # _parse_args_kwargs
            #         pass
            #
            #     is_last = i == (len(call_stack) - 1)
            #     if not is_last:
            #         value, raised = execute(obj, method_name)
            #         if raised:
            #             break
            #         obj = value
            #     else:
            #         value, raised = execute(obj, method_name, args, kwargs)
            #
            # self._parent_connection.send((value, raised))


# def _parse_args_kwargs(args_kwargs: str) -> Tuple[List[Any], Dict[str, Any]]:
#     """
#     TODO
#     :param args_kwargs:
#     :return:
#     """
#     def parser(*args, **kwargs):
#         return args, kwargs
#
#     return eval(f"parser({args_kwargs})")
#
#
# def execute(obj: Any, method_name: str, args: Sequence[Any] = (), kwargs: Dict[str, Any] = MappingProxyType({})):
#     """
#     TODO
#     :param obj:
#     :param method_name:
#     :param args:
#     :param kwargs:
#     :return:
#     """
#     print(obj, method_name, args, kwargs)
#
#     if isinstance(getattr(type(obj), method_name, None), property):
#         if len(args) > 0:
#             return ValueError(f"\"{method_name}\" is a property and therefore takes no args: {args}"), True
#         if len(kwargs) > 0:
#             return ValueError(f"\"{method_name}\" is a property and therefore takes no kwargs: {kwargs}"), True
#         try:
#             value = getattr(obj, method_name)
#         except Exception as e:
#             return e, True
#     else:
#         try:
#             method = getattr(obj, method_name)
#             value = method(*args, **kwargs)
#         except Exception as e:
#             return e, True
#
#     return value, False


def kill(display_controller_receiver: MultiprocessDisplayControllerReceiver):
    """
    TODO
    :param display_controller_receiver:
    :return:
    """
    # print(f"Killing {display_controller_receiver}")
    display_controller_receiver.connector.send(MultiprocessDisplayControllerReceiver.RUN_POISON)
    # print(f"Killed {display_controller_receiver}")
