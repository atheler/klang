import collections

import numpy as np

from klang.block import output_neighbors, input_neighbors
from klang.graph import graph_matrix, topological_sorting


def network_graph(blocks):
    """Get network graph and mapping."""
    block2idx = {}
    idx2block = {}
    queue = collections.deque(blocks)
    visited = set()
    edges = set()

    def get_block_index(block):
        """Get index for block."""
        if block not in block2idx:
            newId = len(block2idx)
            block2idx[block] = newId
            idx2block[newId] = block

        return block2idx[block]

    # Collect all blocks
    while queue:
        block = queue.popleft()
        if block in visited:
            continue

        visited.add(block)
        here = get_block_index(block)
        for child in output_neighbors(block):
            there = get_block_index(child)
            edges.add((here, there))
            queue.append(child)

        for parent in input_neighbors(block):
            back = get_block_index(parent)
            edges.add((back, here))
            queue.append(parent)

    if edges:
        graph = graph_matrix(list(edges))
    else:
        graph = np.zeros((1, 1), dtype=int)

    return idx2block, graph


def determine_execution_order(blocks):
    """Get appropriate execution order for block network."""
    idx2block, graph = network_graph(blocks)
    if graph.size == 1:
        return blocks

    order = topological_sorting(graph)
    return [idx2block[idx] for idx in order]


def execute(blocks):
    """Execute blocks."""
    for block in blocks:
        block.update()
