import pandas as pd
import numpy as np
import dash
from dash import Input, Output, dcc, html, callback, dash_table
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import timedelta, date, datetime
import funciones1 as F1
from io import BytesIO
import base64

dash.register_page(__name__, path='/', name='General') # '/' is home page

itinerarios_bases = pd.read_parquet('./Data/Itinerarios/itinerarios_bases3.parquet')
itinerarios_bases["unplug_hourTime"] = pd.to_datetime(itinerarios_bases["unplug_hourTime"])
itinerarios_bases = itinerarios_bases[itinerarios_bases["unplug_hourTime"].dt.tz_localize(None)>pd.to_datetime("20190801")]
itinerarios_bases["typeofday"] = np.where(itinerarios_bases["dayofweek"].isin([5,6]), 0, 1)

situaciones = pd.read_parquet('Data/SituacionEstaciones/situaciones2.parquet')

# situaciones1 = situaciones[situaciones["hour"]>5]
# situaciones1["hour"] = situaciones1["hour"].replace([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],["12am","1am","2am", "3am", "4am", "5am", "6am", "7am", "8am", "9am", "10am", "11am","12pm", "1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm", "8pm", "9pm", "10pm","11pm"])
# situaciones1 = situaciones1.drop(situaciones1[(situaciones1.free_bases == 0) & (situaciones1.dock_bikes == 0)].index)
# situaciones1["occupancyRate"] = situaciones1['dock_bikes']/situaciones1['total_bases']*100
# situaciones_grouped = situaciones1.groupby(["hour", "number", "name"], as_index=False).agg({"free_bases":"mean", "dock_bikes":"mean", "_id": "count", "occupancyRate":"median"})
# occupancyHigh = situaciones_grouped[situaciones_grouped["occupancyRate"]>75]
# occupancyLow = situaciones_grouped[situaciones_grouped["occupancyRate"]<10]

situaciones["occupancyRate"] = situaciones['dock_bikes']/situaciones['total_bases']*100
situaciones["hour"] = situaciones["hour"].replace([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],["12am","1am","2am", "3am", "4am", "5am", "6am", "7am", "8am", "9am", "10am", "11am","12pm", "1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm", "8pm", "9pm", "10pm","11pm"])
situaciones["number"] = situaciones["number"].astype(str)
occupancyHigh = situaciones[situaciones["occupancyRate"]>80].groupby(["hour", "number", "name"], as_index=False).agg({"free_bases":"mean", "dock_bikes":"mean", "_id": "count"})
occupancyLow = situaciones[situaciones["occupancyRate"]<20].groupby(["hour", "number", "name"], as_index=False).agg({"free_bases":"mean", "dock_bikes":"mean", "_id": "count"})
occupancyLow = occupancyLow.drop(occupancyLow[(occupancyLow.free_bases == 0) & (occupancyLow.dock_bikes == 0)].index)
occupancyHigh = occupancyHigh[occupancyHigh["_id"]>80]
occupancyLow = occupancyLow[occupancyLow["_id"]>90]


today = pd.to_datetime(date(2019,12,12))

cardAlert = dbc.Card(
    [
        dbc.CardHeader("Alertas situación estaciones", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody([
            dbc.Row([
                dcc.Dropdown(
                    id="dropdown-occupancy",
                    options=[
                        {"label": "Alta ocupación", "value": "highOccupancy"},
                        {"label": "Baja ocupación", "value": "lowOccupancy"},
                    ],
                    value="highOccupancy",
                ),
            ], style={"padding-bottom":"0.5rem"}), 
            html.Div(id='dash-table'),
            html.Div(id='datatable-interactivity-container')
        ])
        
    ], className="h-100"
)


@callback(
    Output('dash-table', "children"),
    [Input('dropdown-occupancy', "value"), 
    Input("typeofday-checklist", "value")]
)
def display_table(value, typeofday):
    if(value == "highOccupancy"):
        data = occupancyHigh.to_dict('records')
    else:
        data = occupancyLow.to_dict('records')
    
    return [
        dash_table.DataTable(
                    id='alertTable',
                    columns = [{"name": "id", "id": "number"},
                            {"name": "hora", "id": "hour"}],
                    data=data,
                    #editable=True,
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    #column_selectable="single",
                    row_selectable="single",
                    #row_deletable=True,
                    #selected_columns=[],
                    selected_rows=[0],
                    page_action="native",
                    page_current= 0,
                    page_size= 12,
                ),
    ]

@callback(
    Output('datatable-interactivity-container', "children"),
    Input('alertTable', "derived_virtual_data"),
    Input('alertTable', "derived_virtual_selected_rows"))
def update_graphs(rows, derived_virtual_selected_rows):
    if derived_virtual_selected_rows is None:
        return[html.Div()]
    else:
        dff = situaciones if rows is None else pd.DataFrame(rows)
        return [
        html.Div([
            html.P(dff["name"][derived_virtual_selected_rows], style = {"color":"#18bc9c"}),
            dbc.Row([
                dbc.Col(html.P("Bases libres:"), width=9,style={"font-weight": "bold"}),
                dbc.Col(html.P(round(dff["free_bases"][derived_virtual_selected_rows])),width=3),
            ]),
            dbc.Row([
                dbc.Col(html.P("Bases ocupadas:"), width=9, style={"font-weight": "bold"}),
                dbc.Col(html.P(round(dff["dock_bikes"][derived_virtual_selected_rows])), width=3),
            ]),
        ])
    ]
    
cardTable = dbc.Card([
        dbc.CardHeader("Información Estaciones", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody(id="table-display")
    ], className="h-100"
)
@callback(
    Output("table-display", "children"),
    [Input("select-distrito", "value"), 
    Input("typeofday-checklist", "value")]
)
def displayTable(value, typeofday):
    if (value == None) | (value == []):
        return [
        dbc.Row([
            dcc.Graph(figure = F1.tablaInfo(itinerarios_bases, itinerarios_bases.Distrito_Salida.unique(), typeofday), config={'displayModeBar': False})
        ])
    ]
    else:
        return [
            dbc.Row([
                dcc.Graph(figure = F1.tablaInfo(itinerarios_bases, value, typeofday))
            ])
        ]

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
    [Input("traveltime-slider", "value"),
    Input("typeofday-checklist", "value")]
)
def display_edades(value, typeofday):
    return [
        dbc.Row(
            children = [
                dcc.Graph(figure = F1.pyramidDisplay(itinerarios_bases, value, typeofday), config={'displayModeBar': False})
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
    [Input("btn-status", "value"),
    Input("typeofday-checklist", "value")]
)
def display_status(value, typeofday):
    return [
        dbc.Row(
                children = [
                    dcc.Graph(figure = F1.gaugeDisplay(itinerarios_bases, today, value, typeofday), config={'displayModeBar': False})
                ]
            ),
            dbc.Row(
                children = [
                    dcc.Graph(figure = F1.timelineDisplay(itinerarios_bases, today, value, typeofday), config={'displayModeBar': False})
                ]
            )
    ]

cardDemandaHoras = dbc.Card(
    [
        dbc.CardHeader("Demanda media por horas", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody(id = "dh-display")
    ], className="h-100"
)
@callback(
    Output("dh-display", "children"),
    Input("typeofday-checklist", "value")
)
def dh_display(typeofday):
    return [dcc.Graph(figure = F1.estacionalidadHoras(itinerarios_bases, typeofday))]

cardDemandaDias = dbc.Card(
    [
        dbc.CardHeader("Demanda media por día de la semana", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody(dcc.Graph(figure = F1.estacionalidadDias(itinerarios_bases)))
    ], className="h-100"
)

cardDemandaMeses = dbc.Card(
    [
        dbc.CardHeader("Demanda media por mes", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody(id = "dm-display")
    ], className="h-100"
)
@callback(
    Output("dm-display", "children"),
    Input("typeofday-checklist", "value")
)
def dm_display(typeofday):
    return [dcc.Graph(figure = F1.estacionalidadMeses(itinerarios_bases, typeofday))]

cardMap = dbc.Card(
    [
        dbc.CardHeader("Estaciones BiciMAD por distrito", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody([
            dbc.Row([
                dcc.Dropdown(
                    id="select-distrito",
                    options = itinerarios_bases.Distrito_Salida.unique(),
                    multi=True,
                    style={"color": "#2c3e50", "width":"80%"},
                    placeholder="Seleccionar un distrito"
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
            dbc.RadioItems(
                    id="btn-wc",
                    className="btn-group",
                    inputClassName="btn-check",
                    labelClassName="btn btn-outline-primary",
                    labelCheckedClassName="active",
                    options=[
                        {"label": "Estación", "value": "name_Salida"},
                        {"label": "Distrito", "value": "Distrito_Salida"},
                        {"label": "Barrio", "value": "Barrio_Salida"},
                    ],
                    value="name_Salida",
                ),
            html.Div(id="wordcloud-display",
                children =[
                    dbc.Row(
                        children = [
                            #dcc.Graph(figure = F1.wordcloudDisplay(itinerarios_bases), config={'displayModeBar': False}, style = {"padding": "1rem", "width" : "100%"})
                            #html.Div(html.Img(id="image_wc"), style = { 'height': '100%'})
                            html.Img(id="image_wc")
                        ], 
                    ),
                ])
        ])
    ], className="h-100", 
)
@callback(
    Output('image_wc', 'src'), 
    [Input('image_wc', 'id'),
    Input('btn-wc', 'value')]
)
def make_image(b, value):
    img = BytesIO()
    F1.wordcloudDisplay2(itinerarios_bases, value).save(img, format='PNG')
    return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())


cardTopRutas = dbc.Card(
    [
        dbc.CardHeader("Rutas Más Concurridas", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody([
            dbc.Row([
                dcc.Dropdown(
                    id="select-Rutasdistrito",
                    options = itinerarios_bases.Distrito_Salida.unique(),
                    multi=False,
                    style={"color": "#2c3e50", "width":"80%"},
                    placeholder="Seleccionar un distrito para ver sus rutas más concurridas"
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
    return [
        dbc.Row([
            dcc.Graph(figure = F1.mapRutasDisplay(itinerarios_bases, value), config={'displayModeBar': False})
        ])
    ]


cardSunburstItinerarios = dbc.Card(
    [
        dbc.CardHeader("Distribución Top Itinerarios", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Col(html.P("NºEstaciones de salida:"),width=9),
                    dbc.Col(dbc.Input(id="N",type="number", min=0,max=10,step=1, value=5), width=3)
                ], width = 6),
                dbc.Col([
                    dbc.Col(html.P("NºEstaciones de llegada:"), width=9),
                    dbc.Col(dbc.Input(id="M",type="number", min=0,max=10,step=1, value=10), width=3)
                ], width =6),
            ]),
            dbc.Row(id="sunburst-display")
        ])
    ], className="h-100"
)
@callback(
    Output("sunburst-display", "children"),
    [Input("N", "value"), 
    Input("M", "value")]
)
def sunburst_display(N, M):
    return [dcc.Graph(figure = F1.sunburstItinerarios(itinerarios_bases, N,M))]

layout = dbc.Container(
    children = [
            dbc.Row([
                dbc.Col([
                    dbc.Col(html.Div(html.H2("General", style={"color":"#18bc9c", "vertical-align":"middle"}))),
                    dbc.Col(html.P(html.P(today.strftime("%d %B, %Y %I%p"),style={"color":"#18bc9c", "vertical-align":"middle"})))
                ], width = 3, style = {"padding":"1rem 1rem"}), 
                dbc.Col([
                    #dbc.Col(html.P(html.P('Día de la semana',style={"color":"#18bc9c", "vertical-align":"bottom"}))),
                    dbc.Col(dbc.Checklist(
                        id = "typeofday-checklist",
                        options=[
                            {"label": "Laboral", "value": 1},
                            {"label": "Fin de semana", "value": 0},                                                    
                            ],
                        label_checked_style={"color": "#2c3e50"},
                        input_checked_style={"backgroundColor": "#2c3e50","borderColor": "#5b80a5"},
                        value=[0, 1],
                        inline=False),style= {'vertical-align': 'bottom'} )
                    ], width={"size": 2, "offset": 7}, style = {"padding":"1rem 1rem"})
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
                                children = [
                                    dbc.Row([
                                        dbc.Col(cardMap, width = 6, style = {"height":"800px"}),
                                        dbc.Col([
                                            dbc.Card(cardTable, style = {"height":"400px", "margin-bottom": "5px"}),
                                            dbc.Card(cardCloud, style = {"height":"390px", "margin-top": "5px"}),
                                        ],width = 6),
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
                        ], always_open = False)
                    )                     
                ], width = 12),
            ],  justify = "center", style = {"padding-bottom": "2rem"})
    ]  ,
    fluid = True,
    className="mt-3"
)
