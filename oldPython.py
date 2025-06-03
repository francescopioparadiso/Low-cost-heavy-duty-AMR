from math import pi
import numpy as np

import requests
from bs4 import BeautifulSoup

import time
import sys
import sqlite3

# FUNCTIONS ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
database_path = "/Users/francescopioparadiso/Library/Mobile Documents/com~apple~CloudDocs/PARADISO/01. Francesco/01. Education/02. University/BSc Politecnico di Torino/3 Year/02. Tesi/Tesi/database.db"
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

updates = {}
def latex_update(updates: dict):
    document_path = "/Users/francescopioparadiso/Library/Mobile Documents/com~apple~CloudDocs/PARADISO/01. Francesco/01. Education/02. University/BSc Politecnico di Torino/3 Year/02. Tesi/Tesi/document.tex"
    updated_path = "/Users/francescopioparadiso/Library/Mobile Documents/com~apple~CloudDocs/PARADISO/01. Francesco/01. Education/02. University/BSc Politecnico di Torino/3 Year/02. Tesi/Tesi/LaTeX/updated_document.tex"

    with open(document_path, 'r') as file:
        latex_content = file.read()

    for reference, value in updates.items():
        latex_content = latex_content.replace('{{' + reference + '}}', str(value))

    with open(updated_path, 'w') as file:
        file.write(latex_content)

def get_springs():
    for mass in masses:
        effective_mass = round(mass - m_platform)
        print(f"\n🏋 Processing mass: {round(mass-m_platform)}kg")

        for page in range(15, 20):
            url = f"https://www.molle-industriali.it/prodotti/molle-a-compressione?p={page}&product_list_limit=200"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            rows = soup.find_all("tr")

            bar_length = 29
            current_page = page +1
            filled_length = round(bar_length * current_page / 29)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            sys.stdout.write(f"\r|{bar}| {round(current_page / 29 * 100)}% (Page {current_page}/{29})")
            sys.stdout.flush()

            for row in rows:
                button = row.find("button")
                if button:

                    data = row.find_all("td")
                    if len(data) < 12:
                        continue

                    try:
                        wire_diameter = float(data[2].text.strip().replace(".", "").replace(",", ".")) if data[2].text.strip() != "N/A" else None
                    except ValueError:
                        wire_diameter = None

                    if wire_diameter is None:
                        continue
                    
                    try:
                        outer_diameter = float(data[3].text.strip().replace(".", "").replace(",", ".")) if data[3].text.strip() != "N/A" else None
                    except ValueError:
                        outer_diameter = None

                    try:
                        free_length = float(data[5].text.strip().replace(".", "").replace(",", ".")) if data[5].text.strip() != "N/A" else None
                    except ValueError:
                        free_length = None

                    try:
                        max_force_length = float(data[6].text.strip().replace(".", "").replace(",", ".")) if data[6].text.strip() != "N/A" else None
                    except ValueError:
                        max_force_length = None

                    try:
                        forza_massima = float(data[8].text.strip().replace(".", "").replace(",", ".")) if data[8].text.strip() != "N/A" else None
                    except ValueError:
                        forza_massima = None

                    try:
                        spring_constant = float(data[9].text.strip().replace(".", "").replace(",", ".")) if data[9].text.strip() != "N/A" else None
                    except ValueError:
                        spring_constant = None

                    code = data[11].text.strip() if len(data) > 11 else None

                    # ---------------------------------------------------------------------------------------------------------------------------------------------------------

                    if max_force_length is None:
                        continue

                    bases_distance = platform_height + ground_adhesion_deflection - wheel_radius - wheel_support_radius - 2*base_thickness
                    print(bases_distance)

                    obstacles_deflection = bases_distance - max_force_length - ground_adhesion_deflection

                    if free_length >= bases_distance and max_force_length <= (bases_distance - ground_adhesion_deflection) and max_force_length > supports_height:
                        F_tot = mass*g/2
                        F_molla = weight_distribution*F_tot
                        
                        mean_diameter = outer_diameter - wire_diameter
                        c = mean_diameter/wire_diameter
                        i_eff = G*wire_diameter/(8*c**3*spring_constant)
                        #L_b = wire_diameter*(1+i)
                        #g_res = wire_diameter/4
                        #L_Fmax = L_b + g_res*i

                        # verifica statica
                        lambda_first = (4*c-1)/(4*c-4)+0.615/c
                        tau_amm = 0.5*R_m
                        tau_max = lambda_first*8*F_molla*c/(pi*wire_diameter**2)
                        static_safety_coefficient = tau_amm/tau_max

                        # verifica dinamica
                        lambda_third = 1+2/c
                        tau_min = lambda_third*8*F_min*c/(pi*wire_diameter**2)
                        delta_tau_amm = b_D*delta_tau_0-b_tau*tau_min
                        delta_F = forza_massima-F_min
                        delta_tau_max = lambda_first*8*delta_F*c/(pi*wire_diameter**2)
                        fatigue_safety_coefficient = delta_tau_amm/delta_tau_max

                        if (CS_static_range[0] <= static_safety_coefficient <= CS_static_range[1]) and (CS_fatigue_range[0] <= fatigue_safety_coefficient <= CS_fatigue_range[1]):
                            cursor.execute('''
                                INSERT INTO springss (
                                           mass, code, wire_diameter, mean_diameter, free_length, max_force_length, spring_constant, static_safety_coefficient, fatigue_safety_coefficient, obstacles_deflection, effective_num_turns
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (effective_mass, 
                                    code,
                                    round(wire_diameter, 2),
                                    round(mean_diameter, 2),
                                    round(free_length, 2),
                                    round(max_force_length, 2),
                                    round(spring_constant, 2),
                                    round(static_safety_coefficient, 2),
                                    round(fatigue_safety_coefficient, 2),
                                    round(obstacles_deflection, 2),
                                    round(i_eff, 2)
                            ))
                            conn.commit()
    
def should_refresh_springs(bool):
    if bool:
        cursor.execute('DROP TABLE IF EXISTS springss')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS springss (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mass INT,
            code TEXT,
            wire_diameter REAL,
            mean_diameter REAL,
            free_length REAL,
            max_force_length REAL,
            spring_constant REAL,
            static_safety_coefficient REAL,
            fatigue_safety_coefficient REAL,
            obstacles_deflection REAL,
            effective_num_turns REAL
        )
        ''')
        conn.commit()

        start_time = time.time()
        get_springs()
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        print(f"\n⏰ Execution completed in: {minutes}m {seconds}s \n")
        print("🗂️  Database created successfully!")

# INITIAL DATA --------------------------------------------------------------------------------------------------------------------------------------------------------------------
g = 9.80665
m_platform = 5.3 + 2.7
weight_distribution = 0.2

masses = np.linspace(30, 150, 1) + m_platform
F_min = m_platform*g/2

R_m = 1200 # MPa
R_eh = 900 # MPa
G = 80000 # MPa
b_D = 0.83
delta_tau_0 = 390 # MPa
b_tau = 0.22

# FILTERS ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
CS_static_range = [1.05, 2.0]
CS_fatigue_range = [1.05, 2.0]

platform_height = 118
wheel_radius = 50
wheel_support_radius = 25
base_thickness = 5
ground_adhesion_deflection = 5
supports_height = 18

database = {}

# START ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    should_refresh_springs(True)

    for i,value in enumerate(masses):
        cursor.execute('SELECT mass, code, wire_diameter, mean_diameter, free_length, max_force_length, spring_constant, static_safety_coefficient, fatigue_safety_coefficient, obstacles_deflection, effective_num_turns FROM springss WHERE mass = ? ORDER BY obstacles_deflection DESC', (round(value-m_platform),))
        conn.commit()
        mass, code, wire_diameter, mean_diameter, free_length, max_force_length, spring_constant, static_safety_coefficient, fatigue_safety_coefficient, obstacles_deflection, effective_num_turns = cursor.fetchone()

        updates[f"mass{i}"] = f"{mass:.0f}"
        updates[f"code{i}"] = code
        updates[f"wire_diameter{i}"] = f"{wire_diameter:.2f}"
        updates[f"mean_diameter{i}"] = f"{mean_diameter:.2f}"
        updates[f"free_length{i}"] = f"{free_length:.2f}"
        updates[f"max_force_length{i}"] = f"{max_force_length:.2f}"
        updates[f"spring_constant{i}"] = f"{spring_constant:.2f}"
        updates[f"static_safety_coefficient{i}"] = f"{static_safety_coefficient:.2f}"
        updates[f"fatigue_safety_coefficient{i}"] = f"{fatigue_safety_coefficient:.2f}"
        updates[f"obstacles_deflection{i}"] = f"{obstacles_deflection:.2f}"
        updates[f"effective_num_turns{i}"] = f"{effective_num_turns:.2f}"

    m_max = masses.max() - m_platform
    updates["mass_max"] = f"{m_max:.0f}"

    obstacles_deflection_min = 10
    updates["obstacles_deflection_min"] = f"{obstacles_deflection_min:.0f}"

    cost_max = 1000
    updates["cost_max"] = f"{cost_max:.0f}"

    latex_update(updates)
    cursor.close()
    conn.close()