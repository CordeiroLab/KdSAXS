from dash import html, dcc
import dash_bootstrap_components as dbc

formulas = {
    'kds_saxs_mon_oligomer': '''
    Mass balance equations:
    
    $$
    nM \leftrightarrow oligomer
    $$
    
    $$
    M_{total} = [M] + n[oligomer]
    $$
    
    $$
    K_D = \\frac{[M]^n}{[oligomer]}
    $$
    
    $$
    M = monomer, \quad
    n = stoichiometry
    $$
    ''',
    'kds_saxs_oligomer_fitting': '''
    Mass balance equations:

    $$
    R_{total} = \sum_{j=0}^{n} R_j \quad ,
    $$
    
    $$
    L_{total} = L_{free} + \sum_{j=1}^{n} j \cdot R_j \quad ,
    $$
    
    $$
    K_{D,j} = jK_d / (n - j + 1), \quad j \in \mathbb{Z}, \, j > 0 \quad ,
    $$
    
    $$
    K_{D,j} = \\frac{[R]_{j-1}[L_{free}]}{[R]_j} \quad  \quad 
    $$
    
    $$
    R = Receptor , \quad
    L = Ligand, \quad
    n = number \, of \, binding \, sites
    $$
    '''
}


def create_popovers():
    return [
        dbc.Popover(
            "Please choose a model to fit your data",
            target="model-info",
            trigger="hover",
            placement="right",
            className="popover-body"
        ),
        dbc.Popover(
            [
                html.P("Please upload your experimental SAXS profiles and concentrations:"),
                html.P("File format should have three columns: Momentum transfer or vector, Intensity and experimental error."),
                html.P("Concentration units are per-user choice and should be self-consistent in units with the Kd and concentration ranges used for simulations."),
                
            ],
            target="exp-saxs-info",
            trigger="hover",
            placement="right",
            className="popover-body"
        ),
        dbc.Popover(
            [
                html.P("Please upload your theoretical SAXS profiles or PDB files:"),
                html.P("File format, for SAXS profile, should have two columns: Momentum transfer or vector and Intensity."),
                html.P("Concentration units are per-user choice and should be self-consistent in units with the Kd and concentration ranges used for simulations."),
                html.P("If uploading PDB files it will automatically calculate and average the SAXS profiles for each state.")
            ],
            target="theo-saxs-info",
            trigger="hover",
            placement="right",
            className="popover-body"
        ),
        dbc.Popover(
            [
                html.P("Please choose your parameters for simulation:"),
                html.P("Kd max, min and points are the maximum, minimum and number of Kd values for simulation, respectively."),
                html.P("Conc. max, min and points are the maximum, minimum and number of concentration values for simulation, respectively.")
            ],
            target="sim-params-info",
            trigger="hover",
            placement="right",
            className="popover-body"
        ),
        dbc.Popover(
            dcc.Markdown(formulas['kds_saxs_mon_oligomer'], mathjax=True),
            target="popover-mon-oligomer",
            trigger="hover",
            placement="bottom",
            className="popover-body"
        ),
        dbc.Popover(
            dcc.Markdown(formulas['kds_saxs_oligomer_fitting'], mathjax=True),
            target="popover-oligomer-fitting",
            trigger="hover",
            placement="bottom",
            className="popover-body"
        )
    ]
