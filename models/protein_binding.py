# models/protein_binding.py
from .base_model import SAXSModel
from .calculations import ProteinBindingCalculation

class ProteinBindingModel(SAXSModel):
    def calculate(self, exp_saxs, theoretical_saxs_files, receptor_concentration, ligand_concentration, n, kd_range, kd_points, session_dir, q_units):
        if len(theoretical_saxs_files) != n + 2:
            raise ValueError(f"Expected {n+2} theoretical SAXS profiles for stoichiometry {n}, but got {len(theoretical_saxs_files)}")
        return ProteinBindingCalculation.calculate(exp_saxs, theoretical_saxs_files, receptor_concentration, ligand_concentration, n, kd_range, kd_points, session_dir, q_units)
