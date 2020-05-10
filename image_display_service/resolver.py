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
from re import Match

from connexion import Resolver
from connexion.operations import AbstractOperation


class ExtendedRestyResolver(Resolver):
    """
    TODO
    """
    @staticmethod
    def _match_path(operation: AbstractOperation) -> Match:
        return re.search(
            r"^/?(?P<resource_name>([\w\-](?<!/))*)(?P<trailing_slash>/*)(?P<extended_path>.*)$", operation.path
        )

    def __init__(self, default_module_name: str, collection_endpoint_name: str = "search"):
        super().__init__()
        self.default_module_name = default_module_name
        self.collection_endpoint_name = collection_endpoint_name

    def resolve_operation_id(self, operation: AbstractOperation) -> str:
        return self.resolve_operation_id_using_rest_semantics(operation)

    def resolve_operation_id_using_rest_semantics(self, operation: AbstractOperation) -> str:
        return f"{self.get_controller_name(operation)}.{self.get_function_name(operation)}"

    def get_controller_name(self, operation: AbstractOperation) -> str:
        x_router_controller = operation.router_controller

        name = self.default_module_name
        resource_name = ExtendedRestyResolver._match_path(operation).group("resource_name")

        if x_router_controller:
            name = x_router_controller

        elif resource_name:
            resource_controller_name = resource_name.replace("-", "_")
            name += "." + resource_controller_name

        return name

    def get_function_name(self, operation: AbstractOperation) -> str:
        method = operation.method

        path_match = ExtendedRestyResolver._match_path(operation)
        extended_path = path_match.group("extended_path")

        is_collection_endpoint = \
            method.lower() == "get" \
            and path_match.group("resource_name") \
            and not extended_path.strip().endswith("}")

        suffix = self.collection_endpoint_name if is_collection_endpoint else method.lower()

        if "/" not in extended_path:
            return suffix

        path = re.sub(r"{.+?}", "", extended_path)
        path = re.sub(r"//", "/", path)
        path = path.strip("/")
        return f"{path.replace('/', '_')}_{suffix}"
