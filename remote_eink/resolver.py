import re

from connexion import Resolver
from connexion.operations import AbstractOperation


class CustomRestResolver(Resolver):
    """
    Custom rest resolver.
    """

    DEFAULT_COLLECTION_ENDPOINT = "search"

    def __init__(self, default_module_name: str, collection_endpoint_name: str = DEFAULT_COLLECTION_ENDPOINT):
        super().__init__()
        self.default_module_name = default_module_name
        self.collection_endpoint_name = collection_endpoint_name

    def resolve_operation_id(self, operation: AbstractOperation) -> str:
        path = operation.path.replace("-", "_")

        is_collection_endpoint = operation.method.lower() == "get" and not operation.path.strip("/").endswith("}")
        suffix = self.collection_endpoint_name if is_collection_endpoint else operation.method.lower()

        # Remove arguments from path
        path = re.sub(r"{.+?}", "", path)
        path = re.sub(r"//", "/", path)
        path = path.strip("/")

        resolved = f"{self.default_module_name}.{path.replace('/', '.')}.{suffix}"
        return resolved
