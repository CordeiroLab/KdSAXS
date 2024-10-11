# models/model_factory.py
from .monomer_oligomer import MonomerOligomerModel
from .protein_binding import ProteinBindingModel

class ModelFactory:
    @staticmethod
    def get_model(model_name):
        if model_name == 'kds_saxs_mon_oligomer':
            return MonomerOligomerModel()
        elif model_name == 'kds_saxs_oligomer_fitting':
            return ProteinBindingModel()
        else:
            raise ValueError(f"Unknown model: {model_name}")
