"""Execution order in directed graph."""
import collections

from klang.graph import get_successors, get_predecessors, remove_back_edges


def node_is_ready(graph, node, execOrder):
    """Check if node is ready for execution order."""
    for predecessor in get_predecessors(graph, node):
        if predecessor not in execOrder:
            return False

    return True


def execution_order(graph):
    """Find appropriate execution order in directed graph with cycles. Based on
    original algorithm from Nico Neureiter.

    Args:
        graph (array): Graph adjacency matrix.

    Returns:
        list: Node execution order.
    """
    graph = remove_back_edges(graph)
    nNodes, _ = graph.shape
    allNodes = range(nNodes)
    queue = collections.deque(allNodes)
    visited = set()
    execOrder = []
    while queue:
        node = queue.popleft()
        if node in execOrder:
            continue

        visited.add(node)
        successors = get_successors(graph, node)
        if node_is_ready(graph, node, execOrder):
            execOrder.append(node)
            queue.extendleft(successors)
        else:
            queue.extend(successors)

    return execOrder
