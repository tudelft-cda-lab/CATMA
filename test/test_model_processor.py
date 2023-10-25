from src.model_processor import *
import unittest
import os

TEST_STATIC_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'test_data/test_static_model.json')
TEST_DYNAMIC_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'test_data/test_dynamic_model_normal.dot')

class TestModelProcessor(unittest.TestCase):
    def setUp(self):
        self.static_model_path = TEST_STATIC_MODEL_PATH
        self.test_dynamic_model_path = TEST_DYNAMIC_MODEL_PATH

    def test_read_static_model(self):
        static_model = read_static_model(self.static_model_path)
        num_keys = 1 == len(static_model.keys())
        link_match = 'order-catalog' in static_model['links']
        evidences = static_model['links']['order-catalog']
        num_evidences_match = 1 == len(evidences)
        line_match = "86" == evidences[0][2]
        file_match = "https://github.com/ewolff/microservice/blob/master/microservice-demo/microservice-demo-order/src/main/java/com/ewolff/microservice/order/clients/CatalogClient.java#L86" == evidences[0][1]
        self.assertTrue(num_keys and link_match and num_evidences_match and line_match and file_match)
    
    def test_read_dynamic_model(self):
        dynamic_model = read_dynamic_model(self.test_dynamic_model_path)
        num_nodes = 5 == len(dynamic_model.get_nodes())
        num_edges = 4 == len(dynamic_model.get_edges())
        self.assertTrue(num_nodes and num_edges)



if __name__ == '__main__':
    unittest.main()