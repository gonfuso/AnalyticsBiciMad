import pandas as pd
import dash
from dash import Input, Output, dcc, html, ctx, callback
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import funciones as F
from datetime import timedelta, date, datetime
from dash.exceptions import PreventUpdate
import json 


dash.register_page(__name__,  name='Comparativa') # '/' is home page

situacion= pd.read_parquet('Data/SituacionEstaciones/situaciones2.parquet')
itinerarios_bases=pd.read_parquet('Data/Itinerarios/itinerarios_bases3.parquet')
bases=pd.read_parquet('Data/Bases/basesSituaciones.parquet')
nums=itinerarios_bases.idplug_station.unique()
situacion2=situacion[situacion['number'].isin(nums)]
today = pd.to_datetime(date(2019,12,12))

cardBases = dbc.Card(
    [
        dbc.CardHeader("Estaciones BiciMAD por distrito", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody([
            dbc.Row([
                dbc.RadioItems(
            options=[
                {"label": "Huecos libres", "value": 0},
                {"label": "Bicis disponibles", "value": 1},],
            value=1,id="radioMapa",inline=True),
        
            ]),
            html.Div(id="bases-display", style = {"width" : "100%"}, 
                    children=[] ), 
            dcc.Store(id='memoryBase'),
        ])
    ],
    className="h-100",
)
@callback(Output('memoryBase', 'data'),
          Input('MapaBases', 'clickData'))
def on_data_set_table(data):
    if data is None:
        raise PreventUpdate

    return data
@callback(
    Output('bases-display', 'children'), 
    Input('radioSemana', 'value'),
    Input('Hora', 'value'),
    Input('radioMapa', 'value')
)
def mapaBases( semana,hora, radio): 
    
    itinerarios=itinerarios_bases[ (itinerarios_bases['dayofweek']==semana) & (itinerarios_bases['hour']==hora) ]
    return [dbc.Row([
                dcc.Graph(id='MapaBases',figure = F.GraficoSituacionMapa(F.filtrarHoraDiaSeman(situacion2,semana,hora),itinerarios, radio ), 
                          config={'displayModeBar': False})
            ])
        ] 
cardRutas = dbc.Card(
    [
        dbc.CardHeader("Rutas más frecuentes", style = {"background-color":"#ecf0f1"}), 
        dbc.CardBody([
            dbc.Row([
                dbc.RadioItems(
                    options=[
                        {"label": "Rutas Salida", "value": 0},
                        {"label": "Rutas Llegada", "value": 1},],
                    value=1,id="radioRuta",inline=True),
        
            ]),
            html.Div(id="rutas-display", style = { "width" : "100%"})
            ])
    ],
    className="h-100",
)
cardPolar=dbc.Card(
    [
        dbc.CardHeader("Tiempo medio de viaje", style = {"background-color":"#ecf0f1"}),
        dbc.CardBody([
            html.Div(id="polar-display", style = { "vertical-align":"middle","horizontal-align":"middle", })
        ])
    ]
)
cardHist=dbc.Card(
    [
        dbc.CardHeader("Distribucion de las bases", style = {"background-color":"#ecf0f1"}),
        dbc.CardBody([
            html.Div(id="hist-display", style = {"padding": "1rem", "width" : "100%", "vertical-align":"middle","horizontal-align":"middle", })
        ])
    ]
)
@callback(
    
    Output('rutas-display', 'children'),
    Output('polar-display', 'children'),
    #Output('hist-display', 'children'),
    Input('radioRuta', 'value'), 
    Input('memoryBase', 'data'),
    Input('radioSemana', 'value'),
    Input('Hora', 'value'))
def display_click_data(radio, clickData, semana, hora):
    
    if clickData==None: 
        return([dbc.Row([
                dcc.Graph(id='MapaRutas',figure = F.GráficoMapasRutas("vacio", 10), 
                          config={'displayModeBar': False})])],
               [dbc.Row([
                dcc.Graph(id='PolarTime',figure = F.linepolar('vacio'), 
                          config={'displayModeBar': False}, 
                          style={"horizontal-align":"middle"})], style={"horizontal-align":"middle"} )],
               ) 
    
    estacion=int(clickData['points'][0]['customdata'][2])
    

    if radio==0: 
        itinerarios=itinerarios_bases[itinerarios_bases['idplug_station']==estacion]
    else: 
        itinerarios=itinerarios_bases[itinerarios_bases['idunplug_station']==estacion]
    
    itinerarios=itinerarios[ (itinerarios['dayofweek']==semana) & (itinerarios['hour']==hora) ]
    
     
    return([dbc.Row([
                dcc.Graph(id='MapaRutas',figure = F.GráficoMapasRutas(itinerarios, 10,radio, estacion ),
                          config={'displayModeBar': False})])],
            [dbc.Row([
                dcc.Graph(id='PolarTime',figure = F.linepolar(itinerarios,radio,8),
                          config={'displayModeBar': False})
                
                ])],
            # [dbc.Row([ 
            #     dcc.Graph(id='HistBikes', figure = F.linepolar(itinerarios,radio,8) , 
            #               config={'displayModeBar': False})
            #     ])],
            )


layout = html.Div(
    [
       
         dbc.Row([
                dbc.Col([
                    dbc.Col(html.Div(html.H2("Comparativa", style={"color":"#18bc9c", "vertical-align":"top"}))),
                    dbc.Col(html.P(html.P(today.strftime("%d %B, %Y %I%p"),style={"color":"#18bc9c", "vertical-align":"top"})))
                ], width = 3, style = {"padding":"1rem 1rem"}), 
                
                dbc.Col([
                    dbc.Col(html.P(html.P('Hora',style={"color":"#18bc9c", "vertical-align":"bottom"}))),
                    dbc.Col(dbc.Input(id='Hora',type='number', min=0, max=23, step=1, value=7), style= {'vertical-align': 'bottom'})
                ], width=1, style = {"padding":"1rem 1rem"}),
                dbc.Col([
                    dbc.Col(html.P(html.P('Día de la semana',style={"color":"#18bc9c", "vertical-align":"bottom"}))),
                    dbc.Col(dbc.RadioItems(
                        options=[
                            {"label": "Lunes", "value": 0},
                            {"label": "Martes", "value": 1},
                            {"label": "Miércoles", "value": 2},
                            {"label": "Jueves", "value": 3},
                            {"label": "Viernes", "value": 4},
                            {"label": "Sábado", "value": 5},
                            {"label": "Domingo", "value": 6},                                                        
                            ],
                        value=0,id="radioSemana",inline=True),style= {'vertical-align': 'bottom'} )
                    ], width=8, style = {"padding":"1rem 1rem"})
            ]),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col( [cardBases], width=4, style={ "height": "650px"}),
                dbc.Col([cardRutas ], width=4, style={ "height": "650px"}), 
                dbc.Col( [dbc.Row(cardPolar)], width=4, style={ "height": "650px"})    #cardHist
            ], 
        )
    ]
)
@callback(
    Output('click-data', 'children'),
    Input('MapaRutas', 'clickData'))
def display_click_data(clickData):
    return json.dumps(clickData, indent=2)

