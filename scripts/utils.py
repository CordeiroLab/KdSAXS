import os
import base64
import pandas as pd
import plotly.graph_objects as go

def save_file(name, content, directory):
    """Decode and store a file uploaded with Plotly Dash."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    data = content.encode("utf8").split(b";base64,")[1]
    file_path = os.path.join(directory, name)
    with open(file_path, "wb") as fp:
        fp.write(base64.decodebytes(data))
    return file_path  # Return the path where the file was saved

def uploaded_files(directory):
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(directory):
        path = os.path.join(directory, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files

def truncate_filename(filename, max_length=50):
    if len(filename) <= max_length:
        return filename
    name, extension = os.path.splitext(filename)
    truncated = name[:max_length-3-len(extension)] + '...' + extension
    return truncated
