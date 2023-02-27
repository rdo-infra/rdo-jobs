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

curl -O https://opendev.org/openstack/openstack-tempest-skiplist/raw/branch/master/openstack-operators/tempest_allow.yml
curl -O https://opendev.org/openstack/openstack-tempest-skiplist/raw/branch/master/openstack-operators/tempest_skip.yml

tempest-skip list-allowed --file "${TEMPEST_DIR}/tempest_allow.yml" --group ${JOB_NAME} --job ${JOB_NAME} -f value > "${TEMPEST_LIST}/include.txt"
tempest-skip list-skipped --file "${TEMPEST_DIR}/tempest_skip.yml" --job ${JOB_NAME} -f value > "${TEMPEST_LIST}/exclude.txt"

if [[ $(wc -l < "${TEMPEST_LIST}include.txt") -ge 0 ]]; then
    echo "tempest.api.identity.*.v3" >> "${TEMPEST_LIST}include.txt"
fi

tempest run \
    --include-list ${TEMPEST_LIST}include.txt \
    --exclude-list ${TEMPEST_LIST}exclude.txt

RETURN_VALUE=$?

echo "Generate subunit"
stestr last --subunit > ${TEMPEST_LIST}testrepository.subunit || true

echo "Generate html result"
subunit2html ${TEMPEST_LIST}testrepository.subunit ${TEMPEST_LIST}stestr_results.html || true

popd
popd

exit ${RETURN_VALUE}
