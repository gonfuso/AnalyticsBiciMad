import pickle
import numpy as np
import pandas as pd
import dash
from dash import Input, Output, dcc, html, callback
import plotly.express as px
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from prophet import Prophet
from datetime import timedelta, date, datetime
import numpy as np

# Calcular los regresores que voy a utilizar
def is_friday(df):
    """
    Parametros:
    
    df: pd.DataFrame: Dataframe que contiene la serie temporal en formato prophet
    
    Salida:
    
    Se construye una variable adicional que indica si es viernes
    """
    
    df["is_friday"] = df["ds"].map(lambda x: 1 if x.isoweekday() == 5 else 0)
    return df

def is_weekend(df):
    """
    Parametros:
    
    df: pd.DataFrame: Dataframe que contiene la serie temporal en formato prophet
    
    Salida:
    
    Se construye una variable adicional que indica si es fin de semana
    """
    df["is_weekend"] = df["ds"].map(lambda x: 1 if x.isoweekday() in [6,7] else 0)
    return df

def is_laborable(df):
    """
    Parametros:
    
    df: pd.DataFrame: Dataframe que contiene la serie temporal en formato prophet
    
    Salida:
    
    Se construye una variable adicional que indica si es dia laborable
    """
    df["is_laborable"] = df["ds"].map(lambda x: 1 if x.isoweekday() not in [5,6,7] else 0)
    return df

def entrada_trabajo(df,holidays):
    """
    Parametros:
    
    df: pd.DataFrame: Dataframe que contiene la serie temporal en formato prophet
    
    holidays: pd.DataFrame. Dataframe que contiene las vacaciones en formato Prophet
    
    Salida:
    
    Se construye una variable adicional que indica si es hora de entrada al trabajo
    """
    df["entrada_trabajo"] = df["ds"].map(lambda x: 1 if (x.isoweekday() not in [6,7]) & (x.hour in [6,7,8]) else 0)
    
    df["entrada_trabajo"] = np.where(df["ds"].map(lambda x: datetime(x.year,x.month,x.day)).isin(holidays["ds"]),0,df["entrada_trabajo"])
    
    return df

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
    forecast = is_friday(forecast)
    forecast = is_weekend(forecast)
    forecast = is_laborable(forecast)
    forecast = entrada_trabajo(forecast,fiestas_madrid)

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


def gaugeDisplay(df, date, value): 
    df_filtrado = df[(df["status"]==value) & (df["unplug_hourTime"].dt.tz_localize(None)<pd.to_datetime(date))]
    date_init_week = date - timedelta(days=date.dayofweek)
    lost_this_week = round(df_filtrado[df_filtrado["unplug_hourTime"].dt.tz_localize(None)>pd.to_datetime(date_init_week)].groupby(df_filtrado["unplug_hourTime"].dt.isocalendar().week).size().reset_index(name='Count')["Count"].mean())
    avg_lost_per_week = round(df_filtrado[df_filtrado["unplug_hourTime"].dt.tz_localize(None)<pd.to_datetime(date_init_week)].groupby(df_filtrado["unplug_hourTime"].dt.isocalendar().week).size().reset_index(name='Count')["Count"].mean())
    avg_lost_to_dayofweek = round(df_filtrado[(df_filtrado["unplug_hourTime"].dt.tz_localize(None)<pd.to_datetime(date_init_week))&(df_filtrado["unplug_hourTime"].dt.dayofweek < date.dayofweek)].groupby(df_filtrado["unplug_hourTime"].dt.isocalendar().week).size().reset_index(name='Count')["Count"].mean())

    fig = go.Figure(go.Indicator(
        domain = {'x': [0, 1], 'y': [0, 1]},
        value = lost_this_week,
        mode = "gauge+number+delta",
        delta = {'reference': avg_lost_to_dayofweek},
        gauge = {'axis': {'range': [None, avg_lost_per_week*1.5]},
                'bar': {'color': "#18bc9c"},
                'steps' : [
                    {'range': [0, avg_lost_per_week], 'color': "lightgray"}],
                'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': avg_lost_to_dayofweek}}))
    
    fig.update_layout(margin=dict(l=2,r=2, b=5,t=20,pad = 5), height = 100)

    return fig

def timelineDisplay(df,date, value):
    df_filtrado = df[(df["status"]==value) & (df["unplug_hourTime"].dt.tz_localize(None)<pd.to_datetime(date))]

    fig = go.Figure(go.Scatter(
        x = df_filtrado.groupby(df_filtrado["unplug_hourTime"].dt.date).size().reset_index(name='Count')['unplug_hourTime'],
        y = df_filtrado.groupby(df_filtrado["unplug_hourTime"].dt.date).size().reset_index(name='Count')["Count"], 
        marker_color = "#18bc9c"
    ))
    fig.update_xaxes(
        rangeslider_visible=True,
        tickformatstops = [
            dict(dtickrange=[None, 1000], value="%H:%M:%S.%L ms"),
            dict(dtickrange=[1000, 60000], value="%H:%M:%S s"),
            dict(dtickrange=[60000, 3600000], value="%H:%M m"),
            dict(dtickrange=[3600000, 86400000], value="%H:%M h"),
            dict(dtickrange=[86400000, 604800000], value="%e. %b d"),
            dict(dtickrange=[604800000, "M1"], value="%e. %b w"),
            dict(dtickrange=["M1", "M12"], value="%b '%y M"),
            dict(dtickrange=["M12", None], value="%Y Y")
        ]
    )

    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=1,r=1, b=10,t=20,pad = 5), height = 150)
    fig.update_yaxes(gridcolor="lightgrey")

    return fig


def pyramidDisplay(df, value):
    df["ageRange"] = df["ageRange"].replace([0,1,2,3,4,5,6],["Ind.","0-16","17-18", "19-26", "27-40", "41-65", "66+"])
    df = df[(df["travel_time"]<=1440) & (df["travel_time"]>0)]
    df1 =df[(df["travel_time"]/60>value[0]) & (df["travel_time"]/60<value[1])]
    ageRange_1 = df1[df1["user_type"] == 1].groupby("ageRange").agg({"travel_time":"mean"})
    ageRange_2 = df1[df1["user_type"] == 2].groupby("ageRange").agg({"travel_time":"mean"})

    # traveltime ticks
    #traveltime_ticks = list(range(int(round(-max(max(ageRange_1["travel_time"]), max(ageRange_2["travel_time"])),-3)), int(round(max(max(ageRange_1["travel_time"]), max(ageRange_2["travel_time"])),-3)), 10))
    traveltime_ticks = list(range(-round(1440/60),round(1440/60),20))

    # Creating instance of the figure
    fig = go.Figure(go.Bar(y= ageRange_1.index, x = round(ageRange_1["travel_time"]/60), 
                        name = 'Anuales', 
                        orientation = 'h',
                        marker_color = "#18bc9c",
                        ))

    
    # Adding Male data to the figure
    fig.add_trace((go.Bar(y= ageRange_2.index, x = round(ageRange_2["travel_time"]*-1/60), 
                        name = 'Ocasionales', 
                        orientation = 'h',
                        marker_color = "#395B64",
                        )))
        
        # Updating the layout for our graph
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                        barmode='relative',
                        bargap = 0.0, bargroupgap = 0,
                        xaxis = dict(tickvals = traveltime_ticks,    
                        title = 'Media duración de trayectos',
                        title_font_size = 14),
                        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),
                        margin=dict(l=1,r=1, b=10,t=20,pad = 5),
                        height = 350
                    )
    fig.update_xaxes(gridcolor="lightgrey")
    return fig


def transform_value(value):
    return 10 ** value