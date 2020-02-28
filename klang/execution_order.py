"""Find appropriate block execution order."""
import collections

from klang.graph import get_sources, get_successors, get_predecessors


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
    graph = graph.copy()  # Backedge removal

    # Prepare main queue
    sources = get_sources(graph)
    queue = collections.deque(sources)

    # Prepare secondary waiting queue. Set to all nodes by default to cover the
    # all-is-one-big-cycle case.
    nNodes, _ = graph.shape
    allNodes = range(nNodes)
    waiting = collections.deque(allNodes)

    visited = set()
    execOrder = []
    while queue or waiting:
        node = (queue or waiting).popleft()
        if node in execOrder:
            continue

        visited.add(node)
        successors = get_successors(graph, node)
        if node_is_ready(graph, node, execOrder):
            execOrder.append(node)
            queue.extend(successors)
        else:
            for suc in successors:
                if suc in visited:
                    # Remove backedge from graph
                    graph[node, suc] = 0
                    queue.append(suc)
                    break
            else:
                waiting.extend(successors)

    return execOrder
