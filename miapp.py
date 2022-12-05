import pandas as pd
import dash
from dash import Input, Output, dcc, html #ctx
import plotly.express as px
import dash_bootstrap_components as dbc
import pickle
import plotly.graph_objects as go

app = dash.Dash(__name__, use_pages=True,external_stylesheets=[dbc.themes.FLATLY, dbc.icons.BOOTSTRAP], 
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}],
                suppress_callback_exceptions=True
                )

sidebar = dbc.Card(
    [
        dbc.CardBody([
            dbc.NavItem(dbc.NavLink(html.I(className="bi bi-bicycle", style = {"font-size":"5rem"}), style={"text-align":"center"},href="https://www.bicimad.com/", external_link=True)),
            html.H3("BiciMAD",  style = {"text-align":"center"}),
            html.Hr(),
            html.P("Cuadro de mandos de red de bicicletas eléctricas de la Comunidad de Madrid", className = "lead", style={"font-size":"14px"}),
            dbc.Nav(
                children = [
                    dbc.NavLink([
                        html.Div(page["name"]),
                    ],
                    href=page["path"],
                    active="exact",
                    )
                    for page in dash.page_registry.values()
                ],
                vertical = True,
                pills = True,
            ),
        ], style={"margin-top":"0rem"}),
    ], color = "light",
    style = {"height":"100vh", "width":"13rem", "margin-left":"-1rem",  "position":"fixed"}    
)    

app.layout = dbc.Container([
    dbc.Row(
        [
            dbc.Col(            
                [
                    sidebar
                ], width = 2), 

            dbc.Col(
                [
                    dash.page_container
                ], width=10, style={"margin-left":"13rem"})
        ]
    )
], fluid=True)

if __name__ == "__main__":
    app.run_server(debug=True)