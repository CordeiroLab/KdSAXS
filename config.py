# config.py
import os
import uuid
from datetime import datetime

# Directory configurations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Session management
def create_session_dir():
    session_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = f"session_{session_id}_{timestamp}"
    
    # Create main session directory
    session_path = os.path.join(BASE_DIR, "output_data", "sessions", session_dir)
    
    # Create subdirectories
    os.makedirs(os.path.join(session_path, "uploads", "experimental"), exist_ok=True)
    os.makedirs(os.path.join(session_path, "uploads", "theoretical"), exist_ok=True)
    os.makedirs(os.path.join(session_path, "theoretical_int"), exist_ok=True)
    os.makedirs(os.path.join(session_path, "fits"), exist_ok=True)
    os.makedirs(os.path.join(session_path, "logs"), exist_ok=True)
    
    # For Monomer-Oligomer model
    os.makedirs(os.path.join(session_path, "pdbs", "monomer"), exist_ok=True)
    os.makedirs(os.path.join(session_path, "pdbs", "oligomer"), exist_ok=True)
    
    # For Protein Binding model
    os.makedirs(os.path.join(session_path, "pdbs", "receptor"), exist_ok=True)
    os.makedirs(os.path.join(session_path, "pdbs", "receptor_ligand"), exist_ok=True)
    os.makedirs(os.path.join(session_path, "pdbs", "ligand"), exist_ok=True)
    
    # Common directories for both models
    os.makedirs(os.path.join(session_path, "pdbs", "calculated_profiles"), exist_ok=True)
    os.makedirs(os.path.join(session_path, "pdbs", "averaged_profiles"), exist_ok=True)
    
    return session_path

# Model configurations
ALLOWED_MODELS = ['kds_saxs_mon_oligomer', 'kds_saxs_oligomer_fitting']
DEFAULT_MODEL = 'kds_saxs_mon_oligomer'

# Analysis configurations
KD_RANGE = (0.01, 10000)
KD_POINTS = 50

CONCENTRATION_RANGE = (0.1, 12000)
CONCENTRATION_POINTS = 50

# ATSAS configuration
ATSAS_PATH = "/Users/tiago/ATSAS-3.2.1-1/bin/"

CRYSOL_COMMAND = "crysol"  # Command name
CRYSOL_PARAMS = {
    'points': 101,  # -ns parameter
    'implicit_hydrogens': 1,  # --implicit-hydrogen parameter
}

# Add log directory configuration
LOG_DIRECTORY = os.path.join(BASE_DIR, "output_data", "logs")

# Add to config.py
MAX_PDB_UPLOADS = 20
MAX_PDB_SIZE = 10 * 1024 * 1024  # 10MB in bytes
