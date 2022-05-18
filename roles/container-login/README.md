# container-login

Role to login into registries, using Zuul's secrets or any other defined credential. It uses `tripleo_podman`_ role to
login into registries using `podman`.

## Variables

* 'registry_secrets': (Dict) A dictionary with registries as keys and their respective secret variable names as values. 
  The secret variable should be another dict which provides as data: a username and a password/token. Default: "".
* 'push_containers': (Boolean) When set to true, podman buildah login is also performed. Default: False.

See additional variables in `tripleo_podman`_  role documentation.

Example 1:
  ```yaml
- hosts: all
  tasks:
    - name: Logging into localhost registry
      include_role:
        name: container-login
      vars:
        tripleo_podman_tls_verify: false
        registry_secrets:
          localhost:5000: "test_secret"
        test_secret:
          username: "testuser"
          password: "testpassword"
  ```

.. _tripleo_podman: https://docs.openstack.org/tripleo-ansible/latest/roles/role-tripleo_podman.html
