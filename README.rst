RDO Zuul jobs
=============

This repo contains a set of ansible playbooks which are used by Zuul
for the RDO CI. It also contains job and project-template definitions
for the RDO project. You should edit these files to make configuration
changes to RDO Infrastructure CI.

RDO CI jobs environment settings
--------------------------------

Many RDO CI jobs use `feature sets`_ from the TripleO-quickstart to define
enviroment in which tests and other actions are to be executed.

Other settings, such as playbooks to be executed during or after deployment,
are retrieved from the TripleO-quickstart-extras_ repository.

TripleO CI jobs integration pipelines naming convention
=======================================================

Below is the standard/generalized name for Tripleo CI jobs integration pipelines:

- Master (Development Branch)- openstack-periodic-integration-main
- Master minus 1 release (stable/ussuri) - openstack-periodic-integration-stable1
- Master minus 2 release (stable/train c8) - openstack-periodic-integration-stable2
- Master minus 2 release (stable/train c7) - openstack-periodic-integration-stable2-centos7
- Master minus 3 release (stable/stein) - openstack-periodic-integration-stable3
- Master minus 4 releases and so on (stable/queens and rocky) - openstack-periodic-integration-4-5

.. _`feature sets`: https://docs.openstack.org/tripleo-quickstart/latest/feature-configuration.html
.. _TripleO-quickstart-extras: https://opendev.org/openstack/tripleo-quickstart-extras/
