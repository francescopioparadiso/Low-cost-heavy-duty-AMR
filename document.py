# IMPORTS -----------------------------------------------------------------------------------------------------------------------------
from math import pi
import numpy as np

import requests, json, re
from bs4 import BeautifulSoup

import sys
import sqlite3


# DATABASE CONNECTION ----------------------------------------------------------------------------------------------------------------
database_path = "/Users/francescopioparadiso/Library/Mobile Documents/com~apple~CloudDocs/PARADISO/01. Francesco/01. Education/02. University/BSc Politecnico di Torino/3 Year/02. Tesi/Tesi/database.db"
conn = sqlite3.connect(database_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()


# FUNCTIONS --------------------------------------------------------------------------------------------------------------------------
def refresh_database(active: bool, source: str):
    if active:
        if source == "RS":
            # deletion and recreation of the database
            cursor.execute('DROP TABLE IF EXISTS RS_springs')
            conn.commit()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS RS_springs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    url TEXT,
                    material TEXT,
                    wire_diameter REAL,
                    mean_diameter REAL,
                    free_length REAL,
                    max_force_length REAL,
                    max_force REAL,
                    spring_constant REAL
                )
                ''')
            conn.commit()

            # fetching data from the website
            url = "https://it.rs-online.com/web/c/ferramenta/clip-e-molle/molle-a-compressione/?rpp=100&selectedNavigation=brands=RS%20PRO"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            response = requests.get(url, headers=headers, timeout=10)
            match = re.search(r'<script type="application/ld\+json" data-next-head="">(\{.*?\})</script>', response.text[:10000], re.DOTALL)
            data = json.loads(match.group(1))
            urls = [item["url"] for item in data.get("itemListElement", [])]

            for i, url in enumerate(urls):
                bar_length = len(urls)
                current_page = i + 1
                filled_length = round(bar_length * current_page / bar_length)
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                sys.stdout.write(f"\r|{bar}| {round(current_page / bar_length * 100)}% (Spring {current_page}/{bar_length})")
                sys.stdout.flush()

                resp = requests.get(url, headers=headers, timeout=10)
                match = re.search(r'<script data-testid="product-list-script" type="application/ld\+json" data-next-head="">(\{.*?\})</script>', resp.text[:10000], re.DOTALL)
                data = json.loads(match.group(1))
                props = {p["name"]: p["value"] for p in data.get("additionalProperty", [])}
                
                def extract(name):
                    val = props.get(name)
                    return float(re.sub(r"[^\d.,]", "", val).replace(",", ".")) if val else None

                material = props.get("Materiale")
                wire_diameter = extract("Diametro filo")
                outer_diameter = extract("Diametro esterno")
                free_length = extract("Lunghezza libera")
                max_force_length = extract("Lunghezza minima di lavoro")
                max_force = extract("Carico alla minima lunghezza di lavoro")
                spring_constant = extract("Passo molla")
                code = int(str(url).split("/")[-1])

                mean_diameter = outer_diameter - wire_diameter

                cursor.execute('''
                    INSERT INTO RS_springs (
                        code, url, material, wire_diameter, mean_diameter, free_length, max_force_length, max_force, spring_constant
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    code, url, material, wire_diameter, mean_diameter, free_length, max_force_length, max_force, spring_constant
                ))
                conn.commit()
        elif source == "MI":
            # deletion and recreation of the database
            cursor.execute('DROP TABLE IF EXISTS MI_springs')
            conn.commit()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS MI_springs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    url TEXT,
                    material TEXT,
                    wire_diameter REAL,
                    mean_diameter REAL,
                    free_length REAL,
                    max_force_length REAL,
                    max_force REAL,
                    spring_constant REAL
                )
                ''')
            conn.commit()

            # fetching data from the website
            for page in range(1, 29):
                url = f"https://www.molle-industriali.it/prodotti/molle-a-compressione?p={page}&product_list_limit=200"
                response = requests.get(url)
                soup = BeautifulSoup(response.content, "html.parser")
                rows = soup.find_all("tr")

                bar_length = 29
                current_page = page + 1
                filled_length = round(bar_length * current_page / 29)
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                sys.stdout.write(f"\r|{bar}| {round(current_page / 29 * 100)}% (Page {current_page}/{29})")
                sys.stdout.flush()

                for row in rows:
                    button = row.find("button")
                    if button:
                        data = row.find_all("td")

                        material = data[1].text.strip()
                        wire_diameter = float(data[2].text.strip().replace(".", "").replace(",", ".")) if data[2].text.strip() != "N/A" else None
                        outer_diameter = float(data[3].text.strip().replace(".", "").replace(",", ".")) if data[3].text.strip() != "N/A" else None
                        free_length = float(data[5].text.strip().replace(".", "").replace(",", ".")) if data[5].text.strip() != "N/A" else None
                        max_force_length = float(data[6].text.strip().replace(".", "").replace(",", ".")) if data[6].text.strip() != "N/A" else None
                        max_force = float(data[8].text.strip().replace(".", "").replace(",", ".")) if data[8].text.strip() != "N/A" else None
                        spring_constant = float(data[9].text.strip().replace(".", "").replace(",", ".")) if data[9].text.strip() != "N/A" else None
                        code = data[11].text.strip()
                        url = f"https://www.molle-industriali.it/{code}"

                        mean_diameter = outer_diameter - wire_diameter

                        if wire_diameter is not None and outer_diameter is not None and free_length is not None and max_force_length is not None and max_force is not None and spring_constant is not None:
                            cursor.execute('''
                                INSERT INTO MI_springs (
                                    code, url, material, wire_diameter, mean_diameter, free_length, max_force_length, max_force, spring_constant
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                code, url, material, wire_diameter, mean_diameter, free_length, max_force_length, max_force, spring_constant
                            ))
                            conn.commit()

def refresh_springs(active: bool, source: str):
    if active:
        # deletion and recreation of the database
        if source == "RS":
            cursor.execute('DROP TABLE IF EXISTS RS_selected_springs')
            conn.commit()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS RS_selected_springs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mass INT,
                    source TEXT,
                    code TEXT,
                    url TEXT,
                    material TEXT,
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
        elif source == "MI":
            cursor.execute('DROP TABLE IF EXISTS MI_selected_springs')
            conn.commit()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS MI_selected_springs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mass INT,
                    source TEXT,
                    code TEXT,
                    url TEXT,
                    material TEXT,
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

        # logic to accept or reject the springs
        if source == "RS":
            cursor.execute('SELECT * FROM RS_springs')
            rows = cursor.fetchall()

            for mass in masses:
                effective_mass = round(mass - m_platform)
                for row in rows:
                    material = row["material"]
                    wire_diameter = row["wire_diameter"]
                    mean_diameter = row["mean_diameter"]
                    free_length = row["free_length"]
                    max_force_length = row["max_force_length"]
                    max_force = row["max_force"]
                    spring_constant = row["spring_constant"]
                    code = row["code"]
                    url = row["url"]

                    PWSD = PH + GAD - WR - WS
                    OD = PWSD - GAD - max_force_length

                    if free_length >= PWSD and max_force_length - MBH - PBH >= PBSH and max_force_length - MBH - PBH >= MBSH and OD >= 0:
                        F_tot = mass*g/2
                        F_molla = weight_distribution*F_tot
                        c = mean_diameter/wire_diameter

                        if material == "Acciaio legato":
                            G = G_values["Filo di acciaio armonico"]
                        elif material == "Acciaio inox":
                            G = G_values["Acciaio inossidabile 302"]

                        i_eff = G*wire_diameter/(8*c**3*spring_constant)
                        #L_b = wire_diameter*(1+i)
                        #g_res = wire_diameter/4
                        #L_Fmax = L_b + g_res*i

                        # static verification
                        lambda_first = (4*c-1)/(4*c-4)+0.615/c

                        if material == "Acciaio legato":
                            tau_amm = 0.5 * Rm_values["Filo di acciaio armonico"]
                        elif material == "Acciaio inox":
                            tau_amm = 0.5 * Rm_values["Acciaio inossidabile 302"]

                        tau_max = lambda_first*8*F_molla*c/(pi*wire_diameter**2)
                        static_safety_coefficient = tau_amm/tau_max

                        # fatigue verification
                        lambda_third = 1+2/c
                        tau_min = lambda_third*8*F_min*c/(pi*wire_diameter**2)

                        if material == "Acciaio legato":
                            b_D = b_D_values["Filo di acciaio armonico"]
                        elif material == "Acciaio inox":
                            b_D = b_D_values["Acciaio inossidabile 302"]

                        if material == "Acciaio legato":
                            delta_tau_0 = delta_tau_0_values["Filo di acciaio armonico"]
                        elif material == "Acciaio inox":
                            delta_tau_0 = delta_tau_0_values["Acciaio inossidabile 302"]

                        if material == "Acciaio legato":
                            b_tau = b_tau_values["Filo di acciaio armonico"]
                        elif material == "Acciaio inox":
                            b_tau = b_tau_values["Acciaio inossidabile 302"]

                        delta_tau_amm = b_D*delta_tau_0-b_tau*tau_min
                        delta_F = max_force-F_min
                        delta_tau_max = lambda_first*8*delta_F*c/(pi*wire_diameter**2)
                        fatigue_safety_coefficient = delta_tau_amm/delta_tau_max

                        # logic to save actually the spring to the database (for RS only static analysis validated)
                        if CS_static_range[0] <= float(static_safety_coefficient):
                            cursor.execute('''
                                INSERT INTO RS_selected_springs (
                                    mass, source, code, url, material, wire_diameter, mean_diameter, free_length, max_force_length, spring_constant, static_safety_coefficient, fatigue_safety_coefficient, obstacles_deflection, effective_num_turns
                                ) VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (effective_mass, 
                                    source,
                                    code,
                                    url,
                                    material,
                                    round(wire_diameter, 2),
                                    round(mean_diameter, 2),
                                    round(free_length, 2),
                                    round(max_force_length, 2),
                                    round(spring_constant, 2),
                                    round(static_safety_coefficient, 2),
                                    round(fatigue_safety_coefficient, 2),
                                    round(OD, 2),
                                    round(i_eff, 2)
                            ))
                            conn.commit()
        elif source == "MI":
            cursor.execute('SELECT * FROM MI_springs')
            rows = cursor.fetchall()

            for mass in masses:
                effective_mass = round(mass - m_platform)
                for row in rows:
                    material = row["material"]
                    wire_diameter = row["wire_diameter"]
                    mean_diameter = row["mean_diameter"]
                    free_length = row["free_length"]
                    max_force_length = row["max_force_length"]
                    max_force = row["max_force"]
                    spring_constant = row["spring_constant"]
                    code = row["code"]
                    url = row["url"]

                    PWSD = PH + GAD - WR - WS
                    OD = PWSD - GAD - max_force_length

                    if free_length >= PWSD and max_force_length - MBH - PBH >= PBSH and max_force_length - MBH - PBH >= MBSH and OD >= 0:
                        F_tot = mass*g/2
                        F_molla = weight_distribution*F_tot
                        
                        c = mean_diameter/wire_diameter
                        i_eff = G_values[material]*wire_diameter/(8*c**3*spring_constant)
                        #L_b = wire_diameter*(1+i)
                        #g_res = wire_diameter/4
                        #L_Fmax = L_b + g_res*i

                        # static verification
                        lambda_first = (4*c-1)/(4*c-4)+0.615/c
                        tau_amm = 0.5 * Rm_values[material]
                        tau_max = lambda_first*8*F_molla*c/(pi*wire_diameter**2)
                        static_safety_coefficient = tau_amm/tau_max

                        # fatigue verification
                        lambda_third = 1+2/c
                        tau_min = lambda_third*8*F_min*c/(pi*wire_diameter**2)
                        delta_tau_amm = b_D_values[material]*delta_tau_0_values[material]-b_tau_values[material]*tau_min
                        delta_F = max_force-F_min
                        delta_tau_max = lambda_first*8*delta_F*c/(pi*wire_diameter**2)
                        fatigue_safety_coefficient = delta_tau_amm/delta_tau_max

                        # logic to save actually the spring to the database
                        if (CS_static_range[0] <= float(static_safety_coefficient) <= CS_static_range[1]) and (CS_fatigue_range[0] <= float(fatigue_safety_coefficient) <= CS_fatigue_range[1]):
                            cursor.execute('''
                                INSERT INTO MI_selected_springs (
                                    mass, source, code, url, material, wire_diameter, mean_diameter, free_length, max_force_length, spring_constant, static_safety_coefficient, fatigue_safety_coefficient, obstacles_deflection, effective_num_turns
                                ) VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (effective_mass, 
                                    source,
                                    code,
                                    url,
                                    material,
                                    round(wire_diameter, 2),
                                    round(mean_diameter, 2),
                                    round(free_length, 2),
                                    round(max_force_length, 2),
                                    round(spring_constant, 2),
                                    round(static_safety_coefficient, 2),
                                    round(fatigue_safety_coefficient, 2),
                                    round(OD, 2),
                                    round(i_eff, 2)
                            ))
                            conn.commit()

def latex_update(active: bool, source: str):
    if active:
        document_path = "/Users/francescopioparadiso/Library/Mobile Documents/com~apple~CloudDocs/PARADISO/01. Francesco/01. Education/02. University/BSc Politecnico di Torino/3 Year/02. Tesi/Tesi/document.tex"
        updated_path = "/Users/francescopioparadiso/Library/Mobile Documents/com~apple~CloudDocs/PARADISO/01. Francesco/01. Education/02. University/BSc Politecnico di Torino/3 Year/02. Tesi/Tesi/LaTeX/updated_document.tex"

        with open(document_path, 'r') as file:
            latex_content = file.read()

        updates = {}
        for i,value in enumerate(masses):
            cursor.execute(f'SELECT * FROM {source}_selected_springs WHERE mass = ? ORDER BY obstacles_deflection DESC', (round(value-m_platform),))
            row = cursor.fetchone()
            row_dict = {key: row[key] for key in row.keys()}

            updates[f"source{i}"] = row_dict["source"]
            updates[f"code{i}"] = row_dict["code"]
            updates[f"mass{i}"] = f"{row_dict['mass']:.0f}"
            updates[f"material{i}"] = row_dict["material"]
            updates[f"wire_diameter{i}"] = f"{row_dict['wire_diameter']:.2f}"
            updates[f"mean_diameter{i}"] = f"{row_dict['mean_diameter']:.2f}"
            updates[f"free_length{i}"] = f"{row_dict['free_length']:.2f}"
            updates[f"max_force_length{i}"] = f"{row_dict['max_force_length']:.2f}"
            updates[f"spring_constant{i}"] = f"{row_dict['spring_constant']:.2f}"
            updates[f"static_safety_coefficient{i}"] = f"{row_dict['static_safety_coefficient']:.2f}"
            updates[f"fatigue_safety_coefficient{i}"] = f"{row_dict['fatigue_safety_coefficient']:.2f}"
            updates[f"obstacles_deflection{i}"] = f"{row_dict['obstacles_deflection']:.2f}"
            updates[f"effective_num_turns{i}"] = f"{row_dict['effective_num_turns']:.2f}"
            updates[f"url{i}"] = row_dict["url"]

        updates["PH"] = f"{PH} mm"
        updates["GAD"] = f"{GAD} mm"
        updates["WR"] = f"{WR} mm"
        updates["WS"] = f"{WS} mm"
        updates["MBH"] = f"{MBH} mm"
        updates["PBH"] = f"{PBH} mm"
        updates["MBSH"] = f"{MBSH} mm"
        updates["PBSH"] = f"{PBSH} mm"

        updates["material0"] = "Filo di acciaio armonico"
        updates["material1"] = "Acciaio inossidabile 302"
        updates["material2"] = "Acciaio inossidabile 316"
        updates["material3"] = "Acciaio zincato"
        for i,value in enumerate(Rm_values):
            updates[f"Rm{i}"] = f"{Rm_values[value]}"
        for i,value in enumerate(Reh_values):
            updates[f"Reh{i}"] = f"{Reh_values[value]}"
        for i,value in enumerate(G_values):
            updates[f"G{i}"] = f"{G_values[value]}"
        for i,value in enumerate(b_D_values):
            updates[f"b_D{i}"] = f"{b_D_values[value]}"
        for i,value in enumerate(delta_tau_0_values):
            updates[f"delta_tau_0{i}"] = f"{delta_tau_0_values[value]}"
        for i,value in enumerate(b_tau_values):
            updates[f"b_tau{i}"] = f"{b_tau_values[value]}"

        updates["kdist"] = weight_distribution
        updates["g"] = g

        for reference, value in updates.items():
            latex_content = latex_content.replace('{{' + reference + '}}', str(value))

        with open(updated_path, 'w') as file:
            file.write(latex_content)



# DATA DEFINITION -------------------------------------------------------------------------------------------------------------------
g = 9.80665
m_platform = 5.3 + 2.7
weight_distribution = 0.2

Rm_values = {
    "Filo di acciaio armonico": 2100,    # MPa
    "Acciaio inossidabile 302": 1700,    # MPa
    "Acciaio inossidabile 316": 1350,   # MPa
    "Acciaio zincato": 2100,    # MPa
}

Reh_values = {
    "Filo di acciaio armonico": 1785,    # MPa
    "Acciaio inossidabile 302": 1275,    # MPa
    "Acciaio inossidabile 316": 1050,   # MPa
    "Acciaio zincato": 1785,    # MPa
}

G_values = {
    "Filo di acciaio armonico": 81000,   # MPa
    "Acciaio inossidabile 302": 74000,   # MPa
    "Acciaio inossidabile 316": 73000,  # MPa
    "Acciaio zincato": 81000,   # MPa
}

b_D_values = {
    "Filo di acciaio armonico": 1.0,
    "Acciaio inossidabile 302": 1.0,
    "Acciaio inossidabile 316": 1.0,
    "Acciaio zincato": 1.0,
}

delta_tau_0_values = {
    "Filo di acciaio armonico": 450,      # MPa
    "Acciaio inossidabile 302": 300,      # MPa
    "Acciaio inossidabile 316": 270,     # MPa
    "Acciaio zincato": 450,      # MPa
}

b_tau_values = {
    "Filo di acciaio armonico": 0.3,
    "Acciaio inossidabile 302": 0.3,
    "Acciaio inossidabile 316": 0.3,
    "Acciaio zincato": 0.3,
}

masses = np.linspace(10, 150, 10) + m_platform
F_min = m_platform*g/2

CS_static_range = [1.05, 3.0]
CS_fatigue_range = [1.05, 3.0]

# geometric parameters
PH = 118
GAD = 5
WR = 50
WS = 25
MBH = 4
PBH = 2
MBSH = 20
PBSH = 18


# PROGRAM EXECUTION ----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    refresh_database(active=False, source="MI")
    refresh_springs(active=False, source="MI")
    latex_update(active=True, source="MI")

    cursor.close()
    conn.close()