import dash_bootstrap_components as dbc
from dash import dcc, html
from config import ALLOWED_MODELS, DEFAULT_MODEL, KD_RANGE, CONCENTRATION_RANGE, KD_POINTS, CONCENTRATION_POINTS

def create_model_selection():
    return html.Div([
        html.Div([
            html.Div(["1) Choose model:", html.Sup(html.I(className="fas fa-info-circle", id="model-info", style={'marginLeft': '5px'}))], 
                     className="centered-bold-text"),
        
            dcc.Dropdown(
                id='model-selection',
                options=[{'label': model, 'value': model} for model in ALLOWED_MODELS],
                value=DEFAULT_MODEL,
                style={'width': '60%', 'padding': '5px'}
            ),
        ]),
        create_model_specific_inputs(),
    ], 
    className="section-frame section-frame-0")

def create_saxs_upload_section():
    return html.Div([
        html.Div([
            "2) Upload experimental SAXS profiles and concentrations in μM:",
            html.Sup(html.I(className="fas fa-info-circle", id="exp-saxs-info", style={'marginLeft': '5px'}))
        ], className="centered-bold-text"),
        html.Div(id='saxs-upload-container', children=[
            html.Div([
                html.Div([
                    dcc.Upload(
                        id={'type': 'upload-exp-saxs', 'index': 0},
                        children=html.Div(['Drag and Drop or Select Experimental SAXS File']),
                        className="upload-style",
                        multiple=False
                    ),
                    html.I(className="fas fa-minus-circle", 
                           id={'type': 'delete-saxs', 'index': 0},
                           n_clicks=0,
                           style={'position': 'absolute', 'top': '5px', 'right': '5px', 'cursor': 'pointer'})
                ], style={'position': 'relative', 'flex': '1', 'marginRight': '10px'}),
                dcc.Input(
                    id={'type': 'input-concentration', 'index': 0},
                    type='number',
                    placeholder='Concentration',
                    value=None,
                    min=0,
                    step=0.1,
                    className="input-style"
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'})
        ]),
        html.Button('Add another SAXS profile', id='add-saxs-button', n_clicks=0, className='dash-button'),
    ], className="section-frame section-frame-1")

def create_theoretical_saxs_section():
    return html.Div([
        html.Div([
            "3) Upload theoretical SAXS profiles:",
            html.Sup(html.I(className="fas fa-info-circle", id="theo-saxs-info", style={'marginLeft': '5px'}))
        ], className="centered-bold-text"),
        html.Div(id='theoretical-saxs-upload-container', children=[
            dcc.Upload(
                id={'type': 'upload-theoretical-saxs', 'index': 0},
                children=html.Div(['Drag and Drop or Select Monomer SAXS File']),
                className='upload-style',
                multiple=False
            ),
            dcc.Upload(
                id={'type': 'upload-theoretical-saxs', 'index': 1},
                children=html.Div(['Drag and Drop or Select oligomer SAXS File']),
                className='upload-style',
                multiple=False
            )
        ]),
        html.Div(id='example-file-display')  # New div to display the example file name
    ], className="section-frame section-frame-2")

def create_kd_selection_section():
    return html.Div([
        html.Div([
            "4) Choose parameters for simulation:",
            html.Sup(html.I(className="fas fa-info-circle", id="sim-params-info", style={'marginLeft': '5px'}))
        ], className="centered-bold-text"),
        html.Div([
            html.Div([
                create_input_field("Kd min", "kd-min", value=KD_RANGE[0]),
                create_input_field("Kd max", "kd-max", value=KD_RANGE[1]),
                create_input_field("Points", "kd-points", value=KD_POINTS),
            ], className="input-row"),
            html.Div([
                create_input_field("Conc. min", "conc-min", value=CONCENTRATION_RANGE[0]),
                create_input_field("Conc. max", "conc-max", value=CONCENTRATION_RANGE[1]),
                create_input_field("Points", "conc-points", value=CONCENTRATION_POINTS),
            ], className="input-row"),
        ], className="input-container"),
        html.Button('Run Analysis', id='run-analysis', n_clicks=0, className='dash-button')
    ], className='section-frame section-frame-3')

def create_model_specific_inputs():
    return html.Div([
        html.Div([
            html.Div([
                html.Label("Stoichiometry: "),
                dcc.Input(
                    id='input-n',
                    type='number',
                    value=2,
                    min=1,
                    step=1,
                    className="input-style"
                )
            ], id='n-input-container', style={'display': 'inline-block', 'marginRight': '20px'}),
            html.Div([
                html.Label("Receptor concentration: "),
                dcc.Input(
                    id='input-receptor-concentration',
                    type='number',
                    value=None,
                    min=0,
                    step=0.1,
                    className="input-style"
                )
            ], id='receptor-concentration-container', style={'display': 'inline-block'})
        ], style={'display': 'flex', 'alignItems': 'flex-end'})
    ])

def create_input_field(label, id, value=None):
    return html.Div([
        html.Label(label, style={'display': 'block', 'marginBottom': '5px'}),
        dcc.Input(id=id, type='number', className="input-box", value=value)
    ], className="input-group")

def create_instructions():
    return html.Div([
        html.H2("Instructions", style={'textAlign': 'center', 'marginTop': '5px'}),
        html.Ul([
            html.Li("KdSAXS is a tool for studying protein interactions using Small Angle X-ray Scattering (SAXS) data." 
                    " This application allows you to analyze binding equilibria and determine dissociation constants (Kd) from SAXS experiments."),
            html.Li("Upload your SAXS profiles, set parameters, and visualize results with interactive plots and downloadable CSV and PDF files."),
            html.Li([
                "Choose between: ",
                dbc.Button("Monomer-Oligomer ", id="popover-mon-oligomer", color="link"),
                " and ",
                dbc.Button("Protein binding", id="popover-oligomer-fitting", color="link"),
                "equilibria to fit your experimental data. When you click on a Kd value in the chi2 vs Kd plot the molecular fractions are displayed at the right side plot."
            ]),
            html.Li("The inputed concentrations, choosen parameters for the simulation and the uploaded experimental and theoretical SAXS profiles should be self-consistent in units."),
            # html.Li([
            #     "To see how the app works, you can ",
            #     html.Button("load an example", id="load-example", n_clicks=0, style={'cursor': 'pointer'}),
            #     " dataset."
            # ]),

            html.Li([
                "To see how the app works, you can load the example data in the github repository ",
                html.A("here", href="https://github.com/TiagoLopesGomes/KdSAXS/tree/main/examples/blg/", target="_blank"),
                "."
            ]),
        ]),
    ], className="info-section")

def create_model_selection_tab():
    return dbc.Card(dbc.CardBody([
        create_model_selection()
    ]))

def create_experimental_saxs_tab():
    return dbc.Card(dbc.CardBody([
        create_saxs_upload_section()
    ]))

def create_theoretical_saxs_tab():
    return dbc.Card(dbc.CardBody([
        create_theoretical_saxs_section()
    ]))

def create_analysis_parameters_tab():
    return dbc.Card(dbc.CardBody([
        create_kd_selection_section()
    ]))

def create_info_tab():
    return dbc.Card(dbc.CardBody([
        create_instructions()
    ]))

def create_main_layout():
    return html.Div([
        html.H1("KdSAXS - analysing binding equilibria with SAXS data using ensemble models"),
        html.Br(),
        dbc.Tabs([
            dbc.Tab(create_info_tab(), label="Instructions"),
            dbc.Tab(create_model_selection_tab(), label="Model Selection"),
            dbc.Tab(create_experimental_saxs_tab(), label="Experimental SAXS"),
            dbc.Tab(create_theoretical_saxs_tab(), label="Theoretical SAXS"),
            dbc.Tab(create_analysis_parameters_tab(), label="Run analysis"),
        ]),
        html.Div([
            html.Button("Save Chi2 Plot as CSV", id="save-chi2-csv", className='dash-button', style={'margin-right': '10px'}),
            html.Button('Save Chi2 Plot as PDF', id='save-chi2-pdf', className='dash-button'),
            html.Button("Save Fraction Plot as CSV", id="save-fraction-csv", className='dash-button', style={'margin-right': '10px'}),
            html.Button('Save Fraction Plot as PDF', id='save-fraction-pdf', className='dash-button'),
        ], style={'display': 'flex', 'justify-content': 'flex-end', 'margin-top': '20px', 'margin-bottom': '20px'}),
        html.Div([
            dcc.Graph(id='chi2-plot', style={'height': '400px', 'width': '50%', 'display': 'inline-block'}),
            dcc.Graph(id='fraction-plot', style={'height': '400px', 'width': '50%', 'display': 'inline-block'})
        ]),
        html.Div(id='saxs-fit-plots', style={'width': '100%', 'marginTop': '20px'}),
        dcc.Store(id='message-trigger', storage_type='memory'),
        dcc.Store(id='example-data-store'),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Message")),
                dbc.ModalBody(id='modal-content'),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
                ),
            ],
            id="message-modal",
            is_open=False,
        ),
        dcc.Download(id="download-chi2-csv"),
        dcc.Download(id="download-chi2-pdf"),
        dcc.Download(id="download-fraction-csv"),
        dcc.Download(id="download-fraction-pdf"),
    ])
