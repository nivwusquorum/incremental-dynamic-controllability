from collections import namedtuple
from fast_dc import FastDc


StnuEdge = namedtuple('StnuEdge', ['fro', 'to', 'lower_bound', 'upper_bound'])

class Stnu(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.num_nodes = 0
        self.controllable_edges = []
        self.uncontrollable_edges = []
        self._is_dc = None
        self._update_dc = True
        self._first_time = True

    @property
    def num_edges(self):
        return len(self.uncontrollable_edges) + len(self.controllable_edges)

    def is_dynamically_controllable(self):
        # if nothing changed return cached result
        if not self._update_dc:
            return self._is_dc

        if self._first_time:
            # if we calculate DC from the first time use nonincremental
            self._is_dc = self._fast_dc()
            self._first_time = False
        else:
            self._is_dc = self._incremental_dc()

        self._update_dc = False
        return self._is_dc

    def _fast_dc(self):
        solver = FastDc(self)
        return solver.solve()

class NamedStnu(Stnu):
    def reset(self):
        super(NamedStnu, self).reset()
        self._renaming = {}
        self._inverse_renaming = {}

    def read_from_stdin(self):
        self.reset()
        next_number = [1]
        def read_edges(how_many, where_to):
            for _ in range(how_many):
                start_name, end_name, lower_bound, upper_bound = raw_input().split(' ')
                lower_bound = float(lower_bound)
                upper_bound = float(upper_bound)
                for name in [start_name, end_name]:
                    if name not in self._renaming:
                        self._renaming[name] = next_number[0]
                        self._inverse_renaming[next_number[0]] = name
                        next_number[0] += 1
                where_to.append(StnuEdge(self._renaming[start_name],
                                          self._renaming[end_name],
                                          lower_bound,
                                          upper_bound))
        num_controllable = int(raw_input())
        read_edges(num_controllable, self.controllable_edges)
        num_uncontrollable = int(raw_input())
        read_edges(num_uncontrollable, self.uncontrollable_edges)
        self._num_nodes = len(self._renaming)

    def pretty_print(self):
        print 'Number of nodes: %d' % self.num_nodes
        print 'Number of edges: %d' % self.num_edges
        print 'Number of controllable edges: %d' % len(self.controllable_edges)
        print 'Number of uncontrollable edges: %d' % len(self.uncontrollable_edges)
        print 'List of controllable edges:'
        for edge in self.controllable_edges:
            fro, to, lb, ub = edge
            print '    %s -> %s [%f, %f]' % (self._inverse_renaming[fro],
                                             self._inverse_renaming[to],
                                             lb,
                                             ub)
        print 'List of uncontrollable edges:'
        for edge in self.uncontrollable_edges:
            fro, to, lb, ub = edge
            print '    %s -> %s [%f, %f]' % (self._inverse_renaming[fro],
                                             self._inverse_renaming[to],
                                             lb,
                                             ub)
