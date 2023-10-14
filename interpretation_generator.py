import pandas as pd
import numpy as np
from dynamic_model_code_linking import *
from utils import collect_dynamic_model
from model_processor import *
import os

FF_LINK_MODEL_SUFFIX = '_link_data.csv.ff.final.dot'
FF_SERVICE_MODEL_SUFFIX = '_service_data.csv.ff.final.dot'

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

def collect_and_process_model_for_static_non_conformance(link_dyn_model_path, interpretation, output_folder, output_file_name, static_model_evidences):
        link_dynamic_model = collect_dynamic_model(link_dyn_model_path)
        top_transitions_from_link_dyn_model = compute_top_n_transitions_from_model(link_dynamic_model, 10)
        interpretation['top_transitions_from_link_dyn_model'] = top_transitions_from_link_dyn_model
        add_links_to_code(output_folder + 'code_linked_models/', output_file_name, link_dynamic_model, static_model_evidences)
        interpretation['link_dyn_model'] = output_folder + 'code_linked_models/' + output_file_name + '.svg'

def collect_and_process_model_for_dynamic_non_conformance(serv_dyn_model_path, interpretation, output_folder, output_file_name, static_model_evidences, direction):
    if not os.path.exists(serv_dyn_model_path):
           return None
    else:
        src_component_dynamic_model = collect_dynamic_model(serv_dyn_model_path)
        add_links_to_code(output_folder + 'code_linked_models/', output_file_name, src_component_dynamic_model, static_model_evidences)
        interpretation[direction + '_dyn_model'] = output_folder + 'code_linked_models/' + output_file_name + '.svg'
        return src_component_dynamic_model

def generate_interpretation(non_conformance_type, components, dynamic_models_folder, output_folder, static_model_evidences, general_dynamic_model):
    '''
    This function is used to generate the interpretation of the non-conformance between the static
    and dynamic models. We have two definitions for non-conformances that we detect: static and dynamic.
    for more information from the difference type, please refer to the paper or the README. Based on 
    the type of difference, we generate the corresponding interpretation for the non-conformance.

    :param diff_type: type of difference between the static and dynamic models
    :param components: list of two components that are involved in the non-conformance. Order follows the direction of the link
    :param dynamic_models_folder: path to the folder containing the dynamic models
    :param static_model_evidences: dictionary containing the evidences extracted from the static model
    :param general_dynamic_model: The model that is learned from all HTTP event logs.
    '''
    interpretation = {}
    interpretation['non_conformance_type'] = non_conformance_type
    processed_components = [x.replace('_', '-') for x in components] # change it back to original name
    interpretation['components'] = processed_components
    link_code_evidences = collect_link_code(components[0] + '-' + components[1], static_model_evidences['links'])
    interpretation['link_code_evidences'] = link_code_evidences

    # For if we find non-conformance in the static model; link occurring in the dynamic model
    # but not in the static model
    if non_conformance_type == 'static':
        link_dyn_model_path = dynamic_models_folder + processed_components[0] + '_' + processed_components[1] + FF_LINK_MODEL_SUFFIX
        out_file_name = components[0] + '_' + components[1] + '_link_model'
        collect_and_process_model_for_static_non_conformance(link_dyn_model_path, interpretation, output_folder, out_file_name, static_model_evidences)


    # For if we find non-conformance in the dynamic model; link occurring in the static model
    # but not in the dynamic model    
    if non_conformance_type == 'dynamic':
        # Check if there is dynamic model for component
        src_component_dynamic_model = collect_and_process_model_for_dynamic_non_conformance(
            dynamic_models_folder + processed_components[0] + FF_SERVICE_MODEL_SUFFIX, 
            interpretation, 
            output_folder, 
            processed_components[0] + '_service_model', 
            static_model_evidences,
            'src'
        )
        
        # check if dynamic model exist for destination component
        dst_component_dynamic_model = collect_and_process_model_for_dynamic_non_conformance(
            dynamic_models_folder + processed_components[1] + FF_SERVICE_MODEL_SUFFIX, 
            interpretation, 
            output_folder, 
            processed_components[1] + '_service_model', 
            static_model_evidences,
            'dst'
        )

        if src_component_dynamic_model is not None and dst_component_dynamic_model is not None:
            static_call_sequences = find_previous_sequences_for_link_static_model(static_model_evidences['links'], components[1], components[0], 1000)
            dynamic_paths = do_random_walk_dynamic_model(general_dynamic_model, components[0], components[1], 1000, 20)
            occurred_call_sequences = find_occurred_sequences_in_paths(static_call_sequences, dynamic_paths)
            code_call_sequences = collect_code_call_sequences_from_sequences(static_call_sequences, static_model_evidences['links'])
            interpretation['potential_call_sequences'] = static_call_sequences
            interpretation['occurred_call_sequences'] = occurred_call_sequences
            interpretation['code_call_sequences'] = code_call_sequences
            sequences_call_details = dict()
            for call_sequence in occurred_call_sequences:
                sequences_call_details[str(call_sequence)] = find_sequence_of_call_details(call_sequence, general_dynamic_model)
            
            interpretation['call_details_sequences'] = sequences_call_details
        elif src_component_dynamic_model is None and dst_component_dynamic_model is not None:
            interpretation['missing_dynamic_model'] = [components[0]]
        elif src_component_dynamic_model is not None and dst_component_dynamic_model is None:
            interpretation['missing_dynamic_model'] = [components[1]]
        else:
            interpretation['missing_dynamic_model'] = [components[0], components[1]]

    return interpretation





