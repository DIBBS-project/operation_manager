
class AbstractSchedulingPolicy(object):

    def decide_cluster_deployment(self, appliances, sites, clusters):
        raise not NotImplemented


class DummySchedulingPolicy(AbstractSchedulingPolicy):

    def decide_cluster_deployment(self, appliance, clusters, force_new=False):
        if force_new:
            return None
        for cluster in clusters:
            if str(cluster['appliance']) == str(appliance):
                return cluster
        # Return None to create a new cluster
        return None
