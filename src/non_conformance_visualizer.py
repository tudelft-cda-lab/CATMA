import plantuml


def visualize_non_conformances(static_non_conformances: set, dynamic_non_conformances: set, output_folder: str, processed_static_model: dict) -> int:
    """
    Visualizes found non-conformances by creating a graph of the architecture where non-conformances are highlighted in color.

    :param static_non_conformances: The set of non-conformances found by comparing the static model with the dynamic model.
    :param dynamic_non_conformances: The set of non-conformances found by comparing the dynamic model with the static model.
    :param output_folder: The path to the output folder where the visualization should be stored.
    :param processed_static_model: The static model that is processed by the model processor.
    """
    # get complete architecture from `processed_static_model_evidences``

    links_detected_by_both = set()
    nodes = set()

    # parse all inks from the static model as basis for all links detected by both
    for link in processed_static_model["links"].keys():
        links_detected_by_both.add(link)
        nodes.add(link.split("-")[0])
        nodes.add(link.split("-")[1])
    
    # remove those that are non-conformances -> only links detected by both are left
    for link in static_non_conformances:
        if link in links_detected_by_both:
            links_detected_by_both.remove(link)
    for link in dynamic_non_conformances:
        if link in links_detected_by_both:
            links_detected_by_both.remove(link)


    plantuml_str = add_header("")

    for node in nodes:
        plantuml_str += f"        {node} [label = {node} shape = Mrecord];\n"


    for link in links_detected_by_both:
        plantuml_link = link.replace("-", " -> ")
        plantuml_str += f"\n        {plantuml_link} [color = \"black\"]"

    for link in static_non_conformances:
        plantuml_link = link.replace("-", " -> ")
        plantuml_str += f"\n        {plantuml_link} [color = \"red\"]"

    for link in dynamic_non_conformances:
        plantuml_link = link.replace("-", " -> ")
        plantuml_str += f"\n        {plantuml_link} [color = \"darkgreen\"]"

    plantuml_str = add_footer(plantuml_str)

    write_output(plantuml_str, output_folder)
    #print(plantuml_str)
    return 0


def add_header(plantuml_str: str) -> str:
    """
    Adds the header of the PlantUML file.

    :param plantuml_str: The string that should be extended with the header.
    """

    plantuml_str += """
@startuml
skinparam monochrome true
skinparam ClassBackgroundColor White
skinparam defaultFontName Arial
skinparam defaultFontSize 11


digraph dfd2{
    node[shape=record]
"""
    return plantuml_str


def add_footer(plantuml_str: str) -> str:
    """
    Adds the footer of the PlantUML file.

    :param plantuml_str: The string that should be extended with the footer.
    """

    plantuml_str += """
}
@enduml
"""
    return plantuml_str

def write_output(plantuml_str, output_folder: str):
    """
    Writes PlantUML to file and calls PlantUML server to generate PNG.

    :param plantuml_str: The string that should be written to file and used to generate the PNG.
    :param output_folder: The path to the output folder where the visualization should be stored.
    """ 

    output_file_path = f"{output_folder}visualization/plantuml.txt"

    # write to file
    with open(output_file_path, 'w+') as output_file:
        output_file.write(plantuml_str)

    # generate PNG
    generator = plantuml.PlantUML(url = "http://www.plantuml.com/plantuml/img/")
    try:
        png = generator.processes_file(filename = output_file_path)
    except Exception:
        print("No connection to the PlantUML server possible or malformed input to the server.")
        
    return 0