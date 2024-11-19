import os
from dash import Dash
import dash_bootstrap_components as dbc
from flask import session
from datetime import datetime

from config import create_session_dir
from layouts import create_main_layout
from popovers import create_popovers
from scripts.callbacks_analysis import register_callbacks_analysis
from scripts.callbacks_upload import register_callbacks_upload
from cleanup_sessions import start_cleanup_thread

# Initialize the Dash app with Bootstrap theme
app = Dash(__name__, 
           external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://use.fontawesome.com/releases/v5.8.1/css/all.css'])
app._favicon = "./assets/favicon.ico"
app.title = "KdSAXS"

# Configure server
server = app.server
server.secret_key = os.urandom(24)  # For session management

# Run cleanup when server starts
start_cleanup_thread()

# Create session directory middleware
@server.before_request
def before_request():
    if 'session_dir' not in session:
        session['session_dir'] = create_session_dir()

# Set the app layout
app.layout = create_main_layout()
app.layout.children.extend(create_popovers())

# Register callbacks with session directory
register_callbacks_analysis(app, lambda: session.get('session_dir'))
register_callbacks_upload(app)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
    #app.run_server(host='0.0.0.0', debug=False, port=8050)
