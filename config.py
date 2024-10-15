# config.py
import os

# Directory configurations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIRECTORY = os.path.join(BASE_DIR, "output_data")
LOG_DIRECTORY = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(LOG_DIRECTORY, exist_ok=True)

# Model configurations
ALLOWED_MODELS = ['kds_saxs_mon_oligomer', 'kds_saxs_oligomer_fitting']
DEFAULT_MODEL = 'kds_saxs_mon_oligomer'

# Analysis configurations
KD_RANGE = (0.0001, 10000)
KD_POINTS = 40

CONCENTRATION_RANGE = (1, 1000)
CONCENTRATION_POINTS = 50

# ATSAS configuration
ATSAS_PATH = "/Users/tiago/ATSAS-3.2.1-1/bin/"

# example data paths
EXAMPLE_DATA = {
    'model': 'kds_saxs_mon_oligomer',
    'experimental_saxs': [
        {
            'file': 'examples/blg/exp_saxs_ph8/Blac_1_16_Blac_1_subtraction_0.7_mgml_sample_Blac_1_160000-integrate_subtracted_gunier.dat',
            'concentration': 36
        },
        {
            'file': 'examples/blg/exp_saxs__ph8/Blac_1_11_Blac_1_subtraction_2.5_mgml_sample_Blac_1_110000-integrate_subtracted_gunier.dat',
            'concentration': 138
        }
    ],
    'theoretical_saxs': [
        'examples/blg/theoretical_saxs/avg_mon_ph8.int',
        'examples/blg/theoretical_saxs/avg_dim_ph8.int'
    ]
}
