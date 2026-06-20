"""
Modulo M8 - Arranque de motores electricos trifasicos BT.
Calculo de corriente nominal, corriente de arranque,
metodo de arranque y seleccion de guardamotor.
"""
from motores import (
    calcular_corriente_arranque as _calcular_corriente_arranque_motor,
    calcular_corriente_motor as _calcular_corriente_motor,
    recomendar_metodo_arranque as _recomendar_metodo_arranque,
    seleccionar_guardamotor as _seleccionar_guardamotor_motor,
)


def corriente_nominal(potencia_kw: float, tension_v: float, fp: float, rendimiento: float) -> float:
    """
    Corriente nominal motor trifasico.
    In = P / (sqrt(3) x V x fp x eta).
    Raise ValueError si potencia/tension <= 0 o fp/rendimiento fuera [0,1].
    """
    if potencia_kw <= 0:
        raise ValueError("La potencia debe ser mayor que cero")
    if tension_v <= 0:
        raise ValueError("La tension debe ser mayor que cero")
    if not 0 < fp <= 1:
        raise ValueError("El factor de potencia debe estar en rango (0, 1]")
    if not 0 < rendimiento <= 1:
        raise ValueError("El rendimiento debe estar en rango (0, 1]")

    return _calcular_corriente_motor(potencia_kw, tension_v, fp, rendimiento, sistema="3F")


def corriente_arranque(in_a: float, factor_ia: float = 6.0) -> float:
    """
    Corriente de arranque directo (DOL).
    Ia = In x factor_ia (factor tipico 5-7, default 6).
    Retorna solo I_arranque_A extraido del dict canonico de motores.py;
    esta simplificacion es intencional en la fachada M8 GUI.
    Raise ValueError si in_a <= 0 o factor_ia <= 0.
    """
    if in_a <= 0:
        raise ValueError("La corriente nominal debe ser mayor que cero")
    if factor_ia <= 0:
        raise ValueError("El factor de arranque debe ser mayor que cero")
    resultado = _calcular_corriente_arranque_motor(in_a, "directo", factor_arranque=factor_ia)
    return resultado["I_arranque"]


def metodo_arranque(potencia_kw: float, tension_v: float = 380) -> dict:
    """Fachada GUI: delega en motores.recomendar_metodo_arranque."""
    return _recomendar_metodo_arranque(potencia_kw, tension_v)


def seleccionar_guardamotor(in_a: float) -> dict:
    """
    Selecciona rango de guardamotor segun In.
    Retorna rango_min, rango_max y ajuste_recomendado.
    Raise ValueError si in_a <= 0 o queda fuera de tabla.
    """
    if in_a <= 0:
        raise ValueError("La corriente nominal debe ser mayor que cero")

    resultado = _seleccionar_guardamotor_motor(in_a)
    if not resultado["rango_min"] <= in_a <= resultado["rango_max"]:
        raise ValueError("Corriente fuera de tabla de guardamotores")
    return {
        "rango_min": resultado["rango_min"],
        "rango_max": resultado["rango_max"],
        "ajuste_recomendado": resultado["ajuste"],
    }


def calcular_arranque_completo(
    potencia_kw: float,
    tension_v: float,
    fp: float,
    rendimiento: float,
    factor_ia: float = 6.0,
) -> dict:
    """
    Orquestador: llama a corriente nominal, corriente de arranque,
    metodo de arranque y seleccion de guardamotor.
    Retorna in_a, ia_arranque_a, metodo y guardamotor.
    """
    in_a = corriente_nominal(potencia_kw, tension_v, fp, rendimiento)
    ia_arranque_a = corriente_arranque(in_a, factor_ia)
    metodo = metodo_arranque(potencia_kw, tension_v)
    guardamotor = seleccionar_guardamotor(in_a)
    return {
        "in_a": in_a,
        "ia_arranque_a": ia_arranque_a,
        "metodo": metodo,
        "guardamotor": guardamotor,
    }
