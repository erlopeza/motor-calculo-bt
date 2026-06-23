"""Script de construcción del fixture LEO-ARICA.

Ejecutar UNA VEZ para producir tests/fixtures/leo_arica.xlsx.
El xlsx resultante se versiona; el test lee ese archivo, no este script.

Valores representativos derivados de cargas datacenter LEO-ARICA:
  racks IT, HVAC, servicios generales.
"""
import os
import openpyxl

DST = os.path.join(os.path.dirname(__file__), "fixtures", "leo_arica.xlsx")

# Subconjunto representativo en formato canónico de la herramienta.
# columnas: Nombre, Sistema, Conductor, Paralelos, I_diseno, cos_phi, L_m, Temp_amb, In_A, curva
FILAS = [
    ("TD-RACKS-1", "3F", "70mm2", 1, 160.0, 0.95, 25.0, 30, 200, "C"),
    ("TD-RACKS-2", "3F", "50mm2", 1, 120.0, 0.95, 30.0, 30, 160, "C"),
    ("TD-HVAC",    "3F", "95mm2", 1, 210.0, 0.90, 18.0, 30, 250, "D"),
    ("TD-SERV",    "3F", "25mm2", 1,  70.0, 0.90, 40.0, 30, 100, "C"),
]

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "circuitos"
ws.append(["Nombre", "Sistema", "Conductor", "Paralelos", "I_diseno",
           "cos_phi", "L_m", "Temp_amb", "In_A", "curva"])
for f in FILAS:
    ws.append(list(f))

wp = wb.create_sheet("perfil")
wp.append(["campo", "valor"])
wp.append(["norma", "MM2"])
wp.append(["proyecto", "LEO-ARICA"])

os.makedirs(os.path.dirname(DST), exist_ok=True)
wb.save(DST)
print("fixture escrito:", DST)
