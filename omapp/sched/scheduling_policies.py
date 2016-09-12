
def generic_getter(obj, property_name):
    if hasattr(obj, property_name):
        return getattr(obj, property_name)
    if hasattr(obj, "__dict__"):
        return obj.__dict__.get(property_name, None)
    return None


class AbstractSchedulingPolicy(object):

    def decide_cluster_deployment(self, appliances, sites, clusters):
        raise not NotImplemented


class DummySchedulingPolicy(AbstractSchedulingPolicy):

    def decide_cluster_deployment(self, appliance, clusters, force_new=False):
        if force_new:
            return None
        for cluster in clusters:
            if str(generic_getter(cluster, "appliance")) == str(appliance):
                return cluster
        # Return None to create a new cluster
        return None
