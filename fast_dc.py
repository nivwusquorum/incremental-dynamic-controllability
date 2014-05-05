Edge = namedtuple('Edge', ['fro', 'to', 'lb', 'ub', 'controllable'])

class FastDc(object):
    def __init__(self, network):
        self.network = network

    def solve(self):
        # stub
        return False