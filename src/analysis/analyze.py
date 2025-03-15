
from src.tools.path_tools import PathTools
import networkx as nx
from math import log
import json
import yaml
import os
import matplotlib.pyplot as plt


negativelog = lambda x: -log(x) if x > 0 else 0
giant_component_size = lambda G: len(max(nx.connected_components(G), key=len)) if nx.number_connected_components(G) > 0 else 0

def draw(G, path):
    # Draw the graph
    plt.figure(figsize=(10, 10))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_size=500, node_color="skyblue", font_size=10, font_color="black", edge_color="gray")
    plt.savefig(path)
    plt.close()

def degree_distribution(G: nx.Graph, weight=None):
    """Calculate the degree distribution of a graph."""
    degree_sequence = [d for n, d in G.degree(weight=weight)]
    degree_count = {}
    for degree in degree_sequence:
        if degree not in degree_count:
            degree_count[degree] = 0
        degree_count[degree] += 1
    return degree_count

def subgraph(G, label=None):
    """Extract a subgraph from a graph based on the label value."""
    if label is None:
        return G
    subgraph = nx.Graph()
    for u, v, data in G.edges(data=True):
        if data.get('label') == label:
            subgraph.add_edge(u, v, **data)
    return subgraph

def average_degree(G, weight=None):
    """Calculate the average degree of a graph."""
    degree_sequence = [d for n, d in G.degree(weight=weight)]
    return sum(degree_sequence) / (len(degree_sequence)*(len(degree_sequence) - 1)) if len(degree_sequence) > 1 else len(degree_sequence)  # avoid division by zero

def robustness_smalldegree_neglogcomp(G:nx.Graph, logpath):
    """Calculate the robustness of a graph based on certain deletion rule and connectedness measure."""
    os.makedirs(logpath, exist_ok=True)
    result = {}
    step = 0

    # draw(G, os.path.join(logpath, f"graph_{step}.png"))

    result[step] = negativelog(nx.number_connected_components(G))
    n_nodes = G.number_of_nodes()
    init_gc_size = giant_component_size(G)
    result[step] = 1 


    step += 1
    while G.number_of_nodes() > 0:
        # delete the node with the smallest degree
        min_degree_node = min(G.degree, key=lambda x: x[1])[0]
        G.remove_node(min_degree_node)
        # check if the graph is still connected
        if nx.number_connected_components(G) == 0:
            # if there is no more connected component, set the value to be the total number of nodes in the initial graph
            result[step] = 0
        else:
            # here nx.number_connected_components is supposedly positive integer at least 1.
            # but negativelog function returns 0 for negative values just in case
            result[step] = giant_component_size(G) / init_gc_size

        # draw(G, os.path.join(logpath, f"graph_{step}.png"))

        step += 1

    return result
        

def analyze(filepath, logpath, filetype="gexf"):
    """
    Analyze a graph and return the result in a dictionary.
    Parameters
    ----------
    filepath : str
        The path to the graph file.
    logpath : str
        The path to the log directory.
    filetype : str
        The type of the graph file. Can be 'gexf' or 'adjlist'.
    """

    if filetype not in ["gexf", "adjlist"]:
        raise ValueError(f"{filetype} not supported. Use one of ['gexf', 'adjlist']")
    filepath = str(filepath)
    title = filepath.split("/")[-1].split(".")[0]
    result = {}
    
    
    if filetype == "gexf":
        G = nx.read_gexf(filepath)
    elif filepath == "adjlist":
        G = nx.read_adjlist(filepath)

    G: nx.Graph
    
    # change polarity value based on the label
    for u, v, data in G.edges(data=True):
        if data.get('label') == 'NEGATIVE':
            data['polarity'] = -1
        elif data.get('label') == 'POSITIVE':
            data['polarity'] = 1

    result["title"] = title
    result['path'] = filepath
    result["num_nodes"] = G.number_of_nodes()
    result["num_edges"] = G.number_of_edges()

    # original graph
    result['original'] = {}

    # network level
    result['original']['average_degree'] = average_degree(G, weight=None)
    result['original']['weighted_average_degree'] = average_degree(G, weight='polarity')
    result['original']['density'] = nx.density(G)
    result['original']['average_clustering'] = nx.average_clustering(G, weight=None)
    result['original']['assortativity_coefficient'] = nx.degree_pearson_correlation_coefficient(G, weight="polarity")  
    # pearson correlation coefficient is the same as assortativity coefficient but potentially speeds up the calculation
    # https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.assortativity.degree_pearson_correlation_coefficient.html#networkx.algorithms.assortativity.degree_pearson_correlation_coefficient

    # node level centrality
    result['original']['betweenness_centrality'] = nx.betweenness_centrality(G, weight=None)
    result['original']['closeness_centrality'] = nx.closeness_centrality(G, distance=None)
    result['original']['degree_centrality'] = nx.degree_centrality(G)
    result['original']['degree_distribution'] = degree_distribution(G, weight=None)

    ### positive subgraph ###
    PG = subgraph(G, label='POSITIVE')
    result['positive'] = {}
    # network level
    result['positive']['average_degree'] = average_degree(PG, weight=None)
    result['positive']['density'] = nx.density(PG)
    result['positive']['average_clustering'] = nx.average_clustering(PG, weight=None)
    result['positive']['robustness'] = robustness_smalldegree_neglogcomp(PG, logpath/"pos")

    # node level centrality
    result['positive']['betweenness_centrality'] = nx.betweenness_centrality(PG, weight=None)
    result['positive']['closeness_centrality'] = nx.closeness_centrality(PG, distance=None)
    result['positive']['degree_centrality'] = nx.degree_centrality(PG)
    result['positive']['degree_distribution'] = degree_distribution(PG, weight=None)

    ### negative subgraph ###
    result['negative'] = {}
    NG = subgraph(G, label='NEGATIVE')
    # network level
    result['negative']['average_degree'] = average_degree(NG, weight=None)
    result['negative']['density'] = nx.density(NG)
    result['negative']['average_clustering'] = nx.average_clustering(NG, weight=None)
    result['negative']['robustness'] = robustness_smalldegree_neglogcomp(NG, logpath/"neg")

    # node level centrality
    result['negative']['betweenness_centrality'] = nx.betweenness_centrality(NG, weight=None)
    result['negative']['closeness_centrality'] = nx.closeness_centrality(NG, distance=None)
    result['negative']['degree_centrality'] = nx.degree_centrality(NG)
    result['negative']['degree_distribution'] = degree_distribution(NG, weight=None)


    os.makedirs(logpath, exist_ok=True)
    # save the result to a json file
    with open(os.path.join(logpath, f"{title}.json"), 'w') as f:
        json.dump(result, f, indent=4)
    # save the result to a yaml file
    with open(os.path.join(logpath, f"{title}.yaml"), 'w') as f:
        yaml.dump(result, f)

    # # save the graph to a gexf file
    # nx.write_adjlist(G, os.path.join(logpath, f"{title}_original.adjlist"))
    # nx.write_gexf(G, os.path.join(logpath, f"{title}_original.gexf"))
    # # save the positive subgraph to a gexf file
    # nx.write_adjlist(PG, os.path.join(logpath, f"{title}_positive.adjlist"))
    # nx.write_gexf(PG, os.path.join(logpath, f"{title}_positive.gexf"))
    # # save the negative subgraph to a gexf file
    # nx.write_adjlist(NG, os.path.join(logpath, f"{title}_negative.adjlist"))
    # nx.write_gexf(NG, os.path.join(logpath, f"{title}_negative.gexf"))

    return result, G, PG, NG

if __name__ == "__main__":
    pt = PathTools()
    PATH = pt.get_target_dir("data/networks/llm_ss")
    title = "Echoes of the Singularity_4.gexf"
    result, G = analyze(PATH/title, logpath=None, filetype="gexf")
    G: nx.Graph

    print(result)
    print(G.edges)
    
    

    
    
    
    