import pydot

SINGLE = 'non-conformance' # text for single non-conformance
MULTIPLE = SINGLE + 's' # text for multiple non-conformances

def clean_dynamic_model(dynamic_model):
	'''
	Clean up a dynamic model that has been loaded via the pydot library. We first remove nodes that are 
	created due to the new lines in the DOT file. This part is a hacky as we do not know the cause for 
	the new lines. Maybe this is a bug in the pydot library?

	Then we the remove unnecessary information and coloring from the nodes (added by FlexFringe by default) 
	to reduce clutter and confusion when visualizing the dynamic model.

	:param dynamic_model: The dynamic model loaded via the pydot library.
	'''
	nodes = dynamic_model.get_nodes()
	for n in nodes:
		if n.get_name() == '\"\\n\"':
			dynamic_model.del_node(n)

	for n in nodes:
		# clear label text
		n.set_label('State ' + n.get_name().split('_')[-1] + '\n')
		# remove color
		n.set_fillcolor('white')
	    
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

def compute_num_detected_ncf_text(num_static_ncfs: int, num_dynamic_ncfs: int) -> str:
	'''
	Compute the text that is printed to the console after the non-conformances are detected. 
	The text is based on the number of detected non-conformances.

	:param num_static_ncfs: The number of static non-conformances.
	:param num_dynamic_ncfs: The number of dynamic non-conformances.
	'''

	if num_static_ncfs + num_dynamic_ncfs == 0:
		return ''

	text = 'Detected '
	if num_static_ncfs > 0:
		text += str(num_static_ncfs) + ' static '
		text += SINGLE if num_static_ncfs == 1 else MULTIPLE
	if num_dynamic_ncfs !=0:
		text += ' and ' if num_static_ncfs != 0 else ''
		text += str(num_dynamic_ncfs) + ' dynamic '
		text += SINGLE if num_dynamic_ncfs == 1 else MULTIPLE

	text += ' between implementation and deployment of the system!'
	return text
	
# Testing purposes
# if __name__ == '__main__':
# 	main()