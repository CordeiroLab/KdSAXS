import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import dcc, html
import dash_bootstrap_components as dbc
import os
import numpy as np
import pandas as pd
from models.calculations import MonomerOligomerCalculation, ProteinBindingCalculation
import plotly.io as pio
import plotly.express as px
from scripts.utils import format_concentration, save_file, get_session_path
from models.calculations import extract_chi_squared
from scripts.error_handling import logger

def create_chi_squared_plot(results, concentration_colors, units='µM'):
    if results:
        chi_squared_values = pd.concat(results)
        avg_chi_squared = chi_squared_values.groupby('kd')['chi2'].mean().reset_index()

        fig = go.Figure()

        for concentration in chi_squared_values['concentration'].unique():
            df_subset = chi_squared_values[chi_squared_values['concentration'] == concentration]
            fig.add_trace(go.Scatter(
                x=df_subset['kd'], 
                y=df_subset['chi2'], 
                mode='lines+markers',
                name=f'{concentration}',
                line=dict(color=concentration_colors[concentration])  # concentration is already formatted
            ))

        fig.add_trace(go.Scatter(
            x=avg_chi_squared['kd'],
            y=avg_chi_squared['chi2'],
            mode='lines+markers',
            name='Average',
            line=dict(color='black', width=2, dash='dash')
        ))

        fig.update_xaxes(type="log")
        fig.update_layout(
            legend_title=f'Concentration ({units})',
            xaxis_title=f'Kd ({units})',
            yaxis_title='χ²',
            showlegend=True,
            template='simple_white',
            height=400,
            width=650,
            font=dict(size=16),
            title={
                'text': "χ² vs Kd ",
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=20)
            }
        )
        return fig
    return go.Figure()

def create_saxs_fit_plots(results_or_concentrations, concentration_colors, session_dir, kd=None, chi2_values=None, units='µM'):
    fit_plots_column1 = []
    fit_plots_column2 = []

    if isinstance(results_or_concentrations, list):
        # Case when clicking on chi² plot
        experimental_concentrations = results_or_concentrations
        # Get chi² values for clicked Kd from log files
        if kd is not None:
            chi2_values = []
            for concentration in experimental_concentrations:
                log_file = os.path.join(session_dir, 'logs', f"oligomer_{format_concentration(concentration)}_{kd}.log")
                try:
                    chi2 = extract_chi_squared(log_file)
                    chi2_values.append(chi2)
                except FileNotFoundError:
                    logger.debug(f"Log file not found for kd={kd}, concentration={concentration}")
                    chi2_values.append(None)
    else:
        # Case for initial analysis
        results = results_or_concentrations
        experimental_concentrations = []
        chi2_values = []
        for result in results:
            concentration = result['concentration'].iloc[0]
            experimental_concentrations.append(concentration)
            chi2_values.append(result['chi2'].min())
        kd = results[0]['kd'].iloc[results[0]['chi2'].idxmin()]

    for i, concentration in enumerate(experimental_concentrations):
        fit_filename = f"fit_{format_concentration(concentration)}_{kd}.fit"
        fit_filepath = os.path.join(session_dir, 'fits', fit_filename)

        if os.path.exists(fit_filepath):
            plot = create_single_saxs_fit_plot(fit_filepath, concentration, kd, chi2_values[i], 
                                             concentration_colors[format_concentration(concentration)], units)
            
            save_buttons = html.Div([
                html.Div([
                    dbc.Button(f'Save SAXS Fit {i+1} as CSV', 
                              id={'type': 'save-saxs-fit-csv', 'index': i}, 
                              className='secondary-dash-button', 
                              style={'width': 'auto', 'margin': '10px'}),
                    dcc.Download(id={'type': 'download-saxs-fit-csv', 'index': i}),
                ], style={'display': 'inline-block'}),
                html.Div([
                    dbc.Button(f'Save SAXS Fit {i+1} as PDF', 
                              id={'type': 'save-saxs-fit-pdf', 'index': i}, 
                              className='secondary-dash-button', 
                              style={'width': 'auto', 'margin': '10px'}),
                    dcc.Download(id={'type': 'download-saxs-fit-pdf', 'index': i}),
                ], style={'display': 'inline-block'}),
            ], className="d-flex justify-content-end mb-2")
            
            plot_div = html.Div([save_buttons, dcc.Graph(figure=plot)])
            
            if i % 2 == 0:
                fit_plots_column1.append(plot_div)
            else:
                fit_plots_column2.append(plot_div)

    combined_columns = html.Div([
        html.Div(fit_plots_column1, style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'}),
        html.Div(fit_plots_column2, style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'})
    ])

    return combined_columns

def create_single_saxs_fit_plot(fit_data_or_path, concentration, kd, chi2, color, units='µM'):
    """
    Create a SAXS fit plot from either a filepath or a DataFrame
    Args:
        fit_data_or_path: Either a string (filepath) or pandas DataFrame
        concentration: concentration value
        kd: Kd value
        chi2: chi-squared value
        color: color for the plot
    """
    if isinstance(fit_data_or_path, str):
        # If a filepath is provided, read the data
        fit_data = pd.read_csv(fit_data_or_path, sep='\s+', skiprows=1, header=None,
                              names=['s', 'Iexp', 'sigma', 'Ifit'])
    else:
        # If a DataFrame is provided, use it directly
        fit_data = fit_data_or_path

    fit_data['Iexp_log'] = np.log10(fit_data['Iexp'])
    fit_data['Ifit_log'] = np.log10(fit_data['Ifit'])
    fit_data['residuals'] = (fit_data['Iexp'] - fit_data['Ifit']) / fit_data['sigma']

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.75, 0.25])

    fig.add_trace(go.Scatter(
        x=fit_data['s'], y=fit_data['Iexp_log'],
        mode='markers', opacity=0.8,
        name=f'Iexp ({concentration} {units})',
        marker=dict(color='grey')
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=fit_data['s'], y=fit_data['Ifit_log'],
        mode='lines', name=f'Best fit (Kd: {kd:.2f}, χ²={chi2:.2f})',
        line=dict(color=color, width=4)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=fit_data['s'], y=fit_data['residuals'],
        mode='markers', name=f'Residuals ({concentration} {units})',
        marker=dict(color=color)
    ), row=2, col=1)

    fig.update_layout(
        xaxis=dict(showticklabels=False),
        xaxis2=dict(title='momentum transfer (q) or scattering vector (s)'),
        yaxis=dict(title='Log(Intensity)'),
        yaxis2=dict(title='Residuals', showgrid=True),
        template='simple_white',
        showlegend=True,
        legend=dict(x=0.98, y=0.98, xanchor='right', yanchor='top', bgcolor='rgba(255, 255, 255, 0.5)'),
        margin=dict(t=40, b=40, r=20, l=60),
        height=600,
        font=dict(size=16)
    )
    return fig

def create_fraction_plot(kd, n_value, concentration_range, selected_model, receptor_concentration, experimental_concentrations, concentration_colors, units='µM', xscale='log'):
    if xscale == 'log':
        concentration_range = np.logspace(np.log10(min(concentration_range)), 
                                        np.log10(max(concentration_range)), 
                                        len(concentration_range))
    
    if selected_model == 'kds_saxs_mon_oligomer':
        fractions = MonomerOligomerCalculation.calculate_fractions(kd, concentration_range, n_value)
        # Plot for monomer-oligomer model
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fractions['concentration'], y=fractions['monomer_fraction'],
                                mode='lines', name='Monomer', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=fractions['concentration'], y=fractions['oligomer_fraction'],
                                mode='lines', name='Oligomer', line=dict(color='red')))
    else:
        fractions = ProteinBindingCalculation.calculate_fractions(kd, concentration_range, n_value, receptor_concentration)
        # Plot for protein binding model
        fig = go.Figure()
        for i in range(n_value + 1):
            fig.add_trace(go.Scatter(x=fractions['concentration'], 
                                   y=fractions[f'receptor_{i}_frac'],
                                   mode='lines', 
                                   name=f'Receptor_{i}', 
                                   line=dict(color=px.colors.qualitative.Set1[i])))
        fig.add_trace(go.Scatter(x=fractions['concentration'], 
                                y=fractions['ligand_free_frac'],
                                mode='lines', 
                                name='Free Ligand', 
                                line=dict(color='black')))

    fig.update_layout(
    title={
        'text': f'Molecular fractions (Kd = {kd:.2f}, n = {n_value})',
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': dict(size=20)
    }
)

    # Add scatter traces for experimental concentrations
    for conc in experimental_concentrations:
        # conc should already be formatted from the DataFrame
        fig.add_trace(go.Scatter(
            x=[float(conc), float(conc)],  # Convert string back to float for plotting
            y=[0, 1],
            mode='lines',
            line=dict(color=concentration_colors[conc], width=2, dash='dash'),
            name=f'{conc} {units}',
            showlegend=True
        ))
    
    
    fig.update_layout(
        xaxis_title=f'Ligand Concentration ({units})',
        yaxis_title='Fraction',
        yaxis_range=[0, 1],
        legend_title='Species',
        template='simple_white',
        height=400,
        width=650,
        showlegend=True,
        legend=dict(title='Species'),
        font=dict(size=16)
    )
    
    fig.update_xaxes(type=xscale)

    return fig

def create_empty_fraction_plot(message="Please click on a K<sub>D</sub> value to the left. <br> The estimated molecular fractions will be displayed here, <br> together with the corresponding SAXS data fits below. <br> <br> The K<sub>D</sub> with the lowest χ², or the plot's elbow region when <br> no clear minimum is found, corresponds to the most likely K<sub>D</sub>."):
    fig = go.Figure()
    fig.update_layout(
        showlegend=False,
        template='simple_white',
        height=400,
        width=650,
        annotations=[
            dict(
                text=message,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=17, color="#007bff"),
                align="center"
            )
        ],
        margin=dict(t=50, b=50, l=50, r=50)
    )
    return fig
