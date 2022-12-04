# funciones.oy> 
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash_core_components as dcc
from dash import html

def topNRutas(df, n_top ): 
    cols_rutas=['Origen_destino','Latitud_Salida','Longitud_Salida','Distrito_Salida','Latitud_Llegada','Longitud_Llegada','Distrito_Llegada', 'idplug_station', 'idunplug_station' ]
    df_rutas=df[df['idplug_station']!=df['idunplug_station'] ].groupby(cols_rutas)['return_date'].count().to_frame().reset_index().sort_values('return_date', ascending=False)
    df_rutas.rename(columns= {'return_date': 'viajes'},  inplace=True )
    topRutas=df_rutas.head(25)
    topRutas.loc[:,'ruta']=topRutas.apply(lambda x: sorted([x.Longitud_Salida, x.Latitud_Salida, x.Longitud_Llegada, x.Latitud_Llegada]), axis=1)
    topRutas.loc[:,'ruta']=topRutas['ruta'].apply(lambda x: ' '.join([str(word) for word in x]))
    
    def rutas(df): 
        
        long_llegada=df['Longitud_Llegada'].iloc[0]
        lat_llegada=df['Latitud_Llegada'].iloc[0]
        distrito_llegada=df['Distrito_Llegada'].iloc[0]
        
        'idplug_station',
        'idunplug_station'
        
        idplug_station=df['idplug_station'].iloc[0]
        idunplug_station=df['idunplug_station'].iloc[0]

        long_salida=df['Longitud_Salida'].iloc[0]
        lat_salida=df['Latitud_Salida'].iloc[0]
        distrito_salida=df['Distrito_Salida'].iloc[0]
        viajes=df['viajes'].sum()
        
        cols= ['idplug_station','idunplug_station','Latitud_Salida','Longitud_Salida','Distrito_Salida','Latitud_Llegada','Longitud_Llegada','Distrito_Llegada', 'viajes']
        datos=[idplug_station, idunplug_station, lat_salida, long_salida, distrito_salida, lat_llegada, long_llegada,distrito_llegada, viajes]
        return pd.Series(dict(zip(cols,datos)))
                
    topRutasFin= topRutas.groupby('ruta').apply(rutas).reset_index()
    return(topRutasFin.head(n_top))

def topEstaciones(df): 
    
    cols_llegada_estacion=['Longitud_Llegada','Latitud_Llegada', 'Distrito_Llegada', 'idplug_station' ]
    cols_salida_estacion=['Longitud_Salida', 'Latitud_Salida','Distrito_Salida', 'idunplug_station']
    cols_estaciones=['Longitud','Latitud', 'Distrito', 'numero']

    estaciones_llegada=df[cols_llegada_estacion]
    estaciones_salida=df[cols_salida_estacion]
    estaciones_llegada.rename(columns=dict(zip(cols_llegada_estacion,cols_estaciones)) , inplace=True)
    estaciones_salida.rename(columns=dict(zip(cols_salida_estacion,cols_estaciones)) , inplace=True)

    topEstaciones0=pd.concat([estaciones_salida, estaciones_llegada], axis=0, ignore_index=True )
    topEstaciones0.loc[:,'count']=1
    print(topEstaciones0['numero'])
    def top_estaciones(df): 
        distrito= df['Distrito'].iloc[0]
        #print(df['numero'])
        number= df['numero'].iloc[0]
        count=df['count'].sum()
        cols=['numero','Distrito', 'count']
        datos=[number, distrito, count]
        return(pd.Series(dict(zip(cols,datos))))
    topEstaciones=topEstaciones0.groupby(['Longitud','Latitud']).apply(top_estaciones).reset_index()

    return(topEstaciones)
    
def GráficoMapasRutas(df_itinerarios, n_top, tipo=None, estacion=None):
    if  type(df_itinerarios)==str: 
        data = [[-40, 3]]
        df = pd.DataFrame(data, columns=['lat', 'lon'])

        fig=px.scatter_mapbox(df,lon='lon', lat='lat' ,width = 500, height = 400)

        fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                title='Rutas más concurridas',
                autosize=True,
                hovermode='closest',
                showlegend=True,
                width = 425,
                height = 500,
                mapbox=dict(
                    bearing=0,
                    center=dict(
                        lat=40.425,
                        lon=-3.69),
                    zoom=11.3,
                    style= 'carto-positron' )# 'open-street-map'
                )
        

        return fig
    else: 
        
        top_rutas=topNRutas(df_itinerarios,n_top )
        top_estaciones=topEstaciones(top_rutas) 
        print('La estacion es: '+str(estacion))
        print(estacion)
        # print(top_estaciones.columns)
        print(top_estaciones['numero'])
        print(top_estaciones.dtypes)
        tamano_lines=0.005
        if tipo==0:
            top_estaciones2=top_estaciones[top_estaciones['numero']!=estacion]
        elif tipo==1: 
            top_estaciones2=top_estaciones[top_estaciones['numero']==estacion]
        else: 
            tamano_lines=0.005
            top_estaciones2=top_estaciones
        print(top_estaciones.shape)
            
        fig = px.scatter_mapbox(top_estaciones2, lat="Latitud", lon="Longitud",color='Distrito',width = 400, height = 400 )# zoom = 70, size='count'

        for i in range(top_rutas.shape[0]): 
            valores=top_rutas.iloc[i,:]

            fig.add_trace(
                go.Scattermapbox(
                mode = "lines",
                lon = [valores['Longitud_Salida'], valores['Longitud_Llegada']],
                lat = [valores['Latitud_Salida'], valores['Latitud_Llegada']],
                line= {'width':valores['viajes']*tamano_lines} ,
                name= 'Ruta '+str(1+i), 
                showlegend=False, 
                customdata=valores[['idplug_station','idunplug_station','viajes']], 
                text=valores[['idplug_station','idunplug_station','viajes']]),
                )
        
        fig.update_layout(hovermode="x unified")
        fig.update_layout(
            title='Rutas más concurridas',
            margin=dict(l=0, r=0, t=0, b=0),
            autosize=True,
            hovermode='closest',
            showlegend=True,
            # width = 500,
            # height = 425,
            mapbox=dict(
                bearing=0,
                center=dict(
                    lat=40.425,
                    lon=-3.69),
                zoom=11.3,
                style= 'carto-positron' )# 'open-street-map'
        )
        return fig
# funciones para situaciones

def filtrarHoraDiaSeman(sit, dia, hora): 
    sit_filt=sit[ (sit['weekDay']==dia) & (sit['hour']==hora)]
    cols_grup=['number', 'longitude', 'latitude', 'name', 'total_bases']
    sit_filt2=sit_filt.groupby(cols_grup )[['free_bases', 'dock_bikes']].mean()
    
    return sit_filt2.reset_index()

def GraficoSituacionMapa(situaciones, grafico): 
    dic_grafico={0:'free_bases', 1:'dock_bikes'}
    fig = px.scatter_mapbox(situaciones, lat="latitude", lon="longitude",  color = dic_grafico[grafico],  width = 400, height = 400, zoom = 12,
                            color_continuous_scale=px.colors.diverging.RdBu,
                            hover_data={'latitude':False,
                                        'longitude':False,
                                        'number': True,
                                        'name': True, 
                                        dic_grafico[grafico]: True, 
                                        'total_bases':True
                                        })
    fig.update_traces(mode="markers")
    fig.update_layout(hovermode="x unified")
    title= {0:'Bases libres por estacion', 1:'Bicis disponibles por estacion' }
    fig.update_layout(
        title=title[grafico],
        margin=dict(l=0, r=0, t=0, b=0),
        autosize=True,
        showlegend=True,
        #width = '%100',
        #height = '%100',
        mapbox=dict(
            bearing=0,
            center=dict(
                lat=40.425,
                lon=-3.69
            ),
            zoom=11.3,
            style= 'carto-positron' # 'open-street-map'
            
        ),
        hoverlabel_align = 'right'
    )
    return fig
# def workCloudGeneral(itinerarios_bases): 
    
#     itinerarios_bases=itinerarios_bases.astype({'Distrito_Llegada': str})
#     itinerarios_bases2=itinerarios_bases
#     itinerarios_bases2['Distrito_Llegada']=itinerarios_bases2['Distrito_Llegada'].apply(lambda x: x.replace('\xa0', ''))
#     barrios_llegada = itinerarios_bases2['Distrito_Llegada']


#     barrios_llegada_wordcloud=["".join(i for i in palabra if not i.isdigit()) for palabra in barrios_llegada]
#     barrios_frec=Counter(barrios_llegada_wordcloud)


#     wordcloud = WordCloud (
#                         background_color = 'white',
#                         width = 1000,
#                         height = 750,
#                         collocations=False).generate_from_frequencies(barrios_frec)

#     fig=px.imshow(wordcloud) # image show
#     fig.update_layout(width=1000, height=750)
#     return fig.to_image()

