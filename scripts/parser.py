import gflags
import xml.etree.ElementTree as ET
import sys

from collections import defaultdict

gflags.DEFINE_string('input_file', None, 'XML file to convert')
gflags.MarkFlagAsRequired('input_file')
gflags.DEFINE_enum('input_type', 'xml', ['xml', 'parsable'], 'Type of input file')
gflags.DEFINE_enum('output_type', 'summary', ['summary', 'dot', 'parsable', 'xml'], 'Type of output to convert the file to')

FLAGS = gflags.FLAGS

def get_node_renaming(edge_list):
    def num_to_name(num):
        assert num >= 1
        result = []
        while num > 0:
            result.append(num%26)
            num /= 26
        for i in xrange(len(result)):
            if result[i] <= 0 and i+1 < len(result):
                result[i]+=26
                result[i+1]-=1
        if result[-1] == 0:
            result = result[:-1]
        result.reverse()
        return ''.join([chr(ord('A') + x-1) for x in result])

    names = set()
    for start, end, _, _, _ in edge_list:
        names.add(start)
        names.add(end)
    renaming = {}
    next_number = 1
    # make sure names are sorted
    ordered_names = [ (len(name), name) for name in names]
    ordered_names.sort()

    for _, name in ordered_names:
        renaming[name] = num_to_name(next_number)
        #print '%s -> %s' % (name, renaming[name])
        next_number += 1
    return renaming

def generate_graphviz(edge_list):
    renaming = get_node_renaming(edge_list)
    print "digraph G {"
    print "rankdir=\"LR\";"
    for start, end, lb, ub, etype in edge_list:
        assert etype in ['Controllable', 'Uncontrollable'], \
                "%s is not a valid edge type" % etype
        style = 'dotted' if etype == 'Uncontrollable' else 'solid'
        type_char = '?' if etype == 'Uncontrollable' else ''
        lb = '%.2f' % (float(lb))
        ub = '%.2f' % (float(ub),)

        print "%s -> %s [label=\"[%s, %s]%s\", style=%s];" % (renaming[start],
                                                            renaming[end],
                                                            lb,
                                                            ub,
                                                            type_char,
                                                            style)
    print "}"

def summary(edge_list):
    print 'Number of nodes: %d' % len(get_node_renaming(edge_list))
    print 'Number of edges: %d' % len(edge_list)
    print '    of which'
    controllable = len([e for e in edge_list if e[4] == 'Controllable'])
    uncontrollable = len([e for e in edge_list if e[4] == 'Uncontrollable'])

    print '        controllable: %d' % controllable
    print '        Uncontrollable: %d' % (uncontrollable,)

def parsable(edge_list):
    controllable = [ edge for edge in edge_list if edge[4] == 'Controllable']
    uncontrollable = [edge for edge in edge_list if edge[4] == 'Uncontrollable']
    renaming = get_node_renaming(edge_list)
    print len(controllable)
    for edge in controllable:
        print '%s %s %s %s' % (renaming[edge[0]], renaming[edge[1]], edge[2], edge[3])
    print len(uncontrollable)
    for edge in uncontrollable:
        print '%s %s %s %s' % (renaming[edge[0]], renaming[edge[1]], edge[2], edge[3])

def xml(edge_list):
    names = set([e[0] for e in edge_list] + [e[1] for e in edge_list])
    # topological sort
    neighbors = defaultdict(lambda: set())
    input_degree = {name:0 for name in names}

    for edge in edge_list:
        start, end = edge[0], edge[1]
        neighbors[start].add(end)
        input_degree[end]+=1

    topological_order = []
    new_nodes = [x for x in input_degree if input_degree[x] == 0]
    while len(new_nodes) > 0:
        topological_order.extend(new_nodes)
        newer_nodes = []
        for node in new_nodes:
            for neighbor in neighbors[node]:
                input_degree[neighbor] -= 1
                if input_degree[neighbor] == 0:
                    newer_nodes.append(neighbor)
        new_nodes = newer_nodes
    assert set(input_degree.values()) == set([0])

    start_node = topological_order[0]
    end_node = topological_order[-1]
    print '<CCTP>'
    print '    <NAME>main</NAME>'
    print '    <START>%s</START>' % (start_node,)
    print '    <END>%s</END>' % (end_node,)
    print '    <EVENT-UNIT>millisecond</EVENT-UNIT>'
    print '    <DURATION-UNIT>minute</DURATION-UNIT>'
    for start, end, lb, ub, type in edge_list:
        print '    <CONSTRAINT>'
        print '        <START>%s</START>' % (start,)
        print '        <END>%s</END>' % (end,)
        print '        <ID>edge-%s%s</ID>' % (start, end)
        print '        <NAME>irrelevant</NAME>'
        print '        <LOWERBOUND>%s</LOWERBOUND>' % (lb,)
        print '        <UPPERBOUND>%s</UPPERBOUND>' % (ub,)
        print '        <TYPE>%s;Constraint</TYPE>' % (type,)
        print '    </CONSTRAINT>'
    for name in names:
        print '    <EVENT>'
        print '        <ID>%s</ID>' % (name,)
        print '        <NAME>%s</NAME>' % (name,)
        print '    </EVENT>'
    print '</CCTP>'


def parse_xml():
    tree = ET.parse(FLAGS.input_file)
    edge_list = []
    for constraint in tree.getroot().findall('CONSTRAINT'):
        type = constraint.find('TYPE').text.split(';')[0]
        if type == 'Constraint':
            type = 'Controllable'
        edge_list.append((constraint.find('START').text,
                          constraint.find('END').text,
                          constraint.find('LOWERBOUND').text,
                          constraint.find('UPPERBOUND').text,
                          type))
    return edge_list

def parse_parsable():
    with open(FLAGS.input_file, 'r') as file:
        edge_list = []
        num_controllable = int(file.readline()[:-1])
        for _ in xrange(num_controllable):
            start, end, lb, ub = tuple(file.readline()[:-1].split(' '))
            edge_list.append((start, end, lb, ub, 'Controllable'))
        num_uncontrollable = int(file.readline()[:-1])
        for _ in xrange(num_uncontrollable):
            start, end, lb, ub = tuple(file.readline()[:-1].split(' '))
            edge_list.append((start, end, lb, ub, 'Uncontrollable'))
        return edge_list

def main():
    argv = FLAGS(sys.argv)
    # input parsing
    if FLAGS.input_type == 'xml':
        edge_list = parse_xml()
    if FLAGS.input_type == 'parsable':
        edge_list = parse_parsable()
    # output generation
    if FLAGS.output_type == 'dot':
        generate_graphviz(edge_list)
    if FLAGS.output_type == 'summary':
        summary(edge_list)
    if FLAGS.output_type == 'parsable':
        parsable(edge_list)
    if FLAGS.output_type == 'xml':
        xml(edge_list)

if __name__ == '__main__':
    main()