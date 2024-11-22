import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Any, Tuple, List
from src.tools.charnet import CharNet

def save_graph(graph: CharNet, format:str="gexf", comment:str='', path: str="") -> None:
    """
    Save a graph as a gexf file
    :param graph: graph to save
    :param format: format to save the graph
    :param path: path to save the graph
    """
    formats = ["adjlist", "gexf"]
    if format not in formats:
        raise ValueError(f"{format} format not supported. Use one of {formats}")

    if format == "adjlist":
        nx.write_adjlist(graph, path, comments=comment)
    elif format ==  "gexf":
        nx.write_gexf(graph, path, comment=comment)

def show_graph(graph: CharNet, pos, label:str, label_map:Dict=None, graph_type="polarity", path_to_save: str=None) -> None:
    """
    Save a graph as an image
    :param graph: graph to save
    :param pos: layout of the graph
    :param label: edge label to show on the graph
    :param label_map: dictionary mapping the node id to the node label i.e. {1: "Alice", 2: "Bob"}
    :param graph_type: type of the graph
    :param path_to_save: path to save the graph
    """
    nx.draw(graph, pos, labels=label_map, with_labels=True, node_size=1000, node_color="skyblue", font_size=12)
    edge_labels:dict = nx.get_edge_attributes(graph, label)
    if graph_type in ["polarity"]:
        # get the first letter of the edge labels: i.e. "positive" -> "p" except for "neutral" -> "neu"
        for k, v in edge_labels.items():
            if 'neutral' in v:
                edge_labels[k] = 'neu'
            else:
                edge_labels[k] = v[0]
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_color='red')
    plt.title(f'{graph_type} graph for "{graph.narrative_units.title}"')

    if path_to_save:
        plt.savefig(path_to_save)
        print(f"Graph image saved at {path_to_save}")

    plt.show()




