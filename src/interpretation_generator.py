from src.dynamic_model_code_linking import *
from src.utils import collect_dynamic_model, extract_state_to_edges_mapping_from_dynamic_model
import os
import random

FF_LINK_MODEL_SUFFIX = '_link_data.csv.ff.final.dot'
FF_SERVICE_MODEL_SUFFIX = '_service_data.csv.ff.final.dot'


def generate_interpretation(non_conformance_type, components, dynamic_models_folder, output_folder, static_model, dynamic_model):
    '''
    This function is used to generate the interpretation of the non-conformance between the static
    and dynamic models. We have two definitions for non-conformances that we detect: static and dynamic.
    for more information from the difference type, please refer to the paper or the README. Based on 
    the type of difference, we generate the corresponding interpretation for the non-conformance.

    :param diff_type: type of difference between the static and dynamic models
    :param components: list of two components that are involved in the non-conformance. Order follows the direction of the link
    :param dynamic_models_folder: path to the folder containing the dynamic models
    :param static_model: dictionary containing the evidences extracted from the static model
    :param dynamic_model: The model that is learned from all HTTP event logs.
    '''
    interpretation = {}
    interpretation['non_conformance_type'] = non_conformance_type
    processed_components = [x.replace('_', '-') for x in components] # change it back to original name
    interpretation['components'] = processed_components
    link_code_evidences = collect_link_code(components[0] + '-' + components[1], static_model['links'])
    interpretation['link_code_evidences'] = link_code_evidences

    # For if we find non-conformance in the static model; link occurring in the dynamic model
    # but not in the static model
    if non_conformance_type == 'static':
        link_dyn_model_path = dynamic_models_folder + processed_components[0] + '_' + processed_components[1] + FF_LINK_MODEL_SUFFIX
        out_file_name = components[0] + '_' + components[1] + '_link_model'
        collect_and_process_model_for_static_non_conformance(link_dyn_model_path, interpretation, output_folder, out_file_name, static_model)


    # For if we find non-conformance in the dynamic model; link occurring in the static model
    # but not in the dynamic model    
    if non_conformance_type == 'dynamic':
        # Check if there is dynamic model for component
        src_component_dynamic_model = collect_and_process_model_for_dynamic_non_conformance(
            dynamic_models_folder + processed_components[0] + FF_SERVICE_MODEL_SUFFIX, 
            interpretation, 
            output_folder, 
            processed_components[0] + '_service_model', 
            static_model,
            'src'
        )
        
        # check if dynamic model exist for destination component
        dst_component_dynamic_model = collect_and_process_model_for_dynamic_non_conformance(
            dynamic_models_folder + processed_components[1] + FF_SERVICE_MODEL_SUFFIX, 
            interpretation, 
            output_folder, 
            processed_components[1] + '_service_model', 
            static_model,
            'dst'
        )

        if src_component_dynamic_model is not None and dst_component_dynamic_model is not None:
            static_call_sequences = find_previous_sequences_for_link_static_model(static_model['links'], components[1], components[0], 1000)
            dynamic_paths = do_random_walk_dynamic_model(dynamic_model, components[0], components[1], 1000, 20)
            occurred_call_sequences = find_occurred_sequences_in_paths(static_call_sequences, dynamic_paths)
            code_call_sequences = collect_code_call_sequences_from_sequences(static_call_sequences, static_model['links'])
            interpretation['potential_call_sequences'] = static_call_sequences
            interpretation['occurred_call_sequences'] = occurred_call_sequences
            interpretation['code_call_sequences'] = code_call_sequences
            sequences_call_details = dict()
            for call_sequence in occurred_call_sequences:
                sequences_call_details[str(call_sequence)] = find_sequence_of_call_details(call_sequence, dynamic_model)
            
            interpretation['call_details_sequences'] = sequences_call_details
        elif src_component_dynamic_model is None and dst_component_dynamic_model is not None:
            interpretation['missing_dynamic_model'] = [components[0]]
        elif src_component_dynamic_model is not None and dst_component_dynamic_model is None:
            interpretation['missing_dynamic_model'] = [components[1]]
        else:
            interpretation['missing_dynamic_model'] = [components[0], components[1]]

    return interpretation


def compute_top_n_transitions_from_model(model, n):
    '''
    Find the top N tranitions that occur within the dynamic model. The dynamic model stores the 
    frequency of each transition within the model and we use this information to filter out the 
    top N transitions.

    :param model: dynamic model that is loaded using the pydot library
    :param n: number of top transitions to be returned
    '''

    edges = model.get_edges()
    call_frequencies = {}
    # Go through all edges to collect the call information and its corresponding frequency
    for e in edges:
        # get the edge label
        label = e.get_label()
        if label is None:
            continue
        
        label = label.replace('"', '')
        splitted = label.split('\n')
        call_information = splitted[0]
        frequency = int(splitted[1].strip())
        if call_information in call_frequencies:
            call_frequencies[call_information] += frequency
        else:
            call_frequencies[call_information] = frequency
    
    # Sort the call information based on the frequency and return the top N calls
    top_n_calls = []
    sorted_calls = sorted(call_frequencies.items(), key=lambda x: x[1], reverse=True)
    for i in range(n):
        if i >= len(sorted_calls):
            break
        top_n_calls.append((sorted_calls[i][0], sorted_calls[i][1]))

    return top_n_calls


def collect_link_code(link, link_evidences):
    '''
    Collect the code evidences for the given link. The evidences are collected from the static model.

    :param link: link for which the code evidences are collected
    :param link_evidences: dictionary containing the evidences extracted from the static model
    '''
    code_for_link = []
    for evidence in link_evidences:
        if evidence == link:
            code_for_link += link_evidences[evidence]
    
    return code_for_link


def collect_code_call_sequences_from_sequences(sequences, link_evidences):
    '''
    Collect the code call sequences for the given sequences of links. We basically tranform a sequence of links
    to their corresponding sequence of code calls.

    :param occurred_sequences: list of sequences of links that occurred in the dynamic model.
    :param link_evidences: dictionary containing the link evidences extracted from the static model
    '''
    code_call_sequences = dict()
    for sequence in sequences:
        code_call_sequence = []
        for link in sequence:
            processed_link = link.replace('__', '-')
            code_call_sequence += collect_link_code(processed_link, link_evidences)
        code_call_sequences['-'.join(sequence)] = code_call_sequence
    
    return code_call_sequences


def collect_and_process_model_for_static_non_conformance(link_dyn_model_path, interpretation, output_folder, output_file_name, static_model):
        link_dynamic_model = collect_dynamic_model(link_dyn_model_path)
        top_transitions_from_link_dyn_model = compute_top_n_transitions_from_model(link_dynamic_model, 10)
        interpretation['top_transitions_from_link_dyn_model'] = top_transitions_from_link_dyn_model
        add_links_to_code(output_folder + 'code_linked_models/', output_file_name, link_dynamic_model, static_model)
        interpretation['link_dyn_model'] = output_folder + 'code_linked_models/' + output_file_name + '.svg'


def collect_and_process_model_for_dynamic_non_conformance(serv_dyn_model_path, interpretation, output_folder, output_file_name, static_model, direction):
    if not os.path.exists(serv_dyn_model_path):
           return None
    else:
        src_component_dynamic_model = collect_dynamic_model(serv_dyn_model_path)
        add_links_to_code(output_folder + 'code_linked_models/', output_file_name, src_component_dynamic_model, static_model)
        interpretation[direction + '_dyn_model'] = output_folder + 'code_linked_models/' + output_file_name + '.svg'
        return src_component_dynamic_model


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


