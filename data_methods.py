import pandas as pd
import numpy as np
import networkx as nx
from itertools import cycle
from fa2 import ForceAtlas2

import plotly.graph_objects as go
import plotly.express as px


def graph_preprocessing(network, attribute):
    """
    network:    unpickled network graph
    attribute:  string
    """

    palette = cycle(px.colors.qualitative.Alphabet)

    attribute_group = np.unique([
        *list(dict(nx.get_node_attributes(network, attribute)).values())
    ]).tolist()
    attribute_to_number = dict(
        zip(attribute_group, np.arange(len(attribute_group))))
    culture_colors = [
        attribute_to_number[attributes[attribute]]
        for n, attributes in network.nodes(data=True)
    ]

    palette = cycle(px.colors.qualitative.Alphabet)
    attribute_color_lst = [
        next(iter(palette)) for i in range(len(attribute_group))
    ]
    attribute_color_dict = dict(zip(attribute_group, attribute_color_lst))

    node_sizes = [int(network.degree(n)) for n in network.nodes()]
    max_node_size = np.max(node_sizes)
    min_node_size = np.min(node_sizes)
    degree_dict_plotly = dict(
        zip(list(network.nodes()),
            [(50 - 10) / (max_node_size - min_node_size) *
             (node_size - max_node_size) + 50 for node_size in node_sizes]))

    #edge_sizes = list(nx.get_edge_attributes(network, 'weight'))
    edge_sizes = [network.edges()[edge]['weight'] for edge in network.edges()]
    max_edge_size = np.max(edge_sizes)
    min_edge_size = np.min(edge_sizes)
    edge_width_dict_plotly = dict(
        zip(list(network.edges()),
            [(15 - 2) / (max_edge_size - min_edge_size) *
             (edge_size - max_edge_size) + 15 for edge_size in edge_sizes]))

    node_dict = network.nodes(data=True)
    attribute_edge_colors = []

    for edge in network.edges():
        attribute_edge_colors.append(
            attribute_to_number[node_dict[edge[0]][attribute]])

    return attribute_group, attribute_color_dict, degree_dict_plotly, edge_width_dict_plotly


def make_edge(x, y, text, width, opacity):
    return go.Scatter(x=x,
                      y=y,
                      line=dict(width=width, color='cornflowerblue'),
                      hoverinfo='text',
                      text=([text]),
                      mode='lines',
                      showlegend=False,
                      opacity=opacity)


def make_figure(network, attribute, positions):

    attribute_group, attribute_color_dict, degree_dict_plotly, edge_width_dict_plotly = graph_preprocessing(
        network, attribute)
    node_dict = network.nodes(data=True)

    edge_widths = nx.get_edge_attributes(network, 'weight')
    alphas = (0.8 - 0.05) / (np.max(list(edge_widths.values())) - np.min(
        list(edge_widths.values()))) * (list(edge_widths.values()) - np.max(
            list(edge_widths.values()))) + 0.8
    opacity_dict = dict(zip(list(edge_widths.keys()), alphas))

    # Create edge traces
    edge_traces = []
    for edge in network.edges():

        if network.edges()[edge]['weight'] > 0:
            char_1 = edge[0]
            char_2 = edge[1]
            x0, y0 = positions[char_1]
            x1, y1 = positions[char_2]
            text = char_1 + '--' + char_2 + ': ' + str(
                network.edges()[edge]['weight'])
            opacity = opacity_dict[edge]

            trace = make_edge(
                [x0, x1, None],
                [y0, y1, None],
                text,
                width=edge_width_dict_plotly[
                    edge],  #network.edges()[edge]['weight']*0.2
                opacity=opacity)

            edge_traces.append(trace)

    # Create node traces
    node_traces = []
    for group in attribute_group:
        node_trace = go.Scatter(x=[],
                                y=[],
                                text=[],
                                textposition="top center",
                                textfont_size=10,
                                mode='markers+text',
                                showlegend=True,
                                hoverinfo='text',
                                name=group,
                                hovertext=[],
                                meta=[],
                                customdata=[],
                                marker=dict(color=[], size=[], line=None))

        for node, attributes in network.nodes(data=True):
            if attributes[attribute] == group:

                x, y = positions[node]
                node_trace['x'] += tuple([x])
                node_trace['y'] += tuple([y])
                color_key = node_dict[node][attribute]
                node_trace['marker']['color'] += tuple(
                    [attribute_color_dict[color_key]])
                node_trace['marker']['size'] += tuple(
                    [degree_dict_plotly[node]])
                node_trace['hovertext'] += tuple([node.replace(
                    '_', ' ')])  #tuple([attributes['text']])
                node_trace['text'] += tuple([node.replace('_', ' ')])
                node_trace['customdata'] += tuple([attributes['text']])
                node_trace['meta'] += tuple([attributes['thumbnail']])
        node_traces.append(node_trace)

    return edge_traces, node_traces


def create_thumbnail(img_src):
    # Create figure
    fig = go.Figure()

    # Constants
    img_width = 200
    img_height = 300
    scale_factor = 0.5

    # Add invisible scatter trace.
    # This trace is added to help the autoresize logic work.
    fig.add_trace(
        go.Scatter(x=[0, img_width * scale_factor],
                   y=[0, img_height * scale_factor],
                   mode="markers",
                   marker_opacity=0))

    # Configure axes
    fig.update_xaxes(visible=False, range=[0, img_width * scale_factor])

    fig.update_yaxes(
        visible=False,
        range=[0, img_height * scale_factor],
        # the scaleanchor attribute ensures that the aspect ratio stays constant
        scaleanchor="x")

    # Add image
    fig.add_layout_image(
        dict(x=0,
             sizex=img_width * scale_factor,
             y=img_height * scale_factor,
             sizey=img_height * scale_factor,
             xref="x",
             yref="y",
             opacity=1.0,
             layer="below",
             sizing="stretch",
             source=img_src))

    # Configure other layout
    fig.update_layout(
        width=img_width * scale_factor,
        height=img_height * scale_factor,
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0
        },
    )

    return fig