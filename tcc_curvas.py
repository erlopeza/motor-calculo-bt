# ============================================================
# tcc_curvas.py
# Responsabilidad: librería de curvas TCC (Time-Current Characteristics)
# Catálogo DATA-3: IEC 60898 (B/C/D) e IEC 60255 (NI/VI/EI/LTI)
# Razón para cambiar: agregar nuevos tipos de curva o fabricantes
# ============================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

_CATALOG_PATH = Path(__file__).parent / "data" / "tcc_catalog.json"

# Tiempo de disparo instantáneo — IEC 60947-2 §7.2.1
_T_INST_S = 0.02


def _cargar_json() -> dict:
    with open(_CATALOG_PATH, encoding="utf-8") as fh:
        return json.load(fh)


_CATALOGO_DATA: dict = _cargar_json()

CATALOGO_VERSION: str = _CATALOGO_DATA["version"]


def cargar_catalogo() -> list[dict]:
    """Retorna la lista completa de entradas del catálogo DATA-3."""
    return list(_CATALOGO_DATA["curvas"])


def listar_disponibles() -> dict[str, list[str]]:
    """Retorna {tipo: [modelo, ...]} para todas las curvas del catálogo."""
    resultado: dict[str, list[str]] = {}
    for entrada in _CATALOGO_DATA["curvas"]:
        tipo = entrada["tipo"]
        modelo = entrada["modelo"]
        resultado.setdefault(tipo, [])
        if modelo not in resultado[tipo]:
            resultado[tipo].append(modelo)
    return resultado


def buscar_curva(tipo: str, modelo: str) -> Optional[dict]:
    """Busca una curva en el catálogo por tipo + modelo (insensible a mayúsculas).

    Retorna el dict de la entrada o None si no existe.

    Nota: el catálogo incluye un campo 'fabricante' (hoy solo "generico").
    El filtrado por fabricante se añadirá cuando existan curvas propietarias.
    """
    tipo_n = tipo.upper()
    modelo_n = modelo.upper()
    for entrada in _CATALOGO_DATA["curvas"]:
        if (
            entrada["tipo"].upper() == tipo_n
            and entrada["modelo"].upper() == modelo_n
        ):
            return entrada
    return None


def calcular_tiempo_tcc(
    I_A: float,
    In_A: float,
    tipo: str,
    modelo: str,
    tms: float = 1.0,
) -> dict:
    """Calcula el tiempo de disparo de una curva TCC para la corriente dada.

    Parámetros:
        I_A    : corriente de falla en A
        In_A   : corriente nominal / de pickup en A (según tipo de curva)
        tipo   : "IEC60898" | "IEC60255"
        modelo : "B"/"C"/"D" | "NI"/"VI"/"EI"/"LTI"
        tms    : Time Multiplier Setting (solo IDMT, default 1.0)

    Retorna dict con:
        t_s     : float | None — tiempo en segundos (None si no aplica)
        region  : str — "termico" / "instantaneo" / "idmt" / "no_dispara" / "desconocida"
        dispara : bool | None
        nota    : str
    """
    if float(In_A) <= 0:
        raise ValueError(
            f"In_A (corriente nominal/pickup) debe ser > 0, se recibió {In_A}"
        )

    entrada = buscar_curva(tipo, modelo)
    if entrada is None:
        return {
            "t_s": None,
            "region": "desconocida",
            "dispara": False,
            "nota": f"Curva tipo='{tipo}' modelo='{modelo}' no encontrada en catálogo",
        }

    formula = entrada["formula"]
    p = entrada["parametros"]

    if formula == "termica_k_cuadrado":
        return _calcular_iec60898(float(I_A), float(In_A), p)
    elif formula == "idmt":
        return _calcular_idmt(float(I_A), float(In_A), p, float(tms))

    return {
        "t_s": None,
        "region": "desconocida",
        "dispara": False,
        "nota": f"Fórmula '{formula}' no implementada",
    }


# ---------------------------------------------------------------------------
# Fórmulas internas
# ---------------------------------------------------------------------------

def _calcular_iec60898(I_A: float, In_A: float, p: dict) -> dict:
    """Curva IEC 60898: región térmica t = k/(I/In)^2, región instantánea."""
    k = float(p["k"])
    i_mag_max = float(p["I_mag_max_xIn"]) * In_A
    t_inst = float(p.get("t_inst_s", _T_INST_S))

    if I_A >= i_mag_max:
        return {
            "t_s": t_inst,
            "region": "instantaneo",
            "dispara": True,
            "nota": f"I={I_A:.0f}A ≥ Ii_max={i_mag_max:.0f}A → instantáneo",
        }

    if I_A >= In_A:
        ratio = I_A / In_A
        t = k / (ratio ** 2)
        return {
            "t_s": round(t, 4),
            "region": "termico",
            "dispara": True,
            "nota": f"I={I_A:.0f}A — t = {k}/({ratio:.3f})² = {t:.3f}s",
        }

    return {
        "t_s": None,
        "region": "no_dispara",
        "dispara": False,
        "nota": f"I={I_A:.0f}A < In={In_A:.0f}A → no dispara",
    }


def _calcular_idmt(I_A: float, Is_A: float, p: dict, tms: float) -> dict:
    """Curva IDMT IEC 60255-151: t = TMS × β / ((I/Is)^α − 1).

    Is_A es la corriente de pickup (ajuste del relé).
    """
    alpha = float(p["alpha"])
    beta = float(p["beta"])
    L = float(p.get("L", 0.0))

    if I_A <= Is_A:
        return {
            "t_s": None,
            "region": "no_dispara",
            "dispara": False,
            "nota": f"I={I_A:.0f}A ≤ Is={Is_A:.0f}A → no dispara",
        }

    ratio = I_A / Is_A
    denominador = (ratio ** alpha) - 1.0
    if denominador <= 0:
        return {
            "t_s": None,
            "region": "no_dispara",
            "dispara": False,
            "nota": f"Denominador IDMT={denominador:.6f} ≤ 0 — fuera de rango",
        }

    t = tms * (beta / denominador + L)
    return {
        "t_s": round(t, 4),
        "region": "idmt",
        "dispara": True,
        "nota": f"I={I_A:.0f}A, Is={Is_A:.0f}A, TMS={tms} → t={t:.3f}s (IEC 60255-151)",
    }
