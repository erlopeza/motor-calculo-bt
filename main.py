# ============================================================
# main.py
# Responsabilidad: flujo principal del programa
# Razón para cambiar: modificar interacción con el usuario
# ============================================================

import sys
import math
import openpyxl
from datetime import datetime
from conductores import LIMITE_DV, TENSION_SISTEMA
from calculos import (
    capacidad_corregida, calcular_potencia,
    calcular_caida_tension, clasificar_caida, sugerir_conductor
)
from excel import (
    leer_circuitos_excel, leer_transformador_excel,
    leer_balance_excel, leer_tableros_excel,
    guardar_txt, exportar_excel, leer_perfil_excel
)
from perfiles import obtener_perfil
from transformador import calcular_icc_transformador, icc_desde_tabla, clasificar_icc, reporte_transformador
from icc_punto import calcular_icc_todos_circuitos
from protecciones import verificar_circuito_completo, leer_protecciones_excel
from balance import calcular_balance_tableros, reporte_balance
from demanda import (
    calcular_demanda, seleccionar_transformador,
    dimensionar_acometida_sec, reporte_demanda
)
from excel import leer_demanda_excel, leer_cadena_excel
from coordinacion import verificar_cadena, reporte_coordinacion

# ============================================================
# GENERACIÓN DE REPORTE TXT
# ============================================================

def generar_seccion_transformador(datos_trafo):
    lineas    = []
    resultado = {}

    if datos_trafo is None:
        lineas.append("  TRANSFORMADOR: no se encontró hoja 'Transformador'")
        lineas.append("  Icc en bornes BT: no calculada")
        return lineas, resultado

    modo = datos_trafo["modo"]

    if modo == "A":
        Icc_kA, Zt_ohm, info = calcular_icc_transformador(
            datos_trafo["kVA"], datos_trafo["Vn_BT"], datos_trafo["Ucc_pct"]
        )
        lineas_trafo = reporte_transformador(info, "A", Icc_kA)
    else:
        Icc_kA, Ucc_pct, kVA_ref = icc_desde_tabla(datos_trafo["kVA"])
        Zt_ohm = (Ucc_pct / 100) * (datos_trafo["Vn_BT"] ** 2 / (datos_trafo["kVA"] * 1000))
        info = {
            "kVA":     datos_trafo["kVA"],
            "Vn_BT":   datos_trafo["Vn_BT"],
            "Ucc_pct": Ucc_pct,
            "In_A":    round(datos_trafo["kVA"] * 1000 / (1.732 * datos_trafo["Vn_BT"]), 1),
            "Zt_ohm":  round(Zt_ohm, 6),
            "Icc_A":   round(Icc_kA * 1000, 1),
        }
        lineas_trafo = reporte_transformador(info, "B", Icc_kA)
        lineas_trafo.append(f"  Referencia tabla: {kVA_ref} kVA (IEC 60076)")

    lineas += lineas_trafo
    resultado = {
        "Icc_kA": Icc_kA, "Zt_ohm": Zt_ohm,
        "nivel": clasificar_icc(Icc_kA),
        "nombre": datos_trafo["nombre"], "modo": modo,
    }
    return lineas, resultado


def generar_reporte_txt(nombre_proyecto, circuitos, fecha,
                        datos_trafo=None, protecciones=None,
                        balance_datos=None, tableros_datos=None,
                        params_demanda=None,
                        cadena_datos=None, perfil=None):
    perfil = perfil or {}
    lineas      = []
    total_ok    = 0
    total_falla = 0
    prot_ok     = 0
    prot_falla  = 0

    # --- ENCABEZADO ---
    lineas.append("=" * 60)
    lineas.append(f"  REPORTE — {nombre_proyecto}")
    lineas.append(f"  Fecha        : {fecha}")
    lineas.append(f"  Normativa    : SEC RIC N10 / NEC / IEC 60364")
    lineas.append(f"  Limite caida : {LIMITE_DV}% circuito final / 5% total")
    lineas.append(f"  Circuitos    : {len(circuitos)}")
    lineas.append("=" * 60)

    # --- TRANSFORMADOR ---
    lineas.append("")
    lineas_trafo, resultado_trafo = generar_seccion_transformador(datos_trafo)
    lineas += lineas_trafo

    # --- Icc POR PUNTO — M2 ---
    if resultado_trafo and "Zt_ohm" in resultado_trafo:
        circuitos = calcular_icc_todos_circuitos(
            resultado_trafo["Zt_ohm"], circuitos
        )

    # --- CIRCUITOS ---
    lineas.append("")
    lineas.append("=" * 60)
    lineas.append("  CIRCUITOS — CAÍDA DE TENSIÓN, Icc Y PROTECCIONES")
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

        if "Icc_kA" in c:
            lineas.append(f"  Icc punto : {c['Icc_kA']} kA  -> {c['nivel_icc']}")

        if protecciones and c["nombre"] in protecciones:
            p = protecciones[c["nombre"]]
            r = verificar_circuito_completo(
                c["nombre"], p["In_A"], p["curva"],
                p["poder_corte_kA"], c.get("Icc_kA", 0), V_nom
            )
            lineas.append(
                f"  Proteccion: {p['curva']}{int(p['In_A'])}A / "
                f"{int(p['poder_corte_kA'])}kA -> {r['estado']}"
            )
            lineas.append(
                f"  Im_min    : {r['Im_min_A']}A | "
                f"margen {r['margen_pct']}% -> {r['clasif_margen']}"
            )
            if r["estado"] == "OK":
                prot_ok += 1
            else:
                prot_falla += 1

        if estado_dV == "FALLA" or estado_I == "SUPERA":
            cond, mm2, dv = sugerir_conductor(
                c["L_m"], c["I_diseno"], c["paralelos"],
                c["sistema"], c["temp_amb"],
                norma=perfil.get("norma", "AWG")
            )
            lineas.append(
                f"  SUGERENCIA: usar {cond} ({mm2}mm2) -> dV={dv}%"
                if cond else
                "  SUGERENCIA: ningun conductor en tabla es suficiente"
            )
            total_falla += 1
        else:
            total_ok += 1

    # --- BALANCE DE CARGA — M4 ---
    resultado_balance = None
    if balance_datos and tableros_datos:
        kVA_trafo = datos_trafo["kVA"] if datos_trafo else 1000
        resultado_balance = calcular_balance_tableros(
            circuitos, balance_datos, tableros_datos, kVA_trafo
        )
        lineas.append("")
        lineas += reporte_balance(resultado_balance)

    # --- DEMANDA MÁXIMA — M6 ---
    resultado_demanda = None
    if params_demanda and balance_datos:
        resultado_demanda = calcular_demanda(
            circuitos, balance_datos, params_demanda
        )
        resultado_trafo_m6 = None
        resultado_sec_m6   = None

        if params_demanda.get("tipo_alimentador") == "transformador":
            resultado_trafo_m6 = seleccionar_transformador(
                resultado_demanda["S_futuro_kva"]
            )
        else:
            resultado_sec_m6 = dimensionar_acometida_sec(
                resultado_demanda["S_futuro_kva"],
                params_demanda["tension_alim"],
                params_demanda["sistema_alim"],
                params_demanda.get("zona_sec", "urbana")
            )

        lineas.append("")
        lineas += reporte_demanda(
            resultado_demanda, resultado_trafo_m6, resultado_sec_m6
        )

    # --- COORDINACIÓN TCC — M7 ---
    if cadena_datos:
        # Agrupar dispositivos por modo
        modos = {}
        for d in cadena_datos:
            m = d.get("modo", "red")
            modos.setdefault(m, []).append(d)

        for modo, dispositivos in modos.items():
            # Ordenar por nivel
            dispositivos_ord = sorted(dispositivos, key=lambda x: x["nivel"])
            # Usar Icc del primer dispositivo disponible, o 0
            Icc_A = 0
            for d in reversed(dispositivos_ord):
                if d.get("Icc_kA"):
                    Icc_A = d["Icc_kA"] * 1000
                    break
            if Icc_A > 0:
                res_cadena = verificar_cadena(
                    dispositivos_ord, Icc_A, sistema="3F_380"
                )
                lineas.append("")
                lineas += reporte_coordinacion(
                    res_cadena, f"Modo {modo}"
                )

    # --- RESUMEN FINAL ---
    lineas.append("")
    lineas.append("=" * 60)
    lineas.append(f"  Circuitos OK    : {total_ok}")
    lineas.append(f"  Circuitos FALLA : {total_falla}")
    if resultado_trafo:
        lineas.append(f"  Icc bornes BT   : {resultado_trafo['Icc_kA']} kA")
        lineas.append(f"  Nivel Icc       : {resultado_trafo['nivel']}")
    if protecciones:
        lineas.append(f"  Protecciones OK : {prot_ok}")
        lineas.append(f"  Protec. FALLA   : {prot_falla}")
    if resultado_balance:
        lineas.append(f"  Uso transf.     : {resultado_balance['uso_trafo_pct']}%"
                      f" -> {resultado_balance['estado_trafo']}")
    lineas.append("=" * 60)

    return lineas, total_ok, total_falla

# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

print("=" * 60)
print("  MOTOR DE CALCULO BT — VERSION MODULAR")
print("  ΔV | Icc | Protecciones | Balance de carga")
print("  Normativa: SEC RIC N10 / NEC / IEC 60364")
print("=" * 60)

ahora         = datetime.now()
fecha         = ahora.strftime("%d/%m/%Y %H:%M")
fecha_archivo = ahora.strftime("%Y%m%d_%H%M")

nombre_proyecto = input("\n  Nombre del proyecto : ").strip()
archivo_excel   = input("  Archivo Excel       : ").strip()

if not archivo_excel.endswith(".xlsx"):
    archivo_excel += ".xlsx"

# --- LEER TODAS LAS HOJAS ---
datos_trafo        = leer_transformador_excel(archivo_excel)
protecciones_excel = {}
balance_datos      = {}
tableros_datos     = {}
params_demanda     = None
cadena_datos       = []
perfil             = obtener_perfil("industrial").copy()

try:
    _libro = openpyxl.load_workbook(archivo_excel, data_only=True)
    datos_perfil = leer_perfil_excel(_libro) or {}
    perfil_clave = datos_perfil.get("perfil", "industrial")
    perfil = obtener_perfil(perfil_clave).copy()

    hoja_perfil = next(
        (_libro[nombre] for nombre in _libro.sheetnames if nombre.lower() == "perfil"),
        None
    )
    norma_explicitada = False
    if hoja_perfil:
        for fila in hoja_perfil.iter_rows(min_row=2, values_only=True):
            if fila[0] and str(fila[0]).strip().lower() == "norma":
                norma_explicitada = True
                break
    if norma_explicitada:
        perfil["norma"] = datos_perfil.get("norma", "AWG").upper()

    protecciones_excel = leer_protecciones_excel(_libro)
    balance_datos      = leer_balance_excel(_libro)
    tableros_datos     = leer_tableros_excel(_libro)

    if protecciones_excel:
        print(f"  Protecciones  : {len(protecciones_excel)} circuitos")
    if balance_datos:
        print(f"  Balance       : {len(balance_datos)} circuitos / "
              f"{len(tableros_datos)} tableros")
    params_demanda = leer_demanda_excel(_libro)
    if params_demanda:
        print(f"  Demanda M6    : {params_demanda['tipo_instalacion']} / "
              f"{params_demanda['tipo_alimentador']}")
    cadena_datos = leer_cadena_excel(_libro)
    if cadena_datos:
        print(f"  Coordinación  : {len(cadena_datos)} dispositivos en cadena")
except Exception as e:
    print(f"  AVISO lectura hojas opcionales: {e}")
    params_demanda = None
    cadena_datos   = []

# --- LEER CIRCUITOS ---
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

if len(circuitos) == 0:
    print("\n  ERROR: no se procesó ningún circuito válido.")
    input("\n  Presiona Enter para cerrar...")
    sys.exit()

# --- GENERAR Y MOSTRAR REPORTE ---
lineas, total_ok, total_falla = generar_reporte_txt(
    nombre_proyecto, circuitos, fecha,
    datos_trafo, protecciones_excel,
    balance_datos, tableros_datos,
    params_demanda, cadena_datos,
    perfil=perfil
)

print()
for linea in lineas:
    print(linea)

# --- GUARDAR ---
nombre_txt  = f"REPORTE_{nombre_proyecto.upper()}_{fecha_archivo}.txt"
nombre_xlsx = f"REPORTE_{nombre_proyecto.upper()}_{fecha_archivo}.xlsx"

guardar_txt(lineas, nombre_txt)
exportar_excel(nombre_proyecto, circuitos, fecha, nombre_xlsx, perfil=perfil)

print(f"\n  Proyecto  : {nombre_proyecto}")
print(f"  OK        : {total_ok}")
print(f"  FALLA     : {total_falla}")
print("\n  Listo.")
input("\n  Presiona Enter para cerrar...")
