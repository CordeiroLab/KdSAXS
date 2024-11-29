import os
import subprocess
import numpy as np
from config import ATSAS_PATH, CRYSOL_COMMAND, CRYSOL_PARAMS
from scripts.error_handling import logger

class CrysolHandler:
    def __init__(self, session_dir):
        """
        Initialize CRYSOL handler
        Args:
            session_dir: Path to current session directory
        """
        self.session_dir = session_dir
        self.crysol_path = os.path.join(ATSAS_PATH, CRYSOL_COMMAND)
        
    def run_crysol(self, pdb_file, output_prefix=None):
        """
        Run CRYSOL on a single PDB file
        Args:
            pdb_file: Path to PDB file
            output_prefix: Prefix for output files (optional)
        Returns:
            Path to calculated intensity file
        """
        try:
            if not os.path.exists(pdb_file):
                raise FileNotFoundError(f"PDB file not found: {pdb_file}")
            if not pdb_file.lower().endswith('.pdb'):
                raise ValueError("Invalid file format. Must be .pdb")
            
            # Create command with default parameters
            cmd = [
                self.crysol_path,
                pdb_file,
                '-ns', str(CRYSOL_PARAMS['points']),
                '--implicit-hydrogen=' + str(CRYSOL_PARAMS['implicit_hydrogens'])
            ]
            
            if output_prefix:
                cmd.extend(['-p', output_prefix])
            
            # Run CRYSOL
            result = subprocess.run(cmd, 
                                 capture_output=True, 
                                 text=True, 
                                 cwd=os.path.dirname(pdb_file))
            
            if result.returncode != 0:
                raise RuntimeError(f"CRYSOL failed: {result.stderr}")
            
            # Get output intensity file (ends with 00.int)
            output_file = pdb_file.rsplit('.', 1)[0] + ".int"
            if not os.path.exists(output_file):
                raise FileNotFoundError(f"CRYSOL output file not found: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error running CRYSOL on {pdb_file}: {str(e)}")
            raise
    
    def process_multiple_pdbs(self, pdb_files, state):
        """
        Process multiple PDB files for a given state
        Args:
            pdb_files: List of PDB file paths
            state: State identifier (e.g., 'monomer', 'oligomer', 'receptor', etc.)
        Returns:
            Path to averaged intensity file
        """
        try:
            # Calculate profiles for each PDB
            intensity_files = []
            for pdb_file in pdb_files:
                intensity_file = self.run_crysol(pdb_file)
                # Load only q and I(q) columns from the intensity file
                data = np.loadtxt(intensity_file, skiprows=1)
                intensity_files.append(data[:, [0, 1]])  # Only keep q and I(q) columns
            
            # Average the profiles if multiple files
            if len(intensity_files) > 1:
                avg_profile = self.average_profiles(intensity_files)
            else:
                # If single file, just use the first two columns
                avg_profile = intensity_files[0]
                
            # Save averaged/processed profile
            avg_file = os.path.join(self.session_dir, 'pdbs', 'averaged_profiles', f'avg_{state}.int')
            np.savetxt(avg_file, avg_profile)
            
            return avg_file
            
        except Exception as e:
            logger.error(f"Error processing multiple PDBs for {state}: {str(e)}")
            raise
    
    @staticmethod
    def average_profiles(intensity_files):
        """
        Average multiple intensity profiles
        Args:
            intensity_files: List of numpy arrays containing q and I(q) columns
        Returns:
            Averaged profile as numpy array
        """
        try:
            # All files should already be numpy arrays with q and I(q) columns
            # Stack all intensities and calculate mean
            q_values = intensity_files[0][:, 0]  # q values from first file
            intensities = np.array([profile[:, 1] for profile in intensity_files])
            avg_intensity = np.mean(intensities, axis=0)
            
            # Return combined q and averaged I(q)
            return np.column_stack((q_values, avg_intensity))
            
        except Exception as e:
            logger.error(f"Error averaging profiles: {str(e)}")
            raise
