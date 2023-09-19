
import pandas as pd
import json
import pydot

def read_json_file(path_to_json_file):
	"""
	Read a JSON object given the path. This function is used for reading configuration files or
	texts that are should be used in the interpretation.
 	:param path_to_config_file: Path to the configuration file.
	"""
	return json.load(open(path_to_json_file))

def clean_url_path_data_for_flexfringe(url_data):
    """
    Clean the URL path data for FlexFringe.
    :param url_data: List containing the URL path data
	"""
    cleaned_data = []
    for row in url_data:
        cleaned_data.append(row.replace('/', '>').replace(':', '-'))

    return cleaned_data

def get_path_to_folder(file_path):
	"""
	Get the path to the folder containing the file.
	:param file_path: Path to the file
	"""
	return '/'.join(file_path.split('/')[0:-1]) + '/'

def clean_dynamic_model(dynamic_model):
	'''
	Hacky code for removing extra new lines added to the DOT file?
	We basically remove nodes that are created due to the new lines in the DOT file.
	'''
	nodes = dynamic_model.get_nodes()
	for n in nodes:
		if n.get_name() == '\"\\n\"':
			dynamic_model.del_node(n)
	    
	return dynamic_model

def collect_dynamic_model(model_path):
    '''
    Load the dynamic model based on the given path. We use the pydot library to load the model as
    the models are stored in the dot format.

    :param model_path: path to the dynamic model
    '''
    return pydot.graph_from_dot_file(model_path)[0]

def extract_state_to_edges_mapping_from_dynamic_model(dynamic_model):
	'''
	Extract the mapping between the states to their corresponding outgoing edges from the dynamic model.
	:param dynamic_model: dynamic model
	'''
	state_to_edges_mapping = {}
	edges = dynamic_model.get_edges()
	for edge in edges:
		src = edge.get_source()
		if src not in state_to_edges_mapping:
			state_to_edges_mapping[src] = []
		state_to_edges_mapping[src].append(edge)
	
	return state_to_edges_mapping


def extract_link_from_transtion_label(transition_label):
	'''
	Extract the communication linke between two microservice from a transition label. 
	The transition label is the text that is extracted from the correspnding transition 
	in the dynamic model.
	
	:param transition_label: label(text) extracted from a transition in the dynamic model
	'''
	splitted = transition_label.split('__')
	return splitted[-2] + '-' + splitted[-1].split('\n')[0]
	
# Testing purposes
# if __name__ == '__main__':
# 	main()