from dash.dependencies import Input, Output, State
from dash import html, dcc
import dash
import dash_bootstrap_components as dbc


def register_callbacks_upload(app):
    
    @app.callback(
        Output('saxs-upload-container', 'children'),
        [Input('add-saxs-button', 'n_clicks')],
        [State('saxs-upload-container', 'children')]
    )
    def add_saxs_input(n_clicks, children):
        new_upload = html.Div([
            dcc.Upload(
                id={'type': 'upload-exp-saxs', 'index': n_clicks + 1},
                children=html.Div(['Drag and Drop or Select Experimental SAXS File']),
                className='upload-style',
                multiple=False
            ),
            
            dcc.Input(
                id={'type': 'input-concentration', 'index': n_clicks + 1},
                type='number',
                placeholder='Concentration',
                value=None,
                min=0,
                step=0.1,
                className='input-style'
            )
        ])
        children.append(new_upload)
        return children

    @app.callback(
        Output({'type': 'upload-exp-saxs', 'index': dash.MATCH}, 'children'),
        [Input({'type': 'upload-exp-saxs', 'index': dash.MATCH}, 'filename')]
    )
    def update_exp_saxs_filename(filename):
        if filename:
            return html.Div(filename)
        return html.Div(['Drag and Drop or Select Experimental SAXS File'])

    @app.callback(
        Output('n-input-container', 'style'),
        [Input('model-selection', 'value')]
    )

    def display_n_input(selected_model):
        if selected_model in ['kds_saxs_mon_oligomer', 'kds_saxs_oligomer_fitting']:
            return {'display': 'inline-block', 'marginRight': '20px'}
        return {'display': 'none'}

    @app.callback(
        Output('receptor-concentration-container', 'style'),
        [Input('model-selection', 'value')]
    )

    def toggle_receptor_concentration_input(selected_model):
        if selected_model == 'kds_saxs_oligomer_fitting':
            return {'display': 'block', 'margin-top': '20px'}
        else:
            return {'display': 'none'}


    @app.callback(
        Output('theoretical-saxs-upload-container', 'children'),
        [Input('model-selection', 'value'),
         Input('input-n', 'value')]
    )

    
    def update_theoretical_saxs_uploads(selected_model, n_value):
        if selected_model == 'kds_saxs_oligomer_fitting' and n_value is not None:
            uploads = []
            for i in range(n_value + 2):
                uploads.append(dcc.Upload(
                    id={'type': 'upload-theoretical-saxs', 'index': i},
                    children=html.Div([f'Drag and Drop or Select Theoretical SAXS File {i+1}']),
                    className='upload-style',
                    multiple=False
                ))
            return uploads
        
        elif selected_model == 'kds_saxs_mon_oligomer':
            return [
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
            ]
        else:
            return []

    @app.callback(
        Output({'type': 'upload-theoretical-saxs', 'index': dash.MATCH}, 'children'),
        [Input({'type': 'upload-theoretical-saxs', 'index': dash.MATCH}, 'filename')]
    )
    def update_theoretical_saxs_filename(filename):
        if filename:
            return html.Div(filename)
        return html.Div(['Drag and Drop or Select Theoretical SAXS File'])
