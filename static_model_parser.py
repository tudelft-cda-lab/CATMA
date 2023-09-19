import json
# import argparse

def read_static_model_evidences(evidence_file_path):
    """
    This function is used to read evidences that are collected by the static model.
    It basically load the JSON file and return it as a dictionary.

    :param evidence_file: The path to the JSON file containing the evidences.
    """
    with open(evidence_file_path, 'r') as f:
        return json.load(f)


def extract_code_line(file, line):
    """
    This function is used to extract a specific (source code) line from a file.
    :param file: The file from which the line will be extracted.
    :param line: The line number that will be extracted.
    """
    with open(file, 'r') as f:
        lines = f.readlines()
        if isinstance(line, str):
            return lines[int(line) - 1].strip()
        elif isinstance(line, int):
            return lines[line - 1].strip()
        else:
            raise Exception('Invalid line number')
    

def process_line_evidence(file_path, src_code_folder):
    """
    This function is used to parse and transform the URL into a file path, which will be used
    to parse the specific line from the file. Currently, this is not used.

    :param file_path: The URL of the file.
    :param src_code_folder: The path to the folder containing the source code.

    """
    if 'heuristic' in file_path or 'implicit' in file_path:
        return file_path
    
    splitting_point = src_code_folder.split('/')[-1] + '/'
    processed_file_path = file_path.split(splitting_point)[1].split('#')[0]
    return src_code_folder + '/' + processed_file_path

def process_service_evidences(services):
    """
    This function is used to process the evidences collected from the services in the DFD model.
    We basically parse the evidences and store them in a dictionary. The key is the service and
    the value is a list of tuples containing the file path (URL) and the line number.

    :param services: Dictionary containing the evidences collected for the services in the DFD model.
    """
    service_evidences = {}
    
    for s in services:
        s = s.lower()
        service_evidences[s] = []
        file = services[s]['file'].replace('blob/master/master', 'blob/master')
        line = services[s]['line']

        service_evidences[s].append(('Service', file, line))
        if 'sub_items' in services[s]:
            other_evidences = services[s]['sub_items']
            for evidence in other_evidences:
                file = other_evidences[evidence]['file']
                line = other_evidences[evidence]['line']
                service_evidences[s].append((evidence, file, line))

    return service_evidences

def process_link_evidences(links):
    """
    This function is used to process the evidences collected for the links in the DFD model.
    The structure of this dictionary is the similar as the one used for the services, except 
    for this one we use the link as the key.

    :param links: Dictionary containing the evidences collected for the links
    """
    link_evidences = {}
    for l in links:
        link_name = '-'.join(l.split(' -> ')).lower()
        link_evidences[link_name] = []
        file = links[l]['file'].replace('blob/master/master', 'blob/master')
        line = links[l]['line']
        link_evidences[link_name].append(('Link', file, line))

    return link_evidences

def process_static_model_evidences(evidences):
    """
    This function is used to process the evidences extraced by the static model (DFD model from TUHH).
    Evidences are parsed and stored in the corresponding dictionary; evidences collected from services
    are store in the service_evidence dictionary and evidences collected from links are stored in the
    link_evidences dictionary.

    :param evidences: Dictionary containing the evidences extracted by the static model. This is the JSON by TUHH's tool
    
    """
    # service_evidences = process_service_evidences(evidences['nodes'])
    link_evidences = process_link_evidences(evidences['edges'])
    return {'links' : link_evidences}

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