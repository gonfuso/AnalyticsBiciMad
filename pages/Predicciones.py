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

today = pd.to_datetime(date(2012,12,12))
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

layout = html.Div(
    [
        dbc.Row([
            dbc.Col(html.Div(html.H2("Predicciones",style={"color":"#18bc9c"})), width=3),
            dbc.Col(dcc.Graph(id="avg-demand-day", 
                figure=go.Figure(
                        data=[go.Bar(
                            x = demanda.groupby(demanda["unplug_hourTime"].dt.dayofweek).agg({'Count':'mean'}).index,
                            y = demanda.groupby(demanda["unplug_hourTime"].dt.dayofweek).agg({'Count':'mean'})['Count'],
                            marker_color=colors_day
                        )],
                        layout = go.Layout(plot_bgcolor='rgba(0,0,0,0)',height=300, width=300)
                    ),
                config={'displayModeBar': False}
            ), width=3, style = { "margin-top":"-3rem"}),
            dbc.Col(dcc.Graph(id="avg-demand-hour", 
                figure=go.Figure(
                        data=[go.Bar(
                            x = demanda.groupby(demanda["unplug_hourTime"].dt.hour).agg({'Count':'mean'}).index,
                            y = demanda.groupby(demanda["unplug_hourTime"].dt.hour).agg({'Count':'mean'})['Count'],
                            marker_color=colors_hora
                        )],
                        layout = go.Layout(plot_bgcolor='rgba(0,0,0,0)', height=200, width=300, yaxis={'visible':False}, title={'text': "Demanda por horas",'x':0.5,'xanchor': 'center','yanchor': 'bottom'}),
                        
                    ),
                    config={'displayModeBar': False}
            ), width=3, style = { "margin-top":"-3rem"}),
            dbc.Col(dcc.Graph(id="avg-demand-mes", 
                figure=go.Figure(
                        data=[go.Bar(
                            x = demanda.groupby(demanda["unplug_hourTime"].dt.month).agg({'Count':'mean'}).index,
                            y = demanda.groupby(demanda["unplug_hourTime"].dt.month).agg({'Count':'mean'})['Count'],
                            marker_color=colors_mes
                        )],
                        layout = go.Layout(plot_bgcolor='rgba(0,0,0,0)', height=300, width=300, yaxis={'visible':False}, title={'text': "Evolución último mes",'x':0.5,'xanchor': 'center','yanchor': 'bottom'}),
                        
                    ),
                    config={'displayModeBar': False}
            ), width=3, style = { "margin-top":"-3rem"}),
        ], style = {"padding":"1rem 1rem"}), 

        html.Hr(),           

        dbc.Row([
            dbc.Col(dcc.DatePickerRange(id='my-date-picker-range',min_date_allowed=date(2019, 8, 1), max_date_allowed=date(2020, 1, 7), initial_visible_month=date(2020, 1, 1), end_date=date(2020, 1, 7))),
            
        ], justify='start'), # center, end, between, around

        dbc.Row([
            dbc.Col(dcc.Graph(id='output-container-date-picker-range1', style = {"display": "none" }) )
        ])

        # dbc.Row([
        #     dbc.Col(dcc.Dropdown(id="start-date-prediction", multi=False, value="2020-01-01", options=barrios_dropdown_options), width = 6),
        #     dbc.Col(dcc.Dropdown(id="start-date-prediction", multi=False, value="2020-01-01", options=barrios_dropdown_options), width = 6)   
        # ], justify='start') # center, end, between, around
    ]
)

@callback(
    Output('output-container-date-picker-range1', 'figure'),
    Output("output-container-date-picker-range1", "style"),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date'))

def update_prediction(start_date, end_date):

    fiestas_madrid = pd.DataFrame({
        'holiday': 'fiestas',
        'ds': pd.to_datetime(['2019-08-15', '2019-10-12',
                                '2019-11-01', '2019-11-09',
                                '2019-12-06', '2019-12-09',
                                '2019-12-25', '2020-01-01', 
                                '2020-01-06']),
        'lower_window': -1,
        'upper_window': 0,
    })

    model = pickle.load(open('./Predictions/demandPredicition1.pkl', 'rb'))

    forecast = model.make_future_dataframe(periods = 24*4, freq = "H")
    forecast = F1.is_friday(forecast)
    forecast = F1.is_weekend(forecast)
    forecast = F1.is_laborable(forecast)
    forecast = F1.entrada_trabajo(forecast,fiestas_madrid)

    forecast = model.predict(forecast)
    forecast["yhat"] = np.exp(forecast["yhat"])

    fig = go.Figure(go.Scatter(
        x = forecast['ds'].iloc[-24*4:],
        y = forecast['yhat'].iloc[-24*4:],
        mode='lines',
        name = "Predicción",
        marker_color = "#18bc9c"
    ))

    fig.update_layout(title_text="Predicción demanda BiciMAD", yaxis_title="Demand", plot_bgcolor='rgba(0,0,0,0)')

    return (fig,{"display":"block"})