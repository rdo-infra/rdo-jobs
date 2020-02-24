#!/bin/bash
set -euxo pipefail
# Used by Zuul CI to perform extra bootstrapping

# Platforms coverage:
# Fedora 30 : has vagrant-libvirt no compilation needed
# CentOS 7  : install upstream vagrant rpm and compiles plugin (broken runtime)
# CentOS 8  : install upstream vagrant rpm and compiles plugin (broken runtime)

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Bumping system tox because version from CentOS 7 is too old
# We are not using pip --user due to few bugs in tox role which does not allow
# us to override how is called. Once these are addressed we will switch back
# non-sudo
command -v python3 python

PYTHON=$(command -v python3 python|head -n1)
PKG_CMD=$(command -v dnf yum|head -n1)

# Workaround for missing re2-devel on centos-7/8, needed by fb-re2 pip wheel
source /etc/os-release
if [ "$ID" = "centos" ]; then
    sudo $PKG_CMD install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-$(rpm --eval '%{centos_ver}').noarch.rpm
    sudo $PKG_CMD update
    sudo $PKG_CMD install -y re2-devel
fi
