import pandas as pd
import dash
from dash import Input, Output, dcc, html, ctx, callback
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

dash.register_page(__name__, path='/', name='General') # '/' is home page

itinerarios_bases = pd.read_parquet('./Data/Itinerarios/itinerarios_bases.parquet')

layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Dropdown(options=itinerarios_bases.Distrito_Salida.unique(),
                                     id='cont-choice')
                    ], xs=10, sm=10, md=8, lg=4, xl=4, xxl=4
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Graph(id='line-fig',
                                  figure=px.histogram(itinerarios_bases, x='Distrito_Salida',
                                                      y='travel_time',
                                                      histfunc='avg'))
                    ], width=12
                )
            ]
        )
    ]
)

@callback(
    Output('line-fig', 'figure'),
    Input('cont-choice', 'value')
)
def update_graph(value):
    if value is None:
        fig = px.histogram(itinerarios_bases, x='Distrito_Salida', y='travel_time', histfunc='avg')
    else:
        dff = itinerarios_bases[itinerarios_bases.Distrito_Salida==value]
        fig = px.histogram(dff, x='Barrio_Salida', y='travel_time', histfunc='avg')
    return fig
