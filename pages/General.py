import pandas as pd
import dash
from dash import Input, Output, dcc, html, callback
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import timedelta, date, datetime
import funciones1 as F1

dash.register_page(__name__, path='/', name='General') # '/' is home page

itinerarios_bases = pd.read_parquet('./Data/Itinerarios/itinerarios_bases.parquet')
itinerarios_bases["unplug_hourTime"] = pd.to_datetime(itinerarios_bases["unplug_hourTime"])
itinerarios_bases = itinerarios_bases[itinerarios_bases["unplug_hourTime"].dt.tz_localize(None)>pd.to_datetime("20190801")]

today = pd.to_datetime(date(2019,12,12))

card = dbc.Card(
    [dbc.CardHeader("Distribución de las edades por tipo de usuario", style = {"background-color":"#ecf0f1"}), 
    dbc.CardBody("Body")], className="h-100"
)

cardAge = dbc.Card(
    [
        dbc.CardHeader("Duración viajes por edad y tipo de usuario", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody([
            dbc.Row([
                dcc.RangeSlider(0, 1440,
                    id='traveltime-slider',
                    marks={
                        0: {'label': '0h'},
                        180: {'label': '3h'},
                        720: {'label': '12h'},
                        1440: {'label': '1d', 'style': {'color': '#f50'}},
                        #2880: {'label': '2d', 'style': {'color': '#f50'}},
                    },
                    value=[1, 180],
                    dots=False,
                    step=1,
                    updatemode='drag'
                ),
            ]),
            html.Div(id="edades-display")
        ])
    ], className="h-100"
)
@callback(
    Output("edades-display", "children"),
    Input("traveltime-slider", "value")
)
def display_edades(value):
    #transformed_value = [F1.transform_value(v) for v in value]
    return [
        dbc.Row(
            children = [
                dcc.Graph(figure = F1.pyramidDisplay(itinerarios_bases, value), config={'displayModeBar': False})
            ]
        ),
    ]

cardGauge = dbc.Card(
    [
        dbc.CardHeader("Situación de las bicicletas en los que llevamos de semana",  style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody([
            dbc.Row([
                dbc.RadioItems(
                    id="btn-status",
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-primary",
                    labelCheckedClassName="active",
                    options=[
                        {"label": "Bicis perdidas", "value": "long_rental"},
                        {"label": "Bicis defectuosas", "value": "change_bike"},
                        {"label": "Alquileres exitosos", "value": "short_rental"},
                    ],
                    value="long_rental",
                ),
            ]),
            html.Div(id="status-display")
        ])
    ], className="h-100"
)

@callback(
    Output("status-display", "children"),
    Input("btn-status", "value")
)
def display_status(value):
    return [
        dbc.Row(
                children = [
                    dcc.Graph(figure = F1.gaugeDisplay(itinerarios_bases, today, value), config={'displayModeBar': False})
                ]
            ),
            dbc.Row(
                children = [
                    dcc.Graph(figure = F1.timelineDisplay(itinerarios_bases, today, value), config={'displayModeBar': False})
                ]
            )
    ]

graph_card = dbc.Card(
    [dbc.CardHeader("Here's a graph"), dbc.CardBody("An amazing graph")],
    className="h-100",
)

layout = dbc.Container(
    children = [
            dbc.Row([
                dbc.Col([
                    dbc.Col(html.Div(html.H2("General", style={"color":"#18bc9c", "vertical-align":"middle"}))),
                    dbc.Col(html.P(html.P(today.strftime("%d %B, %Y %I%p"),style={"color":"#18bc9c", "vertical-align":"middle"})))
                ], width = 3, style = {"padding":"1rem 1rem"})
            ]),

            html.Hr(),

            dbc.Row([
                dbc.Col([
                    dbc.Row([
                        dbc.Col(cardGauge, width = 8),
                        dbc.Col(cardAge, width = 4), 
                    ], style = {"height":"450px"}),
                    html.H2("sldfasfdjlaskfjasf"),
                    dbc.Row([
                        dbc.Col(graph_card)
                    ]*2, style = {"height":"400px"})
                ], width = 10),

                dbc.Col(card, width=2)
            ], justify = "center")
    ]  ,
    fluid = True,
    className="mt-3"
)
