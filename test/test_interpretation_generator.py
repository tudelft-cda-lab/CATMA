import socket
from src.interpretation_generator import *
from src.model_processor import *
import unittest
import os

TEST_STATIC_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'test_data/test_static_model.json')
TEST_DYNAMIC_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'test_data/test_dynamic_model_with_call_details.dot')
TEST_OUTPUT_FOLDER_PATH = os.path.join(os.path.dirname(__file__), 'test_data/output/')

class TestInterpretationGenerator(unittest.TestCase):
    def setUp(self):
        self.test_static_model_path = TEST_STATIC_MODEL_PATH
        self.test_dynamic_model_path = TEST_DYNAMIC_MODEL_PATH
        self.test_output_folder_path = TEST_OUTPUT_FOLDER_PATH
        
        if not os.path.exists(self.test_output_folder_path):
            os.makedirs(self.test_output_folder_path)
            os.makedirs(os.path.join(self.test_output_folder_path, 'code_linked_models'))

        self.static_model = read_static_model(self.test_static_model_path)
        self.dynamic_model = read_dynamic_model(self.test_dynamic_model_path)

    def tearDown(self):
        if os.path.exists(os.path.join(self.test_output_folder_path, 'code_linked_models', 'test.svg')):
            os.remove(os.path.join(self.test_output_folder_path, 'code_linked_models', 'test.svg'))

        if os.path.exists(os.path.join(self.test_output_folder_path, 'test.svg')):
            os.remove(os.path.join(self.test_output_folder_path, 'test.svg'))
    
    def test_collect_link_code(self):
        link = 'order-catalog'
        evidences = collect_link_code(link, self.static_model['links'])
        evidence = evidences[0]
        expected = "https://github.com/ewolff/microservice/blob/master/microservice-demo/microservice-demo-order/src/main/java/com/ewolff/microservice/order/clients/CatalogClient.java#L86"
        self.assertEqual(evidence[1], expected)

    def test_compute_top_n_transition_from_dynamic_model(self):
        top_n_transitions = compute_top_n_transitions_from_dynamic_model(self.dynamic_model, 10)
        expected = [
            ("8080.0__>__200.0__get__user__admin-server", 12),
            ("8080.0__>applications__200.0__get__user__admin-server", 9),
            ("8080.0__>assets>js>chunk-common.530a46a5.js__304.0__get__user__admin-server", 8)
        ]
        self.assertEqual(top_n_transitions, expected)

    def test_collect_code_call_sequences_from_sequences(self):
        sequences = [['order-catalog']]
        code_call_sequences = collect_code_call_sequences_from_sequences(sequences, self.static_model['links'])
        expected_num_sequences = 1
        expected_sequence_length = 1
        num_sequences_match = len(code_call_sequences.keys()) == expected_num_sequences
        sequence_length_match = len(code_call_sequences[sequences[0][0]]) == expected_sequence_length
        self.assertTrue(num_sequences_match and sequence_length_match)

    
    def test_find_starting_point_for_sequence(self):
        start_call = 'user__admin-server'
        starting_points = find_starting_points_for_sequence(start_call, self.dynamic_model)
        num_expected_starting_points = 3
        self.assertEqual(len(starting_points), num_expected_starting_points)

    
    def test_add_links_to_code(self):
        add_links_to_code(self.test_output_folder_path, 'test', self.dynamic_model, self.static_model)
        self.assertTrue(os.path.exists(os.path.join(self.test_output_folder_path, 'test.svg')))

    def test_find_occurred_sequences_in_paths(self):
        potential_paths = ['[user, admin-server, order, catalog]', '[user, admin-server, order, order, catalog]']
        paths_from_dynamic_model = ['[user, admin-server, order, catalog]', '[user, catalog, catalog]']
        occurred_sequences = find_occurred_sequences_in_paths(potential_paths, paths_from_dynamic_model)
        length_match = len(occurred_sequences) == 1
        sequence_match = occurred_sequences[0] == paths_from_dynamic_model[0]
        self.assertTrue(length_match and sequence_match)

    def test_do_random_walk_dynamic_model(self):
        num_walks = 1
        walk_length = 4
        random_walks = do_random_walk_dynamic_model(self.dynamic_model, 'user', 'test', num_walks, walk_length)
        num_walk_match = len(random_walks) == num_walks
        walk_length_match = len(random_walks[0]) == walk_length
        walk_path_match = random_walks[0] == ['user', 'admin-server', 'user', 'admin-server']
        self.assertTrue(num_walk_match and walk_length_match, walk_path_match)
    

    def test_find_sequence_of_call_details(self):
        sequence = ['user__admin-server', 'user__admin-server', 'user__test']
        sequence_call_details = find_sequence_of_call_details(sequence, self.dynamic_model)
        sorted_sequence_call_details = sorted([str(x) for x in sequence_call_details])
        expected = [['8080.0__/', ' 8080.0__/applications'], ['8080.0__/applications', ' 8080.0__/assets/js/chunk-common.530a46a5.js']]
        sorted_expected = sorted([str(x) for x in expected])
        self.assertEqual(sorted_sequence_call_details, sorted_expected)
        
    def test_find_previous_sequences_for_link_static_model(self):
        previous_sequences = find_previous_sequences_for_link_static_model(self.static_model['links'], 'catalog', 'order', 2)
        expected = ['order__catalog']
        self.assertEqual(previous_sequences[0], expected)

    def test_transform_static_model_links(self):
        links = self.static_model['links']
        transformed_links = transform_static_model_links(links)
        expected_num_parents = 0
        expected_children = 'catalog'
        num_parents_match = len(transformed_links['order']['parents']) == expected_num_parents
        children_match = list(transformed_links['order']['children'])[0] == expected_children
        expected_parent = 'order'
        children_parent_match = list(transformed_links['catalog']['parents'])[0] == expected_parent
        children_no_children_match = len(transformed_links['catalog']['children']) == 0
        self.assertTrue(num_parents_match and children_match and children_parent_match, children_no_children_match)

    def test_collect_and_process_model_for_dynamic_non_conformance(self):
        serv_dyn_model_path = self.test_dynamic_model_path
        interpretation_data = dict()
        output_folder = self.test_output_folder_path
        output_name = 'test'
        serv_dyn_model = collect_and_process_model_for_dynamic_non_conformance(serv_dyn_model_path, interpretation_data, output_folder, output_name, self.static_model, 'src')
        expect_dict_field = 'src_dyn_model' in interpretation_data
        serv_dyn_model_not_none = serv_dyn_model is not None
        self.assertTrue(expect_dict_field and serv_dyn_model_not_none)

    def test_collect_and_process_model_for_static_non_conformance(self):
        link_dyn_model = self.test_dynamic_model_path
        interpretation_data = dict()
        output_folder = self.test_output_folder_path
        output_name = 'test'
        link_dyn_model = collect_and_process_model_for_static_non_conformance(link_dyn_model, interpretation_data, output_folder, output_name, self.static_model)
        expect_dict_field = 'link_dyn_model' in interpretation_data
        self.assertTrue(expect_dict_field)

        

if __name__ == '__main__':
    unittest.main()