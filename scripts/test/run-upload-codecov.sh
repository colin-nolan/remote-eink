#!/usr/bin/env bash

set -euf -o pipefail

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
src_directory="${script_directory}/../.."

pushd "${src_directory}" > /dev/null

codecov

popd > /dev/null
