"""Block execution."""
import collections

from klang.block import input_neighbors, output_neighbors
from klang.graph import graph_matrix, topological_sorting


def traverse_edges(blocks):
    """Traverse edges of block network."""
    queue = collections.deque(blocks)
    visited = set()
    while queue:
        block = queue.popleft()
        if block in visited:
            continue

        visited.add(block)
        for successor in output_neighbors(block):
            yield block, successor
            queue.append(successor)

        for predecessor in input_neighbors(block):
            yield predecessor, block
            queue.append(predecessor)


def determine_execution_order(blocks):
    """Get appropriate execution order for block network."""
    blocks = list(blocks)
    edges = list(traverse_edges(blocks))
    if not edges:
        return blocks

    # Determine unique block
    #
    # Note that the following did not work:
    #
    # >>> uniqueBlocks = set(itertools.chain.from_iterable(edges))
    #
    # Introduces a irregular bug which only messes up execution order 1 / 15
    # runs (?)
    uniqueBlocks = []
    for src, dst in edges:
        if src not in uniqueBlocks:
            uniqueBlocks.append(src)
        if dst not in uniqueBlocks:
            uniqueBlocks.append(dst)

    # Block <-> int mapping (and back-mapping).
    size = len(uniqueBlocks)
    indices = list(range(size))
    idx2block = dict(zip(indices, uniqueBlocks))
    block2idx = dict(zip(uniqueBlocks, indices))

    intEdges = [(block2idx[src], block2idx[dst]) for src, dst in edges]
    graph = graph_matrix(intEdges)
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
