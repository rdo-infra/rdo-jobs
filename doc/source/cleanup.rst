Nodesets, labels and images cleanup
===================================

Our Zuul infra configuration was growing very fast. Many things was
done for a trasistional period (e.g.: using Fedora 28 jobs).
Currently, some images, nodesets and images are outdated, deprecated and
sometimes even not used.
Taking advantage of the opportunity, some things has been changed like
switching runc images to use Kubernetes pods.


Nodesets
~~~~~~~~
Changes related to the nodesets:

- removed unused nodesets: `container-centos`, `openstack-single-node`,
  `openstack-two-node`, `tripleo-ovb-fedora-28`, `upstream-centos-7`,
  `single-fedora-28-node` and `three-centos-7-nodes`
- `container-fedora` nodeset is using now `pod-fedora-31` instead of
  `runc-fedora-29`


Labels
~~~~~~
No changes in labels.


Images
~~~~~~
No changes in images.
