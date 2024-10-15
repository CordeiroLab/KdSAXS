from dash.dependencies import Input, Output, State, ALL
from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import json
from scripts.utils import truncate_filename


def register_callbacks_upload(app):
    
    @app.callback(
        Output('saxs-upload-container', 'children'),
        [Input('add-saxs-button', 'n_clicks')],
        [State('saxs-upload-container', 'children')]
    )
    def add_saxs_input(n_clicks, children):
        print(f"Add button clicked. n_clicks: {n_clicks}")
        print(f"Current number of children: {len(children)}")
        
        if n_clicks is None:
            print("n_clicks is None, returning no update")
            return dash.no_update
        
        new_index = len(children) + 1
        print(f"Creating new upload with index: {new_index}")
        
        new_upload = html.Div([
            html.Div([
                dcc.Upload(
                    id={'type': 'upload-exp-saxs', 'index': new_index},
                    children=html.Div(['Drag and Drop or Select Experimental SAXS File']),
                    className='upload-style',
                    multiple=False
                ),
                html.I(className="fas fa-minus-circle", 
                       id={'type': 'delete-saxs', 'index': new_index},
                       n_clicks=0,
                       style={'position': 'absolute', 'top': '5px', 'right': '5px', 'cursor': 'pointer'})
            ], style={'position': 'relative', 'flex': '1', 'marginRight': '10px'}),
            dcc.Input(
                id={'type': 'input-concentration', 'index': new_index},
                type='number',
                placeholder='Concentration',
                value=None,
                min=0,
                step=0.1,
                className='input-style'
            )
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'})
        children.append(new_upload)
        print(f"New number of children: {len(children)}")
        return children

    @app.callback(
        Output({'type': 'upload-exp-saxs', 'index': dash.MATCH}, 'children'),
        [Input({'type': 'upload-exp-saxs', 'index': dash.MATCH}, 'filename')]
    )
    def update_exp_saxs_filename(filename):
        if filename:
            truncated = truncate_filename(filename)
            return html.Div([
                html.Span(truncated, className='truncated-filename', title=filename)
            ])
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
        print(f"selected_model: {selected_model}")
        print(f"n_value: {n_value}")

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
                    children=html.Div(['Drag and Drop or Select Monomeric SAXS File']),
                    className='upload-style',
                    multiple=False
                ),
                dcc.Upload(
                    id={'type': 'upload-theoretical-saxs', 'index': 1},
                    children=html.Div(['Drag and Drop or Select Oligomeric SAXS File']),
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
            truncated = truncate_filename(filename)
            return html.Div([
                html.Span(truncated, className='truncated-filename', title=filename)
            ])
        return html.Div(['Drag and Drop or Select Theoretical SAXS File'])

    @app.callback(
        Output('saxs-upload-container', 'children', allow_duplicate=True),
        [Input({'type': 'delete-saxs', 'index': ALL}, 'n_clicks')],
        [State('saxs-upload-container', 'children')],
        prevent_initial_call=True
    )
    def delete_saxs_input(n_clicks, children):
        ctx = dash.callback_context
        if not ctx.triggered or not any(n_clicks):
            return dash.no_update
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        index_to_delete = json.loads(button_id)['index']
        
        print(f"Deleting index: {index_to_delete}")
        for child in children:
            print(f"Child id: {child['props']['children'][0]['props']['children'][0]['props']['id']}")
        
        updated_children = [
            child for child in children 
            if child['props']['children'][0]['props']['children'][0]['props']['id']['index'] != index_to_delete
        ]
        
        # Update indices
        for i, child in enumerate(updated_children, start=1):
            for component in child['props']['children']:
                if isinstance(component, dict) and 'props' in component and 'children' in component['props']:
                    for subcomponent in component['props']['children']:
                        if isinstance(subcomponent, dict) and 'props' in subcomponent and 'id' in subcomponent['props']:
                            subcomponent['props']['id']['index'] = i
        
        return updated_children




