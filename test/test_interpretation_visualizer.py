from src.interpretation_visualizer import *
import unittest
import os

class TestInterpretationVisualizer(unittest.TestCase):
        
    def test_convert_flexfringe_transition_to_call(self):
        transition = ("in__8080.0__>__200.0__get__user__admin-server", 12)
        call = convert_flexfringe_transition_to_call(transition)
        match_port = call['port'] == '8080.0'
        match_status = call['call_status_code'] == '200.0'
        match_url = call['call_url'] == '/'
        match_direction = call['call_direction'] == 'from user to admin-server'
        match_call_frequency = call['call_frequency'] == 12
        self.assertTrue(match_port and match_status and match_url and match_direction and match_call_frequency)

    def test_transform_extracted_call_sequence_to_readable_format(self):
        extracted_call_sequence = ['user__admin-server', 'admin-server__catalog', 'catalog__order', 'order__admin-server']
        readable_call_sequence = transform_extracted_call_sequence_to_readable_format(extracted_call_sequence)
        expected = ['user', 'admin-server', 'catalog', 'order', 'admin-server']
        self.assertEqual(readable_call_sequence, expected)


if __name__ == '__main__':
    unittest.main()

