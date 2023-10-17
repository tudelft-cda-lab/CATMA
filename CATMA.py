import os
import argparse as ap

from src.utils import *
from src.interpretation_generator import *
from src.interpretation_visualizer import *
from src.model_processor import *
from src.non_conformance_detector import *
from src.non_conformance_visualizer import *

FF_SUFFIX = '.csv.ff.final.dot'


def create_output_folders(output_folder):
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(output_folder + 'interpretations/', exist_ok=True)
    os.makedirs(output_folder + 'code_linked_models/', exist_ok=True)
    os.makedirs(output_folder + 'visualization/', exist_ok=True)


def read_arguments():
    arg_parser = ap.ArgumentParser(description='CATMA: Conformance Analysis Tool for Microservice Applications')
    arg_parser.add_argument('--static_model_path', type=str, help='Path to static model.')
    arg_parser.add_argument('--dynamic_models_path', type=str, help='Path to the runtime models.')
    arg_parser.add_argument('--output_path', type=str, help='Path to the output folder.')
    args = arg_parser.parse_args()

    static_model_path = args.static_model_path
    if not static_model_path:
        print("\nNo path to static models provided, please run again.\n")
        return
    dynamic_models_path = args.dynamic_models_path
    if not dynamic_models_path:
        print("\nNo path to dynamic models provided, please run again.\n")
        return
    output_folder = args.output_path
    if not output_folder: output_folder = "./"  # use current directory if no output folder specified

    return static_model_path, dynamic_models_path, output_folder


def main():

    static_model_path, dynamic_models_path, output_folder = read_arguments()
    if (not static_model_path) or (not dynamic_models_path):
        return
    
    # Read config information
    print('Reading configuration file...')
    config = read_json_file('./config/config.json')
    interpretation_texts = read_json_file('./interpretation_texts/interpretation_texts.json')
    
    # Create the subfolders in the output folder
    create_output_folders(output_folder)

    # Workflow step 1: read models 
    print('Processing static model...')
    static_model = read_static_model(static_model_path)
    print('Processing dynamic model...')
    dynamic_model = clean_dynamic_model(collect_dynamic_model(dynamic_models_path + config['general_dynamic_model']  + FF_SUFFIX))
    
    # Workflow step 2: detect non-conformances
    print('Detecting non-conformances...')
    static_non_conformances, dynamic_non_conformances = find_non_conformances(static_model, dynamic_model, config['services'])

    if len(static_non_conformances) + len(dynamic_non_conformances) == 0:
        print('No non-conformances detected between implementation and deployment of system, everything looks good :)')
        return

    print('Detected ' + str(len(static_non_conformances)) + ' static non-conformances and ' + str(len(dynamic_non_conformances)) + ' dynamic non-conformances between implementation and deployment of system!')

    # Workflow step 3: generate interpretations
    print('Generating non-conformance interpretations...')

    ncf_interpretations = list()
    for sncf in static_non_conformances:
        components = sncf.split('-')
        ncf_interpretations.append(generate_interpretation('static', components, dynamic_models_path, output_folder, static_model, dynamic_model))

    for dncf in dynamic_non_conformances:
        components = dncf.split('-')
        ncf_interpretations.append(generate_interpretation('dynamic', components, dynamic_models_path, output_folder, static_model, dynamic_model))
    
    # Workflow step 5: generate visualization for non-conformances
    print('Generating interpretation visualizations...')
    for ncf_interpretation in ncf_interpretations:
        generate_html_for_interpretation(output_folder + 'interpretations/', ncf_interpretation, interpretation_texts)
    
    # Workflow step 4: visualize non-conformances
    print('Generating non-conformance visualizations...')
    visualize_non_conformances(static_non_conformances, dynamic_non_conformances, output_folder, static_model)


if __name__ == '__main__':
    main()
