import os
import pandas as pd
import networkx as nx
from ast import literal_eval
def preprocess_ids(data):
    data['id'] = data['id'].apply(literal_eval)
    return data
path = "data"  # folder holding the input / output workbooks
input_file_path = os.path.join(path, 'Sorted_Exams.xlsx')
output_file_path = os.path.join(path, 'Subgrouped_Exams.xlsx')
data = pd.read_excel(input_file_path)
data = preprocess_ids(data)
def subgroup_exams(data):
    results = {}
    grouped_data = data.groupby('duration_group')
    for name, group in grouped_data:
        G = nx.Graph()
        for index, row in group.iterrows():
            G.add_node(index, ids=set(row['id']))
        
        nodes = list(G.nodes(data=True))
        for i in range(len(nodes) - 1):
            for j in range(i + 1, len(nodes)):
                if not set(nodes[i][1]['ids']).isdisjoint(nodes[j][1]['ids']):
                    G.add_edge(nodes[i][0], nodes[j][0])
        coloring = nx.coloring.greedy_color(G, strategy=nx.coloring.strategy_largest_first)
        for index in group.index:
            results[index] = coloring[index]
    return results
subgroup_results = subgroup_exams(data)
data['Subgroup'] = data.index.map(subgroup_results)
data.to_excel(output_file_path, index=False)
print(f"Data with subgroups has been exported to {output_file_path}.")
