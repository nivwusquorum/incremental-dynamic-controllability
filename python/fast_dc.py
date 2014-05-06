from collections import namedtuple, defaultdict
from Queue import Queue

from stnu import StnuEdge


class EdgeType(object):
    SIMPLE = 1
    LOWER_CASE = 2
    UPPER_CASE = 3

class Edge(namedtuple('Edge', ['fro', 'to', 'value', 'type', 'maybe_letter'])):
    def __new__(cls, fro, to, value, type, maybe_letter=None):
        return cls.__bases__[0].__new__(cls, fro, to, value, type, maybe_letter)
    

class DcTester(object):
    def __init__(self, stnu):
        self.stnu = stnu
        self._is_dc = None
        self._update_dc = True
        self._first_time = True

    def is_dynamically_controllable(self):
        # if nothing changed return cached result
        if not self._update_dc:
            return self._is_dc

        if self._first_time:
            # if we calculate DC from the first time use nonincremental
            alg = FastDc()
            self._is_dc = alg.solve(self.stnu)
            self._first_time = False
        else:
            # stub: use incremental algorithm here
            self._is_dc = None 

        self._update_dc = False
        return self._is_dc


class FastDc(object):
    """Implementation based on paper "A Structural Characterization of Temporal
    Dynamic Controllability" by Paul Morris"""

    def generate_graph(self, network):
        """Generates graph of edges as in section 2.2"""
        num_nodes = network.num_nodes
        edge_list = []

        def add_controllable(e):
            edge_list.append(Edge(e.fro, e.to, e.upper_bound, EdgeType.SIMPLE))
            edge_list.append(Edge(e.to, e.fro, -e.lower_bound, EdgeType.SIMPLE))

        def add_uncontrollable(e):
            edge_list.append(Edge(e.fro, e.to, e.upper_bound, EdgeType.SIMPLE))
            edge_list.append(Edge(e.to, e.fro, -e.lower_bound, EdgeType.SIMPLE))
            edge_list.append(Edge(e.to, e.fro, -e.upper_bound, EdgeType.UPPER_CASE, e.to))
            edge_list.append(Edge(e.fro, e.to, e.lower_bound, EdgeType.LOWER_CASE, e.to))

        for e in network.controllable_edges:
            add_controllable(e)

        for e in network.uncontrollable_edges:
            # contingent edges with bounds [l, u] can be normalized to edge
            # can be replaced by requirement edge [l,l] followed by upper case edge
            if e.lower_bound == 0:
                add_uncontrollable(e)
            else:
                new_node = num_nodes + 1
                num_nodes += 1
                add_controllable(StnuEdge(e.fro, new_node, e.lower_bound, e.lower_bound))
                add_uncontrollable(StnuEdge(new_node, e.to, 0, e.upper_bound - e.lower_bound))

        return num_nodes, edge_list

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

    def reduce_lower_case(self, num_nodes, edge_list, potentials, lc_edge):
        new_edges = []
        distance = [None] * (num_nodes+1)
        distance[lc_edge.to] = 0

        # Notice that here we are going to be using Johnson's algorithm in
        # a nonintuitive way, we will remove some edges from the original
        # graph which we use to calculate potentials. If you look through
        # proof of Johnson's algorithms you will notice that removing edges
        # never invalidate the key properties of potentials
        """outgoing_edges = defaultdict(lambda: [])
        for edge in edge_list:
            # Ignore lower case edges and upper-case edges with the same letter as lc_edge
            # (paper terminology: breach)
            if (edge.type == EdgeType.LOWER_CASE or
                    (edge.type == EdgeType.UPPER_CASE and
                    edge.maybe_letter == lc_edge.maybe_letter)):
                continue"""

        return new_edges

    def solve(self, network):
        """Implementation of pseudocode from end of section 3"""
        K = len(network.uncontrollable_edges)
        num_nodes, new_edges = self.generate_graph(network)
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
                    reduced_edges = self.reduce_lower_case(num_nodes,
                                                           edge_list,
                                                           potentials,
                                                           e)
                    new_edges.extend(reduced_edges)
            completed_iterations += 1
        # Assuming the theory from the paper checks out. We need one extra
        # iteration to verify that no edge was actually added.
        assert completed_iterations <= K+1
        return True