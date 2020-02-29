import collections

import matplotlib.pyplot as plt

from klang.graph import graph_matrix, plot_graph, find_back_edges, topological_sorting

Scenario = collections.namedtuple('Scenario', 'edges positions')


SCENARIOS = {
    # First scenario
    0: Scenario(
        edges=[(0, 1), (1, 2), (1, 3), (3, 1)],
        positions=[[0., 0.], [1., 0.], [2., 0.], [1., 1.]],
    ),

    # Simple line. 0 -> 1 ->2
    1: Scenario(
        edges=[(0, 1), (1, 2)],
        positions=[[0., 0.], [1., 0.], [2., 0.]]
    ),

    # Simple line. 0 -> 1 -> 2 -> 3 and parallel 0 -> 4 -> 3
    2: Scenario(
        edges=[(0, 1), (1, 2), (2, 3), (0, 4), (4, 3)],
        positions=[[0., 0.], [1., 0.], [2., 0.], [3., 0.], [1.5, -1.]],
    ),

    # Simple line. 0 -> 1 -> 2 -> 3 and parallel 0 -> 4 -> 3 [MOD]
    3: Scenario(
        edges=[(0, 1), (1, 2), (2, 3), (0, 4), (4, 3), (2, 4)],
        positions=[[0., 0.], [1., 0.], [2., 0.], [3., 0.], [1.5, -1.]],
    ),

    # Simple line. 0 -> 1 -> 2 -> 3 and parallel 0 -> 4 -> 3 [MOD2]
    4: Scenario(
        edges=[(0, 1), (1, 2), (2, 3), (0, 4), (4, 3), (4, 2)],
        positions=[[0., 0.], [1., 0.], [2., 0.], [3., 0.], [1.5, -1.]],
    ),

    # Loop 0 <-> 1
    5: Scenario(
        edges=[(0, 1), (1, 0)],
        positions=[[0., 0.], [1., 0.]],
    ),

    # Two loops: 0 <-> 1, 2 <-> 3
    6: Scenario(
        edges=[(0, 1), (1, 0), (2, 3), (3, 2)],
        positions=[[0., 0.], [1., 0.], [0., 1.], [1., 1.]],
    ),

    # Bigger loop
    7: Scenario(
        edges=[(0, 1), (1, 2), (2, 0)],
        positions=[[0., 0.], [1., 0.], [.5, .82]],
    ),

    # Parallel branches with loop in the middle
    8: Scenario(
        edges=[
            (0, 1), (0, 2),
            (1, 2), (2, 1),
            (1, 3), (2, 3),
        ],
        positions=[[0., 0.], [1., -1.], [1., 1.], [2., 0.]],
    ),

    # test_resolution_order_weird_cycle
    9: Scenario(
        edges=[
            (0, 1), (1, 2), (2, 6),
            (3, 4), (4, 5), (5, 6),
            (5, 1), (2, 4)
        ],
        positions=[
            [0., 0.], [1., 0.], [2., 0.],
            [0., 2.], [1., 2.], [2., 2.],
            [3., 1]
        ],
    ),

    # Jump over one in chain
    10: Scenario(
        edges=[
            (0, 1), (1, 2), (2, 3), (0, 2)
        ],
        positions=[[0., 0.], [1., 0.], [2., 0.], [3., 0.]],
    ),


    # Nico's fieser case
    11: Scenario(
        edges=[
            (1, 0), (2, 1), (3, 2), (4, 3), (5, 4), (4, 5),
        ],
        positions=[[0., 0.], [-1., 0.], [-2., 0.], [-3., 0.], [-4., 0.], [-4., -1.]],
    ),

    # From video https://www.youtube.com/watch?v=rKQaZuoUR4M
    12: Scenario(
        edges=[
            (0, 1), (1, 2), (0, 2), (0, 3), (3, 4), (4, 5), (5, 3),
        ],
        positions=[[0., 0.], [1., 0.], [1., -1.], [-1., -1.], [0., -2.], [-1., -3.]],
    ),
}


NUMBER = None



if __name__ == '__main__':
    if NUMBER is None:
        cases = SCENARIOS.items()
    else:
        cases = [
            (NUMBER, SCENARIOS[NUMBER])
        ]

    for nr, scenario in cases:
        edges, positions = scenario
        graph = graph_matrix(edges).toarray()

        backEdges = find_back_edges(graph)
        execOrder = topological_sorting(graph)

        fig, ax = plt.subplots(1)
        plot_graph(graph, positions, ax=ax)
        title = 'Scenario {},\nbackEdges: {}\nexecOrder: {}'.format(nr, backEdges, execOrder)
        fig.suptitle(title)
        plt.show()
