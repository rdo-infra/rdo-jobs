#!/bin/bash
set -ex

# Simple script to test several DLRN packages
TAG="${1:-wallaby-uc}"
PACKAGES_TO_BUILD="${2:-python-glanceclient}"
CENTOS_VERSION="${3:-centos7}"
PROJECT_DISTRO_BRANCH="rpm-master"

# Prepare config
if [ "$CENTOS_VERSION" = "centos7" ];then
    target="centos"
    PYTHON_VERSION="py27"
else
    target="centos8"
    PYTHON_VERSION="py36"
fi
baseurl="http://trunk.rdoproject.org/${CENTOS_VERSION}/"
src="master"
branch=""
tag="wallaby-uc"
components="false"

# Setup virtualenv with tox and use it
tox -e${PYTHON_VERSION} --notest
. .tox/${PYTHON_VERSION}/bin/activate

# If we are testing a commit on a specific branch, make sure we are using it
if [[ "${TAG}" != "wallaby-uc" ]]; then
    branch=$(echo $TAG | awk -F- '{print $1}')
    tag=$TAG
    baseurl="http://trunk.rdoproject.org/${branch}/${CENTOS_VERSION}/"
    src="stable/${branch}"
    PROJECT_DISTRO_BRANCH="${TAG}-rdo"
fi

# Enable components for all centos8 builders
if [ "${CENTOS_VERSION}" = "centos8" ]; then
    components="true"
fi

# Update the configuration
sed -i "s%target=.*%target=${target}%" projects.ini
sed -i "s%source=.*%source=${src}%" projects.ini
sed -i "s%baseurl=.*%baseurl=${baseurl}%" projects.ini
sed -i "s%tags=.*%tags=${tag}%" projects.ini
sed -i "s%use_components=.*%use_components=${components}%" projects.ini

PACKAGE_LINE=""
# Prepare directories
mkdir -p data/repos
for PACKAGE in ${PACKAGES_TO_BUILD}; do
    PACKAGE_INFO=$(rdopkg findpkg $PACKAGE -l /tmp/rdoinfo)
    PROJECT_TO_BUILD_MAPPED=$(echo "$PACKAGE_INFO" | awk '/^name:/ {print $2}')
    PROJECT_IN_RDOINFO=$(echo "$PACKAGE_INFO" | awk '/^project:/ {print $2}')
    PROJECT_DISTGIT=$(echo "$PACKAGE_INFO" | awk '/^distgit:/ {print $2}')
    NAMESPACE=$(echo "$PACKAGE_INFO" | awk '/^patches/ { split($2, res, "/"); print res[6] }')
    # Remove trailing .git from distgit name, otherwise Depends-On: will fail
    PROJECT_DISTRO="$NAMESPACE/$(echo $PROJECT_DISTGIT | awk -F/ '{print $NF}' | sed 's/\.git$//')"
    PROJECT_DISTRO_DIR=${PROJECT_TO_BUILD_MAPPED}_distro

    if [ "$PROJECT_DISTGIT" = "https://github.com/openstack/rpm-packaging" ]; then
        GIT_BASE_URL=$(dirname $PROJECT_DISTGIT)
        GIT_BASE="review.openstack.org"
        PROJECT_DISTRO=$(basename $PROJECT_DISTGIT)
    else
        GIT_BASE_URL="https://review.rdoproject.org/r/p"
        GIT_BASE="review.rdoproject.org"
    fi

    # If we are running under Zuul v3, we can find the distgit repos under /home/zuul
    if [ -d ~/src/${GIT_BASE}/${PROJECT_DISTRO} ] ; then
        mkdir -p data/$PROJECT_DISTRO
        cp -dRl ~/src/${GIT_BASE}/${PROJECT_DISTRO}/. data/${PROJECT_DISTRO}
        # NOTE(jpena): is this needed?
        pushd data/${PROJECT_DISTRO}
        git checkout $PROJECT_DISTRO_BRANCH
        popd
        mv data/$PROJECT_DISTRO data/$PROJECT_DISTRO_DIR
    else
        # We re outside the gate, just do a regular git clone
        pushd data/
        # rm -rf first for idempotency
        rm -rf $PROJECT_DISTRO_DIR
        git clone "${GIT_BASE_URL}/${PROJECT_DISTRO}" $PROJECT_DISTRO_DIR
        cd $PROJECT_DISTRO_DIR
        git checkout $PROJECT_DISTRO_BRANCH
        popd
    fi
    PACKAGE_LINE="$PACKAGE_LINE --package-name $PACKAGE"
done


# If the commands below throws an error we still want the logs
function copy_logs {
    mkdir -p logs
    rsync -avzr data/repos logs/centos-$PROJECT_DISTRO_BRANCH
    rsync -avzrL data/repos/current logs/centos-$PROJECT_DISTRO_BRANCH
}
trap copy_logs ERR EXIT

# Run DLRN
dlrn --config-file projects.ini --head-only $PACKAGE_LINE --dev --info-repo /tmp/rdoinfo
# For componentized builds we need to consolidate all updates in a single repodata
if [ -d data/repos/component ] && [ -d data/repos/current ]; then
    mv data/repos/component data/repos/current/
    createrepo -v data/repos/current/
fi
copy_logs
# Clean up mock cache, just in case there is a change for the next run
mock -r data/dlrn-1.cfg --scrub=all
