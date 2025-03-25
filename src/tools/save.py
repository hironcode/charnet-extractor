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
        # print(f"gexf file doesn't support comments", end='\r')
        nx.write_gexf(graph, path)