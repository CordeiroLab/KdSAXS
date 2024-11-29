def create_experimental_saxs_section():
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.H4("Experimental SAXS Data", className="card-title"),
                html.Div([
                    dcc.Upload(
                        id='upload-experimental-saxs',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select SAXS File')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px 0'
                        },
                        multiple=False
                    ),
                    html.Div(id='experimental-saxs-upload-output')
                ])
            ])
        )
    ]) 