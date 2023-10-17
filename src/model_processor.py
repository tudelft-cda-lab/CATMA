import random
from src.utils import extract_state_to_edges_mapping_from_dynamic_model
import json
# import argparse

def transform_static_model_links(static_model_links):
    '''
    Tranform the links from the static model into a dictionary that stores information on the parents and children
    of each component. This is used to find the previous sequences of links that could occur in the static model.

    :param static_model_links: A list of links between the components
    '''
    component_parent_children_mapping = {}
    for link in static_model_links:
        splitted = link.split('-')
        if len(splitted) == 2:
            source = splitted[0]
            target = splitted[1]
        elif len(splitted) == 3:
            source = splitted[0]
            target = splitted[1] + '-' + splitted[2]
        elif len(splitted) == 4:
            source = splitted[0] + '-' + splitted[1]
            target = splitted[2] + '-' + splitted[3]
        
        if source not in component_parent_children_mapping:
            component_parent_children_mapping[source] = {'parents': set(), 'children': set()}
        
        if target not in component_parent_children_mapping:
            component_parent_children_mapping[target] = {'parents': set(), 'children': set()}
        
        component_parent_children_mapping[source]['children'].add(target)
        component_parent_children_mapping[target]['parents'].add(source)
    
    return component_parent_children_mapping

def find_previous_sequences_for_link_static_model(static_model_links, starting_point, required_component, number_of_walks):
    '''
    For a given link that is part of a non-conformance of type static, find the previous sequences of links
    that could occur in the static model. To do so, we start from the destination component of the link and we
    go backwards in the static model to find previous sequences. Currently, we only consider sequences that have 
    a length between 1 and 5.

    :param static_model_links: A dictionary that contains the links between the components
    :param starting_point: The componenent from which we start to walk backwards in the static model
    :param required_components: The component that must be in the path, this would be the source component of the link
    :param number_of_walks: The number of random walks to do
    '''
    component_parent_children_info = transform_static_model_links(static_model_links)
    potential_previous_sequences = []
    potential_previous_sequences_set = set()
    # Do the random backwards walks
    for i in range(number_of_walks):
        current_node = starting_point
        path = []
        walk_length = random.randint(2, 5)
        for j in range(walk_length):
            target_nodes = component_parent_children_info[current_node]['parents']
            if len(target_nodes) == 0:
                break
            next_target_node = random.choice(list(target_nodes))
            path.insert(0, next_target_node)
            current_node = next_target_node

        if str(path) in potential_previous_sequences_set:
            continue
        
        if required_component in path:
            potential_previous_sequences.append(path)
            potential_previous_sequences_set.add(str(path))
        else:
            continue
    
    # Transform the paths into sequences of links
    potential_previous_link_sequences = []
    for path in potential_previous_sequences:
        path.append(starting_point) # include the starting point to show this in the interpretation
        sequence = []
        for i in range(len(path)):
            if i+1 >= len(path):
                break
            sequence.append(path[i] + '__' + path[i+1])
        potential_previous_link_sequences.append(sequence)

    return potential_previous_link_sequences


def do_random_walk_dynamic_model(dynamic_model, required_component, missing_component, number_of_walks, walk_length):
    '''
    Do random walks over the dynamic model to sample paths that were used to learn the dynamic
    model. The paths that are traversed through this model must contain the component that is
    given as the parameter. For each unique path, we also store their corresponding state sequences.

    :param dynamic_model: The dynamic model that is loaded using the pydot library
    :param number_of_walks: The number of random walks to do
    :param required_component: The component that must be in the path
    :param walk_length: The length of each random walk
    '''
    states_to_edges_mapping = extract_state_to_edges_mapping_from_dynamic_model(dynamic_model)

    random_walk_paths = []
    random_walk_paths_set = set()
    for i in range(number_of_walks):
        current_node = '0'
        path = []
        for j in range(walk_length):
            if current_node not in states_to_edges_mapping:
                break
            out_edges = states_to_edges_mapping[current_node]
            selected_edge = random.choice(out_edges)
            next_target_node = selected_edge.get_destination()
            splitted = selected_edge.get_label().split('\n')[0].split('__')
            path.append(splitted[-2] + '__' + splitted[-1])
            current_node = next_target_node

        path.append(required_component + '__' + missing_component) # include the missing link in the path (will be shown in the interpretation).
        if required_component in str(path):
            random_walk_paths.append(path)
            random_walk_paths_set.add(str(path))
        
    
    return random_walk_paths
            
def find_occurred_sequences_in_paths(potential_previous_sequences, dynamic_model_walk_paths):
    '''
    Find sequences, generated from backward walks on the static model, that really occurred in the run-time model.
    We also count how often it has occurred in the run-time model.

    :param potential_previous_sequences: The previous sequences of links that could have occurred for a given link in the static model
    :param dynamic_model_walk_paths: The random paths that were traversed in the run-time model
    '''
    occurred_sequences = []
    occurred_sequence_set = set()
    for seq in potential_previous_sequences:
        processed_seq = str(seq).replace(']', '').replace('[', '')
        for path in dynamic_model_walk_paths:
            if processed_seq in occurred_sequence_set:
                continue
            if processed_seq in str(path):
                occurred_sequences.append(seq)
                occurred_sequence_set.add(processed_seq)

    return occurred_sequences


def find_starting_points_for_sequence(start_call, dynamic_model):
    '''
    Find the possible starting points in the run-time model given a starting call for a call 
    sequence. We basically traverse the run-time model and find transitions that matches 
    the start of the call sequence.

    :param call_sequence: The starting call of the call sequence
    :param dynamic_model: The dynamic model that is loaded using the pydot library
    '''
    starting_points = set()
    for edge in dynamic_model.get_edges():
         # starting transition of state machine
        if edge.get_label() is None:
            continue
        splitted = edge.get_label().split('\n')[0].split('__')
        link = splitted[-2] + '__' + splitted[-1]
        if link == start_call:
            starting_points.add(edge.get_source())

    return list(starting_points)

def find_sequence_of_call_details(call_sequence, dynamic_model):
    '''
    Find the call details from a given call sequence. We basically traverse the run-time model
    and find sequences of transitions that matches the call sequence and then extract the details
    of the call from these sequences of transitions.

    :param call_sequence: The sequence of calls for which we want to find the details
    :param dynamic_model: The dynamic model that is loaded using the pydot library
    '''
    unique_call_details_sequences = set()
    state_to_edges_mapping = extract_state_to_edges_mapping_from_dynamic_model(dynamic_model)
    start_call = call_sequence[0]
    starting_points = find_starting_points_for_sequence(start_call, dynamic_model)
    # We redefine the length of the sequence as the last item in the sequence is the missing link
    # and we do not have any call details for this link, hence we have len(call_sequence) - 1. It
    # could be the case that the call sequence only contains one call, in this case we set the length to 1.
    len_call_sequence = len(call_sequence) - 1 if len(call_sequence) > 1 else 1
    
    # now we traverse the model using the found starting points and we try to find the
    # sequence of call details for the given sequence.
    for p in starting_points:
        sequence_of_details = []
        matching_path = True
        current_node = p
        for i in range(len_call_sequence):
            if current_node not in state_to_edges_mapping:
                matching_path = False
                break
            
            out_edges = state_to_edges_mapping[current_node]
            non_matching_out_edges = False
            for edge in out_edges:
                splitted = edge.get_label().split('\n')[0].split('__')
                link = splitted[-2] + '__' + splitted[-1]
                if link == call_sequence[i]:
                    sequence_of_details.append(splitted[0] + '__' + splitted[1])
                    current_node = edge.get_destination()
                    break
                else:
                    non_matching_out_edges = True
            
            if non_matching_out_edges:
                matching_path = False
                break
            
        if matching_path:
            unique_call_details_sequences.add(str(sequence_of_details))

    # Clean the call details sequences before returning them
    processed_call_details = []
    for call_detail_sequence in unique_call_details_sequences:
        sequence = call_detail_sequence.replace('[', '').replace(']', '').replace('\"', '').replace('\'', '').replace('>', '/').split(',')
        processed_call_details.append(sequence)
    
    return processed_call_details

            

# Old static_model_parser.py from here on

def read_static_model(evidence_file_path):
    """
    This function is used to read evidences that are collected by the static model.
    It first loads the JSON file. Then, it processes the evidences extraced by the static model (DFD model from TUHH).
    Evidences are parsed and stored in the corresponding dictionary; evidences collected from services
    are store in the service_evidence dictionary and evidences collected from links are stored in the
    link_evidences dictionary.

    :param evidence_file: The path to the JSON file containing the evidences.
    
    """

    with open(evidence_file_path, 'r') as f:
        evidences = json.load(f)
    
    link_evidences = process_link_evidences(evidences['edges'])
    return {'links' : link_evidences}


# def extract_code_line(file, line):
#     """
#     This function is used to extract a specific (source code) line from a file.
#     :param file: The file from which the line will be extracted.
#     :param line: The line number that will be extracted.
#     """
#     with open(file, 'r') as f:
#         lines = f.readlines()
#         if isinstance(line, str):
#             return lines[int(line) - 1].strip()
#         elif isinstance(line, int):
#             return lines[line - 1].strip()
#         else:
#             raise Exception('Invalid line number')
    

# def process_line_evidence(file_path, src_code_folder):
#     """
#     This function is used to parse and transform the URL into a file path, which will be used
#     to parse the specific line from the file. Currently, this is not used.

#     :param file_path: The URL of the file.
#     :param src_code_folder: The path to the folder containing the source code.

#     """
#     if 'heuristic' in file_path or 'implicit' in file_path:
#         return file_path
    
#     splitting_point = src_code_folder.split('/')[-1] + '/'
#     processed_file_path = file_path.split(splitting_point)[1].split('#')[0]
#     return src_code_folder + '/' + processed_file_path

def process_link_evidences(links):
    """
    This function is used to process the evidences collected for the links in the DFD model.
    The structure of this dictionary is the similar as the one used for the services, except 
    for this one we use the link as the key.

    :param links: Dictionary containing the evidences collected for the links
    """
    link_evidences = {}
    for l in links:
        services = [x.replace('-','_') for x in l.split(' -> ')]
        link_name = '-'.join(services).lower()
        link_evidences[link_name] = []
        file = links[l]['file'].replace('blob/master/master', 'blob/master')
        line = links[l]['line']
        link_evidences[link_name].append(('Link', file, line))

    return link_evidences


# Testing purposes
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--evidence_file', type=str, help='File containing the evidences extracted by the static model (DFD)')
#     parser.add_argument('--src_folder', type=str, help='Folder containing the source code of the application')
#     args = parser.parse_args()

#     evidence_data = read_static_model_evidence(args.evidence_file)
#     evidences = process_static_model_evidence(evidence_data, args.src_folder)
#     # print(evidences['services'])
#     print(evidences['services']['order'])
#     print(evidences['links'].keys())



