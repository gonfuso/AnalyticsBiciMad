import json

from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import funciones as F
import dash_bootstrap_components as dbc
pd.set_option('display.max_columns', 500)


situacion= pd.read_parquet('Data/SituacionEstaciones/situaciones.parquet')
itinerarios_bases=pd.read_parquet('Data/Itinerarios/itinerarios_bases.parquet')
bases=pd.read_parquet('Data/Bases/basesSituaciones.parquet')
nums=itinerarios_bases.idplug_station.unique()
situacion2=situacion[situacion['number'].isin(nums)]


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP] )

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}



app.layout = html.Div([
    dbc.Row([
        
    dbc.Col( children=[
        dbc.RadioItems(
            options=[
                {"label": "Huecos libres", "value": 0},
                {"label": "Bicis disponibles", "value": 1},],
            value=1,id="radioMapa",inline=True),
        dcc.Graph(id='MapaBases')],
        width=4 ) ,
    
    dbc.Col(children=[
        dbc.RadioItems(
            options=[
                {"label": "Rutas Salida", "value": 0},
                {"label": "Rutas Llegada", "value": 1},],
            value=1,id="radioRuta",inline=True),
            dcc.Graph(id='MapaRutas')], 
            width=4 ), 
    dbc.Col(dcc.Graph(id='Grafico3 '), width=4 ) 
    
    ]),
    
    html.Div(className='row', children=[
        html.Div([
            dcc.Markdown("""
                **Hover Data**

                Mouse over values in the graph.
            """),
            html.Pre(id='hover-data', style=styles['pre'])
        ], className='three columns'),

        html.Div([
            dcc.Markdown("""
                **Click Data**

                Click on points in the graph.
            """),
            html.Pre(id='click-data', style=styles['pre']),
        ], className='three columns')

       
    ])
])


# @app.callback(
#     Output('hover-data', 'children'),
    
#     Input('basic-interactions', 'hoverData'))
# def display_hover_data(hoverData):
#     return json.dumps(hoverData, indent=2)

@app.callback(
    Output('MapaBases', 'figure'), 
    Input('radioMapa', 'value')
)
def mapaBases(radio): 
    return F.GraficoSituacionMapa(F.filtrarHoraDiaSeman(situacion2,1,7), radio )


@app.callback(
    Output('MapaRutas', 'figure'),
    Output('click-data', 'children'),
    Input('radioRuta', 'value'), 
    Input('MapaBases', 'clickData'))
def display_click_data(radio, clickData):
    if clickData==None: 
        return(F.GráficoMapasRutas("vacio", 10),0)
    
    estacion=int(clickData['points'][0]['customdata'][2])
    

    if radio==0: 
        itinerarios=itinerarios_bases[itinerarios_bases['idplug_station']==estacion]
    else: 
        itinerarios=itinerarios_bases[itinerarios_bases['idunplug_station']==estacion]
    
    print('La estacion pinchada es: '+str(estacion))
    fig=F.GráficoMapasRutas(itinerarios, 10,radio, estacion ) 
    return (fig, json.dumps(clickData, indent=2))






if __name__ == '__main__':
    app.run_server(debug=True)
