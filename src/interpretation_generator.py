from src.utils import collect_dynamic_model, extract_state_to_edges_mapping_from_dynamic_model, clean_dynamic_model, extract_link_from_transition_label
import os
import random

FF_LINK_MODEL_SUFFIX = '_link_data.csv.ff.final.dot' # Specific suffix for dynamic models learned for the links (communication behavior between services)
FF_SERVICE_MODEL_SUFFIX = '_service_data.csv.ff.final.dot' # Specific suffix for dynamic models learned for the services ( communication behavior of a service)


def generate_interpretation(non_conformance_type: str, services: list, dynamic_models_folder: str, output_folder: str, static_model: dict, dynamic_model) -> dict:
    """
    This function is used to generate the interpretation of the non-conformance between the static
    and dynamic models. We have two definitions for non-conformances that we detect: static and dynamic.
    for more information from the difference type, please refer to the paper or the README. Based on 
    the type of difference, we generate the corresponding interpretation for the non-conformance.

    :param non_conformance_type: The type of difference between the static and dynamic models
    :param services: The list of two services that are involved in the non-conformance. Order follows the direction of the link
    :param dynamic_models_folder: The path to the folder containing the dynamic models
    :param static_model: The dictionary containing the evidences extracted from the static model
    :param dynamic_model: The model that is learned from all HTTP event logs.
    """
    interpretation = {}
    interpretation['non_conformance_type'] = non_conformance_type
    processed_services = [x.replace('_', '-') for x in services] # change it back to original name
    interpretation['services'] = processed_services
    link_code_evidences = collect_link_code(services[0] + '-' + services[1], static_model['links'])
    interpretation['link_code_evidences'] = link_code_evidences

    # For if we find non-conformance in the static model; link occurring in the dynamic model
    # but not in the static model
    if non_conformance_type == 'static':
        link_dyn_model_path = dynamic_models_folder + processed_services[0] + '_' + processed_services[1] + FF_LINK_MODEL_SUFFIX
        out_file_name = services[0] + '_' + services[1] + '_link_model'
        collect_and_process_model_for_static_non_conformance(link_dyn_model_path, interpretation, output_folder, out_file_name, static_model)


    # For if we find non-conformance in the dynamic model; link occurring in the static model
    # but not in the dynamic model    
    if non_conformance_type == 'dynamic':
        # Check if there is dynamic model for source service
        src_service_dynamic_model = collect_and_process_model_for_dynamic_non_conformance(
            dynamic_models_folder + processed_services[0] + FF_SERVICE_MODEL_SUFFIX, 
            interpretation, 
            output_folder, 
            processed_services[0] + '_service_model', 
            static_model,
            'src'
        )
        
        # Check if dynamic model exist for destination service
        dst_service_dynamic_model = collect_and_process_model_for_dynamic_non_conformance(
            dynamic_models_folder + processed_services[1] + FF_SERVICE_MODEL_SUFFIX, 
            interpretation, 
            output_folder, 
            processed_services[1] + '_service_model', 
            static_model,
            'dst'
        )

        if src_service_dynamic_model is not None and dst_service_dynamic_model is not None:
            static_call_sequences = find_previous_sequences_for_link_static_model(static_model['links'], services[1], services[0], 1000)
            dynamic_paths = do_random_walk_dynamic_model(dynamic_model, services[0], services[1], 1000, 20)
            occurred_call_sequences = find_occurred_sequences_in_paths(static_call_sequences, dynamic_paths)
            code_call_sequences = collect_code_call_sequences_from_sequences(static_call_sequences, static_model['links'])
            interpretation['potential_call_sequences'] = static_call_sequences
            interpretation['occurred_call_sequences'] = occurred_call_sequences
            interpretation['code_call_sequences'] = code_call_sequences
            sequences_call_details = dict()
            for call_sequence in occurred_call_sequences:
                sequences_call_details[str(call_sequence)] = find_sequence_of_call_details(call_sequence, dynamic_model)
            
            interpretation['call_details_sequences'] = sequences_call_details
        elif src_service_dynamic_model is None and dst_service_dynamic_model is not None:
            interpretation['missing_dynamic_model'] = [services[0]]
        elif src_service_dynamic_model is not None and dst_service_dynamic_model is None:
            interpretation['missing_dynamic_model'] = [services[1]]
        else:
            interpretation['missing_dynamic_model'] = [services[0], services[1]]

    return interpretation


def compute_top_n_transitions_from_dynamic_model(dynamic_model, n: int) -> list:
    """
    Find the top N tranitions that occur within the dynamic model. The dynamic model stores the 
    frequency of each transition within the model and we use this information to filter out the 
    top N transitions.

    :param model: The dynamic model that is loaded using the pydot library
    :param n: The number of top transitions to be returned
    """

    edges = dynamic_model.get_edges()
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


def collect_link_code(link: str, link_evidences: dict) -> list:
    """
    Collect the code evidences for the given link. The evidences are collected from the static model.

    :param link: The link for which the code evidences are collected
    :param link_evidences: The dictionary containing the evidences extracted from the static model
    """
    code_for_link = []
    for evidence in link_evidences:
        if evidence == link:
            code_for_link += link_evidences[evidence]
    
    return code_for_link


def collect_code_call_sequences_from_sequences(sequences: list, link_evidences: dict) -> list:
    """
    Collect the code call sequences for the given sequences of links. We basically tranform a sequence of links
    to their corresponding sequence of code calls.

    :param occurred_sequences: The list of sequences of links that occurred in the dynamic model.
    :param link_evidences: The dictionary containing the link evidences extracted from the static model
    """
    code_call_sequences = dict()
    for sequence in sequences:
        code_call_sequence = []
        for link in sequence:
            processed_link = link.replace('__', '-')
            code_call_sequence += collect_link_code(processed_link, link_evidences)
        code_call_sequences['-'.join(sequence)] = code_call_sequence
    
    return code_call_sequences


def collect_and_process_model_for_static_non_conformance(link_dyn_model_path: str, interpretation:dict, output_folder:str, output_file_name:str, static_model:dict):
    """
    Collect and process the dynamic model for a static non-conformance. We compute the top 10 frequently
    occurring transitions from the dynamic model and then convert the model to SVG format.

    :param link_dyn_model_path: The path to the dynamic model inferred for the communication behaviour between the two involved services.
    :param interpretation: The dictionary that stores the interpretation of the non-conformance.
    :param output_folder: The path to the output folder.
    :param output_file_name: The name of the file that should be used to store the dynamic model as SVG file.
    :param static_model: The dictionary containing the evidences extracted from the static model.
    """
    link_dynamic_model = collect_dynamic_model(link_dyn_model_path)
    top_transitions_from_link_dyn_model = compute_top_n_transitions_from_dynamic_model(link_dynamic_model, 10)
    interpretation['top_transitions_from_link_dyn_model'] = top_transitions_from_link_dyn_model
    add_links_to_code(output_folder + 'code_linked_models/', output_file_name, link_dynamic_model, static_model)
    interpretation['link_dyn_model'] = output_folder + 'code_linked_models/' + output_file_name + '.svg'


def collect_and_process_model_for_dynamic_non_conformance(serv_dyn_model_path: str, interpretation: dict, output_folder: str, output_file_name: str, static_model: dict, direction: str) -> list:
    """
    Collect and process the dynamic model for a dynamic non-conformance. We add the links to the code on each
    transition that has occurred in the dynammic model and then convert the model to SVG format.

    :param serv_dyn_model_path: The path to the dynamic model inferred for the communication behaviour of the involved service.
    :param interpretation: The dictionary that stores the interpretation of the non-conformance.
    :param output_folder: The path to the output folder.
    :param output_file_name: The name of the file that should be used to store the dynamic model as SVG file.
    :param static_model: The dictionary containing the evidences extracted from the static model.
    :param direction: The direction of the non-conformance, either source or destination.
    """
    if not os.path.exists(serv_dyn_model_path):
           return None
    else:
        service_dynamic_model = collect_dynamic_model(serv_dyn_model_path)
        add_links_to_code(output_folder + 'code_linked_models/', output_file_name, service_dynamic_model, static_model)
        interpretation[direction + '_dyn_model'] = output_folder + 'code_linked_models/' + output_file_name + '.svg'
        return service_dynamic_model


def transform_static_model_links(static_model_links: list) -> dict:
    """
    Tranform the links from the static model into a dictionary that stores information on the parents and children
    of each service. This is used to find the previous sequences of links that could occur in the static model.

    :param static_model_links: A list of links between the services.
    """
    service_parent_children_mapping = {}
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
        
        if source not in service_parent_children_mapping:
            service_parent_children_mapping[source] = {'parents': set(), 'children': set()}
        
        if target not in service_parent_children_mapping:
            service_parent_children_mapping[target] = {'parents': set(), 'children': set()}
        
        service_parent_children_mapping[source]['children'].add(target)
        service_parent_children_mapping[target]['parents'].add(source)
    
    return service_parent_children_mapping


def find_previous_sequences_for_link_static_model(static_model_links: dict, starting_point: str, required_service: str, number_of_walks: int) -> list:
    """
    For a given link that is part of a non-conformance of type static, find the previous sequences of links
    that could occur in the static model. To do so, we start from the destination service of the link and we
    go backwards in the static model to find (possible) previous sequences. Currently, we only consider 
    sequences that have a length between 1 and 5.

    :param static_model_links: A dictionary that contains the links between the services.
    :param starting_point: The service from which we start to walk backwards in the static model.
    :param required_services: The service that must be in the path, this would be the source service of the link.
    :param number_of_walks: The number of random walks to do.
    """
    service_parent_children_info = transform_static_model_links(static_model_links)
    potential_previous_sequences = []
    potential_previous_sequences_set = set()
    # Do the random backwards walks
    for i in range(number_of_walks):
        current_node = starting_point
        path = []
        walk_length = random.randint(2, 5)
        for j in range(walk_length):
            target_nodes = service_parent_children_info[current_node]['parents']
            if len(target_nodes) == 0:
                break
            next_target_node = random.choice(list(target_nodes))
            path.insert(0, next_target_node)
            current_node = next_target_node

        if str(path) in potential_previous_sequences_set:
            continue
        
        if required_service in path:
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


def find_sequence_of_call_details(call_sequence: list, dynamic_model) -> list:
    """
    Find the call details from a given call sequence. We basically traverse the dynamic model
    and find sequences of transitions that matches the call sequence. We then extract the call 
    details from these sequences of transitions.

    :param call_sequence: The sequence of calls for which we want to find the details.
    :param dynamic_model: The dynamic model that is loaded using the pydot library.
    """
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


def do_random_walk_dynamic_model(dynamic_model, required_service: str, missing_service: str, number_of_walks: int, walk_length: int) -> list:
    """
    Do random walks over the dynamic model to sample paths that were used to infer the dynamic
    model. The paths that are traversed through this model must contain the service that is
    given as the parameter.

    :param dynamic_model: The dynamic model that is loaded using the pydot library.
    :param number_of_walks: The number of random walks to do.
    :param required_service: The service that must be in the path.
    :param walk_length: The length of each random walk.
    """
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

        path.append(required_service + '__' + missing_service) # include the missing link in the path (will be shown in the interpretation).
        if required_service in str(path):
            random_walk_paths.append(path)
            random_walk_paths_set.add(str(path))
        
    
    return random_walk_paths
            
            
def find_occurred_sequences_in_paths(potential_previous_sequences: list, dynamic_model_walk_paths: list) -> list:
    """
    Find sequences, generated from backward walks on the static model, that really occurred in the dynamic model.
    We also count how often it has occurred in the dynamic model.

    :param potential_previous_sequences: The previous sequences of links that could have occurred for a given link in the static model.
    :param dynamic_model_walk_paths: The random paths that were traversed in the dynamic model.
    """
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


def find_starting_points_for_sequence(start_call: str, dynamic_model) -> list:
    """
    Find the possible starting points in the dynamic model given a starting call for a call 
    sequence. We basically traverse the dynamic model and find transitions that matches the 
    start of the call sequence.

    :param call_sequence: The starting call of the call sequence.
    :param dynamic_model: The dynamic model that is loaded using the pydot library.
    """
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


def add_links_to_code(output_folder_path: str, file_name: str, dynamic_model, static_model: dict):
    """
    This function is used to the link a transition shown in the dynamic model to the corresponding line
    of code that produced the behaviour. The links are parsed from the static model (DFD model) extracted 
    using the tool developed by TUHH. We convert the dynamic model into SVG format so that the model could
    be rendered on a HTML page. Moreover, the SVG file allows the user to click on the transition and 
    be redirected to the corresponding line of code.

    :param output_folder_path: The path to the folder processed dynamic model will be saved.
    :param file_name: The file name that should be used to store the dynamic model with the links to code.
    :param dynamic_model: The dynamic model loaded using the pydot library.
    :param evidence_file: The dictionary containing the evidences extracted by the static model (DFD).
    """
    dynamic_model = clean_dynamic_model(dynamic_model)
    edges = dynamic_model.get_edges()

    for e in edges:
        # get the edge label
        label = e.get_label()
        if label is None:
            continue
        link = extract_link_from_transition_label(label)
        if link in static_model['links']:
            url = static_model['links'][link][0][1]
            # add href to the edge
            e.set_href(url)
        else:
            continue

    dynamic_model.write(output_folder_path + file_name + '.svg', format='svg')

