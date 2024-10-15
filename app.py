import os
from dash import Dash
import dash_bootstrap_components as dbc

from scripts.callbacks_analysis import register_callbacks_analysis
from scripts.callbacks_upload import register_callbacks_upload
from config import UPLOAD_DIRECTORY, LOG_DIRECTORY
from layouts import create_main_layout
from popovers import create_popovers


# Initialize the Dash app with Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://use.fontawesome.com/releases/v5.8.1/css/all.css'])

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

if not os.path.exists(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)

# Set the app layout
app.layout = create_main_layout()

# Add popovers
app.layout.children.extend(create_popovers())

# Register callbacks
register_callbacks_analysis(app, UPLOAD_DIRECTORY)
upload_callbacks = register_callbacks_upload(app)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
