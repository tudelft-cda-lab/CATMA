from src.utils import collect_dynamic_model, clean_dynamic_model
import json


def read_static_model(static_model_path):
    """
    This function is used to read evidences that are collected by the static model.
    It first loads the JSON file. Then, it processes the evidences extraced by the static model (DFD model from TUHH).
    Evidences are parsed and stored in the corresponding dictionary; evidences collected from services
    are store in the service_evidence dictionary and evidences collected from links are stored in the
    link_evidences dictionary.

    :param evidence_file: The path to the JSON file containing the evidences.
    """

    with open(static_model_path, 'r') as f:
        static_model = json.load(f)

    link_evidences = dict()
    links = static_model['edges']
    for l in links:
        services = [x.replace('-','_') for x in l.split(' -> ')]
        link_name = '-'.join(services).lower()
        link_evidences[link_name] = []
        file = links[l]['file'].replace('blob/master/master', 'blob/master')
        line = links[l]['line']
        link_evidences[link_name].append(('Link', file, line))

    return {'links' : link_evidences}

def read_dynamic_model(dynamic_models_path):
    return clean_dynamic_model(collect_dynamic_model(dynamic_models_path))
    




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



