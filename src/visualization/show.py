import networkx as nx
import matplotlib.pyplot as plt
from src.tools.charnet import CharNet
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import seaborn as sns


def show_graph(graph: CharNet, pos, label:str, label_map=None, graph_type="polarity", path_to_save: str=None, node_size=1000, font_size=12) -> None:
    """
    Save a graph as an image
    :param graph: graph to save
    :param pos: layout of the graph
    :param label: edge label to show on the graph
    :param label_map: dictionary mapping the node id to the node label i.e. {1: "Alice", 2: "Bob"}
    :param graph_type: type of the graph
    :param path_to_save: path to save the graph
    """

    weights:dict = nx.get_edge_attributes(graph, label)
    if weights:
        norm = mcolors.Normalize(vmin=min(weights.values()), vmax=max(weights.values()))
        edge_colors = [cm.coolwarm(norm(w)) for w in weights.values()]
    else:
        edge_colors = 'gray'

    # low resolution for displaying

    # plt.figure(figsize=(6, 6), dpi=100)  # Increase figure size and DPI

    # nx.draw(
    #     graph,
    #     pos,
    #     with_labels=True,
    #     labels=label_map,
    #     node_color='skyblue',
    #     node_size=node_size,
    #     edge_color=edge_colors,
    #     width=2,
    #     edge_cmap=cm.coolwarm,
    #     font_size=font_size
    # )
    # # nx.draw(graph, pos, labels=label_map, with_labels=True, node_size=node_size, node_color="skyblue", font_size=font_size)

    # # edge_labels:dict = nx.get_edge_attributes(graph, label)
    # # if graph_type in ["polarity"]:
    # #     # get the first letter of the edge labels: i.e. "positive" -> "p" except for "neutral" -> "neu"
    # #     for k, v in edge_labels.items():
    # #         if 'neutral' in v:
    # #             edge_labels[k] = 'neu'
    # #         else:
    # #             edge_labels[k] = v[0]
    # # nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_color='red')
    # plt.title(f'{graph_type} graph for "{graph.narrative_units.title}"')

    # plt.show()

    #####################
    # High resolution for image saving
    plt.figure(figsize=(8, 8), dpi=200)  # Increase figure size and DPI

    nx.draw(
        graph,
        pos,
        with_labels=True,
        labels=label_map,
        node_color='skyblue',
        node_size=node_size,
        edge_color=edge_colors,
        width=2,
        edge_cmap=cm.coolwarm,
        font_size=font_size
    )

    if path_to_save:
        plt.savefig(path_to_save, dpi=300, bbox_inches='tight')
        # print(f"Graph image saved at {path_to_save}")
        plt.close()


def plot_robust(l: list[list], savepath):
    # convert list of lists to a list of dictionaries
    # l = [dict(i, rob[i]) for rob in l for i in range(len(rob))]
    
    # normalize length
    max_length = max([len(i) for i in l])
    new_l = []
    for rob in l:
        # new interval of each step
        intvl_factor = max_length / len(rob)
        new_rob = {}
        for step, v in rob.items():
            new_rob[int(step) * intvl_factor] = v
        new_l.append(new_rob)

    # plot
    plt.figure(figsize=(15, 8))
    plt.xlabel("Step (normalized)")
    plt.ylabel("Robustness")
    for rob in new_l:
        sns.lineplot(x=rob.keys(), y=rob.values())

    plt.savefig(savepath)