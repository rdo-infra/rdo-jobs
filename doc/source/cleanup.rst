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
Some nodesets were not used anywhere, so there were deleted.
Full list of removed nodesets is available here [1]_.
All runc nodesets has been changed to use Kubernetes driver.


Labels
~~~~~~
No changes in labels.


Images
~~~~~~
No changes in images.


References
~~~~~~~~~~

.. [1] https://review.rdoproject.org/r/#/c/25560/
