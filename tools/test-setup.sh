#!/bin/bash
set -euxo pipefail
FAIL=0

for PYTHON in $(command -v python3 python); do

    $PYTHON --version
    $PYTHON -m pip --version || FAIL=1
    $PYTHON -m virtualenv --version || FAIL=1

done

exit $FAIL
