RDO Zuul jobs
=============

This repo contains a set of ansible playbooks which are used by Zuul
for the RDO CI. It also contains job and project-template definitions
for the RDO project. You should edit these files to make configuration
changes to RDO Infrastructure CI.

Changed integration pipelines naming convention
================================================

Keep the standard/generalize name for integration pipelines.

Rename the integration pieplines as below:

1. openstack-periodic-master -> openstack-periodic-integration-main (master)
2. openstack-periodic-latest-released -> openstack-periodic-integration-stable1 (master-1 release)
3. openstack-periodic-24hr -> openstack-periodic-integration-stable2 (master-2 release)
4. New pipeline openstack-periodic-integration-stable3 (master-3 release)
5. openstack-periodic-wednesday-weekend -> openstack-periodic-integration-4-plus (master-4 and so on releases)
