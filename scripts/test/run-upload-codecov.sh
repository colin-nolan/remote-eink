#!/usr/bin/env bash

set -euf -o pipefail

: "${CODECOV_TOKEN:?}"

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
src_directory="${script_directory}/../.."

pushd "${src_directory}" > /dev/null

coverage xml
codecov

popd > /dev/null
