# models/monomer_oligomer.py
from .base_model import SAXSModel
from .calculations import MonomerOligomerCalculation

class MonomerOligomerModel(SAXSModel):
    def calculate(self, exp_saxs, mon_avg_int, dim_avg_int, concentration, n, kd_range, kd_points):
        return MonomerOligomerCalculation.calculate(exp_saxs, mon_avg_int, dim_avg_int, concentration, n, kd_range, kd_points)
