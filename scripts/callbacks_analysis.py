import dash
from dash.dependencies import Input, Output, State, MATCH
from dash import html, no_update, dcc
from plotly.colors import DEFAULT_PLOTLY_COLORS
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scripts.utils import save_file, format_concentration
from models.model_factory import ModelFactory
from scripts.error_handling import logger, handle_callback_errors
from plotting import create_chi_squared_plot, create_saxs_fit_plots, create_fraction_plot, create_single_saxs_fit_plot, create_empty_fraction_plot
from scripts.crysol_handler import CrysolHandler
import plotly.io as pio
import io
import time
from dash.exceptions import PreventUpdate
import os
from config import ATSAS_PATH
import json
from flask import session
from scripts.utils import get_state_from_index
from config import MAX_KD_POINTS, MAX_CONCENTRATION_POINTS


def validate_inputs(selected_model, n_value, upload_container, theoretical_saxs_uploads, kd_range, receptor_concentration, kd_points, conc_points):
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
    
    # Add validation for maximum points
    if kd_points > MAX_KD_POINTS:
        errors.append(f"Number of Kd points cannot exceed {MAX_KD_POINTS}")
    if conc_points > MAX_CONCENTRATION_POINTS:
        errors.append(f"Number of concentration points cannot exceed {MAX_CONCENTRATION_POINTS}")
        
    return errors

def process_saxs_data(selected_model, n_value, upload_container, theoretical_saxs_uploads, kd_range, receptor_concentration, session_dir, kd_points):
    logger.debug(f"Starting process_saxs_data with session_dir: {session_dir}")
    logger.debug(f"Model: {selected_model}")
    
    model = ModelFactory.get_model(selected_model)
    results = []
    concentration_colors = {}
    color_sequence = DEFAULT_PLOTLY_COLORS

    for i, item in enumerate(upload_container):
        exp_saxs, ligand_concentration = extract_saxs_data(item)
        if exp_saxs and ligand_concentration:
            formatted_conc = format_concentration(ligand_concentration)
            if formatted_conc not in concentration_colors:
                color_index = len(concentration_colors) % len(color_sequence)
                concentration_colors[formatted_conc] = color_sequence[color_index]

            exp_file_path = save_file(f"exp_saxs_{i+1}.dat", exp_saxs, session_dir, 'uploads/experimental')
            
            if selected_model == 'kds_saxs_mon_oligomer':
                if 'props' in theoretical_saxs_uploads[0] and isinstance(theoretical_saxs_uploads[0]['props'].get('contents'), list):
                    logger.debug("Processing PDB files")
                    crysol_handler = CrysolHandler(session_dir)
                    
                    # Process monomer PDbs
                    mon_files = []
                    for cont in theoretical_saxs_uploads[0]['props']['contents']:
                        pdb_path = save_file(
                            name=f"pdb_mon_{len(mon_files)}.pdb",
                            content=cont,
                            directory=session_dir,
                            file_type='pdb',
                            model=selected_model,
                            state='monomer'
                        )
                        mon_files.append(pdb_path)
                    mon_file_path = crysol_handler.process_multiple_pdbs(mon_files, 'monomer')
                    
                    # Process oligomer PDbs
                    dim_files = []
                    for cont in theoretical_saxs_uploads[1]['props']['contents']:
                        pdb_path = save_file(
                            name=f"pdb_dim_{len(dim_files)}.pdb",
                            content=cont,
                            directory=session_dir,
                            file_type='pdb',
                            model=selected_model,
                            state='oligomer'
                        )
                        dim_files.append(pdb_path)
                    dim_file_path = crysol_handler.process_multiple_pdbs(dim_files, 'oligomer')
                else:
                    logger.debug("Processing regular SAXS profiles")
                    mon_contents = theoretical_saxs_uploads[0]['props']['contents']
                    dim_contents = theoretical_saxs_uploads[1]['props']['contents']
                    mon_file_path = save_file("mon_saxs.dat", mon_contents, session_dir, 'uploads/theoretical')
                    dim_file_path = save_file("oligomer_saxs.dat", dim_contents, session_dir, 'uploads/theoretical')

                chi_squared_df = model.calculate(exp_file_path, mon_file_path, dim_file_path, 
                                            float(formatted_conc), n_value, kd_range, kd_points, session_dir)
                # Format concentration in results DataFrame
                chi_squared_df['concentration'] = chi_squared_df['concentration'].apply(format_concentration)
                results.append(chi_squared_df)
            else:  # protein binding model
                if 'props' in theoretical_saxs_uploads[0] and isinstance(theoretical_saxs_uploads[0]['props'].get('contents'), list):
                    logger.debug("Processing PDB files for protein binding model")
                    crysol_handler = CrysolHandler(session_dir)
                    theoretical_files = []
                    
                    for j, upload in enumerate(theoretical_saxs_uploads):
                        state = get_state_from_index(selected_model, j, n_value)
                        pdb_files = []
                        
                        for cont in upload['props']['contents']:
                            pdb_path = save_file(
                                name=f"pdb_{state}_{len(pdb_files)}.pdb",
                                content=cont,
                                directory=session_dir,
                                file_type='pdb',
                                model=selected_model,
                                state=state
                            )
                            pdb_files.append(pdb_path)
                        
                        # Process PDbs with CRYSOL and average
                        theo_file_path = crysol_handler.process_multiple_pdbs(pdb_files, state)
                        theoretical_files.append(theo_file_path)
                else:
                    # Handle regular SAXS profiles
                    theoretical_files = []
                    for j, upload in enumerate(theoretical_saxs_uploads):
                        theo_file_path = save_file(
                            f"theo_saxs_{j+1}.dat", 
                            upload['props']['contents'], 
                            session_dir, 
                            'uploads/theoretical'
                        )
                        theoretical_files.append(theo_file_path)
                
                chi_squared_df = model.calculate(
                    exp_file_path, 
                    theoretical_files,
                    receptor_concentration,
                    float(formatted_conc),
                    n_value,
                    kd_range,
                    kd_points,
                    session_dir
                )
                chi_squared_df['concentration'] = chi_squared_df['concentration'].apply(format_concentration)
                results.append(chi_squared_df)

    return results, concentration_colors

def extract_saxs_data(item):
    try:
        # Get the experimental SAXS data
        exp_saxs = item['props']['children'][0]['props']['children'][0]['props']['contents']
        
        # Get the concentration value
        concentration_input = item['props']['children'][1]['props']['value']
        if concentration_input is None:
            logger.error("No concentration value provided")
            return None, None
            
        ligand_concentration = float(concentration_input)
        
        # Format the concentration consistently
        formatted_concentration = format_concentration(ligand_concentration)
        
        return exp_saxs, float(formatted_concentration)
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error extracting SAXS data: {str(e)}")
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

def register_callbacks_analysis(app, get_session_dir):
    # First callback to show loading modal
    @app.callback(
        [Output('loading-modal', 'is_open'),
         Output('calculation-trigger', 'data')],
        Input('run-analysis', 'n_clicks'),
        prevent_initial_call=True
    )
    def show_loading_modal(n_clicks):
        if n_clicks is None:
            raise PreventUpdate
        return True, {'n_clicks': n_clicks}

    # Main callback for calculations
    @app.callback(
        [Output('message-modal', 'is_open'),
         Output('modal-content', 'children'),
         Output('chi2-plot', 'figure'),
         Output('fraction-plot', 'figure'),
         Output('saxs-fit-plots', 'children'),
         Output('experimental-data-store', 'data')],
        [Input('calculation-trigger', 'data'),
         Input('close-modal', 'n_clicks'),
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
         State('concentration-units', 'value'),
         State('experimental-data-store', 'data'),
         State('message-modal', 'is_open')]
    )
    def update_all(calculation_trigger, close_clicks, click_data,
                   selected_model, n_value, upload_container, theoretical_saxs_uploads,
                   kd_min, kd_max, kd_points, conc_min, conc_max, conc_points,
                   receptor_concentration, units, stored_data, modal_is_open):
        
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if trigger_id == 'close-modal':
            return False, '', dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        elif trigger_id == 'calculation-trigger':
            # Basic validation first
            if not os.path.exists(ATSAS_PATH):
                return True, f"Error: ATSAS path '{ATSAS_PATH}' does not exist.", dash.no_update, dash.no_update, dash.no_update, dash.no_update

            if None in [kd_min, kd_max, kd_points, conc_min, conc_max, conc_points]:
                return True, 'Please fill in all Kd and concentration fields.', dash.no_update, dash.no_update, dash.no_update, dash.no_update

            # Create new session for this analysis
            from config import create_session_dir
            session['session_dir'] = create_session_dir()

            kd_range = (kd_min, kd_max)
            concentration_range = np.linspace(conc_min, conc_max, conc_points)
            input_errors = validate_inputs(selected_model, n_value, upload_container, theoretical_saxs_uploads, kd_range, receptor_concentration, kd_points, conc_points)
            if input_errors:
                return True, html.Div([html.P(error) for error in input_errors], className='message-error'), dash.no_update, dash.no_update, dash.no_update, dash.no_update

            try:
                results, concentration_colors = process_saxs_data(selected_model, n_value, upload_container, theoretical_saxs_uploads, 
                                                               kd_range, receptor_concentration, session['session_dir'], kd_points)
                if results:
                    chi_squared_plot = create_chi_squared_plot(results, concentration_colors, units=units)
                    saxs_fit_plots = create_saxs_fit_plots(results, concentration_colors, session['session_dir'], units=units)
                    
                    experimental_concentrations = [result['concentration'].unique()[0] for result in results]
                    
                    # Get chi² values from the average curve
                    chi_squared_values = pd.concat(results)
                    avg_chi_squared = chi_squared_values.groupby('kd')['chi2'].mean()
                    best_kd = avg_chi_squared.index[avg_chi_squared.argmin()]
                    
                    # Instead of creating fraction plot, create empty plot with instruction
                    fraction_plot = create_empty_fraction_plot()
                    
                    stored_data = {
                        'experimental_concentrations': experimental_concentrations,
                        'concentration_colors': concentration_colors,
                        'best_kd': best_kd,
                        'chi2_values': [result['chi2'].min() for result in results],
                        'units': units
                    }
                    
                    return True, html.Div('Analysis Complete!', className='message-success'), chi_squared_plot, fraction_plot, saxs_fit_plots, stored_data
                else:
                    return True, html.Div('No valid data processed.', className='message-error'), dash.no_update, dash.no_update, dash.no_update, dash.no_update
            except Exception as e:
                logger.exception("Error during analysis")
                return True, f'An error occurred during analysis: {str(e)}', dash.no_update, dash.no_update, dash.no_update, dash.no_update

        elif trigger_id == 'chi2-plot':
            if click_data is None or stored_data is None:
                raise PreventUpdate

            clicked_kd = click_data['points'][0]['x']
            # Update stored data with selected Kd
            stored_data['selected_kd'] = clicked_kd
            concentration_range = np.linspace(conc_min, conc_max, conc_points)
            experimental_concentrations = stored_data.get('experimental_concentrations', [])
            concentration_colors = stored_data.get('concentration_colors', {})
            
            # Create fraction plot when Kd is clicked
            fraction_plot = create_fraction_plot(clicked_kd, n_value, concentration_range, selected_model, 
                                              receptor_concentration, experimental_concentrations, 
                                              concentration_colors, units=units)
            
            # Create SAXS fit plots for clicked Kd
            saxs_fit_plots = create_saxs_fit_plots(experimental_concentrations, concentration_colors, 
                                                 session['session_dir'], clicked_kd, 
                                                 stored_data['chi2_values'], units=units)
            
            return False, '', dash.no_update, fraction_plot, saxs_fit_plots, stored_data

        return False, '', dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Callback to close loading modal after calculations
    @app.callback(
        Output('loading-modal', 'is_open', allow_duplicate=True),
        Input('message-modal', 'is_open'),
        prevent_initial_call=True
    )
    def close_loading_modal(message_modal_open):
        return False

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

    @app.callback(
        Output({'type': 'download-saxs-fit-csv', 'index': MATCH}, 'data'),
        Input({'type': 'save-saxs-fit-csv', 'index': MATCH}, 'n_clicks'),
        State('experimental-data-store', 'data'),
        prevent_initial_call=True
    )
    def save_saxs_fit_csv(n_clicks, stored_data):
        if n_clicks is None:
            raise PreventUpdate
        
        # Get current session directory
        session_dir = get_session_dir()
        
        ctx = dash.callback_context
        button_id = ctx.triggered[0]['prop_id']
        index = json.loads(button_id.split('.')[0])['index']
        
        concentration = stored_data["experimental_concentrations"][index]
        kd = stored_data.get("selected_kd", stored_data["best_kd"])
        
        fit_file = os.path.join(session_dir, 'fits', f'fit_{format_concentration(concentration)}_{kd}.fit')
        fit_data = pd.read_csv(fit_file, sep='\s+', skiprows=1, names=['s', 'Iexp', 'sigma', 'Ifit'])
        
        return dcc.send_data_frame(fit_data.to_csv, f"saxs_fit_{index+1}.csv", index=False)

    @app.callback(
        Output({'type': 'download-saxs-fit-pdf', 'index': MATCH}, 'data'),
        Input({'type': 'save-saxs-fit-pdf', 'index': MATCH}, 'n_clicks'),
        State('experimental-data-store', 'data'),
        prevent_initial_call=True
    )
    def save_saxs_fit_pdf(n_clicks, stored_data):
        if n_clicks is None:
            raise PreventUpdate
        
        # Get current session directory
        session_dir = get_session_dir()
        
        ctx = dash.callback_context
        button_id = ctx.triggered[0]['prop_id']
        index = json.loads(button_id.split('.')[0])['index']
        
        # Get the concentration and color for this index
        concentration = stored_data["experimental_concentrations"][index]
        color = stored_data["concentration_colors"][concentration]
        kd = stored_data.get("selected_kd", stored_data["best_kd"])
        chi2 = stored_data["chi2_values"][index]
        
        # Get the fit data from the fits directory
        fit_file = os.path.join(session_dir, 'fits', f'fit_{format_concentration(concentration)}_{kd}.fit')
        fit_data = pd.read_csv(fit_file, sep='\s+', skiprows=1, names=['s', 'Iexp', 'sigma', 'Ifit'])
        
        # Create plot with all required arguments
        fig = create_single_saxs_fit_plot(fit_data, concentration, kd, chi2, color)
        
        # Convert to PDF
        buffer = io.BytesIO()
        pio.write_image(fig, buffer, format='pdf')
        buffer.seek(0)
        
        return dcc.send_bytes(buffer.getvalue(), f"saxs_fit_{index+1}.pdf")

    def create_pdf(figure):
        buffer = io.BytesIO()
        pio.write_image(figure, buffer, format='pdf')
        buffer.seek(0)
        return buffer.getvalue()