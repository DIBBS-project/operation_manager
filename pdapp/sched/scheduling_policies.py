
class AbstractSchedulingPolicy(object):

    def decide_cluster_deployment(self, appliances, sites, clusters):
        raise not NotImplemented


class DummySchedulingPolicy(AbstractSchedulingPolicy):

    def decide_cluster_deployment(self, appliance, clusters, force_new=False):
        if force_new:
            return None
        if len(clusters) > 0:
            return clusters[0]
        # Return None to create a new cluster
        return None
