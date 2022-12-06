import pandas as pd
import dash
from dash import Input, Output, dcc, html, ctx, callback
import plotly.express as px
import dash_bootstrap_components as dbc
import pickle
import plotly.graph_objects as go
from prophet import Prophet
from datetime import timedelta, date, datetime
import numpy as np
import funciones1 as F1

dash.register_page(__name__, name='Predicciones') # '/' is home page

today = pd.to_datetime(date(2019,12,12))
hora = today.hour
dia = today.dayofweek
mes = today.month

# Si se actualizase diariamente:
# hora = datetime.now().hour
# dia = datetime.today().weekday()
# mes = datetime.today().month

colors_day = ['lightslategray']*7
colors_day[dia]="#18bc9c"
colors_hora = ['lightslategray']*24
colors_hora[hora]="#18bc9c"
colors_mes = ['lightslategray']*13
colors_mes[mes]="#18bc9c"

itinerarios_bases = pd.read_parquet('./Data/Itinerarios/itinerarios_bases.parquet')
itinerarios_bases["unplug_hourTime"] = pd.to_datetime(itinerarios_bases["unplug_hourTime"])
demanda = itinerarios_bases.groupby("unplug_hourTime").size().reset_index(name='Count')

barrios_dropdown_options = [{'label':x, 'value':x} for x in sorted(itinerarios_bases["Barrio_Salida"].unique())]

layout = dbc.Container(
    children = [
        dbc.Row([
            dbc.Col(children = 
                [
                    html.Div(html.H2("Predicciones",style={"color":"#18bc9c", "vertical-align":"middle"})),
                    html.Div(html.P(today.strftime("%d %B, %Y %I%p"),style={"color":"#18bc9c", "vertical-align":"middle"}))
                ], width=3),
            
            dbc.Col(dcc.Graph(id="avg-demand-day", 
                figure=go.Figure(
                        data=[go.Bar(
                            x = demanda.groupby(demanda["unplug_hourTime"].dt.dayofweek).agg({'Count':'mean'}).index,
                            y = demanda.groupby(demanda["unplug_hourTime"].dt.dayofweek).agg({'Count':'mean'})['Count'],
                            marker_color=colors_day
                        )],
                        layout = go.Layout(plot_bgcolor='rgba(0,0,0,0)',height=150, width=300,
                        margin=go.layout.Margin(l=50,r=50, b=1,t=50,pad = 5))
                    ),
                config={'displayModeBar': False}
            ), width={"size":3,"offset":2}, style = { "margin-top":"-3rem"}),
            dbc.Col(dcc.Graph(id="avg-demand-hour", 
                figure=go.Figure(
                        data=[go.Bar(
                            x = demanda.groupby(demanda["unplug_hourTime"].dt.hour).agg({'Count':'mean'}).index,
                            y = demanda.groupby(demanda["unplug_hourTime"].dt.hour).agg({'Count':'mean'})['Count'],
                            marker_color=colors_hora
                        )],
                        layout = go.Layout(plot_bgcolor='rgba(0,0,0,0)', height=150, width=300, yaxis={'visible':False}, title={'text': "Demanda por horas",'x':0.5,'xanchor': 'center','yanchor': 'bottom'},
                        margin=go.layout.Margin(l=50,r=50, b=1,t=50,pad = 5))
                    ),
                    config={'displayModeBar': False}
            ), width=3, style = { "margin-top":"-3rem"}),
        ], style = {"padding":"1rem 1rem"}), 

        html.Hr(),           

        # dbc.Row([
        #     dbc.Col(dcc.DatePickerRange(id='my-date-picker-range',min_date_allowed=date(2019, 8, 1), max_date_allowed=date(2020, 1, 7), initial_visible_month=date(2020, 1, 1), end_date=date(2020, 1, 7))),
            
        # ], justify='start'), # center, end, between, around

        dbc.Row([
            dbc.Col(dcc.Graph(figure=F1.update_prediction()) )
        ])

    ],
    fluid = True,
    className="mt-3"
)


