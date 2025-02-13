import base64
import os
import json

import dash
from dash import dcc, html
from dash.dependencies import MATCH, Input, Output, State, ALL
from dash.exceptions import PreventUpdate

from config import BASE_DIR, MAX_PDB_SIZE, MAX_PDB_UPLOADS
from scripts.error_handling import logger
from scripts.utils import truncate_filename


def register_callbacks_upload(app):
    @app.callback(
        Output("saxs-upload-container", "children"),
        [Input("add-saxs-button", "n_clicks")],
        [State("saxs-upload-container", "children")],
    )
    def add_saxs_input(n_clicks, children):
        if n_clicks is None:
            return dash.no_update

        new_index = len(children) + 1
        new_upload = html.Div(
            [
                html.Div(
                    [
                        dcc.Upload(
                            id={"type": "upload-exp-saxs", "index": new_index},
                            children=html.Div(
                                ["Drag and Drop or Select Experimental SAXS File"]
                            ),
                            className="upload-style",
                            multiple=False,
                        ),
                        html.I(
                            className="fas fa-minus-circle",
                            id={"type": "delete-saxs", "index": new_index},
                            n_clicks=0,
                            style={
                                "position": "absolute",
                                "top": "5px",
                                "right": "5px",
                                "cursor": "pointer",
                            },
                        ),
                    ],
                    style={"position": "relative", "flex": "3", "marginRight": "10px"},
                ),
                dcc.Input(
                    id={"type": "input-concentration", "index": new_index},
                    type="number",
                    placeholder="Concentration",
                    value=None,
                    min=0,
                    step=0.1,
                    className="input-style",
                    style={"flex": "1"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "marginBottom": "10px"},
        )
        children.append(new_upload)
        return children

    @app.callback(
        Output({"type": "upload-exp-saxs", "index": MATCH}, "children"),
        [Input({"type": "upload-exp-saxs", "index": MATCH}, "filename")],
    )
    def update_exp_saxs_filename(filename):
        if filename:
            truncated = truncate_filename(filename)
            return html.Div(
                [html.Span(truncated, className="truncated-filename", title=filename)]
            )
        return html.Div(["Drag and Drop or Select Experimental SAXS File"])

    @app.callback(
        Output("n-input-container", "style"), [Input("model-selection", "value")]
    )
    def display_n_input(selected_model):
        if selected_model in ["kds_saxs_mon_oligomer", "kds_saxs_oligomer_fitting"]:
            return {"display": "inline-block", "marginRight": "20px"}
        return {"display": "none"}

    @app.callback(
        Output("receptor-concentration-container", "style"),
        [Input("model-selection", "value")],
    )
    def toggle_receptor_concentration_input(selected_model):
        if selected_model == "kds_saxs_oligomer_fitting":
            return {"display": "inline-block"}
        return {"display": "none"}

    @app.callback(
        Output("theoretical-saxs-upload-container", "children"),
        [
            Input("model-selection", "value"),
            Input("input-n", "value"),
            Input("theoretical-input-type", "value"),
        ],
        prevent_initial_call=False,
    )
    def update_theoretical_saxs_uploads(selected_model, n_value, use_pdb):
        if selected_model == "kds_saxs_oligomer_fitting" and n_value is not None:
            uploads = []
            total_files = n_value + 2

            labels = ["Free Receptor"]
            labels.extend([f"Receptor-Ligand_{i}" for i in range(1, n_value + 1)])
            labels.append("Free Ligand")

            for i, label in enumerate(labels):
                file_type = "PDB" if use_pdb else "SAXS"
                uploads.append(
                    dcc.Upload(
                        id={"type": "upload-theoretical-saxs", "index": i},
                        children=html.Div(
                            [f"Drag and Drop or Select {label} {file_type} File"]
                        ),
                        className="upload-style",
                        multiple=use_pdb,
                        accept=".pdb" if use_pdb else ".dat,.int",
                    )
                )
            return uploads

        elif selected_model == "kds_saxs_mon_oligomer":
            file_type = "PDB" if use_pdb else "SAXS"
            return [
                dcc.Upload(
                    id={"type": "upload-theoretical-saxs", "index": 0},
                    children=html.Div(
                        [f"Drag and Drop or Select Monomeric {file_type} File"]
                    ),
                    className="upload-style",
                    multiple=use_pdb,
                    accept=".pdb" if use_pdb else ".dat,.int",
                ),
                dcc.Upload(
                    id={"type": "upload-theoretical-saxs", "index": 1},
                    children=html.Div(
                        [f"Drag and Drop or Select Oligomeric {file_type} File"]
                    ),
                    className="upload-style",
                    multiple=use_pdb,
                    accept=".pdb" if use_pdb else ".dat,.int",
                ),
            ]
        return []

    @app.callback(
        Output(
            {"type": "upload-theoretical-saxs", "index": MATCH},
            "contents",
            allow_duplicate=True,
        ),
        [Input({"type": "upload-theoretical-saxs", "index": MATCH}, "contents")],
        [
            State({"type": "upload-theoretical-saxs", "index": MATCH}, "filename"),
            State("model-selection", "value"),
            State("theoretical-input-type", "value"),
            State("input-n", "value"),
            State({"type": "upload-theoretical-saxs", "index": MATCH}, "id"),
        ],
        prevent_initial_call=True,
    )
    def handle_theoretical_upload(
        contents, filename, selected_model, use_pdb, n_value, id_dict
    ):
        if not use_pdb or contents is None:
            return contents

        try:
            # Add file count validation
            if isinstance(filename, list) and len(filename) > MAX_PDB_UPLOADS:
                raise PreventUpdate

            # Add file size validation
            if isinstance(filename, list):
                for cont in contents:
                    content_bytes = base64.b64decode(cont.split(",")[1])
                    if len(content_bytes) > MAX_PDB_SIZE:
                        raise PreventUpdate
            else:
                content_bytes = base64.b64decode(contents.split(",")[1])
                if len(content_bytes) > MAX_PDB_SIZE:
                    raise PreventUpdate

            # Just return the raw contents - store metadata in a different way
            return contents

        except Exception as e:
            logger.error(f"Error processing PDB files: {str(e)}")
            raise PreventUpdate

    @app.callback(
        Output({"type": "upload-theoretical-saxs", "index": MATCH}, "children"),
        [
            Input({"type": "upload-theoretical-saxs", "index": MATCH}, "filename"),
            Input({"type": "upload-theoretical-saxs", "index": MATCH}, "contents"),
        ],
        [
            State("theoretical-input-type", "value"),
            State("model-selection", "value"),
            State("input-n", "value"),
            State({"type": "upload-theoretical-saxs", "index": MATCH}, "id"),
        ],
        prevent_initial_call=True,
    )
    def update_filename_display(
        filename, contents, use_pdb, selected_model, n_value, id_dict
    ):
        if filename:
            if use_pdb:
                if isinstance(filename, list):
                    if len(filename) > MAX_PDB_UPLOADS:
                        return html.Div(
                            [f"Error: Maximum {MAX_PDB_UPLOADS} files allowed"],
                            style={"color": "red"},
                        )
                    try:
                        # Only check file size if contents is available
                        if contents and isinstance(contents, list):
                            for cont in contents:
                                if cont:  # Check if content exists
                                    content_bytes = base64.b64decode(cont.split(",")[1])
                                    if len(content_bytes) > MAX_PDB_SIZE:
                                        return html.Div(
                                            [
                                                f"Error: File exceeds {MAX_PDB_SIZE / 1024 / 1024:.1f}MB limit"
                                            ],
                                            style={"color": "red"},
                                        )
                        # If all checks pass, just show number of files
                        return html.Div([f"{len(filename)} PDB files uploaded"])
                    except Exception as e:
                        logger.error(f"Error in update_filename_display: {str(e)}")
                        return html.Div(
                            [f"{len(filename)} PDB files uploaded"]
                        )  # Still show count even if validation fails
                else:
                    try:
                        # For single file, only check size if content is available
                        if contents:
                            content_bytes = base64.b64decode(contents.split(",")[1])
                            if len(content_bytes) > MAX_PDB_SIZE:
                                return html.Div(
                                    [
                                        f"Error: File exceeds {MAX_PDB_SIZE / 1024 / 1024:.1f}MB limit"
                                    ],
                                    style={"color": "red"},
                                )
                        return html.Div(
                            [
                                html.Span(
                                    filename,
                                    className="truncated-filename",
                                    title=filename,
                                )
                            ]
                        )
                    except Exception as e:
                        logger.error(f"Error in update_filename_display: {str(e)}")
                        return html.Div(
                            [
                                html.Span(
                                    filename,
                                    className="truncated-filename",
                                    title=filename,
                                )
                            ]
                        )

            # For regular SAXS files, just show the filename
            return html.Div(
                [html.Span(filename, className="truncated-filename", title=filename)]
            )

        # Default text when no file is selected
        index = id_dict["index"] if id_dict else 0
        file_type = "PDB" if use_pdb else "SAXS"

        if selected_model == "kds_saxs_mon_oligomer":
            label = "Monomeric" if index == 0 else "Oligomeric"
        else:
            if index == 0:
                label = "Free Receptor"
            elif index == n_value + 1:
                label = "Free Ligand"
            else:
                label = f"Receptor-Ligand_{index}"

        return html.Div(
            [
                f"Drag and Drop or Select {label} {file_type} File{'(s)' if use_pdb else ''}"
            ]
        )

    @app.callback(
        Output("saxs-upload-container", "children", allow_duplicate=True),
        [Input("delete-all-exp-saxs", "n_clicks"), Input("load-example", "n_clicks")],
        [State("saxs-upload-container", "children")],
        prevent_initial_call=True,
    )
    def handle_saxs_container_updates(reset_clicks, example_clicks, children):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger_id == "delete-all-exp-saxs":
            if reset_clicks is None:
                raise PreventUpdate

            # Return to initial state with single empty upload field
            initial_state = [
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Upload(
                                    id={"type": "upload-exp-saxs", "index": 1},
                                    children=html.Div(
                                        [
                                            "Drag and Drop or Select Experimental SAXS File"
                                        ]
                                    ),
                                    className="upload-style",
                                    multiple=False,
                                ),
                                html.I(
                                    className="fas fa-minus-circle",
                                    id={"type": "delete-saxs", "index": 1},
                                    n_clicks=0,
                                    style={
                                        "position": "absolute",
                                        "top": "5px",
                                        "right": "5px",
                                        "cursor": "pointer",
                                    },
                                ),
                            ],
                            style={
                                "position": "relative",
                                "flex": "3",
                                "marginRight": "10px",
                            },
                        ),
                        dcc.Input(
                            id={"type": "input-concentration", "index": 1},
                            type="number",
                            placeholder="Concentration",
                            value=None,
                            min=0,
                            step=0.1,
                            className="input-style",
                            style={"flex": "1"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "marginBottom": "10px",
                    },
                )
            ]
            return initial_state

        return dash.no_update

    @app.callback(
        Output("n-input-label", "children"), [Input("model-selection", "value")]
    )
    def update_n_input_label(selected_model):
        if selected_model == "kds_saxs_oligomer_fitting":
            return "Number of binding sites: "
        else:
            return "Stoichiometry: "

    @app.callback(
        [
            Output("saxs-upload-container", "children", allow_duplicate=True),
            Output(
                {"type": "upload-theoretical-saxs", "index": 0},
                "contents",
                allow_duplicate=True,
            ),
            Output(
                {"type": "upload-theoretical-saxs", "index": 1},
                "contents",
                allow_duplicate=True,
            ),
            Output({"type": "upload-theoretical-saxs", "index": 0}, "filename"),
            Output({"type": "upload-theoretical-saxs", "index": 1}, "filename"),
            Output("example-data-store", "data"),
        ],
        [Input("load-example", "n_clicks")],
        prevent_initial_call=True,
    )
    def load_example_files(n_clicks):
        if n_clicks is None:
            raise PreventUpdate

        try:
            # Load example theoretical files
            mon_path = os.path.join(
                BASE_DIR, "examples", "blg", "theoretical_saxs", "avg_mon_ph7.int"
            )
            with open(mon_path, "rb") as f:
                mon_content = f.read()
            mon_encoded = base64.b64encode(mon_content).decode()

            dim_path = os.path.join(
                BASE_DIR, "examples", "blg", "theoretical_saxs", "avg_dim_ph7.int"
            )
            with open(dim_path, "rb") as f:
                dim_content = f.read()
            dim_encoded = base64.b64encode(dim_content).decode()

            # ph7 dsb
            all_concentrations = [
                17.4,
                26.1,
                34.8,
                52.2,
                69.6,
                78.3,
                104.3,
                130.4,
                156.5,
                260.9,
            ]

            all_files = [
                "0.32_mgml_17.4uM_cut_28.dat",
                "0.48_mgml_26.1uM_cut_28.dat",
                "0.64_mgml_34.8uM_cut_28.dat",
                "0.96_mgml_52.2uM_cut_28.dat",
                "1.28_mgml_69.6uM_cut_28.dat",
                "1.44_mgml_78.3uM_cut_28.dat",
                "1.92_mgml_104.3uM_cut_28.dat",
                "2.4_mgml_130.4uM_cut_28.dat",
                "2.88_mgml_156.5uM_cut_28.dat",
                "4.8_mgml_260.9uM_cut_28.dat",
            ]

            ####################################### Load files not GitHub examples ########################################################

            
            
            '''mon_path = os.path.join('/Users/tiago/working_PAPERS/SAXS_oligo_Kd/used_saxs_data/dsblab/ph7/theoretical_saxs','avg_mon_ph7.int')     #change here
            with open(mon_path, 'rb') as f:
                mon_content = f.read()
            mon_encoded = base64.b64encode(mon_content).decode()
            
            dim_path = os.path.join('/Users/tiago/working_PAPERS/SAXS_oligo_Kd/used_saxs_data/dsblab/ph7/theoretical_saxs','avg_dim_ph7.int')     #change here
            with open(dim_path, 'rb') as f:
                dim_content = f.read()
            dim_encoded = base64.b64encode(dim_content).decode()'''
            


            # All concentrations and files

            # ph5 dsb
            """all_concentrations = [17.9, 26.6, 35.9, 53.3, 71.2, 79.9, 107.1, 133.7, 160.3, 213.6, 266.8, 282.1]

            all_files = ['0.33_mgml_cut_37.dat', '0.49_mgml_cut_37.dat', '0.66_mgml_cut_37.dat', 
                         '0.98_mgml_cut_37.dat', '1.31_mgml_cut_37.dat', '1.47_mgml_cut_37.dat',
                         '1.97_mgml_cut_37.dat', '2.46_mgml_cut_37.dat', '2.95_mgml_cut_37.dat',
                         '3.93_mgml_cut_37.dat', '5.19_mgml_cut_37.dat']"""

            #ph3 dsb
            '''all_concentrations = [16.3, 19.6, 27.2, 28.8, 38.0, 58.2, 87.5, 116.3]

            all_files = ['0.3_mgml_16.3uM_cut_41.dat', '0.36_mgml_19.6uM_cut_26.dat', '0.5_mgml_27.2uM_cut_41.dat', '0.53_mgml_28.8uM_cut_26.dat',
                        '0.7_mgml_38.0uM_cut_41.dat', '1.07_mgml_58.2uM_cut_26.dat', '1.6_mgml_87.5uM_cut_26.dat', '2.14_mgml_116.3uM_cut_26.dat']'''
            

            # ph4 maciaslab
            """all_concentrations = [16.3, 27.2, 38.0, 54.3, 70.7, 81.5, 108.7, 135.9, 163.0, 217.4, 271.7]

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
            ]"""

            # ph3 macias lab
            """all_concentrations = [16.3, 27.2, 38.0, 54.3, 70.7, 81.5, 108.7, 135.9, 163.0, 217.4]
            
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
            ]"""

            # Create upload fields for each experimental file
            upload_fields = []
            for i, (filename, concentration) in enumerate(
                zip(all_files, all_concentrations)
            ):
               
                # Load experimental file content for examples and not examples files

                file_path = os.path.join(BASE_DIR, "examples", "blg", "exp_saxs_ph7", filename)

                #file_path = os.path.join('/Users/tiago/working_PAPERS/SAXS_oligo_Kd/used_saxs_data/dsblab/ph3/experimental_saxs/used', filename)       #change here



                with open(file_path, "rb") as f:
                    content = f.read()
                encoded = base64.b64encode(content).decode()

                upload_fields.append(
                    html.Div(
                        [
                            html.Div(
                                [
                                    dcc.Upload(
                                        id={"type": "upload-exp-saxs", "index": i},
                                        children=html.Div([filename]),
                                        contents=f"data:text/plain;base64,{encoded}",
                                        filename=filename,
                                        className="upload-style",
                                        multiple=False,
                                    ),
                                    html.I(
                                        className="fas fa-minus-circle",
                                        id={"type": "delete-saxs", "index": i},
                                        n_clicks=0,
                                        style={
                                            "position": "absolute",
                                            "top": "5px",
                                            "right": "5px",
                                            "cursor": "pointer",
                                        },
                                    ),
                                ],
                                style={
                                    "position": "relative",
                                    "flex": "3",
                                    "marginRight": "10px",
                                },
                            ),
                            dcc.Input(
                                id={"type": "input-concentration", "index": i},
                                type="number",
                                value=concentration,
                                min=0,
                                step=0.1,
                                className="input-style",
                                style={"flex": "1"},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "marginBottom": "10px",
                        },
                    )
                )

            # load true examples
            return (
                upload_fields,
                f"data:text/plain;base64,{mon_encoded}",
                f"data:text/plain;base64,{dim_encoded}",
                "avg_mon_ph7.int",
                "avg_dim_ph7.int",
                {"loaded": True},
            )
        
            #load other examples
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

    @app.callback(
        Output("saxs-upload-container", "children", allow_duplicate=True),
        [Input({"type": "delete-saxs", "index": ALL}, "n_clicks")],
        [State("saxs-upload-container", "children")],
        prevent_initial_call=True
    )
    def delete_individual_saxs(n_clicks_list, children):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        # Only proceed if the callback was triggered by a delete button click
        if not any(n > 0 for n in n_clicks_list):
            raise PreventUpdate
        
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        clicked_index = json.loads(triggered_id)["index"]
        
        # Remove the upload field with matching index
        updated_children = []
        for child in children:
            # Get the index directly from the component's ID dictionary
            upload_component = child["props"]["children"][0]["props"]["children"][0]
            current_index = upload_component["props"]["id"]["index"]
            if current_index != clicked_index:
                updated_children.append(child)
        
        # If all fields are deleted, prevent update
        return updated_children if updated_children else dash.no_update
