# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals


def generic_getter(obj, property_name):
    if hasattr(obj, property_name):
        return getattr(obj, property_name)
    if hasattr(obj, "__dict__"):
        return obj.__dict__.get(property_name, None)
    return None


class AbstractSchedulingPolicy(object):

    def decide_cluster_deployment(self, appliances, sites, clusters, hints=None):
        raise not NotImplemented


class DummySchedulingPolicy(AbstractSchedulingPolicy):

    def decide_cluster_deployment(self, appliance, clusters, force_new=False, hints=None):
        if force_new:
            return None
        for cluster in clusters:
            if str(generic_getter(cluster, "appliance")) == str(appliance):
                return cluster
        # Return None to create a new cluster
        return None
