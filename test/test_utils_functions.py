from src.utils import *
import unittest
import os
import pydot

CORRECT_TEST_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'test_data/test_dynamic_model_normal.dot')
TEST_MODEL_NEWLINE_NODE = os.path.join(os.path.dirname(__file__), 'test_data/test_dynamic_model_with_newline_node.dot')

class TestUtilsFunctions(unittest.TestCase):

    def setUp(self):
        self.correct_test_model_path = CORRECT_TEST_MODEL_PATH
        self.test_model_path_with_newline_node = TEST_MODEL_NEWLINE_NODE

    def test_collect_dynamic_model(self):
        dynamic_model = collect_dynamic_model(self.correct_test_model_path)
        sum_edge_node = len(dynamic_model.get_nodes()) + len(dynamic_model.get_edges())
        self.assertEqual(sum_edge_node, 9)

    def test_clean_dynamic_model(self):
        dynamic_model = collect_dynamic_model(self.test_model_path_with_newline_node)
        before = len(dynamic_model.get_nodes())
        dynamic_model = clean_dynamic_model(dynamic_model)
        after = len(dynamic_model.get_nodes())
        self.assertEqual(1, before-after)

    def test_extract_state_to_edges_mapping_from_dynamic_model(self):
        dynamic_model = collect_dynamic_model(self.correct_test_model_path)
        state_to_edges_mapping = extract_state_to_edges_mapping_from_dynamic_model(dynamic_model)
        self.assertEqual(len(state_to_edges_mapping), 4)

    def test_extract_link_from_transition_label(self):
        transition_label = 'in__8080.0__>__200.0__get__user__admin-server\n12'
        link = extract_link_from_transition_label(transition_label)
        self.assertEqual(link, 'user-admin_server')

    def test_compute_num_detected_ncf_text(self):
        text = compute_num_detected_ncf_text(2, 1)
        self.assertEqual(text, 'Detected 2 static non-conformances and 1 dynamic non-conformance between implementation and deployment of the system!')
    
    def test_compute_num_detected_ncf_text_flipped_counts(self):
        text = compute_num_detected_ncf_text(1, 2)
        self.assertEqual(text, 'Detected 1 static non-conformance and 2 dynamic non-conformances between implementation and deployment of the system!')
    
    def test_compute_num_detected_ncf_text_no_static(self):
        text = compute_num_detected_ncf_text(0, 2)
        self.assertEqual(text, 'Detected 2 dynamic non-conformances between implementation and deployment of the system!')

    def test_compute_num_detected_ncf_text_no_dynamic(self):
        text = compute_num_detected_ncf_text(2, 0)
        self.assertEqual(text, 'Detected 2 static non-conformances between implementation and deployment of the system!')
    
    def test_compute_num_detected_ncf_text_no_ncf(self):
        text = compute_num_detected_ncf_text(0, 0)
        self.assertEqual(text, '')

if __name__ == '__main__':
    unittest.main()
