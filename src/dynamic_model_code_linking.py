from src.utils import clean_dynamic_model, extract_link_from_transition_label

def add_links_to_code(output_folder_path, file_name, dynamic_model, static_model):
    """
    This function is used to the link a transition shown in the run-time model to the corresponding line
    of code that produced the behaviour. The links are parsed from the static model(DFD model) that is 
    extracted using the tool developed by TUHH. We convert the run-time model into a different format 
    so that the user can click on the transition and be redirected to the corresponding line of code.

    :param output_folder_path: path to the folder processed run-time model will be saved
    :param file_name: file name that should be used to store the run-time model with the links to code
    :param dynamic_model: the run-time model loaded using the pydot library
    :param evidence_file: dictionary containing the evidences extracted by the static model (DFD)
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

# # Testing purposes
# if __name__ == '__main__':
#     add_links_to_code('./', 'testCATALOG', './catalog_service_data.csv.ff.final.dot', './data/ewolff_microservice/test.json')