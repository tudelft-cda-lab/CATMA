from tqdm import tqdm
import os
from utils import *
from dynamic_model_code_linking import *
from static_model_parser import *
from interpretation_generator import *
from interpretation_visualizer import *
from model_walker import *
import argparse as ap
from non_conformance_detector import *
import time 

def generate_visualization_for_non_conformance(type, components, output_folder, static_model_evidences, dynamic_model, interpretation_texts, dynamic_models_path):
    """
    Generate the model-based visualization and HTML page with the interpretations for the given non-conformance.
    :param type: type of non-conformance. Either static or dynamic.
    :param components: list of two components that are involved in the non-conformance.
    :param output_folder: path to the output folder where the visualization and interpretation will be stored.
    :param static_model_evidences: dictionary containing the evidences extracted from the static model.
    :param dynamic_model: dynamic model loaded using the pydot library.
    :param interpretation_texts: dictionary containing the interpretation texts for the non-conformance.
    :param dynamic_models_path: path to the folder containing the dynamic models.
    """
    ncf_interpretation = generate_interpretation(type, components, dynamic_models_path, static_model_evidences, dynamic_model)
    generate_html_for_interpretation(output_folder + 'interpretations/', ncf_interpretation, interpretation_texts)

def create_output_folders(output_folder):
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(output_folder + 'interpretations/', exist_ok=True)
    os.makedirs(output_folder + 'code_linked_models/', exist_ok=True)
    # os.makedirs(output_folder + 'non_conformance_visualization/', exist_ok=True)

def main():
    arg_parser = ap.ArgumentParser(description='Model Diff')
    arg_parser.add_argument('--static_model_path', type=str, help='Path to static model.')
    arg_parser.add_argument('--dynamic_models_path', type=str, help='Path to the run-time models.')
    arg_parser.add_argument('--output_path', type=str, help='Path to the output folder.')
    args = arg_parser.parse_args()

    print('Reading configuration file for tool')
    config = read_json_file('./config/config.json')
    interpretation_texts = read_json_file('./interpretation_texts/interpretation_texts.json')
    static_model_evidences_path = args.static_model_path
    output_folder = args.output_path

    # Create the subfolders in the output folder
    create_output_folders(output_folder)

    print('Parsing evidences from static model')
    static_model_evidences = read_static_model_evidences(static_model_evidences_path)
    processed_static_model_evidences = process_static_model_evidences(static_model_evidences)
    general_dynamic_model = clean_dynamic_model(collect_dynamic_model(args.dynamic_models_path + config['general_dynamic_model']  + '.csv.ff.final.dot'))
    dynamic_models_path = args.dynamic_models_path

    print('Finding non-conformances')
    static_non_conformances, dynamic_non_conformances = find_non_conformances(processed_static_model_evidences, general_dynamic_model, config['services'])
    if len(static_non_conformances) + len(dynamic_non_conformances) > 0:
        print('Detected ' + str(len(static_non_conformances)) + ' static non-conformances and ' + str(len(dynamic_non_conformances)) + ' dynamic non-confromances between implementation and deployment of system!')
        print('Generating visualization and interpretation for the static non-conformances')
        for ncf in static_non_conformances:
            non_conformance_type = 'static'
            temp = ncf.split('-')
            if len(temp) == 2:
                components = [temp[0], temp[1]]
            elif len(temp) == 3:
                components = [temp[0], temp[1] + '-' + temp[2]]
            elif len(temp) == 4:
                components = [temp[0] + '-' + temp[1], temp[2] + '-' + temp[3]]

            generate_visualization_for_non_conformance(non_conformance_type, components, output_folder, processed_static_model_evidences, general_dynamic_model, interpretation_texts['static_interpretations'], dynamic_models_path)

        for ncf in dynamic_non_conformances:
            non_conformance_type = 'dynamic'
            temp = ncf.split('-')
            if len(temp) == 2:
                components = [temp[0], temp[1]]
            elif len(temp) == 3:
                components = [temp[0], temp[1] + '-' + temp[2]]
            elif len(temp) == 4:
                components = [temp[0] + '-' + temp[1], temp[2] + '-' + temp[3]]

            generate_visualization_for_non_conformance(non_conformance_type, components, output_folder, processed_static_model_evidences, general_dynamic_model, interpretation_texts['dynamic_interpretations'], dynamic_models_path)

    else:
        print('No non-conformances detected between implementation and deployment of system, everything looks good :)')


if __name__ == '__main__':
    main()
