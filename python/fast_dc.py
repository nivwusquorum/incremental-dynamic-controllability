from collections import namedtuple, defaultdict
from Queue import Queue

class EdgeType(object):
    SIMPLE = 1
    LOWER_CASE = 2
    UPPER_CASE = 3

class Edge(namedtuple('Edge', ['fro', 'to', 'value', 'type', 'maybe_letter'])):
    def __new__(cls, fro, to, value, type, maybe_letter=None):
        return cls.__bases__[0].__new__(cls, fro, to, value, type, maybe_letter)
    

class FastDc(object):
    """Implementation based on paper "A Structural Characterization of Temporal
    Dynamic Controllability" by Paul Morris"""
    def __init__(self, network):
        self.network = network

    def generate_graph(self):
        """Generates graph of edges as in section 2.2"""
        edge_list = []
        for e in self.network.controllable_edges:
            edge_list.append(Edge(e.fro, e.to, e.upper_bound, EdgeType.SIMPLE))
            edge_list.append(Edge(e.to, e.fro, -e.lower_bound, EdgeType.SIMPLE))

        for e in self.network.uncontrollable_edges:
            edge_list.append(Edge(e.fro, e.to, e.upper_bound, EdgeType.SIMPLE))
            edge_list.append(Edge(e.to, e.fro, -e.lower_bound, EdgeType.SIMPLE))
            edge_list.append(Edge(e.to, e.fro, -e.upper_bound, EdgeType.UPPER_CASE, e.to))
            edge_list.append(Edge(e.fro, e.to, e.lower_bound, EdgeType.LOWER_CASE, e.to))
        return edge_list

    def allmax(self, num_nodes, edge_list):
        """Calculates allmax projection of STNU (see section 2.2). 

        Returns two parameters:
            success - true if consistent
            potentials - potentials for use in Dijkstra algorithm
        """
        weights = {}
        neighbor_list = defaultdict(lambda: set())

        for e in edge_list:
            if e.type != EdgeType.LOWER_CASE:
                pair = (e.fro, e.to)
                neighbor_list[e.fro].add(e.to)
                if not pair in weights or weights[pair] > e.value:
                    weights[pair] = e.value
        
        # Like in Johnson's algorithm we add node 0 artificially 
        for node in xrange(1, num_nodes + 1):
            weights[(0,node)] = 0
            neighbor_list[0].add(node)

        source = 0
        terminated, distances = self.spfa(source = 0,
                                          num_nodes=num_nodes + 1,
                                          weights=weights,
                                          neighbor_list=neighbor_list)

        # exclude artificial 0 node from result
        return (terminated, distances[1:] if distances else None)
        
    def spfa(self, source, num_nodes, weights, neighbor_list):
        """Shortest Paths Fastests Algorithm - think optimized Bellman-Ford,
        
        Assumes nodes have numbers from 0 to num_nodes (inclusive).

        Returns two variables:
            success - true if no negative cycle
            distances - shortest distance from the source to each node
                        or None if negative cycle
        """
        # None is Infinity
        distance = [None] * num_nodes
        currently_in_queue = [False] * num_nodes
        times_in_queue = [0] * num_nodes
        q = Queue()

        distance[source] = 0
        currently_in_queue[source] = True
        times_in_queue[source] = 1
        q.put(0)

        negative_cycle = False

        while not q.empty() and not negative_cycle:
            node = q.get()
            currently_in_queue[node] = False
            for neighbor in neighbor_list[node]:
                if (distance[neighbor] is None or
                        distance[neighbor] > distance[node] + weights[(node, neighbor)]):
                    distance[neighbor] = distance[node] + weights[(node, neighbor)]
                    if not currently_in_queue[neighbor]:
                        currently_in_queue[neighbor] = True
                        times_in_queue[neighbor] += 1
                        if times_in_queue[neighbor] > num_nodes:
                            negative_cycle = True
                            break
                        q.put(neighbor)

        if negative_cycle:
            return (False, None)
        else:
            return (True, distance)

    def reduce_lower_case(self, potentials, edge_list, lc_edge):
        new_edges = []
        distances = [0] * self.network.num_nodes

        return new_edges

    def solve(self):
        """Implementation of pseudocode from end of section 3"""
        K = len(self.network.uncontrollable_edges)
        new_edges = self.generate_graph()
        num_nodes = self.network.num_nodes
        completed_iterations = 0
        all_edges = []
        while len(new_edges) > 0 and completed_iterations <= K:
            all_edges.extend(new_edges)
            new_edges = []
            consistent, potentials = self.allmax(num_nodes, all_edges)
            if not consistent:
                return False
            for e in all_edges:
                if e.type == EdgeType.LOWER_CASE:
                    reduced_edges = self.reduce_lower_case(num_nodes, potentials, e)
                    new_edges.extend(reduced_edges)
            completed_iterations += 1
        # Assuming the theory from the paper checks out. We need one extra
        # iteration to verify that no edge was actually added.
        assert completed_iterations <= K+1
        return True