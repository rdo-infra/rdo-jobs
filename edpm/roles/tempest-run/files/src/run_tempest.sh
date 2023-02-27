#!/bin/sh

TEMPEST_DIR=/root/tempest/openshift

pushd /root/tempest

export OS_CLOUD=default

tempest init openshift

pushd $TEMPEST_DIR

discover-tempest-config --os-cloud $OS_CLOUD --debug --create

TEMPEST_LIST="/root/tempest/"
if [ ! -z ${USE_EXTERNAL_FILES} ]; then
    TEMPEST_LIST="/root/external_files/"
fi

tempest run \
    --include-list ${TEMPEST_LIST}include.txt \
    --exclude-list ${TEMPEST_LIST}exclude.txt

RETURN_VALUE=$?

echo "Generate subunit"
stestr last --subunit > ${TEMPEST_LIST}testrepository.subunit

echo "Generate html result"
subunit2html ${TEMPEST_LIST}testrepository.subunit ${TEMPEST_LIST}/stestr_results.html

exit ${RETURN_VALUE}

popd
popd
