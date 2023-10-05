"""
Copyright 2023 Impulse Innovations Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import unittest

import networkx
import numpy

from cai_causal_graph.causal_graph import CausalGraph, Skeleton
from cai_causal_graph.exceptions import CausalGraphErrors


class TestCausalGraphSkeletonSerialization(unittest.TestCase):
    def setUp(self):
        self.empty_graph = CausalGraph()

        self.nodes = ['x', 'y', 'z1', 'z2']
        self.latent_nodes = ['x_L']

        self.fully_connected_graph = CausalGraph()
        self.fully_connected_graph.add_edge('x', 'z1')
        self.fully_connected_graph.add_edge('x', 'z2')
        self.fully_connected_graph.add_edge('y', 'z1')
        self.fully_connected_graph.add_edge('y', 'z2')

        self.fully_connected_graph_edges = [['x', 'z1'], ['x', 'z2'], ['y', 'z1'], ['y', 'z2']]

        self.fully_connected_graph_edges_sources = [('x', 2), ('y', 2)]
        self.fully_connected_graph_edges_destinations = [('z1', 2), ('z2', 2)]

        self.graph_with_latent_node = CausalGraph()
        self.graph_with_latent_node.add_nodes_from(['x', 'y', 'z1', 'z2'])
        self.graph_with_latent_node.add_edge('x', 'x_L')
        self.graph_with_latent_node.add_edge('x_L', 'y')
        self.graph_with_latent_node.add_edge('y', 'z1')
        self.graph_with_latent_node.add_edge('y', 'z2')
        self.graph_with_latent_node.add_edge('x', 'z2')

        self.graph_with_latent_nodes_edges_sources = [('x', 2), ('y', 2), ('x_L', 1)]
        self.graph_with_latent_nodes_edges_destinations = [('x_L', 1), ('y', 1), ('z1', 1), ('z2', 2)]
        self.graph_with_latent_nodes_edges = [['x', 'x_L'], ['x_L', 'y'], ['y', 'z1'], ['y', 'z2'], ['x', 'z2']]

    def assert_graph_skeleton_serialization_is_correct(self, graph: CausalGraph):
        reconstruction = Skeleton.from_dict(graph.skeleton.to_dict())

        # Check that their dict representations are the same.
        self.assertDictEqual(graph.skeleton.to_dict(), reconstruction.to_dict())

        # Also confirm that equality method works.
        self.assertEqual(graph.skeleton, reconstruction)
        self.assertTrue(graph.skeleton.__eq__(reconstruction, True))

        # No metadata
        self.assertDictEqual(graph.skeleton.to_dict(include_meta=False), reconstruction.to_dict(include_meta=False))
        self.assertEqual(graph.skeleton, reconstruction)
        self.assertTrue(graph.skeleton.__eq__(reconstruction, True))

    def assert_graph_networkx_conversion_is_correct(self, graph: CausalGraph):
        reconstruction = Skeleton.from_networkx(graph.skeleton.to_networkx())

        # Confirm we get correct type on to_networkx.
        self.assertIsInstance(graph.skeleton.to_networkx(), networkx.Graph)
        self.assertNotIsInstance(graph.skeleton.to_networkx(), networkx.DiGraph)

        # Check that their dict representations are the same.
        self.assertDictEqual(graph.skeleton.to_dict(), reconstruction.to_dict())

        # Also confirm that equality method works.
        self.assertEqual(graph.skeleton, reconstruction)
        self.assertTrue(graph.skeleton.__eq__(reconstruction, True))

    def assert_graph_gml_conversion_is_correct(self, graph: CausalGraph):
        reconstruction = Skeleton.from_gml_string(graph.skeleton.to_gml_string())

        self.assertIsInstance(graph.skeleton.to_gml_string(), str)

        # Check that their dict representations are the same.
        self.assertDictEqual(graph.skeleton.to_dict(), reconstruction.to_dict())

        # Also confirm that equality method works.
        self.assertEqual(graph.skeleton, reconstruction)
        self.assertTrue(graph.skeleton.__eq__(reconstruction, True))

    def test_fully_connected_graph(self):
        skeleton = self.fully_connected_graph.skeleton
        # Should be able to swap source and destination as edges are always undirected.
        self.assertEqual(
            skeleton.get_edge(source='x', destination='z1'), skeleton.get_edge(source='z1', destination='x')
        )
        self.assertEqual(skeleton.get_edge_by_pair(('x', 'z1')), skeleton.get_edge_by_pair(('z1', 'x')))
        self.assertTrue(skeleton.edge_exists(source='x', destination='z1'))
        self.assertTrue(skeleton.edge_exists(source='z1', destination='x'))
        self.assertTrue(skeleton.is_edge_by_pair(('x', 'z1')))
        self.assertTrue(skeleton.is_edge_by_pair(('z1', 'x')))
        self.assert_graph_skeleton_serialization_is_correct(self.fully_connected_graph)
        self.assert_graph_networkx_conversion_is_correct(self.fully_connected_graph)
        self.assert_graph_gml_conversion_is_correct(self.fully_connected_graph)

    def test_empty_graph(self):
        self.assert_graph_skeleton_serialization_is_correct(self.empty_graph)
        self.assert_graph_networkx_conversion_is_correct(self.empty_graph)
        self.assert_graph_gml_conversion_is_correct(self.empty_graph)

    def test_graph_with_latent_nodes(self):
        self.assert_graph_skeleton_serialization_is_correct(self.graph_with_latent_node)
        self.assert_graph_networkx_conversion_is_correct(self.graph_with_latent_node)
        self.assert_graph_gml_conversion_is_correct(self.graph_with_latent_node)

    def test_get_nodes_empty(self):
        self.assertEqual(len(self.empty_graph.skeleton.nodes), 0)

    def test_get_edges_empty(self):
        self.assertEqual(len(self.empty_graph.edges), 0)

    def test_add_nodes_implicit(self):
        self.fully_connected_graph.add_edge('test_1', 'test_2')
        node_identifiers = [node.identifier for node in self.fully_connected_graph.skeleton.nodes]
        self.assertIn('test_1', node_identifiers)
        self.assertIn('test_2', node_identifiers)

    def test_delete_node(self):
        # Test that deleting the node works well
        self.fully_connected_graph.delete_node('x')
        self.assertNotIn('x', {node.identifier for node in self.fully_connected_graph.skeleton.nodes})

    def test_delete_edge(self):
        # Test that deleting edges works fine
        self.fully_connected_graph.delete_edge('x', 'z1')
        self.assertEqual(3, len(self.fully_connected_graph.skeleton.edges))

    def test_adjacency(self):
        adj_1 = numpy.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]])
        names_1 = ['a', 'b', 'c']
        adj_2 = numpy.array([[0, 1, 0], [0, 0, 0], [1, 0, 0]])
        names_2 = ['b', 'c', 'a']
        graph = CausalGraph(input_list=names_1)
        graph.add_edge('a', 'b')
        graph.add_edge('b', 'c')

        numpy.testing.assert_array_equal(graph.adjacency_matrix, adj_1)

        skeleton_1 = Skeleton.from_adjacency_matrix(adj_1, names_1)

        self.assertEqual(skeleton_1, graph.skeleton)

        # testing isomorphic graphs
        skeleton_2 = Skeleton.from_adjacency_matrix(adj_2, names_2)
        self.assertEqual(skeleton_1, skeleton_2)

        # test non-equal graphs
        skeleton_3 = Skeleton.from_adjacency_matrix(adj_1, names_2)
        self.assertNotEqual(skeleton_2, skeleton_3)

    def test_adjacency_raises(self):
        adj_er_1 = numpy.array([[0, 1, 0], [1, 0, 0], [0, 0, 1], [0, 0, 0]])
        adj_er_2 = numpy.array([[1.1, 1, 0], [0, 0, 0], [1, 0, 0]])
        adj_correct = numpy.array([[0, 1, 0], [0, 0, 0], [1, 0, 0]])
        names_er = ['a', 'b']

        with self.assertRaises(CausalGraphErrors.InvalidAdjacencyMatrixError):
            Skeleton.from_adjacency_matrix(adj_er_1)

        with self.assertRaises(CausalGraphErrors.InvalidAdjacencyMatrixError):
            Skeleton.from_adjacency_matrix(adj_er_2)

        with self.assertRaises(AssertionError):
            Skeleton.from_adjacency_matrix(adj_correct, names_er)
