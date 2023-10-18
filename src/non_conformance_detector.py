from src.utils import extract_link_from_transition_label
from tqdm import tqdm

def extract_occurred_links_from_dynamic_model(dynamic_model, services: list) -> set:
    """
    This function is used to extract occurred links from the dynamic model.
    It basically goes through all the transitions in the dynamic model and 
    generated a dictionary of the occurred links. 

    :param dynamic_model: The dynamic model extracted from runtime logs. This model is a pydot graph.
    :param services: The list of services in the microservice application.
    """
    occurred_links = set()
    for transition in dynamic_model.get_edges():
        if transition.get_label() is None:
            continue
        link = extract_link_from_transition_label(transition.get_label())
        splitted = link.split('-')
        if splitted[0] not in services or splitted[1] not in services:
            continue
        occurred_links.add(link)

    return occurred_links

def find_non_conformance_in_linkset(this_linkset: set, that_linkset: set) -> set:
    """
    This function is used to find non-conformance between two sets of links.
    It basically goes through all the links in the first set and checks whether
    the links are also in the second set.

    :param this_linkset: The first set of links
    :param that_linkset: The second set of links
    """
    non_conformances = set()
    for link in tqdm(this_linkset, desc='Detecting non-conformances'):
        splitted = link.split('-')
        reverse_link = splitted[1] + '-' + splitted[0]
        if link in that_linkset or reverse_link in that_linkset:
            continue
        else:
            non_conformances.add(link)
    
    return non_conformances

        
def detect_non_conformances(static_model: dict, dynamic_model, services: list):
    """
    This function is used to detect differences (non-conformances)
    between the static and dynamic model extracted for a microservice
    applications. It basically goes through all the link evidences in
    the static model and checks whether the links occur in the dynamic model (and vice versa)

    :param static_model: The static model extracted from the source code of the microservice application
    :param dynamic_model: The dynamic model extracted from run-time logs. This model is pydot graph.
    :param services: The list of services in the microservice application
    """ 
    static_links = static_model['links']
    processed_services = [x.replace('-', '_') for x in services]
    dynamic_links = extract_occurred_links_from_dynamic_model(dynamic_model, processed_services)
    dynamic_non_conformances = find_non_conformance_in_linkset(static_links, dynamic_links)
    static_non_conformances = find_non_conformance_in_linkset(dynamic_links, static_links)
    return static_non_conformances, dynamic_non_conformances


