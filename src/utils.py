import pydot

def clean_dynamic_model(dynamic_model):
	'''
	Hacky code for removing extra new lines added to the DOT file?
	We basically remove nodes that are created due to the new lines in the DOT file.
	Maybe this is a bug in the pydot library?

	:param dynamic_model: The dynamic model loaded via the pydot library.
	'''
	nodes = dynamic_model.get_nodes()
	for n in nodes:
		if n.get_name() == '\"\\n\"':
			dynamic_model.del_node(n)
	    
	return dynamic_model

def collect_dynamic_model(model_path: str):
    '''
    Load the dynamic model based on the given path. We use the pydot library to load the model as
    the models are stored in the dot format.

    :param model_path: The path to the dynamic model.
    '''
    return pydot.graph_from_dot_file(model_path)[0]

def extract_state_to_edges_mapping_from_dynamic_model(dynamic_model):
	'''
	Extract the mapping between the states to their corresponding outgoing edges from the dynamic model.

	:param dynamic_model: The dynamic model.
	'''
	state_to_edges_mapping = {}
	edges = dynamic_model.get_edges()
	for edge in edges:
		src = edge.get_source()
		if src not in state_to_edges_mapping:
			state_to_edges_mapping[src] = []
		state_to_edges_mapping[src].append(edge)
	
	return state_to_edges_mapping


def extract_link_from_transition_label(transition_label: str) -> str:
	'''
	Extract the communication linke between two microservice from a transition label. 
	The transition label is the text that is extracted from the correspnding transition 
	in the dynamic model.
	
	:param transition_label: The label(text) extracted from a transition in the dynamic model.
	'''
	splitted = transition_label.split('__')
	return splitted[-2].replace('-', '_') + '-' + splitted[-1].split('\n')[0].replace('-', '_')
	
# Testing purposes
# if __name__ == '__main__':
# 	main()