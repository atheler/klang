import unittest

import numpy as np
from numpy.testing import assert_equal

from klang.graph import graph_matrix, active_edges, get_sources, topological_sorting


EDGES = [
    (0, 1),
    (0, 2),
    (0, 3),
    (1, 4),
    (2, 4),
    (3, 4),
]
"""list: Simple reference DAG for testing.

    o
   ^ \
  /   \
 /     v
o-->o-->o
 \     ^
  \   /
   v /
    o
"""

GRAPH = graph_matrix(EDGES)
"""ndarray: Graph adjacency matrix."""


SOURCE_DAG = graph_matrix([
    (0, 1), (0, 2), (0, 3),
])


SINK_DAG = graph_matrix([
    (0, 3), (1, 3), (2, 3),
])

SOURCE_SINK_DAG = graph_matrix([
    (0, 1), (1, 4),
    (0, 2), (2, 4),
    (0, 3), (3, 4),
])


SINK_SOURE_DAG = graph_matrix([
    (0, 3), (1, 3), (2, 3),
    (3, 4), (3, 5), (3, 6),
])


TWO_DAG = graph_matrix([
    (0, 1), (2, 3)
])


class TestGraphMatrix(unittest.TestCase):

    """Test graph_matrix() function."""

    def test_graph_matrix_with_reference_dag(self):
        """Test graph_matrix() with reference dag."""
        graph = graph_matrix(EDGES)
        np.testing.assert_equal(graph, [
            [0, 1, 1, 1, 0],
            [0, 0, 0, 0, 1],
            [0, 0, 0, 0, 1],
            [0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0],
        ])


class TestActiveEdges(unittest.TestCase):

    """Test active_edges() function."""

    def test_outgoing_edges(self):
        """Correct outgoing edges."""
        assert_equal(active_edges(GRAPH, 0), [1, 2, 3])
        assert_equal(active_edges(GRAPH, 1), [4])
        assert_equal(active_edges(GRAPH, 2), [4])
        assert_equal(active_edges(GRAPH, 3), [4])
        assert_equal(active_edges(GRAPH, 4), [])

    def test_ingoung_edges(self):
        """Correct ingoing edges."""
        assert_equal(active_edges(GRAPH.T, 0), [])
        assert_equal(active_edges(GRAPH.T, 1), [0])
        assert_equal(active_edges(GRAPH.T, 2), [0])
        assert_equal(active_edges(GRAPH.T, 3), [0])
        assert_equal(active_edges(GRAPH.T, 4), [1, 2, 3])

    def test_with_matrix(self):
        """Test active_edges() with dense matrix input."""
        matrix = GRAPH

        assert_equal(active_edges(matrix, 0), [1, 2, 3])
        assert_equal(active_edges(matrix, 1), [4])
        assert_equal(active_edges(matrix, 2), [4])
        assert_equal(active_edges(matrix, 3), [4])
        assert_equal(active_edges(matrix, 4), [])

    def test_with_array(self):
        """Test active_edges() with dense array input."""
        array = GRAPH

        assert_equal(active_edges(array, 0), [1, 2, 3])
        assert_equal(active_edges(array, 1), [4])
        assert_equal(active_edges(array, 2), [4])
        assert_equal(active_edges(array, 3), [4])
        assert_equal(active_edges(array, 4), [])


class TestGetSources(unittest.TestCase):
    def test_with_source_dag(self):
        sources = get_sources(SOURCE_DAG)

        assert_equal(sources, [0])

    def test_with_sink_dag(self):
        sources = get_sources(SINK_DAG)

        assert_equal(sources, [0, 1, 2])

    def test_with_source_sink_dag(self):
        sources = get_sources(SOURCE_SINK_DAG)

        assert_equal(sources, [0])

    def test_with_sink_source_dag(self):
        sources = get_sources(SINK_SOURE_DAG)

        assert_equal(sources, [0, 1, 2])


class TopologicalSorting(unittest.TestCase):
    def test_sequence_of_three(self):
        edges = [(0, 1), (1, 2)]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [0, 1, 2])

    def test_simple_back_edge(self):
        edges = [(0, 1), (1, 2), (1, 3), (3, 1)]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [0, 1, 3, 2])

    def test_two_branches(self):
        edges = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 3)]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [0, 4, 1, 2, 3])

    def test_two_branches_with_bridge(self):
        edges = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 3), (2, 4)]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [0, 1, 2, 4, 3])

    def test_two_branches_with_bridge_reverse(self):
        edges = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 3), (4, 2)]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [0, 4, 1, 2, 3])

    def test_duo_circle(self):
        edges = [(0, 1), (1, 0)]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [0, 1])

    def test_double_duo_circle(self):
        edges = [(0, 1), (1, 0), (2, 3), (3, 2)]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [0, 1, 2, 3])

    def test_circle_of_three(self):
        edges = [(0, 1), (1, 2), (2, 0)]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [0, 1, 2])

    def test_raute_with_circle(self):
        edges = [(0, 1), (0, 2), (1, 2), (1, 3), (2, 1), (2, 3)]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [0, 1, 2, 3])

    def test_merge_with_back_bridges(self):
        edges = [
            (0, 1), (1, 2), (2, 6),
            (3, 4), (4, 5), (5, 6),
            (2, 4), (5, 1),
        ]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [0, 1, 2, 3, 4, 5, 6])

    def test_sequence_of_four_with_skip(self):
        edges = [
            (0, 1), (1, 2), (2, 3),
            (1, 2)
        ]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [0, 1, 2, 3])

    def test_reverse_sequence_of_five_with_circle_at_the_beginning(self):
        edges = [(1, 0), (2, 1), (3, 2), (4, 3), (5, 4), (4, 5)]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [4, 5, 3, 2, 1, 0])

    def test_other_graph_from_youtube_video(self):
        edges = [
            (0, 1), (0, 2), (0, 3),
            (1, 2),
            (3, 4),
            (4, 5),
            (5, 3),
        ]
        graph = graph_matrix(edges)
        order = topological_sorting(graph)

        self.assertEqual(order, [0, 3, 4, 5, 1, 2])


if __name__ == '__main__':
    unittest.main()
