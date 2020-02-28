"""All things graph related. Graph helper functions."""
import matplotlib as mpl
import numpy as np
from matplotlib import pyplot as plt
from scipy.sparse import csr_matrix


def graph_matrix(edges, directed=True):
    """Build adjacency graph matrix from edges relationships.

    Args:
        edges (list): List of edges (tuples).

    Returns:
        array: Dense graph matrix.
    """
    edges = np.asarray(edges)
    nNodes = edges.max() + 1
    shape = (nNodes, nNodes)
    graph = csr_matrix(shape, dtype=int)
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


def get_successors(graph, node):
    """Get successors of node in directed graph."""
    return active_edges(graph, node)


def get_predecessors(graph, node):
    """Get predecessors of node in directed graph."""
    return active_edges(graph.T, node)


def plot_node(position, label='', radius=.1, fontsize=10, ax=None):
    """Plot graph node."""
    ax = ax or plt.gca()
    circle = plt.Circle(position, radius=radius)
    ax.add_patch(circle)
    if label:
        x, y = position
        ax.annotate(label, xy=(x, y-.25*radius), fontsize=fontsize, ha='center')


def plot_edge(start, end, color='black', ax=None, **kwargs):
    """Plot edge arrow"""
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
