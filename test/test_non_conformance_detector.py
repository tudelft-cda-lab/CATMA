from src.non_conformance_detector import *
from src.model_processor import *
import unittest
import os

TEST_STATIC_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'test_data/test_static_model.json')
TEST_DYNAMIC_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'test_data/test_dynamic_model_normal.dot')

class TestNonConformanceDetector(unittest.TestCase):
    def setUp(self):
        self.static_model_path = TEST_STATIC_MODEL_PATH
        self.test_dynamic_model_path = TEST_DYNAMIC_MODEL_PATH
    
    def test_extract_occurred_links_from_dynamic_model(self):
        dynamic_model = read_dynamic_model(self.test_dynamic_model_path)
        services = ['admin_server', 'user']
        occurred_links = extract_occurred_links_from_dynamic_model(dynamic_model, services)
        num_occurred_links_match = 1 == len(occurred_links)
        link_match = 'user-admin_server' in occurred_links
        self.assertTrue(num_occurred_links_match and link_match)
    
    def test_find_non_conformance_in_linkset(self):
        this_linkset = {'user-admin_server', 'user-catalog', 'catalog-admin_server'}
        that_linkset = {'user-admin_server', 'user-catalog'}
        non_conformances = find_non_conformance_in_linkset(this_linkset, that_linkset)
        num_non_conformances_match = 1 == len(non_conformances)
        link_match = 'catalog-admin_server' in non_conformances
        self.assertTrue(num_non_conformances_match and link_match)

    def test_detect_non_conformances(self):
        static_model = read_static_model(self.static_model_path)
        dynamic_model = read_dynamic_model(self.test_dynamic_model_path)
        services = ['admin-server', 'user']
        static_ncf, dynamic_ncf = detect_non_conformances(static_model, dynamic_model, services)
        num_static_ncf_match = 1 == len(static_ncf)
        num_dynamic_ncf_match = 1 == len(dynamic_ncf)
        static_ncf_match = 'user-admin_server' in static_ncf
        dynamic_ncf_match = 'order-catalog' in dynamic_ncf
        self.assertTrue(num_static_ncf_match and num_dynamic_ncf_match and static_ncf_match and dynamic_ncf_match)

if __name__ == '__main__':
    unittest.main()