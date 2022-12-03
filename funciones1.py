import pickle
import numpy as np
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