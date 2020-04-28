import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import dash_table
from dash.dependencies import Input, Output, State
import base64
import pymongo
import datetime as dt
import copy
import plotly.graph_objects as go
from controls import WELL_COLORS

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}])
colors = {
    'background': '#111111',
    'text': '#7FDBFF'}

app.config.suppress_callback_exceptions = False

# Create global chart template
mapbox_access_token = "pk.eyJ1IjoiamFja2x1byIsImEiOiJjajNlcnh3MzEwMHZtMzNueGw3NWw5ZXF5In0.fk8k06T96Ml9CLGgKmk81w"

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="",
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="light",
        center=dict(lon=-78.05, lat=42.54),
        zoom=7,
    ),
)
test_png = './logoObservatorioEPT.jpeg'
# test_png = r'.\logoObservatorioEPT.jpeg'
test_base64 = base64.b64encode(open(test_png, 'rb').read()).decode('ascii')

myclient = pymongo.MongoClient("mongodb://localhost:27017/")

# _______________________________________________________________________________________________________________________

# BANCO DE DADOS
mydb = myclient['Rede']
mycol = mydb['Instituicoes']
cursor = mycol.find({}, {"_id": 0})
df = pd.DataFrame(list(cursor))
campus = df['Instituicao'].dropna().unique()

mydb3 = myclient['Professores']
mycol3 = mydb3['CEFET']
cursor3 = mycol3.find({}, {"_id": 0})
df3 = pd.DataFrame(list(cursor3))
mycolDoc = mydb3['Todos']
cursorDoc = mycolDoc.find({}, {"_id": 0})
docentes = pd.DataFrame(list(cursorDoc))
docentes = docentes.drop("CEP", axis=1)
docentes = docentes.drop("Cidade", axis=1)
docentes = docentes[['ID-Lattes', 'Nome', 'Nível', 'Área', 'Linha de pesquisa', 'Instituicao',
                     'Patente']]  # organiza ordem exibição TAble Docentes

# df = df[['preço', 'vitamina', 'fruta']]

mydb4 = myclient['Rede']
mycol4 = mydb4['Cursos']
cursor4 = mycol4.find({}, {"_id": 0})
df4 = pd.DataFrame(list(cursor4))
instituicoes = sorted(df4['Instituição'].dropna().unique())
list_inst = list(instituicoes)
list_inst = np.insert(list_inst, 0, 'Todas')

mydb5 = myclient['MinasGerais']
mycol5 = mydb5['CidadesRede']
cursor5 = mycol5.find({}, {"_id": 0})
df5 = pd.DataFrame(list(cursor5))
cidadesRede = df5['nome'].dropna().unique()
cidadesRede = np.insert(cidadesRede, 0, 'Todas')

mydb6 = myclient['MinasGerais']
mycol6 = mydb6['Top10AtividadesPorCidadesRede']
cursor6 = mycol6.find({}, {"_id": 0})
df6 = pd.DataFrame(list(cursor6))
secclass = df6.groupby(['industry_class', 'industry_section']).size().reset_index()
secclass = secclass[['industry_class', 'industry_section']]
classe = df6['industry_class'].dropna().unique()
# classe = np.insert(classe, 0, 'Todas')
anos = list(df6['year'].dropna().unique())
# del anos[12]  #ultimo vazio, conferir  para bd novo

mydb7 = myclient['MinasGerais']
mycol7 = mydb7['AtividadesPorCidadeRede']
cursor7 = mycol7.find({}, {"_id": 0})
df7 = pd.DataFrame(list(cursor7))
secclassTot = df7.groupby(['industry_class', 'industry_section']).size().reset_index()
secclassTot = secclass[['industry_class', 'industry_section']]
classeTotal = df7['industry_class'].dropna().unique()

# _______________________________________________________________________________________________________________________

parametrosAtiv = ['Ganho de Oportunidade', 'Renda Mensal Média', 'Empregos', 'Estabelecimentos',
                  'Crescimento de Salários']

# Variaveis auxiliares
niveis = sorted(df4['Nível'].dropna().unique())
tipos = sorted(df4['Articulação'].str[0].dropna().unique())
# list_inst = ['Todas', 'CEFET', 'IFMG', 'IFNMG', 'IFSUL', 'IFSudeste', 'IFTM']
list_cursos = df4

# Soma Num Docentes
cont_docentes_total = 0
for x in list_inst:
    mycol3 = mydb3[x]
    cursor3 = mycol3.find({}, {"_id": 0})
    cont_docentes = pd.DataFrame(list(cursor3))
    cont_docentes_total += len(cont_docentes)

# PATENTES
df31 = df3.drop("Área", axis=1)
dfp = df31
lattes = df31['ID-Lattes'].dropna().unique()
nome = df31['Nome'].dropna().unique()
nm = []
patente = []

for x in df3['Patente'].dropna().unique():
    if x != '':
        patente.append(x)

area = mycol3.distinct("Área")
nivel = mycol3.find({}, {"_id": 0, "Nome": 1, "Nível": 1})
iid = mycol3.distinct("ID-Lattes")
pat = mycol3.distinct("Patente")

app.layout = html.Div([

    dcc.Store(id="aggregate_data"),
    # empty Div to trigger javascript file for graph resizing
    html.Div(id="output-clientside"),
    html.Div([
        # CABEÇALHO
        html.Div([
            html.Img(src='data:image/png;base64,{}'.format(test_base64),
                     className="app__logo",
                     style={
                         "height": "115px",
                         "width": "auto",
                         "margin-bottom": "10px",
                     },
                     )
        ], className="one column"),
        # CABEÇALHO
        html.Div([
            html.Div([
                html.H4("OBSERVATÓRIO DA EDUCAÇÃO PROFISSIONAL E TECNOLÓGICA",
                        style={
                            "margin-bottom": "0px"}),
                html.H6("Minas Gerais",
                        style={"margin-top": "0px"}),
            ], className="twelve columns", id="title"),
        ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"}),

        html.Hr(),

        html.Div([
            dcc.Tabs(id="tabs", children=[
                # TAB REDE
                dcc.Tab(label='REDE', children=[
                    # CABEÇALHO TAB REDE
                    html.Div([
                        html.Div([
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.H5("""Instituição """,
                                                    style={'margin-right': '2em'})
                                        ],
                                    ),
                                    dcc.Dropdown(
                                        id="instituicao_dropd",
                                        options=[{'label': i, 'value': i} for i in list_inst],
                                        # multi=True,
                                        value='Todas',
                                        # disabled=True,
                                        # searchable=False,
                                        placeholder="Selecione uma instituição",
                                        clearable=False,  # impede entrada invalida e/ou vazia
                                        className="dcc_control",
                                        style=dict(
                                            width='100%',
                                            height='30px',
                                            verticalAlign="middle"
                                        )
                                    ),
                                ],
                                style=dict(display='flex')
                            ),

                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.H5("""Campus""",
                                                    style={'margin-right': '2.8em'})
                                        ],
                                    ),

                                    dcc.Dropdown(
                                        id="campus_dropd",
                                        # options=[],
                                        # multi=True,
                                        value='Todos',
                                        disabled=True,
                                        # searchable=False,
                                        placeholder="Todos",
                                        clearable=False,  # impede entrada invalida e/ou vazi
                                        className="dcc_control",
                                        style=dict(
                                            width='100%',
                                            height='30px',
                                            verticalAlign="middle"
                                        )
                                    ),

                                ],
                                style=dict(display='flex')
                            ),

                        ],
                            className="pretty_container four columns",
                            id="cross-filter-options",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [html.H5(id="campusText"), html.H6(id="auxC", children=[""])],
                                            id="campus",
                                            className="mini_container",
                                            style={"flex": "2",
                                                   "text-align": "center"},
                                        ),
                                        html.Div(
                                            [html.H5(id="cursosText"), html.H6("Cursos")],
                                            id="Cursos",
                                            className="mini_container",
                                            style={"flex": "2",
                                                   "text-align": "center"},
                                        ),
                                        html.Div(
                                            [html.H5(id="docentesText"), html.H6("Docentes")],
                                            id="docentes",
                                            className="mini_container",
                                            style={"flex": "2",
                                                   "text-align": "center"},
                                        ),
                                    ],
                                    id="info-container",
                                    className="row container-display",
                                ),
                            ],
                            id="right-column",
                            className="eight columns",
                        ),
                    ], className="row flex-display",
                    ),
                    # PACOTE - CURSOS
                    html.Div([
                        html.Div([
                            html.H5("CURSOS", className="control_label"),
                            html.Hr(),
                            dcc.RadioItems(
                                id="nivel_selector",
                                options=[
                                    {"label": "Selecionar Nível de Formação", "value": "inst"},
                                    {"label": "Todos ", "value": "all"},
                                ],
                                value="all",
                                # labelStyle={"display": "inline-block"},
                                className="dcc_control",
                            ),
                            dcc.Dropdown(
                                id="nivel_dropd",
                                options=[{'label': i, 'value': i} for i in niveis],
                                multi=True,
                                # value=niveis,
                                disabled=True,
                                # searchable=False,
                                placeholder="Selecione um nível de formação",
                                className="dcc_control",
                                style={'height': '200px', 'width': '100%', 'overflow': 'scroll'}
                            ),
                            html.Hr(),
                            dcc.RadioItems(
                                id="tipo_selector",
                                options=[
                                    {"label": "Selecionar Articulação", "value": "inst"},
                                    {"label": "Todos ", "value": "all"},
                                ],
                                value="all",
                                # labelStyle={"display": "inline-block"},
                                className="dcc_control",
                            ),
                            dcc.Dropdown(
                                id="tipo_dropd",
                                options=[{'label': i, 'value': i} for i in tipos],
                                # {"label": "All ", "value": "all"}],
                                multi=True,
                                # value=tipos,
                                disabled=True,
                                # searchable=False,
                                placeholder="Selecione um tipo/articulação",
                                className="dcc_control",
                                style={'height': '200px', 'width': '100%', 'overflow': 'scroll'},
                                # optionHeight=20,
                            ),
                        ],
                            className="pretty_container three columns",
                            style={'max-height': '870px'},
                            id="cursos-filter-options",
                        ),
                        html.Div([
                            # Mapa
                            html.Div(
                                children=dcc.Graph(
                                    id='map_graph',
                                    figure={
                                        'data': [{
                                            'text': df.nome + ", " + df.Instituicao,
                                            'lat': df.latitude,
                                            'lon': df.longitude,
                                            'type': 'scattermapbox',
                                            'mode': 'markers',
                                            'marker': go.scattermapbox.Marker(size=14, colorscale='Rainbow',
                                                                              color=list(range(len(df.codigo_ibge)))),
                                            'hover_name': df5.nome,
                                            'hoverinfo': 'text',

                                        }],
                                        'layout': {
                                            'mapbox': {
                                                'accesstoken': (
                                                        'pk.eyJ1IjoiY2hyaWRkeXAiLCJhIjoiY2ozcGI1MTZ3M' +
                                                        'DBpcTJ3cXR4b3owdDQwaCJ9.8jpMunbKjdq1anXwU5gxIw'
                                                ),
                                                # 'style': "satellite",  #IMAGEM SATELITE
                                                # 'style': 'light',
                                                'style': "outdoors",  # IMAGEM CARTOGRAFICA
                                                'autosize': 'true',
                                                'bearing': 0,
                                                # 'center': [ -70, 30],  #BH: -19.841644, -43.986511
                                                'center': {
                                                    'lat': -18.341,
                                                    'lon': -43.98
                                                },
                                                'zoom': 5,
                                                'showlegend': True,
                                            },

                                            'margin': {
                                                'l': 0, 'r': 0, 'b': 0, 't': 0
                                            },
                                            'hovermode': 'closest',
                                            'max-height': '380px'
                                        }
                                    },
                                    style={'max-height': '380px'},
                                ),
                                className="pretty_container seven columns ",
                                style={'max-height': '400px', 'width': '50%'},
                            ),
                            # Cursos Pie
                            html.Div(
                                [dcc.Graph(id="cursos_graph")],
                                className="pretty_container seven columns ",
                                style={'height': '400px', 'width': '45%'},
                            ),
                            # Cursos Tabela
                            html.Div([
                                dash_table.DataTable(
                                    id='cursos_table',
                                    columns=[{'name': i, 'id': i} for i in list_cursos],
                                    data=list_cursos.to_dict("records"),
                                    style_data_conditional=[
                                        {
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': 'rgb(248, 248, 248)'
                                        }
                                    ],
                                    style_header={
                                        'backgroundColor': 'rgb(230, 230, 230)',
                                        'fontWeight': 'bold'
                                    },
                                    style_cell={
                                        'minWidth': '100px',
                                        'maxWidth': '190px',
                                        'textAlign': 'left',
                                        'overflow': 'hidden',
                                        'textOverflow': 'ellipsis',
                                    },
                                    style_cell_conditional=[
                                        {'if': {'column_id': 'Date'},
                                         'width': '40%'},
                                        {'if': {'column_id': 'Region'},
                                         'width': '40%'},
                                    ],
                                    fixed_rows={'headers': True, 'data': 0},
                                    style_table={'max-height': '220px', 'width': '1050px'},
                                    # export_format='xlsx',
                                    # export_headers='display',
                                    # merge_duplicate_headers=True,
                                ),
                            ],
                                className="pretty_container eleven columns",
                                style={'height': '300px', 'width': '97%'},
                            ),
                        ],
                            className="nine columns",
                            style={'max-height': '460px',
                                   'verticalAlign': "middle"},
                        ),

                    ],
                        className="row flex-display",
                        # style={'max-height': '460px', 'flex-grow': '1'},
                    ),

                    # PACOTE - DOCENTES
                    html.Div([
                        html.Div([
                            html.H5("DOCENTES", className="control_label"),
                            html.Hr(),
                            dcc.RadioItems(
                                id="nivelDoc_selector",
                                options=[
                                    {"label": "Selecionar nível de formação", "value": "inst"},
                                    {"label": "Todos ", "value": "all"},
                                ],
                                value="all",
                                # labelStyle={"display": "inline-block"},
                                className="dcc_control",
                            ),
                            dcc.Dropdown(
                                id="nivelDoc_dropd",
                                options=[],
                                multi=True,
                                value=niveis,
                                disabled=True,
                                # searchable=False,
                                placeholder="Selecione um nível de formação",
                                className="dcc_control",
                                # style={'display': 'block'}
                            ),

                            html.Hr(),
                            dcc.RadioItems(
                                id="areaDoc_selector",
                                options=[
                                    {"label": "Selecionar Área do Conhecimento", "value": "inst"},
                                    {"label": "Todos ", "value": "all"},
                                ],
                                value="all",
                                # labelStyle={"display": "inline-block"},
                                className="dcc_control",
                            ),
                            dcc.Dropdown(
                                id="areaDoc_dropd",
                                options=[{'label': i, 'value': i} for i in tipos],
                                # {"label": "All ", "value": "all"}],
                                multi=True,
                                value=tipos,
                                disabled=True,
                                # searchable=False,
                                placeholder="Selecione uma area do conhecimento",
                                className="dcc_control",

                                style={'height': '300px', 'width': '100%', 'overflow': 'scroll'}
                            ),
                        ],
                            className="pretty_container three columns",
                            style={'height': '700px'},
                            id="docentes-filter-options",
                        ),

                        html.Div([
                            html.Div(
                                [dcc.Graph(id="docentes_graph")],
                                className="pretty_container",
                                style={'max-height': '360px'},
                            ),
                            html.Div([
                                dash_table.DataTable(
                                    id='docentes_table',
                                    columns=[{'name': i, 'id': i} for i in docentes],
                                    data=docentes.to_dict("records"),
                                    style_data_conditional=[
                                        {
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': 'rgb(248, 248, 248)'
                                        }
                                    ],
                                    style_header={
                                        'backgroundColor': 'rgb(230, 230, 230)',
                                        'fontWeight': 'bold'
                                    },
                                    style_cell={
                                        'minWidth': '100px',
                                        'maxWidth': '400px',
                                        'textAlign': 'left',
                                        'overflow': 'hidden',
                                        'textOverflow': 'ellipsis',
                                    },
                                    style_cell_conditional=[
                                        {'if': {'column_id': 'Date'},
                                         'width': '40%'},
                                        {'if': {'column_id': 'Region'},
                                         'width': '40%'},
                                    ],
                                    fixed_rows={'headers': True, 'data': 0},
                                    style_table={'height': '230px', 'width': '1079px'},
                                    # export_format='xlsx',
                                    # export_headers='display',
                                    # merge_duplicate_headers=True
                                ),
                            ], className="pretty_container eleven columns",
                                style={'height': '300px', 'width': '1099px'},
                            ),
                        ],
                            className="nine columns",
                            style={'max-height': '460px',
                                   'verticalAlign': 'middle'},
                        ),
                    ],
                        className="row flex-display",
                    ),
                ]),

                # TAB ATIVIDADES ECONOMICAS
                dcc.Tab(
                    label='ATIVIDADES ECONÔMICAS',
                    children=[
                        # CABEÇALHO TAB ATIV ECON
                        html.Div([
                            html.Div([
                                html.Hr(style={'margin': '15px'}),
                                # Principais Atv Econ
                                html.Div([
                                    dcc.RadioItems(
                                        id="ativ_selector",
                                        options=[
                                            {"label": "Minas Gerais", "value": "all"},
                                            {"label": "Selecionar Cidade", "value": "inst"},
                                        ],
                                        value="all",
                                        labelStyle={"display": "inline-block"},
                                        className="dcc_control",
                                    ),
                                    html.Div(
                                        [
                                            dcc.Dropdown(
                                                id="cidade_dropd",
                                                options=[{'label': i, 'value': i} for i in cidadesRede],
                                                # multi=True,
                                                value="Todas",
                                                disabled=True,
                                                # searchable=False,
                                                placeholder="Selecione uma cidade",
                                                clearable=False,  # impede entrada invalida e/ou vazia
                                                className="dcc_control",
                                                style=dict(
                                                    width='100%',
                                                    # verticalAlign="middle"
                                                )
                                            ),
                                        ],
                                        style=dict(display='flex')
                                    ),

                                    html.Hr(style={'margin': '15px'}),

                                    html.H5("Principais Atividades Econômicas", className="control_label"),

                                    html.Hr(style={'margin': '15px'}),

                                    # Tabela TOP10 Ativ

                                    dash_table.DataTable(
                                        id='top10ativ_table',
                                        columns=[{'name': 'Seção', 'id': 'industry_section'},
                                                 {'name': 'Classe', 'id': 'industry_class'}],
                                        data=secclass.to_dict("records"),
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(248, 248, 248)'
                                            }
                                        ],

                                        style_header={
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold',
                                            'textAlign': 'center',
                                        },
                                        style_cell={
                                            'minWidth': '350px',
                                            'maxWidth': '490px',
                                            'textAlign': 'center',
                                            'overflow': 'hidden',
                                            # 'textOverflow': 'ellipsis',
                                        },
                                        fixed_rows={'headers': True, 'data': 0},
                                        style_table={'height': '360px', 'width': '760px'},
                                        # export_format='xlsx',
                                        # export_headers='display',
                                        # merge_duplicate_headers=True,
                                    ),

                                    html.Hr(style={'margin': '25px'}),

                                    # GRafico GERAL
                                    dcc.Dropdown(
                                        id='parametroAtiv-dropd',
                                        options=[{'label': i, 'value': i} for i in parametrosAtiv],
                                        value=parametrosAtiv[0],
                                    ),
                                    dcc.Graph(
                                        id='geral-graph',
                                        # hoverData={'points': [{'customdata': 'Japan'}]}
                                    ),


                                    # html.Hr(style={'margin': '25px'}),

                                ],
                                    style={'width': '46%', 'display': 'inline-block'}),

                                html.Div([
                                    dcc.Dropdown(
                                        id='ativ-dropd',
                                        options=[{'label': i, 'value': i} for i in classe],
                                        value=classe[0],
                                        placeholder="",
                                        clearable=False,  # impede entrada invalida e/ou vazia
                                    ),

                                    html.Hr(style={'margin': '15px'}),

                                    # GRAFICOS ATIV INDIVIDUAL
                                    html.Div([
                                        dcc.Graph(id='rendaMed-graph'),
                                        dcc.Graph(id='numEst-graph'),
                                    ], style={'display': 'inline-block'}),
                                ], style={'width': '46%', 'float': 'right', 'display': 'inline-block',
                                          'margin': '43px','height': '1200px' })
                            ], style={
                                'height': '1400px',
                                'borderBottom': 'thin lightgrey solid',
                                'backgroundColor': 'rgb(250, 250, 250)',
                                'padding': '10px 5px',
                                'width': '1610px',

                            }),

                        ], className="row flex-display",
                            style={'width': '1600px'},

                        ),

                    ],  # style={'width': '2700px'},
                )
            ])
        ], className="tabs__container"),
    ]), ], id="mainContainer",
    style={"display": "flex",
           "flex-direction": "column",
           "margin": "0%",
           'width': '100%'})


# Cabeçalho dropdown
@app.callback(
    [
        Output("auxC", "children"),
        Output("campusText", "children"),
        Output("cursosText", "children"),
        Output("docentesText", "children"),
        Output('campus_dropd', 'options'),
        Output('campus_dropd', 'disabled'),
        Output('campus_dropd', 'value'),
        Output('nivel_selector', 'value'),
        Output('nivelDoc_selector', 'value'),

    ],
    [Input("instituicao_dropd", "value")], )
def update_top(selector):
    if selector == 'Todas':
        cont_campus = len(df4['Instituição'].dropna().unique())
        cont_cursos = len(df4['Curso'])

        # Soma Num Docentes
        cont_docentes_total = 0
        mycol3 = mydb3['Todos']
        cursor3 = mycol3.find({}, {"_id": 0})
        cont_docentes = pd.DataFrame(list(cursor3))
        cont_docentes_total += len(cont_docentes)
        return 'Instituições', cont_campus, cont_cursos, cont_docentes_total, [], True, 'Todos', 'all', 'all'  # , 'all'

    elif (selector != 'Todas') and (selector in list_inst):
        cont_campus = len(df[df['Instituicao'] == selector])
        cont_cursos = len(df4[df4['Instituição'] == selector])
        mycol3 = mydb3[selector]
        cursor3 = mycol3.find({}, {"_id": 0})
        cont_docentes = len(pd.DataFrame(list(cursor3)))
        instituicao = df4[df4['Instituição'] == selector]
        campus = sorted(instituicao["Campus"].dropna().unique())
        campus = np.insert(campus, 0, 'Todos')
        tiposInst = sorted(instituicao['Articulação'].str[0].dropna().unique())

        return 'Campus', cont_campus, cont_cursos, cont_docentes, [{'label': i, 'value': i} for i in
                                                                   campus], False, 'Todos', 'all', 'all'  # , 'all'


# habilita dropd Articulaçao - ABA REDE
@app.callback(
    Output('tipo_dropd', 'disabled'),
    [Input("tipo_selector", "value")])
def display_tipo(selector):
    if selector == "all":
        return True
    elif selector == "inst":
        return False


# habilita dropd Nivel - ABA REDE
@app.callback(
    Output('nivel_dropd', 'disabled'),
    [Input('nivel_selector', 'value')])
def display_nivel(selector):
    if selector == "all":
        return True
    else:
        return False


# Grafico Cursos
@app.callback(
    Output("cursos_graph", "figure"),
    [Input("instituicao_dropd", "value"),
     Input("campus_dropd", "value")], )
def make_figure_cursos(selector_inst, selector_campus):
    layout_pie = copy.deepcopy(layout)

    if selector_inst == 'Todas':
        instituicao = df4
        niveis = pd.Series(sum([item for item in df4.Articulação], [])).value_counts()

        data = [
            dict(
                type="pie",
                title='Articulações',
                labels=niveis.index,
                values=niveis.values,
                name="Nível de Formação",
                hoverinfo="label+value+percent",
                textinfo="label",
                hole=0.35,
                domain={"x": [0, 1], "y": [0.2, 1]},
                showlegend=False),
        ]
        layout_pie["font"] = dict(color="#777777")
        layout_pie["height"] = '380'
        figure = dict(data=data, layout=layout_pie)
        return figure
    else:
        if (selector_inst in list_inst) and (selector_campus == "Todos"):
            instituicao = df4[df4['Instituição'] == selector_inst]
            niveis = pd.Series(sum([item for item in instituicao.Articulação], [])).value_counts()
            data = [
                dict(
                    type="pie",
                    title='Articulações',
                    labels=niveis.index,
                    values=niveis.values,
                    name="Nível de Formação",
                    hoverinfo="label+value+percent",
                    textinfo="label",
                    hole=0.35,
                    domain={"x": [0, 1], "y": [0.2, 1]},
                    showlegend=False)
            ]
            layout_pie["font"] = dict(color="#777777")
            layout_pie["height"] = '380'
            figure = dict(data=data, layout=layout_pie)

            return figure

        elif (selector_campus != 'Todos') and (selector_inst in list_inst):
            instituicao = df4[df4['Instituição'] == selector_inst]
            campus = instituicao[instituicao['Campus'] == selector_campus]
            niveis = pd.Series(sum([item for item in campus.Articulação], [])).value_counts()
            data = [
                dict(
                    type="pie",
                    title='Articulações',
                    labels=niveis.index,
                    values=niveis.values,
                    name="Nível de Formação",
                    hoverinfo="label+value+percent",
                    textinfo="label",
                    hole=0.35,
                    domain={"x": [0, 1], "y": [0.2, 1]},
                    showlegend=False)
            ]
            # layout_pie["title"] = "CURSOS"
            layout_pie["font"] = dict(color="#777777")
            layout_pie["height"] = '380'
            domain = {"x": [0.1, 0.9], "y": [0.1, 0.9]},
            figure = dict(data=data, layout=layout_pie)
            return figure


# Dropdown Cursos
@app.callback(
    [Output("nivel_dropd", "value"),
     Output("tipo_dropd", "value"),
     Output('cursos_table', 'data')],
    [Input('campus_dropd', 'value'),
     Input("instituicao_dropd", "value")])
def update_cursosDropdown(selector_campus, selector_inst):
    instituicao = df4[df4['Instituição'] == selector_inst]
    campus = sorted(instituicao["Campus"].dropna().unique())
    niveis = sorted(df4['Nível'].dropna().unique())
    #tipos = sorted(df4['Articulação'].dropna().unique())

    if selector_inst == "Todas":
        niveis = sorted(df4['Nível'].dropna().unique())
        tipos = pd.Series(sum([item for item in df4['Articulação']], [])).value_counts()
        return list(niveis), tipos.index, list_cursos.to_dict("rows")

    elif (selector_inst in list_inst) and (selector_campus == "Todos"):
        instituicao = df4[df4['Instituição'] == selector_inst]
        niveis = sorted(instituicao['Nível'].dropna().unique())
        tipos = pd.Series(sum([item for item in instituicao.Articulação], [])).value_counts()
        return list(niveis), tipos.index, instituicao.to_dict("rows")

    elif (selector_inst in list_inst) and (selector_campus != 'Todos'):
        instituicao = df4[df4['Instituição'] == selector_inst]
        campus = instituicao[instituicao['Campus'] == selector_campus]
        niveis = sorted(campus['Nível'].dropna().unique())
        tipos = pd.Series(sum([item for item in campus.Articulação], [])).value_counts()
        return list(niveis), tipos.index, campus.to_dict("rows")


# Grafico Docentes
@app.callback(
    Output("docentes_graph", "figure"),
    [Input("instituicao_dropd", "value")], )
def make_pie_figure_docentes(selector):
    layout_pie = copy.deepcopy(layout)
    cpat = 0
    if selector == 'Todas':
        list_aux = list_inst[1:-1]
        for x in list_aux:
            mycol3 = mydb3[x]
            cursor3 = mycol3.find({}, {"_id": 0})
            iid = mycol3.distinct("ID-Lattes")
            pat = mycol3.distinct("Patente")
            area = docentes['Área'].str[0].value_counts()
            nivel = docentes['Nível'].value_counts()
            if pat is not None or pat is not '':
                for x in pat:
                    if x != 0:
                        cpat += 1
        data = [
            dict(
                type="pie",
                title='Nível',
                labels=nivel.index,
                showlegend=True,
                values=nivel.values,
                name="Nível Profissional",
                hoverinfo="label+value+percent",
                textinfo="percent",
                hole=0.4,
                # marker=dict(colors=["#fac1b7", "#a9bb95", "#92d8d8"]),
                marker=dict(colors=["#FDBF6F", "#FC9272", "#D0D1E6", "#FFA62F"]),
                domain={"x": [0, 0.50], "y": [0.1, 0.9]},
            ),
            dict(
                type="pie",
                title='Área',
                labels=area.index,
                showlegend=False,
                values=area.values,
                name="Áreas do Conhecimento",
                hoverinfo="label+value+percent",
                textinfo="none",
                hole=0.4,
                marker=dict(colors=["#FFEDA0", '#FA9FB5', '#A1D99B', "#67BD65", "#BFD3E6", "#B3DE69"]),
                # marker=dict(colors=[WELL_COLORS[i] for i in lista]),
                domain={"x": [0.45, 1.2], "y": [0, 1.2]},
            )]

        # layout_pie["title"] = "DOCENTES"
        layout_pie["font"] = dict(color="#777777")
        layout_pie["legend"] = dict(
            font=dict(color="#212121", size="11"), orientation="h", bgcolor="rgba(0,0,0,0)"
        )
        layout_pie["height"] = '350'

        figure = dict(data=data, layout=layout_pie)
        return figure

    elif selector in list_inst:
        mycol3 = mydb3[selector]
        cursor3 = mycol3.find({}, {"_id": 0})
        df3 = pd.DataFrame(list(cursor3))
        iid = mycol3.distinct("ID-Lattes")
        pat = mycol3.distinct("Patente")
        area = docentes['Área'].str[0].value_counts()
        nivel = docentes['Nível'].value_counts()
        if pat is not None or pat is not '':
            for x in pat:
                if x != 0:
                    cpat += 1

        data = [
            dict(
                type="pie",
                title='Nível',
                labels=nivel.index,
                showlegend=True,
                values=nivel.values,
                name="Nível Profissional",
                hoverinfo="label+value+percent",
                textinfo="none",
                hole=0.4,
                # marker=dict(colors=["#fac1b7", "#a9bb95", "#92d8d8"]),
                marker=dict(colors=["#FDBF6F", "#FC9272", "#D0D1E6", "#FFA62F"]),
                domain={"x": [0, 0.50], "y": [0.1, 0.9]},
            ),
            dict(
                type="pie",
                title='Área',
                labels=area.index,
                showlegend=False,
                values=area.values,
                name="Áreas do Conhecimento",
                hoverinfo="label+value+percent",
                textinfo="none",
                hole=0.4,
                marker=dict(colors=["#FFEDA0", '#FA9FB5', '#A1D99B', "#67BD65", "#BFD3E6", "#B3DE69"]),
                # marker=dict(colors=[WELL_COLORS[i] for i in lista]),
                domain={"x": [0.45, 1.2], "y": [0, 1.2]},
            )]
        # layout_pie["title"] = "DOCENTES"
        layout_pie["font"] = dict(color="#777777")
        layout_pie["legend"] = dict(font=dict(color="#212121", size="11"), orientation="h", bgcolor="rgba(0,0,0,0)")
        layout_pie["height"] = '350'

        figure = dict(data=data, layout=layout_pie)
        return figure


@app.callback(
    Output('nivelDoc_dropd', 'disabled'),
    [Input("nivelDoc_selector", "value")])
def display_status(selector):
    if selector == "all":
        return True
    elif selector == "inst":
        return False


@app.callback(
    Output('areaDoc_dropd', 'disabled'),
    [Input("areaDoc_selector", "value")])
def display_status(selector):
    if selector == "all":
        return True
    elif selector == "inst":
        return False


@app.callback([
    Output('docentes_table', 'data'),
    Output('nivelDoc_dropd', 'value'),
    Output("nivelDoc_dropd", "options"),
    Output('areaDoc_dropd', 'value'),
    Output('areaDoc_dropd', 'options')],
    [Input("instituicao_dropd", "value")])
def update_docentesTable(selector_inst):
    if selector_inst == "Todas":
        niveisDoc = sorted(docentes['Nível'].dropna().unique())
        mycolDoc = mydb3['Todos']
        area = mycolDoc.distinct("Área")
        return docentes.to_dict("rows"), list(niveisDoc), [{'label': i, 'value': i} for i in niveisDoc], list(area), [
            {'label': i, 'value': i} for i in area]

    elif (selector_inst != "Todas") and (selector_inst in list_inst):
        docentesCampus = docentes[docentes['Instituicao'] == selector_inst]
        mycolDoc = mydb3[selector_inst]
        niveisDocCamp = mycolDoc.distinct("Nível")
        area = mycolDoc.distinct("Área")
        return docentesCampus.to_dict("rows"), list(niveisDocCamp), [{'label': i, 'value': i} for i in
                                                                     niveisDocCamp], list(area), [
                   {'label': i, 'value': i} for i in area]


# Habilita dropdown Cidades - ABA ATIVIDADES | Atribui valor cidades para Ativ_dropd
@app.callback(
    [Output('cidade_dropd', 'disabled'),
     Output('cidade_dropd', 'value')],
    [Input("ativ_selector", "value")])
def display_status(selector):
    if selector == "all":
        return True, "Todas"
    elif selector == "inst":

        return False, cidadesRede[1],


# GRAFICO GERAL  - ABA ATIVIDADES
@app.callback(
    Output('geral-graph', 'figure'),
    [Input('cidade_dropd', 'value'),
     Input('ativ_selector', 'value'),
     Input('parametroAtiv-dropd', 'value')])
# dash.dependencies.Input('crossfilter-year--slider', 'value')])
# 'Ganho de Oportunidade', 'Renda Mensal Média', 'Empregos', 'Estabelecimentos', 'Crescimento de Salários'

def update_graph(selector_cidade, selector_ativ, selector_param):
    if selector_param == 'Ganho de Oportunidade':
        param = 'opp_gain'
    elif selector_param == 'Renda Mensal Média':
        param = 'wage_avg'
    elif selector_param == 'Empregos':
        param = 'num_jobs'
    elif selector_param == 'Estabelecimentos':
        param = 'num_emp'
    elif selector_param == 'Crescimento de Salários':
        param = 'wage_growth'
    if selector_cidade == 'Todas':
        dff = df6
        if param in dff.columns:
            return {
                'data': [dict(
                    x=dff['year'],
                    y=dff[param],
                    text=dff['industry_class'] + ' \n' + dff.cidade,
                    mode='markers',  # marcação vertical
                    marker=go.scattermapbox.Marker(size=14, colorscale='jet', color=list(range(len(dff[param])))),
                    hoverinfo='text',
                )],
                'layout': dict(
                    xaxis={
                        # 'title': 'Ano',
                        'type': 'linear',
                        'automargin': True,
                    },
                    yaxis={
                        'title': selector_param,  # mudar para param
                        'type': 'linear',
                        'margin': '20px',
                    },
                    margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
                    height=430,
                    hovermode='closest'
                )
            }
    elif (selector_cidade != 'Todas') and (selector_cidade in cidadesRede):
        dff = df6[df6['cidade'] == selector_cidade]
        return {
            'data': [dict(
                x=dff['year'],
                y=dff[param],
                text=dff.industry_class + ' \n' + dff.cidade,
                mode='markers',  # marcação vertical
                marker=go.scattermapbox.Marker(size=14, colorscale='jet', color=list(range(len(dff[param])))),
                hoverinfo='text',
            )],
            'layout': dict(
                xaxis={
                    'type': 'linear',
                    'automargin': True,
                },
                yaxis={
                    'title': selector_param,  # mudar para param
                    'type': 'linear',
                    'margin': '20px',
                },
                margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
                height=450,
                hovermode='closest'
            )
        }


@app.callback(
    [Output('rendaMed-graph', 'figure'),
     Output('numEst-graph', 'figure')],

    [Input('ativ-dropd', 'value'),
     Input('cidade_dropd', 'value')])
def update_bar_atividades(selector_ativ, selector_cidade):
    layout_pie = copy.deepcopy(layout)
    dfff = df6[df6['industry_class'] == selector_ativ]
    if selector_cidade == 'Todas':
        data1 = [
            dict(
                type="bar",
                title='Renda Mensal Média',
                x=dfff.year,
                y=dfff.wage_avg,
                marker=go.scattermapbox.Marker(colorscale='jet', color=list(range(len(dfff['cidade'])))),
                text=dfff.industry_class,  # + ' ' + dff.cidade,
                hoverinfo="text",
            ),
        ]
        data2 = [
            dict(
                type="bar",
                title='Número de Estabelecimetos',
                x=dfff.year,
                y=dfff.num_emp,  # .dropna().mean(),
                marker=go.scattermapbox.Marker(colorscale='jet', color=list(range(len(dfff['cidade'])))),
                text=dfff.industry_class,  # + ' ' + dff.cidade,
                hoverinfo="text",
            ),
        ]
        layout_pie["title"] = "RENDA MENSAL MÉDIA"
        layout_pie["font"] = dict(color="#777777")
        layout_pie["height"] = '480'
        figure1 = dict(data=data1, layout=layout_pie)
        figure2 = dict(data=data2, layout={'title':"NÚMERO DE ESTABELECIMENTOS", 'font': dict(color="#777777"), 'height':'480',
                                           'autosize' : 'True', 'automargin' : 'True', 'margin' : dict(l=30, r=30, b=20, t=40),
                                           'hovermode' : "closest", 'plot_bgcolor' : "#F9F9F9", 'paper_bgcolor' : "#F9F9F9"})


        return figure1, figure2

    elif (selector_cidade != 'Todas') and (selector_cidade in cidadesRede):

        dfff = df7[df7['cidade'] == selector_cidade]
        dfff = dfff[dfff['industry_class'] == selector_ativ]
        data1 = [
            dict(
                type="markers",
                mode='markers',
                title='Renda Mensal Média',
                x=dfff.year,
                y=dfff.wage_avg,
                marker=go.scattermapbox.Marker(colorscale='jet'),  # , color=list(range(len(dff['cidade'])))),
                text=dfff.industry_class + ' ' + dfff.cidade,
                hoverinfo="text",
            ),
        ]
        data2 = [
            dict(
                type="markers",
                mode='markers',
                title='Número de Estabelecimetos',
                x=dfff.year,
                y=dfff.num_emp,  # .dropna().mean(),
                marker=go.scattermapbox.Marker(colorscale='jet'),  # color=list(range(len(dff['cidade'])))),
                text=dfff.industry_class + ' ' + dfff.cidade,
                hoverinfo="text",
            ),
        ]
        layout_pie["title"] = "RENDA MENSAL MÉDIA"

        layout_pie["font"] = dict(color="#777777")
        layout_pie["height"] = '480'
        figure1 = dict(data=data1, layout=layout_pie)
        figure2 = dict(data=data2,
                       layout={'title': "NÚMERO DE ESTABELECIMENTOS", 'font': dict(color="#777777"), 'height': '480',
                               'autosize': 'True', 'automargin': 'True', 'margin': dict(l=30, r=30, b=20, t=40),
                               'hovermode': "closest", 'plot_bgcolor': "#F9F9F9", 'paper_bgcolor': "#F9F9F9"})

        return figure1, figure2


if __name__ == '__main__':
    app.run_server(debug=True)
