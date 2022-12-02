import pandas as pd
import dash
from dash import Input, Output, dcc, html, ctx, callback
import plotly.express as px
import dash_bootstrap_components as dbc
import pickle
import plotly.graph_objects as go
from fbprophet import Prophet
import datetime
from datetime import date, timedelta

dash.register_page(__name__, name='Predicciones') # '/' is home page

hora = datetime.datetime.now().hour
dia = datetime.datetime.today().weekday()
mes = datetime.datetime.today().month

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
            dbc.Col(html.Div(html.H1("Predicciones",style={"color":"#18bc9c"})), width=3),
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
                        layout = go.Layout(plot_bgcolor='rgba(0,0,0,0)', height=300, width=300, yaxis={'visible':False}, title={'text': "Demanda por horas",'x':0.5,'xanchor': 'center','yanchor': 'bottom'}),
                        
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

    m = pickle.load(open('./Predictions/demandpredicition.pkl', 'rb'))
    if start_date and end_date:
        dates = pd.date_range(pd.to_datetime(start_date),pd.to_datetime(end_date)-timedelta(days=1),freq='h')
        future = pd.DataFrame(dates)
        future.columns = ['ds']
        future['ds'] = pd.to_datetime(future['ds'])  
        future['typeofday'] = future['ds'].apply(typeofday)
        forecast = m.predict(future)

        fig = go.Figure(go.Scatter(
            x = forecast['ds'],
            y = forecast['yhat'],
            mode='lines',
            name = "Predicción",
            marker_color = "#18bc9c"
        ))

        fig.update_layout(title_text="Predicción semanal demanda <b>Neural Prophet</b> BiciMAD", yaxis_title="Demand", plot_bgcolor='rgba(0,0,0,0)')

        return (fig,{"display":"block"})
    else:
        dates = pd.date_range(pd.to_datetime(date(2020,1,1)),pd.to_datetime(date(2020,1,7))-timedelta(days=1),freq='h')
        future = pd.DataFrame(dates)
        future.columns = ['ds']
        future['ds'] = pd.to_datetime(future['ds'])  
        future['typeofday'] = future['ds'].apply(typeofday)
        forecast = m.predict(future)

        fig = go.Figure(go.Scatter(
            x = forecast['ds'],
            y = forecast['yhat'],
            mode='lines',
            name = "Predicción",
            marker_color = "#18bc9c"
        ))

        fig.update_layout(title_text="Predicción <b>demanda</b> BiciMAD", yaxis_title="Demand", plot_bgcolor='rgba(0,0,0,0)')

        return (fig,{"display":"block"})

def typeofday(ds):
        date = pd.to_datetime(ds)
        if (date.weekday() == 5 or date.weekday() == 6):
            return 0
        elif(date.weekday() == 4):
            return 1
        else:
            return 2
    