"""Escenarios de referencia para comparacion con SIMARIS Rev02."""

from __future__ import annotations

CATEGORIAS = {
    "ERROR_MOTOR": "Error en formula o supuesto del Motor BT - corregir",
    "SUPUESTO_CONSERVADOR": "SIMARIS usa supuesto mas conservador - documentar",
    "EQUIPO_DISTINTO": "SIMARIS modela equipo diferente al real - documentar",
    "VARIABLE_IGNORADA": "Motor BT considera variable que SIMARIS ignora - ventaja",
    "PENDIENTE": "Sin categoria asignada - requiere analisis manual",
}


ESCENARIOS = [
    {
        "id": "S01",
        "descripcion": "Icc maximo en bornes secundario trafo - modo red",
        "modulo_motor": "transformador",
        "parametros_motor": {
            "Sn_kVA": 1000,
            "Ukr_pct": 4.85,
            "Vn_V": 400,
            "c_max": 1.1,
            "c_min": 0.95,
        },
        "parametros_simaris": {
            "c_max": 1.1,
            "c_min": 0.9,
        },
        "resultado_simaris": {
            "Icc_max_kA": 30.978,
            "Icc_min_kA": None,
        },
        "variable_analisis": "c_min IEC 60909 4.3 vs supuesto SIMARIS",
        "categoria_esperada": "SUPUESTO_CONSERVADOR",
        "metrica": "Icc_max_kA",
    },
    {
        "id": "S02",
        "descripcion": "Icc en bus SWG02-BARRA A despues de ATS01",
        "modulo_motor": "icc_punto",
        "parametros_motor": {
            "Sn_kVA": 1000,
            "Ukr_pct": 4.85,
            "Vn_V": 400,
            "c_max": 1.1,
            "L_cable_m": 5,
            "seccion_mm2": 240,
            "n_cables_paralelo": 4,
            "material": "CU",
            "temp_C": 20,
        },
        "resultado_simaris": {
            "Icc_max_kA": 27.469,
        },
        "variable_analisis": "impedancia cable C/L 15.3 - 4x240mm2 CU 5m",
        "categoria_esperada": "SUPUESTO_CONSERVADOR",
        "metrica": "Icc_max_kA",
    },
    {
        "id": "S03",
        "descripcion": "Icc en bornes GE - modo generador",
        "modulo_motor": "generador",
        "parametros_motor": {
            "Sn_kVA": 404,
            "Vn_V": 380,
            "Xd_pp_pct": 12.0,
            "R1_pct": None,
            "Rs_ohm": 0.0041,
            "c_max": 1.05,
        },
        "parametros_simaris": {
            "Sn_kVA": 650,
            "Vn_V": 400,
            "Xd_pp_pct": 14.0,
            "R1_pct": 2.1,
        },
        "resultado_simaris": {
            "Icc_kA": 2.815,
        },
        "variable_analisis": "SIMARIS modela GE generico 650kVA/400V vs Rivera 404kVA/380V",
        "categoria_esperada": "EQUIPO_DISTINTO",
        "metrica": "Icc_kA",
    },
    {
        "id": "S04",
        "descripcion": "DeltaV circuito C/L 18.1 - BARRA A a CHAMDP01 - 25m 240mm2",
        "modulo_motor": "calculos",
        "parametros_motor": {
            "L_m": 25,
            "seccion_mm2": 240,
            "Ib_A": 322.978,
            "Vn_V": 400,
            "cos_phi": 0.85,
            "sistema": "3F",
            "T_conductor_C": 20,
            "T_conductor_op_C": 60,
        },
        "resultado_simaris": {
            "dv_tramo_pct": 0.529,
            "sum_dv_pct": 0.849,
        },
        "variable_analisis": "temperatura conductor 20C SIMARIS vs 60C operacion real",
        "nota_tecnica": (
            "Motor BT calcula XL del conductor y la documenta como sugerencia tecnica; "
            "no la suma automaticamente al DeltaV. SIMARIS incluye "
            "DeltaU_transformer=2.413% como referencia desde secundario de trafo. "
            "Motor BT reporta DeltaV de tramo independiente. Diferencia de convencion."
        ),
        "categoria_esperada": "VARIABLE_IGNORADA",
        "metrica": "dv_tramo_pct",
    },
    {
        "id": "S05",
        "descripcion": "DeltaV acumulada hasta ANTENNA 1-A - cadena de tramos",
        "modulo_motor": "calculos",
        "parametros_motor": {
            "tramos": [
                {"L_m": 25, "seccion_mm2": 240, "Ib_A": 322.978, "cos_phi": 0.85},
                {"L_m": 5, "seccion_mm2": 35, "Ib_A": 33.962, "cos_phi": 0.85},
            ],
            "Vn_V": 400,
            "sistema": "3F",
        },
        "resultado_simaris": {
            "sum_dv_pct": 0.895,
        },
        "variable_analisis": "propagacion DeltaV en cadena de tableros",
        "nota_tecnica": (
            "DeltaV acumulada SIMARIS incluye DeltaU_trafo(2.413%) + suma de tramos cable. "
            "Motor BT calcula tramos independientes. Para DeltaV total desde secundario trafo, "
            "sumar DeltaU_trafo + suma tramos. Criterio RIC N10 5.1.2."
        ),
        "categoria_esperada": "SUPUESTO_CONSERVADOR",
        "metrica": "sum_dv_pct",
    },
    {
        "id": "S06",
        "descripcion": "Factor simultaneidad SWG02-BARRA A - gi=0.75 SIMARIS",
        "modulo_motor": "demanda",
        "parametros_motor": {
            "cargas": [
                {"nombre": "CRAC 1-A", "P_kW": 50, "cos_phi": 0.85, "ai": 1.0},
                {"nombre": "CRAC 2-A", "P_kW": 50, "cos_phi": 0.85, "ai": 1.0},
                {"nombre": "TRAFO 250-01", "P_kW": 250, "cos_phi": 1.0, "ai": 1.0},
                {"nombre": "TRAFO 250-02", "P_kW": 250, "cos_phi": 1.0, "ai": 1.0},
            ],
            "gi_simaris": 0.75,
            "gi_real_datacenter": 0.85,
        },
        "resultado_simaris": {
            "Ib_A": 986.787,
        },
        "variable_analisis": "gi=0.75 SIMARIS vs gi real datacenter 0.85",
        "categoria_esperada": "VARIABLE_IGNORADA",
        "metrica": "Ib_A",
    },
]
