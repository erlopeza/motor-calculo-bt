"""Base de conocimiento de sugerencias para flujo guiado."""

from __future__ import annotations

import difflib
import unicodedata


VALORES_TIPICOS_GE = {
    "t_arranque_ms": {
        "valor": 10000,
        "rango": (8000, 15000),
        "unidad": "ms",
        "fuente": "Cummins / Caterpillar - arranque en frio",
        "pregunta": "Cuanto tiempo puede tolerar sin energia?",
        "opciones": {
            "critico_sts": {"max_ms": 4, "label": "< 4ms - requiere STS/UPS"},
            "critico_ups": {"max_ms": 500, "label": "< 0.5s - requiere UPS"},
            "normal": {"max_ms": 30000, "label": "10-30s - GE estandar"},
            "no_importa": {"max_ms": 60000, "label": "Hasta 1 min - aceptable"},
        },
    },
    "t_estabilizacion_ms": {
        "valor": 5000,
        "rango": (3000, 10000),
        "unidad": "ms",
        "fuente": "Estandar industria - V y f nominales post arranque",
        "nota": "Depende del regulador AVR y carga conectada",
    },
    "derrateo_altitud_m": {
        "valor": 0,
        "rango": (0, 5000),
        "unidad": "m",
        "fuente": "Stamford de-rate table - BS EN 60034",
        "nota": "3% por cada 500m sobre 1000m snm",
    },
}

VALORES_TIPICOS_MOTOR = {
    "factor_arranque": {
        "DOL": {"valor": 6.0, "rango": (5.0, 8.0), "label": "Arranque directo"},
        "YD": {"valor": 2.5, "rango": (2.0, 3.0), "label": "Estrella-triangulo"},
        "VFD": {"valor": 1.2, "rango": (1.0, 1.5), "label": "Variador de frecuencia"},
        "SS": {"valor": 3.0, "rango": (2.5, 4.0), "label": "Softstarter"},
    },
    "fuente": "NCh 4-2003 12.28 / IEC 60034-1",
}

VALORES_TIPICOS_UPS = {
    "profundidad_descarga": {
        "AGM": {"valor": 0.80, "label": "Baterias AGM estandar"},
        "VRLA": {"valor": 0.50, "label": "VRLA - vida util extendida"},
        "LiFePO4": {"valor": 1.00, "label": "Litio - descarga total permitida"},
    },
    "fuente": "IEEE 1184 / fabricante",
}

CARGAS_TIPICAS_RESIDENCIAL = {
    "TV": {"P_W": 150, "cos_phi": 0.95, "fuente": "IEC 62087"},
    "PC_escritorio": {"P_W": 300, "cos_phi": 0.90, "fuente": "Energy Star"},
    "PC_notebook": {"P_W": 65, "cos_phi": 0.90, "fuente": "Energy Star"},
    "Lavadora": {"P_W": 2200, "cos_phi": 0.85, "fuente": "NCh 4-2003 ref"},
    "Refrigerador": {"P_W": 200, "cos_phi": 0.85, "fuente": "Energy Star"},
    "Microondas": {"P_W": 1200, "cos_phi": 0.90, "fuente": "tipico mercado"},
    "Aire_acondicionado_1ton": {"P_W": 1200, "cos_phi": 0.85, "fuente": "ASHRAE"},
    "Iluminacion_LED_punto": {"P_W": 10, "cos_phi": 0.90, "fuente": "IEC 62612"},
}

PARAMETROS_PERFIL = {
    "INDUSTRIAL": {
        "gi": 1.25,
        "cos_phi_base": 0.85,
        "Vn_V": 380,
        "sistema": "3F",
        "fuente": "RIC N04 / NCh 4-2003 - criterio industrial BT",
    },
    "DATACENTER": {
        "gi": 1.25,
        "cos_phi_base": 0.90,
        "Vn_V": 380,
        "sistema": "3F",
        "fuente": "TIA-942 / IEC 60364 - cargas criticas TI",
    },
    "COMERCIAL": {
        "gi": 1.15,
        "cos_phi_base": 0.90,
        "Vn_V": 220,
        "sistema": "1F",
        "fuente": "RIC N04 / criterio comercial BT",
    },
}

CARGAS_TIPICAS_POR_PERFIL = {
    "RESIDENCIAL": CARGAS_TIPICAS_RESIDENCIAL,
    "INDUSTRIAL": {
        "Motor_industrial": {"P_W": 15000, "cos_phi": 0.85, "fuente": "IEC 60034-1"},
        "Bomba_industrial": {"P_W": 7500, "cos_phi": 0.85, "fuente": "NCh 4-2003 motor BT"},
        "Ventilador_industrial": {"P_W": 5500, "cos_phi": 0.82, "fuente": "IEC 60034-1"},
        "Tablero_control": {"P_W": 1000, "cos_phi": 0.90, "fuente": "criterio mercado industrial"},
        "Iluminacion_industrial": {"P_W": 150, "cos_phi": 0.92, "fuente": "IEC 62612"},
    },
    "DATACENTER": {
        "UPS": {"P_W": 220000, "cos_phi": 0.90, "fuente": "IEC 62040 / TIA-942"},
        "STS": {"P_W": 180000, "cos_phi": 0.90, "fuente": "IEC 62310 / TIA-942"},
        "CRAC": {"P_W": 35000, "cos_phi": 0.85, "fuente": "ASHRAE / TIA-942"},
        "Rack_servidores": {"P_W": 8000, "cos_phi": 0.95, "fuente": "TIA-942 carga TI"},
        "Iluminacion_tecnica": {"P_W": 500, "cos_phi": 0.90, "fuente": "IEC 62612"},
    },
    "COMERCIAL": {
        "Iluminacion_comercial": {"P_W": 800, "cos_phi": 0.90, "fuente": "IEC 62612"},
        "Tomacorrientes": {"P_W": 1500, "cos_phi": 0.90, "fuente": "RIC N04 criterio comercial"},
        "HVAC_comercial": {"P_W": 12000, "cos_phi": 0.85, "fuente": "ASHRAE"},
        "Ascensor": {"P_W": 11000, "cos_phi": 0.82, "fuente": "IEC 60034-1"},
        "Escalera_mecanica": {"P_W": 7500, "cos_phi": 0.82, "fuente": "IEC 60034-1"},
    },
}

ALIAS_CARGAS = {
    "television": "TV",
    "televisor": "TV",
    "tv": "TV",
    "notebook": "PC_notebook",
    "laptop": "PC_notebook",
    "pc": "PC_escritorio",
    "aire": "Aire_acondicionado_1ton",
    "bomba": "Bomba_industrial",
    "motor": "Motor_industrial",
    "ventilador": "Ventilador_industrial",
    "ups": "UPS",
    "sts": "STS",
    "crac": "CRAC",
    "rack": "Rack_servidores",
    "servidor": "Rack_servidores",
    "iluminacion": "Iluminacion_comercial",
    "tomacorriente": "Tomacorrientes",
    "hvac": "HVAC_comercial",
    "ascensor": "Ascensor",
}


def _normalize(text: str) -> str:
    txt = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    return txt.lower().replace(" ", "_")


def _normalizar_perfil(perfil: str = None) -> str | None:
    if perfil is None:
        return None
    perfil_norm = _normalize(perfil).upper()
    if perfil_norm in CARGAS_TIPICAS_POR_PERFIL:
        return perfil_norm
    return None


def listar_perfiles() -> list[str]:
    """Retorna perfiles disponibles para el flujo guiado."""
    return sorted(PARAMETROS_PERFIL.keys())


def sugerir_parametros_por_perfil(perfil: str) -> dict:
    """
    Retorna parametros electricos base para un perfil guiado.
    """
    perfil_norm = _normalizar_perfil(perfil)
    if perfil_norm not in PARAMETROS_PERFIL:
        raise ValueError(f"Perfil no reconocido: {perfil}")
    return dict(PARAMETROS_PERFIL[perfil_norm])


def sugerir_parametros_ge(
    P_kVA: float,
    tolerancia_interrupcion: str = None,
) -> dict:
    """
    Dado kVA requerido y tolerancia de interrupcion, retorna sugerencias.
    """
    tol = str(tolerancia_interrupcion or "normal").strip().lower()
    opciones = VALORES_TIPICOS_GE["t_arranque_ms"]["opciones"]
    if tol not in opciones:
        tol = "normal"

    t_arranque = VALORES_TIPICOS_GE["t_arranque_ms"]["valor"]
    t_est = VALORES_TIPICOS_GE["t_estabilizacion_ms"]["valor"]
    max_ms = opciones[tol]["max_ms"]

    topologia = "GE_ESTANDAR"
    advertencias = []
    notas = [
        f"Fuente t_arranque: {VALORES_TIPICOS_GE['t_arranque_ms']['fuente']}",
        f"Fuente t_estabilizacion: {VALORES_TIPICOS_GE['t_estabilizacion_ms']['fuente']}",
    ]

    if tol == "critico_sts":
        topologia = "STS_O_UPS_REQUERIDO"
        advertencias.append("Interrupcion critica (<4ms): GE por si solo no cumple continuidad.")
    elif tol == "critico_ups":
        topologia = "UPS_REQUERIDO"
        advertencias.append("Interrupcion <500ms: considerar UPS de respaldo durante arranque GE.")

    return {
        "parametros": {
            "P_kVA_requerido": float(P_kVA),
            "t_arranque_ms": t_arranque,
            "t_estabilizacion_ms": t_est,
            "derrateo_altitud_m": VALORES_TIPICOS_GE["derrateo_altitud_m"]["valor"],
            "interrupcion_max_ms": max_ms,
        },
        "advertencias": advertencias,
        "topologia_recomendada": topologia,
        "notas": notas,
    }


def sugerir_parametros_motor(
    P_kW: float,
    tipo_arranque: str = None,
) -> dict:
    """
    Dado kW y tipo de arranque, retorna factor de arranque y dV esperada.
    """
    tipo = str(tipo_arranque or "DOL").strip().upper()
    tabla = VALORES_TIPICOS_MOTOR["factor_arranque"]
    if tipo not in tabla:
        tipo = "DOL"
    f = tabla[tipo]

    # Estimacion simple de dV relativa para orientacion inicial.
    dv_esperada_pct = round(min(25.0, 2.0 + f["valor"] * 1.5), 2)

    return {
        "parametros": {
            "P_kW": float(P_kW),
            "tipo_arranque": tipo,
            "factor_arranque": f["valor"],
            "rango_factor": f["rango"],
            "dv_esperada_pct": dv_esperada_pct,
        },
        "notas": [VALORES_TIPICOS_MOTOR["fuente"]],
    }


def sugerir_carga_por_nombre(nombre: str, perfil: str = None) -> dict:
    """
    Dado nombre de artefacto en lenguaje natural, retorna P_W, cos_phi y fuente.
    """
    if not nombre:
        return {}

    norm = _normalize(nombre)
    perfil_norm = _normalizar_perfil(perfil)
    perfiles_busqueda = [perfil_norm] if perfil_norm else []
    perfiles_busqueda.extend(p for p in ["RESIDENCIAL", "INDUSTRIAL", "DATACENTER", "COMERCIAL"] if p not in perfiles_busqueda)

    if norm in ALIAS_CARGAS:
        key = ALIAS_CARGAS[norm]
        for perfil_actual in perfiles_busqueda:
            tabla_actual = CARGAS_TIPICAS_POR_PERFIL[perfil_actual]
            if key in tabla_actual:
                return {"nombre": key, "perfil": perfil_actual, **tabla_actual[key]}

    cargas = {}
    for perfil_actual in perfiles_busqueda:
        for key, value in CARGAS_TIPICAS_POR_PERFIL[perfil_actual].items():
            cargas[key] = {"perfil": perfil_actual, **value}

    norm_keys = {_normalize(k): k for k in cargas.keys()}

    if norm in norm_keys:
        k = norm_keys[norm]
        return {"nombre": k, **cargas[k]}

    match = difflib.get_close_matches(norm, list(norm_keys.keys()), n=1, cutoff=0.5)
    if match:
        k = norm_keys[match[0]]
        return {"nombre": k, **cargas[k]}

    return {}


def detectar_sobredimensionamiento(
    valor_ingresado,
    valor_sugerido,
    tolerancia_pct: float = 30.0,
) -> dict:
    """
    Detecta sobre-dimensionamiento respecto al valor sugerido.
    """
    v_in = float(valor_ingresado)
    v_sug = max(float(valor_sugerido), 1e-9)
    factor = v_in / v_sug
    limite = 1.0 + float(tolerancia_pct) / 100.0
    sobredimensionado = factor > limite

    if sobredimensionado:
        mensaje = "Valor sobredimensionado respecto a referencia sugerida."
        sugerencia = f"Reducir a ~{round(v_sug, 3)} (factor actual {round(factor, 3)}x)."
    else:
        mensaje = "Valor dentro de tolerancia."
        sugerencia = "Mantener valor o ajustar segun criterio de ingenieria."

    return {
        "sobredimensionado": sobredimensionado,
        "factor": round(factor, 3),
        "mensaje": mensaje,
        "sugerencia": sugerencia,
    }
