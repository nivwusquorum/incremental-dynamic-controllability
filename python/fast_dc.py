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
        self.edge_list = []
        for e in self.network.controllable_edges:
            self.edge_list.append(Edge(e.fro, e.to, e.upper_bound, EdgeType.SIMPLE))
            self.edge_list.append(Edge(e.to, e.fro, -e.lower_bound, EdgeType.SIMPLE))

        for e in self.network.uncontrollable_edges:
            self.edge_list.append(Edge(e.fro, e.to, e.upper_bound, EdgeType.SIMPLE))
            self.edge_list.append(Edge(e.to, e.fro, -e.lower_bound, EdgeType.SIMPLE))
            self.edge_list.append(Edge(e.to, e.fro, -e.upper_bound, EdgeType.UPPER_CASE, e.to))
            self.edge_list.append(Edge(e.fro, e.to, e.lower_bound, EdgeType.LOWER_CASE, e.to))

    def allmax(self):
        """Calculates allmax projection of STNU (see section 2.2). 

        Returns two parameters:
            success - true if consistent
            potentials - potentials for use in Dijkstra algorithm
        """
        weights = {}
        neighbor_list = defaultdict(lambda: set())

        for e in self.edge_list:
            if e.type != EdgeType.LOWER_CASE:
                pair = (e.fro, e.to)
                neighbor_list[e.fro].add(e.to)
                if not pair in weights or weights[pair] > e.value:
                    weights[pair] = e.value
        
        # Like in Johnson's algorithm we add node 0 artificially 
        for node in range(1, self.network.num_nodes + 1):
            weights[(0,node)] = 0
            neighbor_list[0].add(node)

        source = 0
        num_nodes = self.network.num_edges + 1
        terminated, distances = self.spfa(source, num_nodes, weights, neighbor_list)

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

    def reduce_lower_case(self, lc_edge):
        # FIXME(szymon): stub
        return []

    def solve(self):
        """Implementation of pseudocode from end of section 3"""
        K = len(self.network.uncontrollable_edges)
        self.generate_graph()
        for _ in range(K):
            consistent, potentials = self.allmax()
            if not consistent:
                return False
            for e in self.edge_list:
                if e.type == EdgeType.LOWER_CASE:
                    new_edges = self.reduce_lower_case(e)
                    self.edge_list.extend(new_edges)
        return True