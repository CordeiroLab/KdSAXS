import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import dcc, html
import os
import numpy as np
import pandas as pd
from models.calculations import MonomerOligomerCalculation, ProteinBindingCalculation
import plotly.io as pio

def create_chi_squared_plot(results, concentration_colors):
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
                line=dict(color=concentration_colors[concentration])
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
            legend_title='Concentration',
            xaxis_title='Kd (concentration units)',
            yaxis_title='χ²',
            showlegend=True,
            template='simple_white',
            height=400,
            width=650
        )
        fig.update_layout(
            title={
                'text': "χ² vs Kd ",
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            }
        )
        return fig
    return go.Figure()

def create_saxs_fit_plots(results, concentration_colors, upload_directory):
    fit_plots_column1 = []
    fit_plots_column2 = []

    for i, chi_squared_df in enumerate(results):
        best_fit = chi_squared_df.loc[chi_squared_df['chi2'].idxmin()]
        best_kd = best_fit['kd']
        best_chi2 = best_fit['chi2']
        best_concentration = best_fit['concentration']

        fit_filename = f"fit_{int(best_concentration)}_{best_kd}.fit"
        fit_filepath = os.path.join(upload_directory, fit_filename)

        if os.path.exists(fit_filepath):
            plot = create_single_saxs_fit_plot(fit_filepath, best_concentration, best_kd, best_chi2, concentration_colors[best_concentration])
            save_button = html.Button(f'Save SAXS Fit {i+1} as CSV', id={'type': 'save-saxs-fit', 'index': i}, className='secondary-dash-button', style={'width': 'auto', 'margin': '10px'})
            plot_with_button = html.Div([save_button, plot])
            if i % 2 == 0:
                fit_plots_column1.append(plot_with_button)
            else:
                fit_plots_column2.append(plot_with_button)

    combined_columns = html.Div(style={'display': 'flex'}, children=[
        html.Div(style={'width': '50%'}, children=fit_plots_column1),
        html.Div(style={'width': '50%'}, children=fit_plots_column2)
    ])

    return combined_columns

def create_single_saxs_fit_plot(fit_filepath, concentration, kd, chi2, color):
    fit_data = pd.read_csv(fit_filepath, delim_whitespace=True, skiprows=1, header=None,
                           names=['s', 'Iexp', 'sigma', 'Ifit'])
    fit_data['Iexp_log'] = np.log10(fit_data['Iexp'])
    fit_data['Ifit_log'] = np.log10(fit_data['Ifit'])
    fit_data['residuals'] = (fit_data['Iexp'] - fit_data['Ifit']) / fit_data['sigma']

    combined_plot = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.75, 0.25])

    combined_plot.add_trace(go.Scatter(
        x=fit_data['s'], y=fit_data['Iexp_log'],
        mode='markers', opacity=0.8,
        name=f'Iexp ({concentration})',
        marker=dict(color='grey')
    ), row=1, col=1)

    combined_plot.add_trace(go.Scatter(
        x=fit_data['s'], y=fit_data['Ifit_log'],
        mode='lines', name=f'Best fit (Kd: {kd:.2f}, χ²={chi2:.2f})',
        line=dict(color=color, width=4)
    ), row=1, col=1)

    combined_plot.add_trace(go.Scatter(
        x=fit_data['s'], y=fit_data['residuals'],
        mode='markers', name=f'Residuals ({concentration})',
        marker=dict(color=color)
    ), row=2, col=1)

    combined_plot.update_layout(
        xaxis=dict(showticklabels=False),
        xaxis2=dict(title='momentum transfer (q) or scattering vector (s)'),
        yaxis=dict(title='Log(Intensity)'),
        yaxis2=dict(title='Residuals', showgrid=True),
        template='simple_white',
        showlegend=True,
        legend=dict(x=0.98, y=0.98, xanchor='right', yanchor='top', bgcolor='rgba(255, 255, 255, 0.5)'),
        margin=dict(t=40, b=40, r=20, l=60),
        height=600
    )
    return dcc.Graph(figure=combined_plot)

def create_fraction_plot(kd, n_value, concentration_range, selected_model, receptor_concentration, experimental_concentrations, concentration_colors):
    if selected_model == 'kds_saxs_mon_oligomer':
        fractions = MonomerOligomerCalculation.calculate_fractions(kd, concentration_range, n_value)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fractions['concentration'], y=fractions['monomer_fraction'],
                                 mode='lines', name='Monomer', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=fractions['concentration'], y=fractions['oligomer_fraction'],
                                 mode='lines', name='Oligomer', line=dict(color='red')))
        
        fig.update_layout(
        title={
            'text': f'Molecular fractions (Kd = {kd:.2f}, n = {n_value})',
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }
    )

    elif selected_model == 'kds_saxs_oligomer_fitting':
        fractions = ProteinBindingCalculation.calculate_fractions(kd, concentration_range, n_value, receptor_concentration)
        
        fig = go.Figure()
        for i in range(n_value + 1):
            fig.add_trace(go.Scatter(x=fractions['concentration'], y=fractions[f'receptor_{i}_frac'],
                                     mode='lines', name=f'Receptor_{i}'))
        fig.add_trace(go.Scatter(x=fractions['concentration'], y=fractions['ligand_free_frac'],
                                 mode='lines', name='Free Ligand'))
        
        fig.update_layout(
        title={
            'text': f'Molecular fractions (Kd = {kd:.2f}, n = {n_value}, Receptor Conc. = {receptor_concentration:.2f})',
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }
    )   
            
    # Print for debugging
    print("Concentration colors in update_fraction_plot:", concentration_colors)

    # Add scatter traces for experimental concentrations
    for conc in experimental_concentrations:
        color = concentration_colors.get(str(conc), 'black')  # Convert conc to string
        print(f"Concentration: {conc}, Color: {color}")  # Print for debugging
        fig.add_trace(go.Scatter(
            x=[conc, conc],
            y=[0, 1],  # Create a vertical line from bottom to top
            mode='lines',
            line=dict(color=color, width=2, dash='dash'),
            name=f'Conc. ({conc})',
            showlegend=True
        ))
    
    fig.update_layout(
        xaxis_title='Ligand Concentration (concentration units)',
        yaxis_title='Fraction',
        yaxis_range=[0, 1],
        legend_title='Species',
        template='simple_white',
        height=400,
        width=650,
        showlegend=True,
        legend=dict(title='Species')
    )
    

    return fig
