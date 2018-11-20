OVB manage
=========

Ansible roles for managing a heat stack to deploy an OpenStack cloud using OpenStack Virtual Baremetal.

Requirements
------------

These roles assume that the host cloud has already been patched as per
https://github.com/cybertron/openstack-virtual-baremetal/blob/master/README.rst#patching-the-host-cloud.

Role Variables
--------------

**Note:** Make sure to include all environment file and options from your [initial Overcloud creation](http://docs.openstack.org/developer/tripleo-docs/basic_deployment/basic_deployment_cli.html#deploy-the-overcloud)

To interact with the Openstack Virtual Baremetal host cloud, credentials are needed:
- os_username: <cloud_username>
- os_password: <user_password>
- os_tenant_name: <tenant_name>
- os_auth_url: <cloud_auth_url> # For example http://190.1.1.5:5000/v2.0
- os_region_name: <os_region_name> # Most probably RegionOne
- identity_api_version: <api_version> version of identity API 2 or 3
- os_user_domain_name: <user_domain_name> for API 3
- os_project_domain_name: <project_domain_name> for API 3

Parameters required to access the stack:
- stack_name: <'baremetal_{{ idnum }}'> -- name for OVB heat stack
- clouds_yaml: <path> path to clouds.yaml file
- cloud_name: <cloud_name> name of cloud in clouds.yaml file
- cloud_credentials: dictionary of cloud credentials for authentication
- key_name: <key_name> key name to attache to ovb


Parameters used the env.yaml file to create the OVB heat stack (See defaults/main.yml for default values):
- create_undercloud
- env_args
- failed_log
- fail_in_remove
- logs_dir
- net_args
- nodes_file
- ovb_args
- ovb_clone
- ovb_repo_directory
- ovb_repo_source_dir
- ovb_repo_url
- ovb_repo_version
- ovb_working_dir
- role_args
- undercloud_args

- net_iso: <multi-nic> -- other options are 'none' and 'public-bond'

Dependencies
------------

This playbook depends on the  library and https://github.com/cybertron/openstack-virtual-baremetal.

Example Playbook
----------------

Playbooks to create the strack prior to TripleO Quickstart deployments will require:

- name: Create the OVB stack
  hosts: localhost
  roles:
    - { role: ovb-manage, ovb_manage_stack_mode: 'create' }

License
-------

Apache

Author Information
------------------

RDO-CI Team

