#!/usr/bin/env bash

set -euf -o pipefail

: "${BUILD_DOCKER_IMAGES:=0}"
: "${RUN_TESTS:=0}"

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null 2>&1 && pwd)"
repository_root_directory="$(cd "${script_directory}" && git rev-parse --show-toplevel)"

if [[ "${BUILD_DOCKER_IMAGES}" -eq 1 ]]; then
    "${script_directory}/../setup/build-tester.sh"
fi
if [[ "${RUN_TESTS}" -eq 1 ]]; then
    "${script_directory}/run-python-tests.sh"
fi

docker run -e CODECOV_TOKEN -u $(id -u):$(id -g) -w "${repository_root_directory}" --rm \
    -v "${repository_root_directory}":"${repository_root_directory}" tester \
    scripts/test/run-upload-codecov.sh
