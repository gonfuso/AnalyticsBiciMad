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
from collections import Counter 
from wordcloud import WordCloud

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
    
    fig.update_layout(margin=dict(l=2,r=2, b=5,t=40,pad = 5), height = 160)

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

    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=1,r=15, b=10,t=20,pad = 5), height = 150)
    fig.update_yaxes(gridcolor="lightgrey")

    return fig


def pyramidDisplay(df, value):
    df["ageRange"] = df["ageRange"].replace([0,1,2,3,4,5,6],["Ind.","0-16","17-18", "19-26", "27-40", "41-65", "66+"])
    df = df[(df["travel_time"]<=1440) & (df["travel_time"]>0)]
    df1 =df[(df["travel_time"]>value[0]) & (df["travel_time"]<value[1])]
    df1["travel_time"] = df1["travel_time"]/60
    ageRange_1 = df1[df1["user_type"] == 1].groupby("ageRange").agg({"travel_time":"mean"})
    ageRange_2 = df1[df1["user_type"] == 2].groupby("ageRange").agg({"travel_time":"mean"})

    # traveltime ticks
    #traveltime_ticks = list(range(int(round(-max(max(ageRange_1["travel_time"]), max(ageRange_2["travel_time"])),-3)), int(round(max(max(ageRange_1["travel_time"]), max(ageRange_2["travel_time"])),-3)), 10))
    traveltime_ticks = list(range(-round(1440/60),round(1440/60),2))

    # Creating instance of the figure
    fig = go.Figure(go.Bar(y= ageRange_1.index, x = round(ageRange_1["travel_time"],1), 
                        name = 'Anuales', 
                        orientation = 'h',
                        marker_color = "#18bc9c",
                        ))

    
    # Adding Male data to the figure
    fig.add_trace((go.Bar(y= ageRange_2.index, x = round(ageRange_2["travel_time"]*-1,1), 
                        name = 'Ocasionales', 
                        orientation = 'h',
                        marker_color = "#395B64",
                        )))
        
        # Updating the layout for our graph
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)',
                        barmode='relative',
                        bargap = 0.0, bargroupgap = 0,
                        xaxis = dict(tickvals = traveltime_ticks,    
                        title = 'Media duración de trayectos (h)',
                        title_font_size = 14),
                        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),
                        margin=dict(l=1,r=1, b=10,t=20,pad = 5),
                        height = 300
                    )
    fig.update_xaxes(gridcolor="lightgrey")
    return fig

def mapDisplay(itinerarios_bases, distrito):
    df = itinerarios_bases[itinerarios_bases["Distrito_Salida"].isin(distrito)]
    df1 = df.groupby(["idunplug_station", "Distrito_Salida", "Barrio_Salida", "Número de Plazas_Salida", "Latitud_Salida", "Longitud_Salida"]).size().reset_index(name='Count')

    fig = px.scatter_mapbox(df1, lat="Latitud_Salida", lon="Longitud_Salida",  color = "Distrito_Salida", size=df1["Count"], 
                              zoom = 12, 
                            color_discrete_sequence=px.colors.qualitative.Prism, )
                        #color_discrete_sequence=[to_hex(c) for c in sns.color_palette('colorblind', 15)])
    # fig.update_traces(hovertemplate=None)

    fig.update_layout(
        #autosize=True,
        showlegend=True,
        
        height = 650,
        mapbox=dict(
            bearing=0,
            center=dict(
                lat=40.435,
                lon=-3.69
            ),
            zoom=11.5,
            style= 'carto-positron' # 'open-street-map'
        ),
         legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),
          margin=dict(l=1,r=1, b=10,t=20,pad = 5),
        hoverlabel_align = 'right'
    )

    return fig

def wordcloudDisplay(df): 
    df=df.astype({'Distrito_Llegada': str})
    barrios_llegada = df['Distrito_Llegada']

    barrios_llegada_wordcloud=["".join(i for i in palabra if not i.isdigit()) for palabra in barrios_llegada]
    barrios_frec=Counter(barrios_llegada_wordcloud)

    set(barrios_llegada_wordcloud)

    wordcloud = WordCloud (
                        background_color = 'white',
                        width = 400,
                        height = 300,
                        collocations=False, colormap="YlGnBu").generate_from_frequencies(barrios_frec)

    fig=px.imshow(wordcloud) # image show
    fig.update_layout(  height = 300, template="simple_white", yaxis={'visible':False}, xaxis={'visible':False}, margin=dict(l=0,r=0, b=0,t=0,pad = 5))

    return fig

def estacionalidadHoras(df):
    demanda = df.groupby("unplug_hourTime").size().reset_index(name='Count')
    demanda_agrupada = demanda.groupby(demanda["unplug_hourTime"].dt.hour).agg({'Count':'mean'})

    fig=go.Figure(go.Bar(
            x = demanda_agrupada.index,
            y = demanda_agrupada['Count'],
            marker_color = SetColor(demanda_agrupada)
        ))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', height = 150, margin = dict(l=10,r=10, b=1,t=10,pad = 5))
    fig.update_yaxes(gridcolor="lightgrey")

    return fig

def estacionalidadDias(df):
    demanda = df.groupby("unplug_hourTime").size().reset_index(name='Count')
    demanda_agrupada = demanda.groupby(demanda["unplug_hourTime"].dt.dayofweek).agg({'Count':'mean'})

    fig=go.Figure(go.Bar(
            x = ["L", "M", "X", "J", "V", "S", "D"],
            y = demanda_agrupada['Count'],
            marker_color = SetColor(demanda_agrupada)
        ))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', height = 150, margin = dict(l=10,r=10, b=1,t=10,pad = 5))
    fig.update_yaxes(gridcolor="lightgrey")
    #fig.update_xaxes(ticktext=["L", "M", "X", "J", "V", "S", "D"])

    return fig

def estacionalidadMeses(df):
    demanda = df.groupby("unplug_hourTime").size().reset_index(name='Count')
    demanda_agrupada = demanda.groupby(demanda["unplug_hourTime"].dt.month).agg({'Count':'mean'})
    fig=go.Figure(go.Bar(
            x = [ "Ago", "Sep", "Oct", "Nov", "Dec"],
            y = demanda_agrupada['Count'],
            marker_color = SetColor(demanda_agrupada)
        ))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', height = 150, margin = dict(l=10,r=10, b=1,t=10,pad = 5))
    fig.update_yaxes(gridcolor="lightgrey")
    #fig.update_xaxes(ticktext=["E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])

    return fig

def SetColor(df):
    values = df["Count"].tolist()
    color_list = []
    for i in values:
        if(i > 498):
            color_list.append("#18bc9c")
        else:
            color_list.append("lightgrey")

    return color_list

def mapRutasDisplay(itinerarios_bases, distrito): 
    df = itinerarios_bases[itinerarios_bases["Distrito_Salida"].isin(distrito)]
    cols_rutas=['Origen_destino','Latitud_Salida','Longitud_Salida','Distrito_Salida','Latitud_Llegada','Longitud_Llegada','Distrito_Llegada', 'idplug_station', 'idunplug_station' ]
    df_rutas=df[df['idplug_station']!=df['idunplug_station'] ].groupby(cols_rutas)['idplug_base'].count().to_frame().reset_index().sort_values('idplug_base', ascending=False)
    df_rutas.rename(columns={'idplug_base': 'viajes'}, inplace=True)
    
    topRutas=df_rutas.head(16)
    topRutas['ruta']=topRutas.apply(lambda x: sorted([x.Longitud_Salida, x.Latitud_Salida, x.Longitud_Llegada, x.Latitud_Llegada]), axis=1)
    topRutas['ruta']=topRutas['ruta'].apply(lambda x: ' '.join([str(word) for word in x]))
    cols_rutas=['Latitud_Salida','Longitud_Salida','Latitud_Llegada','Longitud_Llegada', 'ruta']
                
    topRutasUnicas= topRutas.groupby('ruta').apply(rutas).reset_index()
    cols_llegada_estacion=['Longitud_Llegada','Latitud_Llegada', 'Distrito_Llegada' ]
    cols_salida_estacion=['Longitud_Salida', 'Latitud_Salida','Distrito_Salida']
    cols_estaciones=['Longitud','Latitud', 'Distrito']

    estaciones_llegada=topRutas[cols_llegada_estacion]
    estaciones_salida=topRutas[cols_salida_estacion]
    estaciones_llegada.rename(columns=dict(zip(cols_llegada_estacion,cols_estaciones)) , inplace=True)
    estaciones_salida.rename(columns=dict(zip(cols_salida_estacion,cols_estaciones)) , inplace=True)

    top10estaciones0=pd.concat([estaciones_salida, estaciones_llegada], axis=0, ignore_index=True )
    top10estaciones0['count']=1
    
    topEstaciones=top10estaciones0.groupby(['Longitud','Latitud']).apply(top_estaciones).reset_index()

    fig = px.scatter_mapbox(topEstaciones, lat="Latitud", lon="Longitud",  zoom = 50)

    for i in range(topRutasUnicas.shape[0]): 
        valores=topRutasUnicas.iloc[i,:]

        fig.add_trace(
            go.Scattermapbox(
            mode = "markers+lines",
            lon = [valores['Longitud_Salida'], valores['Longitud_Llegada']],
            lat = [valores['Latitud_Salida'], valores['Latitud_Llegada']],
            line= {'width':valores['viajes']*0.005} ,
            name= 'Ruta '+str(1+i), 
            marker_color = px.colors.qualitative.Prism,

            ))

    fig.update_layout(
        autosize=True,
        hovermode='closest',
        showlegend=False,
        margin=dict(l=1,r=1, b=10,t=20,pad = 5),
        height = 650,
        mapbox=dict(
            bearing=0,
            center=dict(
                lat=40.435,
                lon=-3.69
            ),
            zoom=12,
            style= 'carto-positron', # 'open-street-map'    
        )
    )
    return fig


def rutas(df): 
        
    long_llegada=df['Longitud_Llegada'].iloc[0]
    lat_llegada=df['Latitud_Llegada'].iloc[0]
    long_salida=df['Longitud_Salida'].iloc[0]
    lat_salida=df['Latitud_Salida'].iloc[0]
    num_viajes=df['viajes'].sum()
    cols= ['Latitud_Salida','Longitud_Salida','Latitud_Llegada','Longitud_Llegada', 'viajes']
    datos=[lat_salida, long_salida,lat_llegada, long_llegada, num_viajes ]
    return pd.Series(dict(zip(cols,datos)))

def top_estaciones(df): 
        distrito= df['Distrito'].iloc[0]
        count=df['count'].sum()
        cols=['Distrito', 'count']
        datos=[distrito, count]
        return(pd.Series(dict(zip(cols,datos))))


def sunburstItinerarios(itinerarios_bases, N, M):
    estaciones_mas_concurridas = itinerarios_bases.groupby(["idunplug_station"]).size().reset_index().rename(columns={0:"count"}).sort_values(by=['count'], ascending = False).head(N).reset_index(drop=True)
    estaciones_mas_concurridas1 = itinerarios_bases[itinerarios_bases["idunplug_station"].isin(estaciones_mas_concurridas["idunplug_station"])]

    df_combinations = estaciones_mas_concurridas1.groupby(["idunplug_station", "Distrito_Llegada", "idplug_station"]).size().reset_index().rename(columns={0:"count"}).sort_values(by=['count'], ascending = False)

    topCombinaciones = pd.DataFrame()
    for i in df_combinations["idunplug_station"].unique():
        estacion_origen = df_combinations[df_combinations["idunplug_station"] == i]
        topCombinacionesi = estacion_origen.sort_values(by=['count'], ascending = False).head(M)
        topCombinaciones = topCombinaciones.append(topCombinacionesi)
    topCombinaciones.reset_index(drop=True)
    topCombinaciones.head()

    fig = px.sunburst(
        topCombinaciones,
        path = ["idunplug_station", "Distrito_Llegada", "idplug_station"],
        color = "idunplug_station",
        height=800,
        values='count',
        color_continuous_scale='YlGnBu'

    )
    fig.update_layout(margin=dict(l=1,r=1, b=10,t=20,pad = 5), showlegend=False)
    
    return fig
