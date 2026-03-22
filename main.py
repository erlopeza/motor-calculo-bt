# ============================================================
# main.py
# Responsabilidad: flujo principal del programa
# Razón para cambiar: modificar interacción con el usuario
# ============================================================

# Importa todo lo necesario desde los otros módulos
import sys
from datetime import datetime
from conductores import LIMITE_DV, TENSION_SISTEMA
from calculos import (
    capacidad_corregida, calcular_potencia,
    calcular_caida_tension, clasificar_caida, sugerir_conductor
)
from excel import leer_circuitos_excel, guardar_txt, exportar_excel

def generar_reporte_txt(nombre_proyecto, circuitos, fecha):
    """Genera reporte completo como lista de líneas de texto."""
    lineas      = []
    total_ok    = 0
    total_falla = 0

    lineas.append("=" * 60)
    lineas.append(f"  REPORTE — {nombre_proyecto}")
    lineas.append(f"  Fecha        : {fecha}")
    lineas.append(f"  Normativa    : SEC RIC N10 / NEC / IEC 60364")
    lineas.append(f"  Limite caida : {LIMITE_DV}% circuito final / 5% total")
    lineas.append(f"  Circuitos    : {len(circuitos)}")
    lineas.append("=" * 60)

    for c in circuitos:
        I_cap        = capacidad_corregida(c["I_max"], c["paralelos"], c["temp_amb"])
        P_watts      = calcular_potencia(c["I_diseno"], c["cos_phi"], c["sistema"])
        dV_V, dV_pct = calcular_caida_tension(
            c["L_m"], c["S_mm2"], c["I_diseno"], c["paralelos"], c["sistema"]
        )
        estado_dV = clasificar_caida(dV_pct)
        estado_I  = "OK" if c["I_diseno"] <= I_cap else "SUPERA"

        desc_cond = f"{c['paralelos']}x{c['conductor']} (S={c['S_mm2']*c['paralelos']}mm2)" if c["paralelos"] > 1 else f"{c['conductor']} ({c['S_mm2']}mm2)"
        V_nom     = TENSION_SISTEMA[c["sistema"]]

        lineas.append("")
        lineas.append(f"  Circuito  : {c['nombre']}")
        lineas.append(f"  Sistema   : {c['sistema']} / {V_nom}V | Temp: {c['temp_amb']}C")
        lineas.append(f"  Conductor : {desc_cond}")
        lineas.append(f"  Corriente : {c['I_diseno']}A -> {estado_I} (cap. {I_cap}A)")
        lineas.append(f"  Potencia  : {P_watts} W")
        lineas.append(f"  Caida dV  : {dV_V}V ({dV_pct}%) -> {estado_dV}")

        if estado_dV == "FALLA" or estado_I == "SUPERA":
            cond, mm2, dv = sugerir_conductor(
                c["L_m"], c["I_diseno"], c["paralelos"],
                c["sistema"], c["temp_amb"]
            )
            lineas.append(f"  SUGERENCIA: usar {cond} ({mm2}mm2) -> dV={dv}%" if cond else "  SUGERENCIA: ningún conductor en tabla es suficiente")
            total_falla += 1
        else:
            total_ok += 1

    lineas.append("")
    lineas.append("=" * 60)
    lineas.append(f"  Circuitos OK    : {total_ok}")
    lineas.append(f"  Circuitos FALLA : {total_falla}")
    lineas.append("=" * 60)

    return lineas, total_ok, total_falla

# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

print("=" * 60)
print("  MOTOR DE CALCULO BT — VERSION MODULAR")
print("  1F / 2F / 3F | Paralelos | Temp | Sugerencia")
print("  Normativa: SEC RIC N10 / NEC / IEC 60364")
print("=" * 60)

ahora         = datetime.now()
fecha         = ahora.strftime("%d/%m/%Y %H:%M")
fecha_archivo = ahora.strftime("%Y%m%d_%H%M")

nombre_proyecto = input("\n  Nombre del proyecto : ").strip()
archivo_excel   = input("  Archivo Excel       : ").strip()

if not archivo_excel.endswith(".xlsx"):
    archivo_excel += ".xlsx"

try:
    circuitos = leer_circuitos_excel(archivo_excel)
except FileNotFoundError:
    print(f"\n  ERROR: no se encontro '{archivo_excel}'")
    print("  Verifica que el archivo esta en la misma carpeta")
    input("\n  Presiona Enter para cerrar...")
    sys.exit()

if len(circuitos) == 0:
    print("  ERROR: no se encontraron circuitos validos")
    input("\n  Presiona Enter para cerrar...")
    sys.exit()

lineas, total_ok, total_falla = generar_reporte_txt(
    nombre_proyecto, circuitos, fecha
)

print()
for linea in lineas:
    print(linea)

nombre_txt   = f"REPORTE_{nombre_proyecto.upper()}_{fecha_archivo}.txt"
nombre_xlsx  = f"REPORTE_{nombre_proyecto.upper()}_{fecha_archivo}.xlsx"

guardar_txt(lineas, nombre_txt)
exportar_excel(nombre_proyecto, circuitos, fecha, nombre_xlsx)

print(f"\n  Proyecto  : {nombre_proyecto}")
print(f"  OK        : {total_ok}")
print(f"  FALLA     : {total_falla}")
print("\n  Listo.")
input("\n  Presiona Enter para cerrar...")