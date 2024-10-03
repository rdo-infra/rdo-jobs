#!/usr/bin/env bash

# This script is based on https://github.com/rdo-infra/rdo-dashboards repo.

set -e
set -x

export PATH=$PATH:/usr/local/bin/

report_csv_file="/tmp/ftbfs_report.csv"
releng_workdir="${HOME}/releng"

# upgrade pip
pip install pip -U

python3 -c 'import dnf' && echo "DNF ok" || echo "Please install package dnf"


echo ""
python_version=$(python3 --version)
echo "python version: $python_version"

echo ""
echo "*** cloning releng scripts"
if [ ! -d "$releng_workdir" ]; then
    git clone https://review.rdoproject.org/r/rdo-infra/releng "$releng_workdir"
fi
pushd "$releng_workdir"
git fetch origin && git rebase origin
pip install -r requirements.txt
python3 setup.py install
rdo_list_ftbfs -o "$report_csv_file"
popd

echo ""
echo "*** add releng scripts to PYTHONPATH"
export PYTHONPATH="${PYTHONPATH}:${HOME}/releng/scripts"
echo "PYTHONPATH='${PYTHONPATH}'"

