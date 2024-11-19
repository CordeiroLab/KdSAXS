from dash.dependencies import Input, Output, State, ALL, MATCH
from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
import json
from scripts.utils import truncate_filename
import os
import base64
from dash.exceptions import PreventUpdate
from config import BASE_DIR
from scripts.error_handling import logger


def register_callbacks_upload(app):
    
    @app.callback(
        Output('saxs-upload-container', 'children'),
        [Input('add-saxs-button', 'n_clicks')],
        [State('saxs-upload-container', 'children')]
    )
    def add_saxs_input(n_clicks, children):
        if n_clicks is None:
            return dash.no_update
        
        new_index = len(children) + 1
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
            ], style={'position': 'relative', 'flex': '3', 'marginRight': '10px'}),
            
            dcc.Input(
                id={'type': 'input-concentration', 'index': new_index},
                type='number',
                placeholder='Concentration',
                value=None,
                min=0,
                step=0.1,
                className='input-style',
                style={'flex': '1'}
            )
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'})
        children.append(new_upload)
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
        #print(f"selected_model: {selected_model}")
        #print(f"n_value: {n_value}")

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
            return html.Div([
                html.Span(filename, className='truncated-filename', title=filename)
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
        
        '''print(f"Deleting index: {index_to_delete}")
        for child in children:
            print(f"Child id: {child['props']['children'][0]['props']['children'][0]['props']['id']}")'''
        
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

    @app.callback(
        Output('n-input-label', 'children'),
        [Input('model-selection', 'value')]
    )
    def update_n_input_label(selected_model):
        if selected_model == 'kds_saxs_oligomer_fitting':
            return "Number of binding sites: "
        else:
            return "Stoichiometry: "

    @app.callback(
        [Output('saxs-upload-container', 'children', allow_duplicate=True),
         Output({'type': 'upload-theoretical-saxs', 'index': 0}, 'contents'),
         Output({'type': 'upload-theoretical-saxs', 'index': 1}, 'contents'),
         Output({'type': 'upload-theoretical-saxs', 'index': 0}, 'filename'),
         Output({'type': 'upload-theoretical-saxs', 'index': 1}, 'filename'),
         Output('example-data-store', 'data')],
        [Input('load-example', 'n_clicks')],
        prevent_initial_call=True
    )
    def load_example_files(n_clicks):
        if n_clicks is None:
            raise PreventUpdate
        
        try:
            # Load example theoretical files
            mon_path = os.path.join(BASE_DIR, 'examples', 'blg', 'theoretical_saxs', 'avg_mon_ph7.int')
            with open(mon_path, 'rb') as f:
                mon_content = f.read()
            mon_encoded = base64.b64encode(mon_content).decode()
            
            dim_path = os.path.join(BASE_DIR, 'examples', 'blg', 'theoretical_saxs', 'avg_dim_ph7.int')
            with open(dim_path, 'rb') as f:
                dim_content = f.read()
            dim_encoded = base64.b64encode(dim_content).decode()


            # ph7 dsb
            all_concentrations = [17.4, 26.1, 34.8, 52.2, 69.6, 78.3, 104.3, 130.4, 156.5, 260.9]

            all_files = ['0.32_mgml_cut_28.dat', '0.48_mgml_cut_28.dat', '0.64_mgml_cut_28.dat', 
                         '0.96_mgml_cut_28.dat', '1.28_mgml_cut_28.dat', '1.44_mgml_cut_28.dat',
                          '1.92_mgml_cut_28.dat', '2.4_mgml_cut_28.dat', '2.88_mgml_cut_28.dat',
                          '4.8_mgml_cut_28.dat']



            '''# Load theoretical files not examples
            mon_path = os.path.join('/Users/tiago/working_PAPERS/SAXS_oligo_Kd/used_saxs_data/dsblab/ph3/theoretical_saxs','avg_mon_ph3.int')     #change here
            with open(mon_path, 'rb') as f:
                mon_content = f.read()
            mon_encoded = base64.b64encode(mon_content).decode()
            
            dim_path = os.path.join('/Users/tiago/working_PAPERS/SAXS_oligo_Kd/used_saxs_data/dsblab/ph3/theoretical_saxs','avg_dim_ph3.int')     #change here
            with open(dim_path, 'rb') as f:
                dim_content = f.read()
            dim_encoded = base64.b64encode(dim_content).decode()
'''


            # All concentrations and files

            #ph5 dsb
            '''all_concentrations = [17.9, 26.6, 35.9, 53.3, 71.2, 79.9, 107.1, 133.7, 160.3, 213.6, 266.8, 282.1]

            all_files = ['0.33_mgml_cut_37.dat', '0.49_mgml_cut_37.dat', '0.66_mgml_cut_37.dat', 
                         '0.98_mgml_cut_37.dat', '1.31_mgml_cut_37.dat', '1.47_mgml_cut_37.dat',
                         '1.97_mgml_cut_37.dat', '2.46_mgml_cut_37.dat', '2.95_mgml_cut_37.dat',
                         '3.93_mgml_cut_37.dat', '4.91_mgml_cut_37.dat', '5.19_mgml_cut_37.dat']'''
            

            '''#ph3 dsb
            all_concentrations = [16.3, 19.6, 27.2, 28.8, 38.0, 38.6, 54.3, 58.2, 70.7, 77.2, 81.5,
                                87.0, 108.7, 116.3, 135.9, 145.1, 163.0, 217.4, 271.7, 326.1, 451.1, 581.0]

            all_files = ['0.3_mgml_cut_41.dat', '0.36_mgml_cut_26.dat', '0.5_mgml_cut_41.dat', '0.53_mgml_cut_26.dat',
             '0.7_mgml_cut_41.dat', '0.71_mgml_cut_26.dat', '1.0_mgml_cut_41.dat', '1.07_mgml_cut_26.dat',
             '1.3_mgml_cut_41.dat', '1.42_mgml_cut_26.dat', '1.5_mgml_cut_41.dat', '1.6_mgml_cut_26.dat',
             '2.0_mgml_cut_41.dat', '2.14_mgml_cut_26.dat', '2.5_mgml_cut_41.dat', '2.67_mgml_cut_26.dat',
             '3.0_mgml_cut_41.dat', '4.0_mgml_cut_41.dat', '5.0_mgml_cut_41.dat', '6.0_mgml_cut_41.dat',
             '8.3_mgml_cut_41.dat', '10.69_mgml_cut_26.dat']'''
            

            #ph4 maciaslab
            '''all_concentrations = [16.3, 27.2, 38.0, 54.3, 70.7, 81.5, 108.7, 135.9, 163.0, 217.4, 271.7]

            all_files = [
                'Blac_3_18_Blac_3_subtraction_0.3_mgml_sample_Blac_3_180000-integrate_subtracted_gunier.dat',
                'Blac_3_17_Blac_3_subtraction_0.5_mgml_sample_Blac_3_170000-integrate_subtracted_gunier.dat',
                'Blac_3_16_Blac_3_subtraction_0.7_mgml_sample_Blac_3_160000-integrate_subtracted_gunier.dat',
                'Blac_3_15_Blac_3_subtraction_1.0_mgml_sample_Blac_3_150000-integrate_subtracted_gunier.dat',
                'Blac_3_14_Blac_3_subtraction_1.3_mgml_sample_Blac_3_140000-integrate_subtracted_gunier.dat',
                'Blac_3_13_Blac_3_subtraction_1.5_mgml_sample_Blac_3_130000-integrate_subtracted_gunier.dat',
                'Blac_3_12_Blac_3_subtraction_2.0_mgml_sample_Blac_3_120000-integrate_subtracted_gunier.dat',
                'Blac_3_11_Blac_3_subtraction_2.5_mgml_sample_Blac_3_110000-integrate_subtracted_gunier.dat',
                'Blac_3_10_Blac_3_subtraction_3.0_mgml_sample_Blac_3_100000-integrate_subtracted_gunier.dat',
                'Blac_3_9_Blac_3_subtraction_4.0_mgml_sample_Blac_3_90000-integrate_subtracted_gunier.dat',
                'Blac_3_8_Blac_3_subtraction_5.0_mgml_sample_Blac_3_80000-integrate_subtracted_gunier.dat'
            ]'''


            #ph3 macias lab

            '''all_concentrations = [16.3, 27.2, 38.0, 54.3, 70.7, 81.5, 108.7, 135.9, 163.0, 217.4]
            
            all_files = [
                'BLAC18_BLAC_buffer_subtraction_0.3_mgml_sample_BLAC180000-integrate_subtracted_gunier.dat',
                'BLAC17_BLAC_buffer_subtraction_0.5_mgml_sample_BLAC170000-integrate_subtracted_gunier.dat',
                'BLAC16_BLAC_buffer_subtraction_0.7_mgml_sample_BLAC160000-integrate_subtracted_gunier.dat',
                'BLAC15_BLAC_buffer_subtraction_1.0_mgml_sample_BLAC150000-integrate_subtracted_gunier.dat',
                'BLAC14_BLAC_buffer_subtraction_1.3_mgml_sample_BLAC140000-integrate_subtracted_gunier.dat',
                'BLAC13_BLAC_buffer_subtraction_1.5_mgml_sample_BLAC130000-integrate_subtracted_gunier.dat',
                'BLAC12_BLAC_buffer_subtraction_2.0_mgml_sample_BLAC120000-integrate_subtracted_gunier.dat',
                'BLAC11_BLAC_buffer_subtraction_2.5_mgml_sample_BLAC110000-integrate_subtracted_gunier.dat',
                'BLAC10_BLAC_buffer_subtraction_3.0_mgml_sample_BLAC100000-integrate_subtracted_gunier.dat',
                'BLAC9_BLAC_buffer_subtraction_4.0_mgml_sample_BLAC90000-integrate_subtracted_gunier.dat'
            ]'''




            # Create upload fields for each experimental file
            upload_fields = []
            for i, (filename, concentration) in enumerate(zip(all_files, all_concentrations)):
                # Load experimental file content for examples and not examples files

                file_path = os.path.join(BASE_DIR, 'examples', 'blg', 'exp_saxs_ph7', filename)
                #file_path = os.path.join('/Users/tiago/working_PAPERS/SAXS_oligo_Kd/used_saxs_data/dsblab/ph3/experimental_saxs', filename)     #change here

                with open(file_path, 'rb') as f:
                    content = f.read()
                encoded = base64.b64encode(content).decode()
                
                upload_fields.append(html.Div([
                    html.Div([
                        dcc.Upload(
                            id={'type': 'upload-exp-saxs', 'index': i},
                            children=html.Div([filename]),
                            contents=f'data:text/plain;base64,{encoded}',
                            filename=filename,
                            className='upload-style',
                            multiple=False
                        ),
                        html.I(className="fas fa-minus-circle", 
                              id={'type': 'delete-saxs', 'index': i},
                              n_clicks=0,
                              style={'position': 'absolute', 'top': '5px', 'right': '5px', 'cursor': 'pointer'})
                    ], style={'position': 'relative', 'flex': '3', 'marginRight': '10px'}),
                    dcc.Input(
                        id={'type': 'input-concentration', 'index': i},
                        type='number',
                        value=concentration,
                        min=0,
                        step=0.1,
                        className='input-style',
                        style={'flex': '1'}
                    )
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}))


            #load true examples
            return (
                upload_fields,
                f'data:text/plain;base64,{mon_encoded}',
                f'data:text/plain;base64,{dim_encoded}',
                'avg_mon_ph7.int',
                'avg_dim_ph7.int',
                {'loaded': True}
            )
        
            '''return (
                upload_fields,
                f'data:text/plain;base64,{mon_encoded}',
                f'data:text/plain;base64,{dim_encoded}',
                'avg_mon_ph3.int',                                          #change here
                'avg_dim_ph3.int',                                          #change here
                {'loaded': True}
            )'''
        
            
        except Exception as e:
            logger.error(f"Error loading example files: {str(e)}")
            raise PreventUpdate




