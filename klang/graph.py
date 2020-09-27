"""All things graph related.

Graph helper functions. Graph is defined as an sparse adjacency matrix and a
node is an index.
"""
import collections

import numpy as np


def graph_matrix(edges, directed=True, order=-1):
    """Build adjacency graph matrix from edges relationships.

    Args:
        edges (list): List of edges (tuples).

    Kwargs:
        directed (bool): If directed graph. Undirected otherwise.  order (int):
            Predefined graph order (number of nodes). Has to be bigger than the
            maximum node index in edges. If < 0 will be determined from unique
            nodes in edges.

    Returns:
        array: Dense graph matrix.
    """
    edges = np.asarray(edges)
    if order < 0:
        order = edges.max() + 1

    shape = (order, order)
    graph = np.zeros(shape, dtype=int)
    indices = tuple(edges.T)
    graph[indices] = 1
    if not directed:
        graph[indices[::-1]] = 1

    return graph


def active_edges(graph, node):
    """Get active edges for a node. With matrix transpose can be used to get
    either out- or ingoing edges.

    Usage:
        >>> graph = csr_matrix([
        ...     [0, 1, 1, 0],
        ...     [0, 0, 0, 1],
        ...     [0, 0, 0, 1],
        ...     [0, 0, 0, 0],
        ... ])
        ... outNodes = active_edges(graph, 0)
        array([1, 2], dtype=int32)

        >>> inNodes = active_edges(graph.T, 1)
        array([0], dtype=int32)

    Args:
        graph (array): Graph matrix.
        node (int): Node index.

    Returns:
        array: Indices of child nodes.
    """
    row = graph[node]
    indices = row.nonzero()
    return indices[-1]


def get_sources(graph):
    """Get all source nodes from graph (no incoming edges)."""
    nIncoming = graph.sum(axis=0)
    indices = (nIncoming == 0).nonzero()
    return indices[-1]


def get_sinks(graph):
    """Get all sink nodes from graph (no outgoing edges)."""
    return get_sources(graph.T)


def get_successors(graph, node):
    """Get successors of node in directed graph."""
    return active_edges(graph, node)


def get_predecessors(graph, node):
    """Get predecessors of node in directed graph."""
    return active_edges(graph.T, node)


def find_back_edges(graph):
    """Find back edges in directed graph.

    Resources:
      - https://www.youtube.com/watch?v=rKQaZuoUR4M
    """
    nNodes, _ = graph.shape
    allNodes = range(nNodes)
    white = set(allNodes)
    gray = set()
    black = set()
    backEdges = []

    def move_node(node, src, dst):
        """Move node from one set to another."""
        src.remove(node)
        dst.add(node)

    def dfs(parent):
        """Depth first search graph traversal."""
        move_node(parent, white, gray)
        for child in get_successors(graph, parent):
            if child in black:
                continue

            if child in gray:
                backEdges.append((parent, child))
                continue

            dfs(child)

        move_node(parent, gray, black)

    while white:
        node = next(iter(white))  # white.pop() would remove item from set!
        dfs(node)

    return backEdges


def remove_back_edges(graph):
    """Remove back edges from directed graph and return DAG."""
    dag = graph.copy()
    for edge in find_back_edges(graph):
        dag[edge] = 0

    return dag


def _node_is_ready(graph, node, order):
    """Check if `node` is ready for topological sorting `order`, that is, all
    predecessors of `node` have to be in `order` list.
    """
    for predecessor in get_predecessors(graph, node):
        if predecessor not in order:
            return False

    return True


def topological_sorting(graph):
    """Find appropriate execution order in directed graph with cycles.

    Args:
        graph (array): Graph adjacency matrix.

    Returns:
        list: Node execution order.
    """
    dag = remove_back_edges(graph)
    nNodes, _ = dag.shape
    allNodes = range(nNodes)
    queue = collections.deque(allNodes)
    order = []
    while queue:
        node = queue.popleft()
        if node not in order:
            successors = get_successors(dag, node)
            if _node_is_ready(dag, node, order):
                queue.extendleft(successors)
                order.append(node)
            else:
                queue.extend(successors)

    return order


def plot_node(position, label='', radius=.1, fontsize=10, ax=None):
    """Plot graph node."""
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    ax = ax or plt.gca()
    circle = plt.Circle(position, radius=radius)
    ax.add_patch(circle)
    if label:
        x, y = position
        ax.annotate(label, xy=(x, y-.25*radius), fontsize=fontsize, ha='center')


def plot_edge(start, end, color='black', ax=None, **kwargs):
    """Plot edge arrow"""
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    ax = ax or plt.gca()
    arrow = mpl.patches.FancyArrowPatch(
        start,
        end,
        shrinkA=20.,
        shrinkB=20.,
        connectionstyle='arc3,rad=.1',
        arrowstyle='Simple, tail_width=0.5, head_width=8, head_length=8',
        color=color,
        **kwargs,
    )
    ax.add_patch(arrow)


def plot_graph(graph, positions, ax=None, edgeColor='black'):
    """Plot graph matrix."""
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    ax = ax or plt.gca()
    n, _ = graph.shape
    for node in range(n):
        for child in active_edges(graph, node):
            #print(node, '->', child)
            plot_edge(positions[node], positions[child], color=edgeColor)

    for i, pos in enumerate(positions):
        plot_node(pos, label=str(i))

    ax.axis('off')
    ax.set_aspect('equal')
    ax.autoscale_view()
