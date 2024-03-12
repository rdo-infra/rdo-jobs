#!/bin/bash -xe
#
# Build a Puppetfile with latest dependencies
#

PACKSTACK_DIR="${1:-packstack}"
POI_PACKSTACK_DIR="${2:-puppet-openstack-integration}"

# header
echo -e "# Auto-generated Puppetfile for Packstack project\n" > $PACKSTACK_DIR/Puppetfile

# OpenStack Modules
echo -e "moduledir '/usr/share/openstack-puppet/modules'\n" >> $PACKSTACK_DIR/Puppetfile
echo -e "## OpenStack modules\n" >> $PACKSTACK_DIR/Puppetfile
for p in $(cat $PACKSTACK_DIR/openstack_modules.txt); do
    cat >> $PACKSTACK_DIR/Puppetfile <<EOF
mod '$title',
  :git => 'https://github.com/openstack/puppet-$p',
  :ref => 'master'

EOF
done

# External Modules
echo -e "## Non-OpenStack modules\n" >> $PACKSTACK_DIR/Puppetfile
for e in $(cat $PACKSTACK_DIR/external_modules.txt); do
    namespace=$(echo $e | awk -F'/' '{print $1}' | cut -d "," -f 1)
    module=$(echo $e | awk -F'/' '{print $2}' | cut -d "," -f 1)
    title=$(echo $module | awk -F'/' '{print $1}' | cut -d "-" -f 2)
    pin=$(echo $e | grep "," | cut -d "," -f 2)
    if [ ! -z "$pin" ]; then
        git ls-remote --exit-code https://github.com/$namespace/$module $pin
        if (($? == 2)); then
            if ! git ls-remote --exit-code https://github.com/$namespace/$module | grep -q $pin; then
                echo "Wrong pin: $pin does not exist in $module module."
                exit 1
            else
                tag=$pin
            fi
        else
            tag=$pin
        fi
    else
        tag=$(grep -A1 -e "https://github.com/$namespace/$module" $POI_PACKSTACK_DIR/Puppetfile | grep -e ":ref" | cut -d"'" -f2)
        if [ -z "$tag" ]; then
            git clone https://github.com/$namespace/$module modules/$module
            tag=$(cd modules/$module; git describe --tags $(git rev-list --tags --max-count=1))
            rm -rf modules/$module
        fi
    fi
    cat >> $PACKSTACK_DIR/Puppetfile <<EOF
mod '$title',
  :git => 'https://github.com/$namespace/$module',
  :ref => '$tag'

EOF
done

# for debug
cat $PACKSTACK_DIR/Puppetfile
