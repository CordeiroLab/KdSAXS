import dash
from dash.dependencies import Input, Output, State
from dash import html, no_update, dcc
from plotly.colors import DEFAULT_PLOTLY_COLORS
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scripts.utils import save_file
from models.model_factory import ModelFactory
from scripts.error_handling import logger, handle_callback_errors
from plotting import create_chi_squared_plot, create_saxs_fit_plots, create_fraction_plot
import plotly.io as pio
import io
import time
from dash.exceptions import PreventUpdate
import os
from config import ATSAS_PATH


def validate_inputs(selected_model, n_value, upload_container, theoretical_saxs_uploads, kd_range, receptor_concentration):
    errors = []
    if not selected_model:
        errors.append("No model selected.")
    if not n_value or n_value <= 0:
        errors.append("Invalid n value.")
    if not upload_container:
        errors.append("No experimental SAXS data uploaded.")
    if not theoretical_saxs_uploads:
        errors.append("No theoretical SAXS data uploaded.")
    if not kd_range or len(kd_range) != 2 or kd_range[0] >= kd_range[1]:
        errors.append("Invalid Kd range.")
    if selected_model == 'kds_saxs_oligomer_fitting' and receptor_concentration is None:
        errors.append("Receptor concentration is required for the selected model.")
    return errors

def process_saxs_data(selected_model, n_value, upload_container, theoretical_saxs_uploads, kd_range, receptor_concentration, upload_directory, kd_points):
    model = ModelFactory.get_model(selected_model)
    results = []
    concentration_colors = {}
    color_sequence = DEFAULT_PLOTLY_COLORS

    for i, item in enumerate(upload_container):
        exp_saxs, ligand_concentration = extract_saxs_data(item)
        if exp_saxs and ligand_concentration:
            if ligand_concentration not in concentration_colors:
                color_index = len(concentration_colors) % len(color_sequence)
                concentration_colors[ligand_concentration] = color_sequence[color_index]

            exp_file_path = save_file(f"exp_saxs_{i+1}.dat", exp_saxs, upload_directory)
            chi_squared_df = calculate_chi_squared(model, selected_model, exp_file_path, theoretical_saxs_uploads, 
                                                   ligand_concentration, n_value, kd_range, receptor_concentration, upload_directory, kd_points)
            results.append(chi_squared_df)

    return results, concentration_colors

def extract_saxs_data(item):
    try:
        exp_saxs = item['props']['children'][0]['props']['children'][0]['props']['contents']
        ligand_concentration = item['props']['children'][1]['props']['value']
        return exp_saxs, ligand_concentration
    except KeyError as e:
        logger.error(f"KeyError: {e} in item")
        return None, None

def calculate_chi_squared(model, selected_model, exp_file_path, theoretical_saxs_uploads, ligand_concentration, n_value, kd_range, receptor_concentration, upload_directory, kd_points):
    if selected_model == 'kds_saxs_mon_oligomer':
        mon_file_path = save_file("mon_saxs.dat", theoretical_saxs_uploads[0]['props']['contents'], upload_directory)
        dim_file_path = save_file("oligomer_saxs.dat", theoretical_saxs_uploads[1]['props']['contents'], upload_directory)
        return model.calculate(exp_file_path, mon_file_path, dim_file_path, ligand_concentration, n_value, kd_range, kd_points)
    elif selected_model == 'kds_saxs_oligomer_fitting':
        if receptor_concentration is None:
            raise ValueError("Receptor concentration is required for the ProteinBindingCalculation model")
        theoretical_files = [save_file(f"theo_saxs_{j+1}.dat", upload['props']['contents'], upload_directory)
                             for j, upload in enumerate(theoretical_saxs_uploads)]
        return model.calculate(exp_file_path, theoretical_files, receptor_concentration, ligand_concentration, n_value, kd_range, kd_points)
    else:
        raise ValueError(f"Unknown model: {selected_model}")

def register_callbacks_analysis(app, upload_directory):
    @app.callback(
        [Output('message-trigger', 'data'),
         Output('chi2-plot', 'figure'),
         Output('fraction-plot', 'figure'),
         Output('saxs-fit-plots', 'children'),
         Output('experimental-data-store', 'data')],
        [Input('run-analysis', 'n_clicks'),
         Input('chi2-plot', 'clickData')],
        [State('model-selection', 'value'),
         State('input-n', 'value'),
         State('saxs-upload-container', 'children'),
         State('theoretical-saxs-upload-container', 'children'),
         State('kd-min', 'value'),
         State('kd-max', 'value'),
         State('kd-points', 'value'),
         State('conc-min', 'value'),
         State('conc-max', 'value'),
         State('conc-points', 'value'),
         State('input-receptor-concentration', 'value'),
         State('experimental-data-store', 'data')]
    )
    def update_plots(n_clicks, click_data, selected_model, n_value, upload_container, theoretical_saxs_uploads, 
                     kd_min, kd_max, kd_points, conc_min, conc_max, conc_points, receptor_concentration, stored_data):
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if trigger_id == 'run-analysis':
            return handle_run_analysis(n_clicks, selected_model, n_value, upload_container, theoretical_saxs_uploads, 
                                       kd_min, kd_max, kd_points, conc_min, conc_max, conc_points, receptor_concentration)
        elif trigger_id == 'chi2-plot':
            return handle_chi2_plot_click(click_data, n_value, conc_min, conc_max, conc_points, selected_model, receptor_concentration, stored_data)

        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    def handle_run_analysis(n_clicks, selected_model, n_value, upload_container, theoretical_saxs_uploads, 
                            kd_min, kd_max, kd_points, conc_min, conc_max, conc_points, receptor_concentration):
        if n_clicks is None:
            return no_update, go.Figure(), go.Figure(), html.Div(), no_update

        # Check if ATSAS_PATH exists
        if not os.path.exists(ATSAS_PATH):
            error_message = f"Error: ATSAS path '{ATSAS_PATH}' does not exist. Please check the ATSAS_PATH in config.py and ensure it points to the correct location."
            return {'message': error_message, 'is_error': True, 'timestamp': time.time()}, no_update, no_update, no_update, no_update

        if None in [kd_min, kd_max, kd_points, conc_min, conc_max, conc_points]:
            return {'message': 'Please fill in all Kd and concentration fields.', 'is_error': True, 'timestamp': time.time()}, no_update, no_update, no_update, no_update

        kd_range = (kd_min, kd_max)
        concentration_range = np.linspace(conc_min, conc_max, conc_points)
        input_errors = validate_inputs(selected_model, n_value, upload_container, theoretical_saxs_uploads, kd_range, receptor_concentration)
        if input_errors:
            return {'message': '\n'.join(input_errors), 'is_error': True, 'timestamp': time.time()}, no_update, no_update, no_update, no_update

        try:
            results, concentration_colors = process_saxs_data(selected_model, n_value, upload_container, theoretical_saxs_uploads, kd_range, receptor_concentration, upload_directory, kd_points)
            if results:
                chi_squared_plot = create_chi_squared_plot(results, concentration_colors)
                saxs_fit_plots = create_saxs_fit_plots(results, concentration_colors, upload_directory)
                
                # Extract experimental concentrations from results
                experimental_concentrations = [result['concentration'].unique()[0] for result in results]
                
                best_kd = results[0]['kd'].iloc[results[0]['chi2'].idxmin()]
                fraction_plot = create_fraction_plot(best_kd, n_value, concentration_range, selected_model, 
                                                     receptor_concentration, experimental_concentrations, concentration_colors)
                
                # Store both concentrations and colors
                stored_data = {
                    'experimental_concentrations': experimental_concentrations,
                    'concentration_colors': concentration_colors
                }
                
                return {'message': 'Analysis Complete!', 'is_error': False, 'timestamp': time.time()}, chi_squared_plot, fraction_plot, saxs_fit_plots, stored_data
            else:
                return {'message': 'No valid data processed.', 'is_error': True, 'timestamp': time.time()}, no_update, no_update, no_update, no_update
        except Exception as e:
            logger.exception("Error during analysis")
            return {'message': f'An error occurred during analysis: {str(e)}', 'is_error': True, 'timestamp': time.time()}, no_update, no_update, no_update, no_update

    def handle_chi2_plot_click(click_data, n_value, conc_min, conc_max, conc_points, selected_model, receptor_concentration, stored_data):
        if click_data is None:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        clicked_kd = click_data['points'][0]['x']
        concentration_range = np.linspace(conc_min, conc_max, conc_points)
        
        # Retrieve the experimental_concentrations and concentration_colors from stored_data
        experimental_concentrations = stored_data.get('experimental_concentrations', [])
        concentration_colors = stored_data.get('concentration_colors', {})
        
        # Print for debugging
        print("Concentration colors in handle_chi2_plot_click:", concentration_colors)
        
        fraction_plot = create_fraction_plot(clicked_kd, n_value, concentration_range, selected_model, 
                                             receptor_concentration, experimental_concentrations, concentration_colors)
        return dash.no_update, dash.no_update, fraction_plot, dash.no_update, dash.no_update

    @app.callback(
        Output('message-modal', 'is_open'),
        Output('modal-content', 'children'),
        Input('message-trigger', 'data'),
        Input('close-modal', 'n_clicks'),
        State('message-modal', 'is_open')
    )
    def toggle_modal(message_data, n_clicks, is_open):
        ctx = dash.callback_context
        if not ctx.triggered:
            return False, ''
        
        trigger = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if trigger == 'message-trigger' and message_data:
            return True, message_data['message']
        elif trigger == 'close-modal':
            return False, ''
        return is_open, ''

    @app.callback(
        Output('download-chi2-csv', 'data'),
        Input('save-chi2-csv', 'n_clicks'),
        State('chi2-plot', 'figure'),
        prevent_initial_call=True
    )
    def save_chi2_csv(n_clicks, figure):
        if figure is not None:
            df = pd.DataFrame({'Kd': figure['data'][0]['x'], 'Chi2': figure['data'][0]['y']})
            return dcc.send_data_frame(df.to_csv, "chi2_plot.csv", index=False)
        return dash.no_update

    @app.callback(
        Output('download-chi2-pdf', 'data'),
        Input('save-chi2-pdf', 'n_clicks'),
        State('chi2-plot', 'figure'),
        prevent_initial_call=True
    )
    def save_chi2_pdf(n_clicks, figure):
        if figure is not None:
            return dcc.send_bytes(create_pdf(figure), "chi2_plot.pdf")
        return dash.no_update

    @app.callback(
        Output('download-fraction-csv', 'data'),
        Input('save-fraction-csv', 'n_clicks'),
        State('fraction-plot', 'figure'),
        prevent_initial_call=True
    )
    def save_fraction_csv(n_clicks, figure):
        if figure is not None:
            df = pd.DataFrame({'Concentration': figure['data'][0]['x'], 'Fraction': figure['data'][0]['y']})
            return dcc.send_data_frame(df.to_csv, "fraction_plot.csv", index=False)
        return dash.no_update

    @app.callback(
        Output('download-fraction-pdf', 'data'),
        Input('save-fraction-pdf', 'n_clicks'),
        State('fraction-plot', 'figure'),
        prevent_initial_call=True
    )
    def save_fraction_pdf(n_clicks, figure):
        if figure is not None:
            return dcc.send_bytes(create_pdf(figure), "fraction_plot.pdf")
        return dash.no_update

    def create_pdf(figure):
        buffer = io.BytesIO()
        pio.write_image(figure, buffer, format='pdf')
        buffer.seek(0)
        return buffer.getvalue()