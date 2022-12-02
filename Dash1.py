import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
from dash import html
from dash.dependencies import Input, Output
from collections import Counter 
#from wordcloud import WordCloud
import plotly.express as px
from io import BytesIO
import base64
import funciones as F
import dash_bootstrap_components as dbc

itinerarios_bases= pd.read_parquet('./Data/Itinerarios/itinerarios_bases.parquet')
options_usuarios=[{'label': 'Anual' ,'value':1 },
                  {'label': 'Ocasional' ,'value':2 },
                  {'label': 'Empleados' ,'value':3 }
                  ]

label_usuarios=['Anualnual','Ocasional','Empleados']
valores_usarios=[1,2,3]

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

app.layout = html.Div(
    children = [
        html.H1(
            id = "titulo",
            children = "Situación transporte Bicimad", 
            style={'text-align': 'center'}
        ),
        dcc.Tabs(
            id = "tabs", value='Situación General',
            children = [
                dcc.Tab(
                    id = "tab-1",value = "Situación General",label = "Situación General", 
                    children=[
                        ]),
                dcc.Tab(
                    id = "tab-2",value = "Comparacion Estaciones",label = "Comparacion Estaciones"),
                dcc.Tab(
                    id = "tab-3",value = "Predicción estaciones",label = "Predicción estaciones")   
            ],
        ),
        html.Div(id = "resultado-tabulacion")
    ]
) 
@app.callback(
    Output('resultado-tabulacion', 'children'),
    Input('tabs', 'value')
)

def render_content(tab):
    
    if tab == 'Situación General':
        return [html.Div(
            children = [
                
                dbc.Row([
                   dbc.Col (html.H3(id = "titulo-tab-1",children = "Graficas descriptivas"), width=4), 
                   dbc.Col(
                       dbc.Checklist( id='CheckListSG',options=options_usuarios,value=[1,2,3], inline=True) )
                ]), 
                
                html.Div(
                     [
                        dbc.Row(
                        [
                        dbc.Col(dcc.Graph(id = 'mapa_rutas',figure= F.GráficoMapasRutas(itinerarios_bases, 7))),
                        dbc.Col(dcc.Graph(id = 'mapa_rutas2',figure= F.GráficoMapasRutas(itinerarios_bases, 7)))
                        ])                        
                    ])
            ]
        )]
    elif tab == 'Comparacion Estaciones':
       return [html.Div(
            children = [
                html.H3(
                    id = "titulo-tab-2",
                   children = "Analisis del modelo"
               ),
               html.Div(
                   id = "inferencias"
               )
            ]
            )]

@app.callback(
    
    Output("mapa_rutas", "figure"),    
    Input("CheckListSG", "value"),
    
)
def filtroUsuarios(values): 
    df=itinerarios_bases[itinerarios_bases['user_type'].isin(values) ]
    if df.empty: 
        return F.GráficoMapasRutas("Vacio", 7)
    else: 
        return F.GráficoMapasRutas(df, 7)
    
if __name__ == '__main__':
    #app.run_server(debug=True)
    #app2.run_server(debug=True)
    app.run_server(debug=True, port= 8053)
    
# Funciones para crear los gráficos  


        