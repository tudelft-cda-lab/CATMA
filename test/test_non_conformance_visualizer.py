from src.model_processor import read_static_model
from src.non_conformance_visualizer import *
import unittest
import os

OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'test_data/output/')
TEST_STATIC_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'test_data/test_static_model.json')

class TestNonConformanceVisualizer(unittest.TestCase):
    def setUp(self):
        self.output_folder = OUTPUT_FOLDER
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.test_static_model_path = TEST_STATIC_MODEL_PATH

    def tearDown(self):
        if os.path.exists(os.path.join(self.output_folder, 'visualization')):
            os.remove(os.path.join(self.output_folder, 'visualization', 'plantuml.png'))
            os.remove(os.path.join(self.output_folder, 'visualization', 'plantuml.txt'))

            
    
    def test_generation_of_visualization_of_empty_conformances(self):
        static_non_conformances = set()
        dynamic_non_conformances = set()
        static_model = read_static_model(self.test_static_model_path)
        visualize_non_conformances(static_non_conformances, dynamic_non_conformances, self.output_folder, static_model)
        self.assertTrue(len(os.listdir(self.output_folder + '/visualization')) == 2)

    def test_generation_of_visualization_of_non_empty_non_conformances(self):
        static_non_conformances = set()
        static_non_conformances.add('order-order')
        dynamic_non_conformances = set()
        dynamic_non_conformances.add('order-catalog')
        static_model = read_static_model(self.test_static_model_path)
        visualize_non_conformances(static_non_conformances, dynamic_non_conformances, self.output_folder, static_model)
        self.assertTrue(len(os.listdir(self.output_folder + '/visualization')) == 2)

    def test_generation_of_visualization_of_overlapping_non_conforances(self):
        static_non_conformances = set()
        static_non_conformances.add('order-catalog')
        dynamic_non_conformances = set()
        dynamic_non_conformances.add('order-catalog')
        static_model = read_static_model(self.test_static_model_path)
        visualize_non_conformances(static_non_conformances, dynamic_non_conformances, self.output_folder, static_model)
        self.assertTrue(len(os.listdir(self.output_folder + '/visualization')) == 2)

if __name__ == '__main__':
    unittest.main()