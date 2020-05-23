"""Block execution."""
import collections

from klang.block import input_neighbors, output_neighbors
from klang.graph import graph_matrix, topological_sorting


def traverse_network(blocks):
    """Traverse block network and collect vertices and edges. Vertices are
    returned as a list, not as a set, for preserving sequence order / better
    edge case handling.

    Args:
        blocks (iterable): Starting blocks for graph traversal.

    Returns:
        tuple: Network vertices and edges.
    """
    vertices = []
    edges = set()
    queue = collections.deque(blocks)
    while queue:
        block = queue.popleft()
        if block not in vertices:
            vertices.append(block)
            for successor in output_neighbors(block):
                edges.add((block, successor))
                queue.append(successor)

            for predecessor in input_neighbors(block):
                edges.add((predecessor, block))
                queue.append(predecessor)

    return vertices, edges


def determine_execution_order(blocks):
    """Get appropriate execution order for block network."""
    blocks = list(blocks)
    vertices, edges = traverse_network(blocks)
    if not edges:
        return vertices

    nNodes = len(vertices)  # Network size

    # klang.graph module operates with integer indices as nodes. We need a
    # block <-> index mapping (and back-mapping).
    indices = list(range(nNodes))
    idx2block = dict(zip(indices, vertices))
    block2idx = dict(zip(vertices, indices))

    # Topological sort -> execution order
    intEdges = [(block2idx[src], block2idx[dst]) for src, dst in edges]
    graph = graph_matrix(intEdges, order=nNodes)
    order = topological_sorting(graph)
    execOrder = [idx2block[idx] for idx in order]
    #print_exec_order(execOrder)
    return execOrder


def execute(blocks):
    """Execute blocks."""
    for block in blocks:
        block.update()


def print_exec_order(execOrder):
    """Print numbered execution order."""
    for iblock in enumerate(execOrder, 1):
        print('%d) %s' % iblock)

    print()
