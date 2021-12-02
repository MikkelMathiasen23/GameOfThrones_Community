import json
import networkx as nx
import pandas as pd

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

from data_methods import make_figure
from data_methods import create_thumbnail
from fa2 import ForceAtlas2

# from skimage import io
import random
import os
import gunicorn
from whitenoise import WhiteNoise

from PIL import Image
import requests
import pickle
from io import BytesIO

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
config_thumbnail = {'staticPlot': True}

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

styles = {'pre': {'border': 'thin lightgrey solid', 'overflowY': 'scroll'}}

# os.chdir('network_app/')
network = nx.read_gpickle("got_G.gpickle")
with open('link_partition.pickle', 'rb') as handle:
    links = pickle.load(handle)


def compute_positions(network):

    forceatlas2 = ForceAtlas2(
        # Behavior alternatives
        outboundAttractionDistribution=True,  # Dissuade hubs
        edgeWeightInfluence=1,

        # Performance
        jitterTolerance=0.2,  # Tolerance
        barnesHutOptimize=True,
        barnesHutTheta=0.5,
        multiThreaded=False,  # NOT IMPLEMENTED

        # Tuning
        scalingRatio=10.0,
        strongGravityMode=False,
        gravity=0.01,

        # Log
        verbose=True)

    positions = forceatlas2.forceatlas2_networkx_layout(G=network,
                                                        pos=None,
                                                        iterations=2000)
    return positions


random.seed(1)
positions = compute_positions(network)
attribute = 'religion'

edge_traces, node_traces = make_figure(network, attribute, positions)

layout = go.Layout(
    paper_bgcolor='rgba(0,0,0,0)',  # transparent background
    plot_bgcolor='rgba(0,0,0,0)',  # transparent 2nd background
    xaxis={
        'showgrid': False,
        'zeroline': False
    },  # no gridlines
    yaxis={
        'showgrid': False,
        'zeroline': False
    },  # no gridlines
)

#Create figure
fig = go.Figure(layout=layout)
thumbnail = go.Figure(layout=layout)

# Add all edge traces
for trace in edge_traces:
    fig.add_trace(trace)  # Add node trace
for trace in node_traces:
    fig.add_trace(trace)

fig.update_xaxes(showticklabels=False)
fig.update_yaxes(showticklabels=False)
fig.update_layout(clickmode='event+select')

app.layout = html.Div([
    dcc.Graph(id='computed_figure', figure=fig, style={'height': '70vh'}),
    html.Div(
        className='row',
        children=[
            html.Div([
                dcc.Markdown("""
                **Community selection**
                Select a community to view the corresponding network.
            """),
                dcc.Dropdown(id="com_dropdown_menu",
                             options=[{
                                 'label': 'Community 0',
                                 'value': '0'
                             }, {
                                 'label': 'Community 1',
                                 'value': '1'
                             }, {
                                 'label': 'Community 2',
                                 'value': '2'
                             }, {
                                 'label': 'Community 3',
                                 'value': '3'
                             }, {
                                 'label': 'Community 4',
                                 'value': '4'
                             }, {
                                 'label': 'Community 5',
                                 'value': '5'
                             }],
                             value='0'),
                html.Pre(id='com_dropdown', style=styles['pre'])
            ],
                     className='three columns'),
            html.Div([
                dcc.Markdown("""
                **Graph attribute overlay**
                Select attribute overlay of the graph.
            """),
                dcc.Dropdown(id="attribute_dropdown_menu",
                             options=[{
                                 'label': 'Allegiance',
                                 'value': 'allegiance'
                             }, {
                                 'label': 'Religion',
                                 'value': 'religion'
                             }, {
                                 'label': 'Culture',
                                 'value': 'culture'
                             }],
                             value='religion'),
                html.Pre(id='attribute_dropdown', style=styles['pre']),
            ],
                     className='three columns'),
            html.Div([
                dcc.Markdown("""
                **Click Data**
                Click on points in the graph to show meta data and the characters most frequently used words according to Term Frequency Inverse Document Count.
            """),
                html.Pre(id='click-data', style=styles['pre']),
            ],
                     className='three columns'),
            html.Div(
                [
                    dcc.Markdown("""
                **Character Image**
            """),
                    dcc.Graph(id='selected-data', figure=thumbnail),
                    #html.Pre(id='selected-data', style=styles['pre']),
                ],
                className='three columns'),
        ])
])


@app.callback(Output('computed_figure', 'figure'), [
    Input('com_dropdown_menu', 'value'),
    Input('attribute_dropdown_menu', 'value')
])
def display_figure(com_dropdown_menu, attribute_dropdown_menu):

    network = nx.read_gpickle("got_G.gpickle")
    network = network.subgraph(links[int(com_dropdown_menu)])

    attribute = attribute_dropdown_menu
    random.seed(1)
    positions = compute_positions(network)

    edge_traces, node_traces = make_figure(network, attribute, positions)

    # Create figure
    fig = go.Figure(layout=layout)

    # Add all edge traces
    for trace in edge_traces:
        fig.add_trace(trace)  # Add node trace
    for trace in node_traces:
        fig.add_trace(trace)

    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    fig.update_layout(clickmode='event+select')

    return fig


@app.callback(
    [Output('click-data', 'children'),
     Output('selected-data', 'figure')], Input('computed_figure', 'clickData'))
def display_click_data(clickData):
    if clickData is not None:
        path = clickData['points'][0]['meta']
        response = requests.get(path)
        img = Image.open(BytesIO(response.content))
        thumbnail = create_thumbnail(img)

        return clickData['points'][0]['customdata'], thumbnail

    path = "https://static.wikia.nocookie.net/gameofthrones/images/c/c8/Iron_throne.jpg/revision/latest/scale-to-width-down/334?cb=20131005175755"
    response = requests.get(path)
    img = Image.open(BytesIO(response.content))
    thumbnail = create_thumbnail(img)
    return json.dumps(clickData, indent=2), thumbnail


server = app.server
server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/')
