RDO Zuul jobs
=============

This repo contains a set of ansible playbooks which are used by Zuul
for the RDO CI. It also contains job and project-template definitions
for the RDO project. You should edit these files to make configuration
changes to RDO Infrastructure CI.

TripleO CI jobs integration pipelines naming convention
=======================================================

Below is the standard/generalized name for Tripleo CI jobs integration pipelines:

- Main (Development Branch)- openstack-periodic-integration-main
- Main minus 1 release (stable/wallaby) - openstack-periodic-integration-stable1
- Main minus 1 release (stable/wallaby cs9) - openstack-periodic-integration-stable1-cs9
- Main minus 2 release (stable/victoria) - openstack-periodic-integration-stable2
- Main minus 3 release (stable/ussuri) - openstack-periodic-integration-stable3
- Main minus 4 release (stable/train) - openstack-periodic-integration-stable4
- Main minus 4 release (stable/train c7) - openstack-periodic-integration-stable4-centos7
