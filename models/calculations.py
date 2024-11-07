# models/calculations.py
import os
import numpy as np
import pandas as pd
from scipy.optimize import fsolve
import subprocess
import re
from config import KD_RANGE, KD_POINTS, ATSAS_PATH, LOG_DIRECTORY
from scripts.error_handling import logger
from scripts.utils import format_concentration

def extract_chi_squared(log_file_path):
    try:
        # Ensure the log directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        with open(log_file_path, 'r') as file:
            log_content = file.read()

        # Find all occurrences of .dat followed by a chi-squared value
        matches = re.findall(r'\.dat.*?(\d+\.\d+)', log_content)

        # Check if we have at least two .dat occurrences and extract the second chi-squared value
        if len(matches) >= 2:
            chi_squared = float(matches[1])  # Second chi-squared value
            return chi_squared
        else:
            print("Less than two .dat occurrences found.")
            return None
    except FileNotFoundError:
        print(f"File not found: {log_file_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

class MonomerOligomerCalculation:
    @staticmethod
    def solve_system(concentration, Kd, n):
        def equations(vars):
            M, O = vars
            eq1 = O * Kd - M**n
            eq2 = concentration - (M + n * O)
            return [eq1, eq2]
        
        initial_guesses = [concentration, concentration / 3]
        solution = fsolve(equations, initial_guesses)
        
        if all(x >= 0 for x in solution):
            return solution
        else:
            return [np.nan, np.nan]


    @staticmethod
    def calculate(exp_saxs, mon_avg_int, dim_avg_int, concentration, n, kd_range, kd_points):
        try:
            Kd_values = np.round(np.geomspace(kd_range[0], kd_range[1], num=kd_points), decimals=2)

            mon_avg_int = np.loadtxt(mon_avg_int, skiprows=1)
            dim_avg_int = np.loadtxt(dim_avg_int, skiprows=1)
        
            chi_squared_values = []
        
            for Kd in Kd_values:
                #print(Kd)
                M, O = MonomerOligomerCalculation.solve_system(concentration, Kd, n)
                if not np.isnan(M):
                    monomer_fraction = M / concentration
                    oligomer_fraction = n * O / concentration  # Multiply by n because each oligomer contains n monomers
        
                    #print(f"Concentration is : {concentration}")
                    #print(f" Fractions are: monomer : {monomer_fraction}, oligomer : {oligomer_fraction}")
        
                    # Calculate the weighted sum of the theoretical scattering curves
                    theoretical_sum_int = monomer_fraction * mon_avg_int + oligomer_fraction * dim_avg_int
        
                    # Save the summed intensity file for use with oligomer
                    np.savetxt(f"./output_data/theoretical_{Kd}.int", theoretical_sum_int)
        
                    # Ensure log directory exists
                    os.makedirs(LOG_DIRECTORY, exist_ok=True)
        
                    # System call to oligomer to calculate chi-squared to the experimental data
                    cmd = f"{ATSAS_PATH}/oligomer -ff ./output_data/theoretical_{Kd}.int {exp_saxs} --fit=./output_data/fit_{format_concentration(concentration)}_{Kd}.fit --out={os.path.join(LOG_DIRECTORY, 'oligomer.log')} -cst -ws -un=2"
                    cmd = cmd.replace('\0', '')  # because of \ in pathname
        
                    #print(cmd)
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
                    # Parse the output from oligomer to retrieve the chi-squared value
                    chi_squared = extract_chi_squared(os.path.join(LOG_DIRECTORY, 'oligomer.log'))
        
                    #print(f"For Kd={Kd} uM  X2={chi_squared}")
                    
                    chi_squared_values.append((Kd, concentration, monomer_fraction, oligomer_fraction, chi_squared))
        
            chi_squared_values = pd.DataFrame(chi_squared_values, columns=["kd", "concentration", "mon_frac", "dim_frac", "chi2"])
            chi_squared_values.fillna(0, inplace=True)
        
            return chi_squared_values
        except Exception as e:
            logger.error(f"Error in MonomerOligomerCalculation: {str(e)}")
            raise

    @staticmethod
    def calculate_fractions(kd, concentration_range, n):
        fractions = []
        for concentration in concentration_range:
            M, O = MonomerOligomerCalculation.solve_system(concentration, kd, n)
            monomer_fraction = M / concentration
            oligomer_fraction = n * O / concentration
            fractions.append((concentration, monomer_fraction, oligomer_fraction))
        return pd.DataFrame(fractions, columns=['concentration', 'monomer_fraction', 'oligomer_fraction'])

    

class ProteinBindingCalculation:
    @staticmethod
    def solve_system(receptor_concentration , ligand_concentration, Kd, n):
        def equations(vars):
            receptor_vals = vars[:n+1]  # receptor_0, receptor_1, ..., receptor_n
            ligand_free = vars[n+1]  # Free ligand

            eqs = []
            eq1 = sum(receptor_vals) - receptor_concentration  # Total receptor balance
            eq2 = ligand_free + sum(j * receptor_vals[j] for j in range(1, n+1)) - ligand_concentration  # Total ligand balance

            # Create equilibrium equations dynamically based on n
            for j in range(1, n+1):
                scaling_factor = j / (n - j + 1)  # Kd scaling factor
                eq_kd = scaling_factor * Kd * receptor_vals[j] - receptor_vals[j-1] * ligand_free
                eqs.append(eq_kd)

            return [eq1, eq2] + eqs  # Ensure the number of equations matches the variables

        initial_guesses = [receptor_concentration / (10 ** j) for j in range(n+1)]
        initial_guesses.append(ligand_concentration)  # Initial guess for ligand_free

        solution = fsolve(equations, initial_guesses, xtol=1e-8)

        if all(x >= 0 for x in solution):
            receptor_vals = solution[:n+1]
            ligand_free = solution[n+1]
            return receptor_vals, ligand_free
        else:
            return [np.nan] * (n + 1), np.nan

    @staticmethod
    def calculate_fractions(kd, concentration_range, n, receptor_concentration):
        fractions = []
        for ligand_concentration in concentration_range:
            receptor_vals, ligand_free = ProteinBindingCalculation.solve_system(
                receptor_concentration / n, ligand_concentration, kd, n)
            
            total = sum(receptor_vals) + ligand_free
            receptor_fracs = [receptor_val / total for receptor_val in receptor_vals]
            ligand_free_frac = ligand_free / total
            
            fractions.append((ligand_concentration, *receptor_fracs, ligand_free_frac))
        
        columns = ['concentration'] + [f'receptor_{i}_frac' for i in range(n+1)] + ['ligand_free_frac']
        return pd.DataFrame(fractions, columns=columns)

    @staticmethod
    def calculate(exp_saxs, theoretical_saxs_files, receptor_concentration, ligand_concentration, n, kd_range, kd_points):
        try:
            if receptor_concentration is None:
                raise ValueError("Receptor concentration cannot be None")
            
            Kd_values = np.round(np.geomspace(kd_range[0], kd_range[1], num=kd_points), decimals=2)
            chi_squared_values = []

            # Loop through each Kd value
            for Kd in Kd_values:
                receptor_vals, ligand_free = ProteinBindingCalculation.solve_system(receptor_concentration / n, ligand_concentration, Kd, n)

                if not any(np.isnan(x) for x in receptor_vals + [ligand_free]):
                    receptor_fracs = [receptor_val / (ligand_free + receptor_concentration / n) for receptor_val in receptor_vals]
                    ligand_free_frac = ligand_free / (ligand_free + receptor_concentration / n)

                    # Load theoretical SAXS curves
                    theoretical_saxs = np.zeros_like(np.loadtxt(theoretical_saxs_files[0], usecols=(0, 1)))

                    # Sum SAXS curves using calculated molecular fractions
                    for j in range(n+1):
                        theoretical_saxs += receptor_fracs[j] * np.loadtxt(theoretical_saxs_files[j], usecols=(0, 1))

                    # Add free ligand contribution
                    theoretical_saxs += ligand_free_frac * np.loadtxt(theoretical_saxs_files[n+1], usecols=(0, 1))

                    # Save the resulting theoretical SAXS file
                    np.savetxt(f"./output_data/theoretical_{Kd}.int", theoretical_saxs)

                    # Ensure log directory exists
                    os.makedirs(LOG_DIRECTORY, exist_ok=True)

                    # Run ATSAS oligomer tool to calculate chi-squared
                    cmd = f"{ATSAS_PATH}/oligomer -ff ./output_data/theoretical_{Kd}.int {exp_saxs} --fit=./output_data/fit_{format_concentration(ligand_concentration)}_{Kd}.fit --out={os.path.join(LOG_DIRECTORY, 'oligomer.log')} -cst -ws -un=1"
                    cmd = cmd.replace('\0', '')  # because of \ in pathname

                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                    # Parse the log file for chi-squared value
                    chi_squared = extract_chi_squared(os.path.join(LOG_DIRECTORY, 'oligomer.log'))

                    chi_squared_values.append((Kd, ligand_concentration, *receptor_fracs, ligand_free_frac, sum(receptor_fracs) + ligand_free_frac, chi_squared))

            # Return the results in a DataFrame
            chi_squared_values = pd.DataFrame(chi_squared_values, columns=["kd","concentration"] + [f"receptor_{i}_frac" for i in range(n+1)] + ["ligand_free_frac", "total_fractions", "chi2"])
            chi_squared_values.fillna(0, inplace=True)

            return pd.DataFrame(chi_squared_values, columns=["kd", "chi2", "concentration"])
        except Exception as e:
            logger.error(f"Error in ProteinBindingCalculation: {str(e)}")
            raise
