import time
from flexfringe import FlexFringe
import pandas as pd
import os
import pydot
from random import randint
from sklearn.model_selection import KFold
from sklearn.metrics import confusion_matrix
from tqdm import tqdm
from statistics import fmean
from collections import Counter

def load_state_machine(path_to_sm):
    sm = dict()
    graph =  pydot.graph_from_dot_file(path_to_sm)[0]
    nodes = graph.get_nodes()
    edges = graph.get_edges()
    sm['num_edges'] = len(edges)
    sm['num_nodes'] = len(nodes) - 1 

    for n in nodes:
        if n.get_name() == '\"\\n\"':
            graph.del_node(n)

        if n.get_name() not in sm:
            sm[n.get_name()] = {'incoming': dict(), 'outgoing': dict()}

    for e in edges:
        if e.get_label() is None:
            continue

        source = e.get_source()
        destination = e.get_destination()
        label = e.get_label()
        label = label.replace('\"', '').split('\n')[0]

        if label not in sm[source]['outgoing']:
            sm[source]['outgoing'][label] = []
        
        if label not in sm[destination]['incoming']:
            sm[destination]['incoming'][label] = []

        sm[source]['outgoing'][label].append(destination)
        sm[destination]['incoming'][label].append(source)
    
    return sm

def simulate_trace_on_sm(trace, sm):
    current_state = '0'
    index = 0
    while index < len(trace):
        event = trace[index]
        if event in sm[current_state]['outgoing']:
            current_state = sm[current_state]['outgoing'][event][0]
            index += 1
        else:
            return False
    
    return True

def train(train_data_path, ini_file_path):
    ff = FlexFringe(
        flexfringe_path= os.environ.get('FLEXFRINGE_PATH') + '/flexfringe',
        ini=ini_file_path
    )

    ff.fit(train_data_path)

def generate_abbadingo_trace_file(prediction_file, output_path):
    prediction_df = pd.read_csv(prediction_file, sep=';')
    traces = prediction_df[' abbadingo trace']
    num_traces = len(traces)
    with open(output_path, 'w') as f:
        f.write(str(num_traces) + ' 50\n')
        for i in range(num_traces):
            trace = traces[i].strip()
            trace = trace.replace('\"', '')
            f.write(trace + '\n')

def read_trace_file(path_to_trace_file):
    traces = []
    with open(path_to_trace_file) as f:
        next(f)
        lines = f.readlines()
        for line in lines:
            trace = line.strip()
            traces.append(trace.split(' ')[2:])

    return traces

def extract_alphabet_from_traces(traces):
    alphabet = set()
    for trace in traces:
        for event in trace:
            alphabet.add(event)

    return list(alphabet)


def generate_negative_traces(positive_trace, split_alphabet, global_alphabet):
    negative_trace = positive_trace.copy()
    negative_trace_types = ['insert', 'replace', 'swap']
    max_subseq_mutations = 3
    num_events = len(positive_trace)
    num_mutations = randint(1, max_subseq_mutations)
    for i in range(num_mutations):
        mutation_type = negative_trace_types[randint(0, len(negative_trace_types) - 1)]
        if mutation_type == 'insert':
            start_time = time.time()
            index = randint(0, num_events - 1)
            event = global_alphabet[randint(0, len(global_alphabet) - 1)]
            while event in split_alphabet:
                elapsed_time = time.time() - start_time
                if elapsed_time > 300:
                    break
                event = global_alphabet[randint(0, len(global_alphabet) - 1)]
            
            negative_trace.insert(index, event)

        elif mutation_type == 'replace':
            index = randint(0, num_events - 1)
            event = global_alphabet[randint(0, len(global_alphabet) - 1)]
            start_time = time.time()
            while event in split_alphabet:
                elapsed_time = time.time() - start_time
                if elapsed_time > 300:
                    break
                event = global_alphabet[randint(0, len(global_alphabet) - 1)]
            
            negative_trace[index] = event

        elif mutation_type == 'swap':
            index1 = randint(0, num_events - 1)
            index2 = randint(0, num_events - 1)
            while index1 == index2:
                index2 = randint(0, num_events - 1)
            
            temp = negative_trace[index1]
            negative_trace[index1] = negative_trace[index2]
            negative_trace[index2] = temp

    return negative_trace

def generate_kfold_splits(traces, k):
    kf = KFold(n_splits=k, shuffle=True)
    splits = []
    for train_index, test_index in kf.split(traces):
        splits.append((train_index, test_index))
    
    return splits

def generate_train_test_set_from_kfold_split(split, traces):
    train_set = []
    test_set = []
    for train_index in split[0]:
        train_set.append(traces[train_index])
    
    for test_index in split[1]:
        test_set.append(traces[test_index])
    
    return train_set, test_set

def write_abbadingo_traces_file(traces, alphabet, output_path):
    with open(output_path, 'w') as f:
        f.write(str(len(traces)) + ' ' +  str(len(alphabet)) + '\n')
        for trace in traces:
            trace_string = '0 ' + str(len(trace)) + ' '
            if len(trace) == 1:
                trace_string += trace[0]
            else:
                trace_string += ' '.join(trace)
            f.write(trace_string + '\n')

def main():
    print('Reading data and generated traces...')
    trace_file = 'abbadingo_traces.dat'
    predictions = 'ms_http_data.csv.ff.final.json.result.csv'
    generate_abbadingo_trace_file(predictions, trace_file)
    traces = read_trace_file(trace_file)
    print('Extracting global alphabet...')
    global_alphabet = extract_alphabet_from_traces(traces)
    print('Generating splits...')
    kfold_splits = generate_kfold_splits(traces, 10)
    num_negative_traces = 50

    recall_scores = []
    specificity_scores = []
    balanced_accuracy_scores = []
    model_sizes = {'edges': [], 'nodes': []}

    for split in tqdm(kfold_splits, desc='Doing K-Fold Cross Validation'):
        train_set, test_set = generate_train_test_set_from_kfold_split(split, traces)
        train_traces_set = set()
        test_traces_set = set()
        for trace in train_set:
            train_traces_set.add(str(trace))

        for trace in test_set:
            test_traces_set.add(str(trace))


        processed_test_set = []
        for trace in test_set:
            if str(trace) in train_traces_set:
                processed_test_set.append(trace)

        if len(processed_test_set) < num_negative_traces:
            for i in range(num_negative_traces - len(processed_test_set)):
                random_trace = processed_test_set[randint(0, len(processed_test_set) - 1)]
                processed_test_set.append(random_trace)
        
        test_set = processed_test_set
        train_set_alphabet = extract_alphabet_from_traces(train_set)
        test_set_alphabet = extract_alphabet_from_traces(test_set)
        negative_traces = []
        start_time = time.time()
        while len(negative_traces) < num_negative_traces:
            elapsed_time = time.time() - start_time
            if len(negative_traces) > 0 and elapsed_time > 300:
                break
            negative_trace = generate_negative_traces(test_set[randint(0, len(test_set) - 1)], test_set_alphabet, global_alphabet)
            negative_traces.append(negative_trace)

        test_labels = [1] * len(test_set)
        test_set = test_set + negative_traces
        test_labels = test_labels + [-1] * len(negative_traces)
        train_file = 'abbadingo_train_traces.dat'
        write_abbadingo_traces_file(train_set, train_set_alphabet, train_file)
        
        train('abbadingo_train_traces.dat', 'sm_aic_correctness.ini')
        sm = load_state_machine(train_file + '.ff.final.dot')

        test_traces_classification = [1 if simulate_trace_on_sm(test_set[i], sm) else -1 for i in range(len(test_set))]
        
        tn, fp, fn, tp = confusion_matrix(test_labels, test_traces_classification).ravel()
        recall = tp / (tp + fn)
        specificity = tn / (tn + fp)
        balanced_accuracy = (recall + specificity) / 2
        recall_scores.append(recall)
        specificity_scores.append(specificity)
        balanced_accuracy_scores.append(balanced_accuracy)
        model_sizes['edges'].append(sm['num_edges'])
        model_sizes['nodes'].append(sm['num_nodes'])

    
    print('Average Recall: ' + str(fmean(recall_scores)))
    print('Average Specificity: ' + str(fmean(specificity_scores)))
    print('Average Balanced Accuracy: ' + str(fmean(balanced_accuracy_scores)))
    print('Average Model Size: ' + str(fmean(model_sizes['edges'])) + ' edges, ' + str(fmean(model_sizes['nodes'])) + ' nodes')


if __name__ == '__main__':
    main()

