import pandas as pd
import dash
from dash import Input, Output, dcc, html, callback
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import timedelta, date, datetime
import funciones1 as F1
from io import BytesIO
import base64

dash.register_page(__name__, path='/', name='General') # '/' is home page

itinerarios_bases = pd.read_parquet('./Data/Itinerarios/itinerarios_bases.parquet')
itinerarios_bases["unplug_hourTime"] = pd.to_datetime(itinerarios_bases["unplug_hourTime"])
itinerarios_bases = itinerarios_bases[itinerarios_bases["unplug_hourTime"].dt.tz_localize(None)>pd.to_datetime("20190801")]

today = pd.to_datetime(date(2019,12,12))

cardAlert = dbc.Card(
    [dbc.CardHeader("Alertas situación estaciones", style = {"background-color":"#ecf0f1"}), 
    dbc.CardBody("Aquí va una lista del día y la hora en que ciertas estaciones están completas o por el contrrio, vacías.")], className="h-100"
)

cardTable = dbc.Card(
    [dbc.CardHeader("Tabla métircas", style = {"background-color":"#ecf0f1"}), 
    dbc.CardBody("Aquí va una tabla de infrmación importante. Aún no se cual")], className="h-100"
)

cardAge = dbc.Card(
    [
        dbc.CardHeader("Duración viajes por edad y tipo de usuario", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody([
            dbc.Row([
                dcc.RangeSlider(1, 1440,
                    id='traveltime-slider',
                    marks={
                        1: {'label': '1min'},
                        180: {'label': '3h'},
                        360: {'label': '6h'},
                        540: {'label': '9h'},
                        720: {'label': '12h'},
                        1080: {'label': '18h'},
                        1440: {'label': '1d', 'style': {'color': '#2c3e50'}},
                    },
                    value=[1, 1440],
                    dots=False,
                    step=1,
                    updatemode='drag',
                    #className = "m-4"
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

cardDemandaHoras = dbc.Card(
    [
        dbc.CardHeader("Demanda media por horas", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody(dcc.Graph(figure = F1.estacionalidadHoras(itinerarios_bases)))
    ], className="h-100"
)

cardDemandaDias = dbc.Card(
    [
        dbc.CardHeader("Demanda media por día de la semana", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody(dcc.Graph(figure = F1.estacionalidadDias(itinerarios_bases)))
    ], className="h-100"
)

cardDemandaMeses = dbc.Card(
    [
        dbc.CardHeader("Demanda media por mes", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody(dcc.Graph(figure = F1.estacionalidadMeses(itinerarios_bases)))
    ], className="h-100"
)


cardMap = dbc.Card(
    [
        dbc.CardHeader("Estaciones BiciMAD por distrito", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody([
            dbc.Row([
                dcc.Dropdown(
                    id="select-distrito",
                    options = itinerarios_bases.Distrito_Salida.unique(),
                    multi=True,
                    style={"color": "#2c3e50", "width":"80%"}
                )
            ]),
            html.Div(id="map-display", style = {"padding": "1rem", "width" : "100%"})
        ])
    ],
    className="h-100",
)
@callback(
    Output("map-display", "children"),
    Input("select-distrito", "value")
)
def displayMap(value):
    if (value == None) | (value == []):
        return [
        dbc.Row([
            dcc.Graph(figure = F1.mapDisplay(itinerarios_bases, itinerarios_bases.Distrito_Salida.unique()), config={'displayModeBar': False})
        ])
    ]
    else:
        return [
            dbc.Row([
                dcc.Graph(figure = F1.mapDisplay(itinerarios_bases, value), config={'displayModeBar': False})
            ])
        ]

cardCloud = dbc.Card(
    [
        dbc.CardHeader("Estaciones más frecuentadas", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody([
            html.Div(id="wordcloud-display",
                children =[
                    dbc.Row(
                        children = [
                            #dcc.Graph(figure = F1.wordcloudDisplay(itinerarios_bases), config={'displayModeBar': False}, style = {"padding": "1rem", "width" : "100%"})
                            html.Img(id="image_wc")
                        ]
                    ),
                ])
        ])
    ], className="h-100", 
)
@callback(Output('image_wc', 'src'), [Input('image_wc', 'id')])
def make_image(b):
    img = BytesIO()
    F1.wordcloudDisplay2(itinerarios_bases).save(img, format='PNG')
    return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())
# @callback(
#     Output("wordcloud-display", "children"),
#     Input("traveltime-slider", "value")
# )
# def displayWordCloud(itinerarios_bases):
#     return [
#         dbc.Row(
#             children = [
#                 dcc.Graph(figure = F1.wordcloudDisplay(itinerarios_bases), config={'displayModeBar': False})
#             ]
#         ),
#     ]

cardTopRutas = dbc.Card(
    [
        dbc.CardHeader("Rutas Más Concurridas", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody([
            dbc.Row([
                dcc.Dropdown(
                    id="select-Rutasdistrito",
                    options = itinerarios_bases.Distrito_Salida.unique(),
                    multi=True,
                    style={"color": "#2c3e50", "width":"80%"}
                )
            ]),
            html.Div(id="mapRutas-display", style = {"padding": "1rem", "width" : "100%"})
        ])
    ],
    className="h-100",
)
@callback(
    Output("mapRutas-display", "children"),
    Input("select-Rutasdistrito", "value")
)
def displayRutasMap(value):
    if (value == None) | (value == []):
        return [
        dbc.Row([
            dcc.Graph(figure = F1.mapRutasDisplay(itinerarios_bases, itinerarios_bases.Distrito_Salida.unique()), config={'displayModeBar': False})
        ])
    ]
    else:
        return [
            dbc.Row([
                dcc.Graph(figure = F1.mapRutasDisplay(itinerarios_bases, value), config={'displayModeBar': False})
            ])
        ]


cardSunburstItinerarios = dbc.Card(
    [
        dbc.CardHeader("Distribución Top Itinerarios", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody(dcc.Graph(figure = F1.sunburstItinerarios(itinerarios_bases, 5,10)))
    ], className="h-100"
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
                    html.Div(
                        html.H3("Estacionalidad", style={"color":"#2c3e50", "padding-top":"3rem"}),
                    ),
                    dbc.Row([
                        dbc.Col(cardDemandaHoras, width = 4),
                        dbc.Col(cardDemandaDias, width = 4),
                        dbc.Col(cardDemandaMeses, width = 4),
                    ]),
                ]),
                dbc.Col(cardAlert, width=2)
            ], justify = "center"),

            dbc.Row([
                html.Div(
                        html.H3("Análisis estaciones y rutas", style={"color":"#2c3e50", "padding-top":"3rem"}),
                ),
                dbc.Col([
                    html.Div(
                        dbc.Accordion([
                            dbc.AccordionItem(
                                title = "Estaciones", 
                                # style ={"background-color": "black"},
                                children = [
                                    dbc.Row([
                                        dbc.Col(cardMap, width = 6, style = {"height":"800px"}),
                                        dbc.Col([
                                            dbc.Card(cardCloud, style = {"height":"400px", "margin-bottom": "5px"}),
                                            dbc.Card(cardTable, style = {"height":"395px", "margin-top": "5px"})
                                        ],width = 6)
                                    ], ),
                                ]
                            ),
                            dbc.AccordionItem(
                                title = "Rutas", 
                                children = [
                                    dbc.Row([
                                        dbc.Col(cardTopRutas, width = 6, style = {"height":"800px"}),
                                        dbc.Col(cardSunburstItinerarios, width = 6, style = {"height":"800px"})
                                    ], ),
                                ]
                            ),
                        ], always_open = True)
                    )                     
                ], width = 12),
            ],  justify = "center", style = {"padding-bottom": "2rem"})
    ]  ,
    fluid = True,
    className="mt-3"
)
