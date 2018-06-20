This is a fork of upstream zuul-jobs role, until we land:

  https://review.openstack.org/576933/

Fetch the zuul-cloner shim and install to the destination.

.. zuul:rolevar:: repo_src_dir

   Location of the Zuul source root directory. EG: /home/zuul/src

.. zuul:rolevar:: destination

   Where to install the zuul-cloner shim. This should be the full path
   and filename.
