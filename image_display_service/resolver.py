# Based off: https://github.com/zalando/connexion/blob/master/connexion/resolver.py
#
# Copyright 2015 Zalando SE
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
import re

from connexion import Resolver
from connexion.operations import AbstractOperation


class ExtendedRestyResolver(Resolver):
    """
    TODO
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
