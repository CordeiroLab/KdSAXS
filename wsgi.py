from app import app

server = app.server

# Add Gunicorn configurations
timeout = 300  # 5 minutes

if __name__ == "__main__":
    app.run_server(debug=False)
