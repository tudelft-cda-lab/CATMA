import dominate
from dominate.tags import *
from dominate.util import raw

def convert_flexfringe_transition_to_call(transition_info):
    '''
    Convert the transition information that is collected from the run-time model to a
    more human readable information. We basically extract here the URL, port, status code,
    the direction of the call HTTP event call and the frequence of the call.
    
    :param transition_info: The transition information that is collected from the run-time model.
    '''
    transition = transition_info[0]
    transition_frequency = transition_info[1]
    splitted = transition.split('__')
    start_index = 0
    if splitted[0] == 'in' or splitted[0] == 'out':
        start_index = 1
    
    call_info = dict()
    call_info['port'] = splitted[start_index]
    call_info['call_url'] = splitted[start_index + 1].replace('>', '/').replace('-', ':')
    call_info['call_status_code'] = splitted[start_index + 2]
    call_info['call_direction'] = 'from ' + splitted[start_index + 4] + ' to ' + splitted[start_index + 5]
    call_info['call_frequency'] = transition_frequency
    return call_info

def load_dynamic_model_as_svg(model_path):
    '''
    Load the run-time model that in which we added the links to the code. Links are added in
    the interpretation generation part and they are stored as SVG files. We read the SVG file 
    here and return the content as result.

    :param model_path: path to the run-time model stored as SVG file
    '''
    with open(model_path, 'r') as f:
        model = f.read()
    return model


def generate_html_table_of_code_evidences(doc, evidences):
    '''
    Genrerate a table in HTML format that will show all the code evidences collected 
    for a given link or component.

    :param doc: The HTML document to which the table will be added
    :param evidences: The code evidences that will be added to the table
    '''
    d = div(id = 'evidences')
    tbl = table(id ='evidence_table', border='1')
    d.add(tbl)
    # add header of table
    with tbl:
        with tr():
            th('Type of evidence')
            th('File for evidence')
            th('Line number of evidence')

    # add content of table
    for evidence in evidences:
        with tbl:
            with tr():
                td(evidence[0])
                if '.' in evidence[1]:
                    td(a(evidence[1], href=evidence[1]))
                else:
                    td(evidence[1])
                td(evidence[2])

    return doc

def generate_html_list_for_top_N_transitions(doc, runtime_model_transitions):
    '''
    Generate a DIV element containing a list of the top 10 transitions that have been
    extracted from the run-time model. The list is generated in HTML format.

    :param doc: The HTML document to which the list will be added
    :param runtime_model_transitions: The list of the top 10 transitions that will be added to the list, extracted from the run-time model
    '''
    for transition in runtime_model_transitions:
            call_info = convert_flexfringe_transition_to_call(transition)
            with div(id = 'call_info'):
                h3('Endpoint: ' + call_info['call_url'])
                with ul():
                    li('Port: ' + call_info['port'])
                    # li('Call url: ' + call_info['call_url'])
                    li('Call status code: ' + call_info['call_status_code'])
                    li('Call direction: ' + call_info['call_direction'])
                    li('Call frequency: ' + str(call_info['call_frequency']))

    return doc


def generate_static_non_conformance_interpretation(doc, interpretation_data, intepretation_texts):
    '''
    Generate the interpretation for non-conformance of type static; something that was detected 
    during run-time (dynamic) but not within the code (static). The interpretation is added to 
    the HTML document.

    :param doc: The HTML document to which the interpretation will be added
    :param interpretation_data: The interpretation data that we generated for the non-conformance
    '''

    with div(id = 'interpretations'):
        h2('Potential Interpretations For the Non-Conformance')
        for text in intepretation_texts:
            text_tile = text['title']
            text_content = text['description']
            with div(id = 'interpretation_text'):
                h3(text_tile)
                p(text_content)

    with div(id = 'interpretation_basis'):
        h2('The following information could help with the understanding of the detected non-conformance:')
        with div(id = 'dynamic_model'):
            run_time_model_div = div(id = 'model')
            run_time_model_div.add(
                generate_div_with_svg_model(
                    interpretation_data['link_dyn_model'],  
                    'Dynamic model learned for the communication behavior between ' + interpretation_data['components'][0] + ' and ' + interpretation_data['components'][1] + ':',
                    'static_ncf_svg'
                    )
                )
            
        with div(id = 'static_ncf_dynamic_model_calls'):
            h3('Frequently occurring endpoint calls extracted from the dynamic model learned for the communication behavior between ' + interpretation_data['components'][0] + ' and ' + interpretation_data['components'][1] + ':')
            doc = generate_html_list_for_top_N_transitions(doc, interpretation_data['top_transitions_from_link_dyn_model'])

    return doc


def transform_extracted_call_sequence_to_readable_format(call_sequence):
    '''
    Transform the call sequence to a more human readable format.

    :param call_sequence: The call sequence that is extracted from the static model
    '''
    readable_sequence = []
    for link in call_sequence:
        link = link.split('__')
        if link[0] not in readable_sequence:
            readable_sequence.append(link[0])
        readable_sequence.append(link[1])
             
    return readable_sequence

def generate_html_list_for_call_sequences(doc, call_sequences, code_call_sequences):
    '''
    Generate a list element for showing list of call sequences. The link to the source code 
    is added as a hyperlink in the arrows that are generated. 

    :param doc: The HTML document to which the list will be added
    :param call_sequences: The list of call sequences that will be added to the list
    :param code_call_sequences: The list of code call sequences that belongs to the call sequences
    '''
    with ul():
        for call_sequence in call_sequences:
            code_call_sequence = code_call_sequences['-'.join(call_sequence)]
            readable_sequence = transform_extracted_call_sequence_to_readable_format(call_sequence)
            list_item = li()
            list_item.add(readable_sequence[0])
            for i in range(1, len(readable_sequence)):
                list_item.add(' ')
                if code_call_sequence[i-1][1] == 'implicit':
                    list_item.add(raw('&#8594;'))
                    list_item.add('(implicit)')
                else:
                    list_item.add(a(raw('&#8594;'), href=code_call_sequence[i-1][1]))
                list_item.add(' ' + readable_sequence[i])

    return doc

def generate_html_for_call_sequences_leading_to_missing_link(doc, call_sequences, code_call_sequences):
    '''
    Generate the HTMl DIV element that will contain the call sequences that should lead to the 
    missing link in a dynamic non-conformance.

    :param doc: The HTML document to which the DIV element will be added
    :param interpretation_data: The interpretation data that we generated for the non-conformance
    '''
    with div(id = 'call_sequences'):
        generate_html_list_for_call_sequences(doc, call_sequences, code_call_sequences)

    return doc


def generate_div_with_svg_model(link_to_svg, text, ncf_type):
    '''
    Generate a HTML DIV element that will contain the SVG of a dynamic model. This is basically
    used to visualize the run-time model on the HTML page (with clickable transitions)

    :param link_to_svg: The link to the SVG file that will be added to the DIV element.
    :param text: The text that will be added to the DIV element.
    '''
    svg_div = div(id = 'model_svg')
    svg_div.add(h3(text))
    model = load_dynamic_model_as_svg(link_to_svg)
    # add id to the svg element
    model = model.replace('<svg', '<svg id="' + ncf_type + '"')
    svg_div.add(raw(model))
    return svg_div


def generate_dynamic_non_conformance_interpretation(doc, interpretation_data, interpretation_texts):
    '''
    Generate the interpretation for non-conformance of type dynamic; something that was detected
    within the code (static) but not during run-time (dynamic). The interpretation is added to
    the HTML document.

    :param doc: The HTML document to which the interpretation will be added
    :param interpretation_data: The interpretation data that we generated for the non-conformance
    '''
    with div(id = 'interpretations'):
        h2('Potential interpretations for the non-conformance')
        for text in interpretation_texts:
            text_tile = text['title']
            text_content = text['description']
            with div(id = 'interpretation_text'):
                h3(text_tile)
                p(text_content)

    with div(id = 'interpretation_basis'):
        h2('The folowing information could help with understanding of the detected non-conformance:')

        with div(id = 'dynamic_ncf_code_evidences'):
            h3('The following line of code should produce a call between ' + interpretation_data['components'][0] + ' and ' + interpretation_data['components'][1] + ' but no such call was seen during run-time. ')
            doc = generate_html_table_of_code_evidences(doc, interpretation_data['link_code_evidences'])
        
        if 'missing_dynamic_model' in interpretation_data:
            with div(id = 'dynamic_ncf_missing_dynamic_model'):
                if len(interpretation_data['missing_dynamic_model']) > 1:
                    p('No data run-time data was found for ' + interpretation_data['missing_dynamic_model'][0] + ' and ' + interpretation_data['missing_dynamic_model'][1] + '. Are these perhaps external components?')
                else:
                    p('No data run-time data was found for ' + interpretation_data['missing_dynamic_model'][0] + '. Is this perhaps an external component?')
        else:
            with div(id = 'dynamic_ncf_possible_sequences'):
                h3('Sequences extracted from the static model that should produce run-time behaviour for link between ' + interpretation_data['components'][0] + ' and ' + interpretation_data['components'][1])
                static_call_sequences = interpretation_data['potential_call_sequences']
                code_call_sequences = interpretation_data['code_call_sequences']
                doc = generate_html_for_call_sequences_leading_to_missing_link(doc, static_call_sequences, code_call_sequences)

            with div(id = 'dynamic_ncf_occurred_sequences'):
                h3('Sequences that occurred in the dynamic model that should produce run-time behaviour for link between ' + interpretation_data['components'][0] + ' and ' + interpretation_data['components'][1])
                runtime_call_sequences = interpretation_data['occurred_call_sequences']
                doc = generate_html_for_call_sequences_leading_to_missing_link(doc, runtime_call_sequences, code_call_sequences)

            with div(id = 'call_details_occurred_sequences'):
                h3('For the occurred sequences, these are the unique sequence of endpoints (parameters) that were used in the sequence')
                for call_sequence in runtime_call_sequences:
                    call_details_sequences = interpretation_data['call_details_sequences'][str(call_sequence)]
                    readable_call_sequence = transform_extracted_call_sequence_to_readable_format(call_sequence)
                    with ul():
                        list_item = li()
                        list_item.add('Sequence: ')
                        list_item.add(readable_call_sequence[0])
                        for i in range(1, len(readable_call_sequence)):
                            list_item.add(' ')
                            list_item.add(raw('&#8594;'))
                            list_item.add(' ' + readable_call_sequence[i])
                        
                        with ul():
                            for sequence in call_details_sequences:
                                list_item = li()
                                for j in range(len(sequence)):
                                    port = sequence[j].split('__')[0]
                                    endpoint = sequence[j].split('__')[1]
                                    if j == 0:
                                        list_item.add('Call started with \"' + endpoint + '\". ')
                                    else:
                                        list_item.add('Then followed by call with \"' + endpoint + '\". ')


            with div(id = 'dynamic_model'):
                h2('The following models can be used to inspect the (sequential) behavior of each component individually:')
                model_div_src = div(id = 'model')
                model_div_src.add(
                    generate_div_with_svg_model(
                        interpretation_data['src_dyn_model'], 
                        'Dynamic model learned for component ' + interpretation_data['components'][0] + ':',
                        'dynamic_ncf_svg'
                        )
                    )
                
                model_div_dst = div(id = 'model')
                model_div_dst.add(
                    generate_div_with_svg_model(
                        interpretation_data['dst_dyn_model'], 
                        'Dynamic model learned for component ' + interpretation_data['components'][1]+ ':',
                        'dynamic_ncf_svg'
                        )
                    )
        

    return doc
    
def generate_style_sheet(file_path):
    '''
    Generate a simple CSS style sheet that will be used to style the HTML document.

    :param file_path: The path to the file where the style sheet will be saved
    '''
    with open(file_path, 'w') as f:
        f.write(
            '''
            body {
                font-family: Arial, Helvetica, sans-serif;
                background-color: #f1f1f1;
            }

            #non-conformance_type, #call_sequences, #dynamic_model, #involved_components, #interpretations, #interpretation_text, #interpretation_basis {
                background-color: #ffffff;
                padding: 20px;
                margin: 20px;
            }

            #dynamic_ncf_code_evidences, #dynamic_ncf_possible_sequences, #dynamic_ncf_occurred_sequences, #static_ncf_dynamic_model_calls, #call_details_occurred_sequences, #model {
                background-color: #ffffff;
                padding: 20px;
                margin: 20px;
                border: 2px solid #000000;
                border-radius: 10px;
            }

            #model_svg {
                width: 100%;
                display: inline-block;
                position: relative;
            }

            svg {
                width: 100%;
                height: auto;
                display: inline-block;
                position: relative;
            }

            #static_ncf_svg {
                width: 70%;
                height: 800px;
                display: inline-block;
            }

            '''
            
        )


def generate_html_for_interpretation(output_path, interpretation_data, interpretation_texts):
    doc = dominate.document(title='Model Non-conformance Interpretation')
    
    with doc.head:
        link(rel='stylesheet', href='style.css')

    with doc:
        non_conformance_type = interpretation_data['non_conformance_type']
        with div(id = 'non-conformance_type'):
            h1('Non-conformance type: ' + non_conformance_type)

            if non_conformance_type == 'static':
                p('This is a non-conformance of which there was no code evidence collected for this link, but calls were detected between the two components during run-time.')
            else:
                p('This is a non-conformance of which there was code evidence collected for this link, but no calls were detected between the two components during run-time.')


        with div(id = 'involved_components'):
            h2('Involved components')
            with ul():
                for component in interpretation_data['components']:
                    li(component)

        if non_conformance_type == 'static':
            doc = generate_static_non_conformance_interpretation(doc, interpretation_data, interpretation_texts['static_interpretations'])
        else:
            doc = generate_dynamic_non_conformance_interpretation(doc, interpretation_data, interpretation_texts['dynamic_interpretations'])
        

    file_name = '_'.join(interpretation_data['components']) + '_' + non_conformance_type + '-non_conformance.html'
    with open(output_path + file_name, 'w') as f:
        f.write(doc.render())

    
    generate_style_sheet(output_path + 'style.css')



    