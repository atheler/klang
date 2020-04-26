import collections
import itertools

from klang.block import input_neighbors, output_neighbors
from klang.graph import graph_matrix, topological_sorting


def traverse_edges(blocks):
    """Traverse edges of block network."""
    queue = collections.deque(blocks)
    visited = set()
    edges = set()
    while queue:
        block = queue.popleft()
        if block in visited:
            continue

        visited.add(block)
        for successor in output_neighbors(block):
            edges.add((block, successor))
            queue.append(successor)

        for predecessor in input_neighbors(block):
            edges.add((predecessor, block))
            queue.append(predecessor)

    return edges


def network_graph(blocks):
    """Get network graph and mapping."""
    edges = traverse_edges(blocks)

    # Determine block <-> index mapping and back-mapping
    uniqueBlocks = set(itertools.chain(*edges))
    nBlocks = len(uniqueBlocks)
    indices = list(range(nBlocks))
    idx2block = dict(zip(indices, uniqueBlocks))
    block2idx = dict(zip(uniqueBlocks, indices))

    intEdges = [(block2idx[src], block2idx[dst]) for src, dst in edges]
    return idx2block, graph_matrix(intEdges)


def determine_execution_order(blocks):
    """Get appropriate execution order for block network."""
    if len(blocks) <= 1:
        return blocks

    idx2block, graph = network_graph(blocks)
    order = topological_sorting(graph)
    return [idx2block[idx] for idx in order]


def execute(blocks):
    """Execute blocks."""
    for block in blocks:
        block.update()
