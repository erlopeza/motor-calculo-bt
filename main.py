# ============================================================
# main.py
# Responsabilidad: flujo principal del programa
# Razón para cambiar: modificar interacción con el usuario
# ============================================================

import sys
from datetime import datetime
from conductores import LIMITE_DV, TENSION_SISTEMA
from calculos import (
    capacidad_corregida, calcular_potencia,
    calcular_caida_tension, clasificar_caida, sugerir_conductor
)
from excel import leer_circuitos_excel, leer_transformador_excel, guardar_txt, exportar_excel
from transformador import calcular_icc_transformador, icc_desde_tabla, clasificar_icc, reporte_transformador

# ============================================================
# GENERACIÓN DE REPORTE TXT
# ============================================================

def generar_seccion_transformador(datos_trafo):
    """
    Genera la sección del transformador para el reporte.
    Usa Modo A (datos de placa) o Modo B (tabla típica).
    Retorna lista de líneas y diccionario con resultados.
    """
    lineas    = []
    resultado = {}

    if datos_trafo is None:
        lineas.append("  TRANSFORMADOR: no se encontró hoja 'Transformador'")
        lineas.append("  Icc en bornes BT: no calculada")
        return lineas, resultado

    modo = datos_trafo["modo"]

    if modo == "A":
        # Modo A — cálculo con datos de placa
        Icc_kA, Zt_ohm, info = calcular_icc_transformador(
            datos_trafo["kVA"],
            datos_trafo["Vn_BT"],
            datos_trafo["Ucc_pct"]
        )
        lineas_trafo = reporte_transformador(info, "A", Icc_kA)
    else:
        # Modo B — valores típicos IEC 60076
        Icc_kA, Ucc_pct, kVA_ref = icc_desde_tabla(datos_trafo["kVA"])
        info = {
            "kVA":     datos_trafo["kVA"],
            "Vn_BT":   datos_trafo["Vn_BT"],
            "Ucc_pct": Ucc_pct,
            "In_A":    round(datos_trafo["kVA"] * 1000 / (1.732 * datos_trafo["Vn_BT"]), 1),
            "Zt_ohm":  round((Ucc_pct/100) * (datos_trafo["Vn_BT"]**2 / (datos_trafo["kVA"]*1000)), 6),
            "Icc_A":   round(Icc_kA * 1000, 1),
        }
        lineas_trafo = reporte_transformador(info, "B", Icc_kA)
        lineas_trafo.append(f"  Referencia tabla: {kVA_ref} kVA (IEC 60076)")

    lineas += lineas_trafo

    # Guardar resultado para usar en módulos siguientes
    resultado = {
        "Icc_kA":  Icc_kA,
        "nivel":   clasificar_icc(Icc_kA),
        "nombre":  datos_trafo["nombre"],
        "modo":    modo,
    }

    return lineas, resultado

def generar_reporte_txt(nombre_proyecto, circuitos, fecha, datos_trafo=None):
    """Genera reporte completo como lista de líneas de texto."""
    lineas      = []
    total_ok    = 0
    total_falla = 0

    # --- ENCABEZADO ---
    lineas.append("=" * 60)
    lineas.append(f"  REPORTE — {nombre_proyecto}")
    lineas.append(f"  Fecha        : {fecha}")
    lineas.append(f"  Normativa    : SEC RIC N10 / NEC / IEC 60364")
    lineas.append(f"  Limite caida : {LIMITE_DV}% circuito final / 5% total")
    lineas.append(f"  Circuitos    : {len(circuitos)}")
    lineas.append("=" * 60)

    # --- SECCIÓN TRANSFORMADOR ---
    lineas.append("")
    lineas_trafo, resultado_trafo = generar_seccion_transformador(datos_trafo)
    lineas += lineas_trafo

    # --- SECCIÓN CIRCUITOS ---
    lineas.append("")
    lineas.append("=" * 60)
    lineas.append("  CIRCUITOS — CAÍDA DE TENSIÓN Y VERIFICACIÓN")
    lineas.append("=" * 60)

    for c in circuitos:
        I_cap        = capacidad_corregida(c["I_max"], c["paralelos"], c["temp_amb"])
        P_watts      = calcular_potencia(c["I_diseno"], c["cos_phi"], c["sistema"])
        dV_V, dV_pct = calcular_caida_tension(
            c["L_m"], c["S_mm2"], c["I_diseno"], c["paralelos"], c["sistema"]
        )
        estado_dV = clasificar_caida(dV_pct)
        estado_I  = "OK" if c["I_diseno"] <= I_cap else "SUPERA"

        desc_cond = (
            f"{c['paralelos']}x{c['conductor']} (S={c['S_mm2']*c['paralelos']}mm2)"
            if c["paralelos"] > 1
            else f"{c['conductor']} ({c['S_mm2']}mm2)"
        )
        V_nom = TENSION_SISTEMA[c["sistema"]]

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
            lineas.append(
                f"  SUGERENCIA: usar {cond} ({mm2}mm2) -> dV={dv}%"
                if cond else
                "  SUGERENCIA: ningun conductor en tabla es suficiente"
            )
            total_falla += 1
        else:
            total_ok += 1

    # --- RESUMEN FINAL ---
    lineas.append("")
    lineas.append("=" * 60)
    lineas.append(f"  Circuitos OK    : {total_ok}")
    lineas.append(f"  Circuitos FALLA : {total_falla}")
    if resultado_trafo:
        lineas.append(f"  Icc bornes BT   : {resultado_trafo['Icc_kA']} kA")
        lineas.append(f"  Nivel Icc       : {resultado_trafo['nivel']}")
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

# --- LEER TRANSFORMADOR ---
# No es obligatorio — si no existe la hoja continúa sin Icc
datos_trafo = leer_transformador_excel(archivo_excel)

# --- LEER CIRCUITOS CON MANEJO DE ERRORES ---
try:
    circuitos = leer_circuitos_excel(archivo_excel)
except FileNotFoundError as e:
    print(f"\n  ERROR: {e}")
    input("\n  Presiona Enter para cerrar...")
    sys.exit()
except ValueError as e:
    print(f"\n  ERROR: {e}")
    input("\n  Presiona Enter para cerrar...")
    sys.exit()
except PermissionError as e:
    print(f"\n  ERROR: {e}")
    input("\n  Presiona Enter para cerrar...")
    sys.exit()
except Exception as e:
    print(f"\n  ERROR inesperado: {e}")
    print("  Contacta al desarrollador con este mensaje.")
    input("\n  Presiona Enter para cerrar...")
    sys.exit()

# --- VALIDAR QUE HAY CIRCUITOS ---
if len(circuitos) == 0:
    print("\n  ERROR: no se procesó ningún circuito válido.")
    print("  Revisa las advertencias anteriores y corrige el Excel.")
    input("\n  Presiona Enter para cerrar...")
    sys.exit()

if len(circuitos) < 10:
    print(f"\n  Continuando con {len(circuitos)} circuitos válidos...")

# --- GENERAR Y MOSTRAR REPORTE ---
lineas, total_ok, total_falla = generar_reporte_txt(
    nombre_proyecto, circuitos, fecha, datos_trafo
)

print()
for linea in lineas:
    print(linea)

# --- GUARDAR ARCHIVOS ---
nombre_txt  = f"REPORTE_{nombre_proyecto.upper()}_{fecha_archivo}.txt"
nombre_xlsx = f"REPORTE_{nombre_proyecto.upper()}_{fecha_archivo}.xlsx"

guardar_txt(lineas, nombre_txt)
exportar_excel(nombre_proyecto, circuitos, fecha, nombre_xlsx)

print(f"\n  Proyecto  : {nombre_proyecto}")
print(f"  OK        : {total_ok}")
print(f"  FALLA     : {total_falla}")
print("\n  Listo.")
input("\n  Presiona Enter para cerrar...")