"""
Modulo M8 - Arranque de motores electricos trifasicos BT.
Calculo de corriente nominal, corriente de arranque,
metodo de arranque y seleccion de guardamotor.
"""
import math


RANGOS_GUARDAMOTOR = [
    (0.1, 0.16),
    (0.16, 0.25),
    (0.25, 0.4),
    (0.4, 0.63),
    (0.63, 1.0),
    (1.0, 1.6),
    (1.6, 2.5),
    (2.5, 4.0),
    (4.0, 6.3),
    (6.3, 10.0),
    (10.0, 16.0),
    (16.0, 25.0),
    (25.0, 40.0),
    (40.0, 63.0),
]


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

    potencia_w = potencia_kw * 1000.0
    in_a = potencia_w / (math.sqrt(3.0) * tension_v * fp * rendimiento)
    return round(in_a, 2)


def corriente_arranque(in_a: float, factor_ia: float = 6.0) -> float:
    """
    Corriente de arranque directo (DOL).
    Ia = In x factor_ia (factor tipico 5-7, default 6).
    Raise ValueError si in_a <= 0 o factor_ia <= 0.
    """
    if in_a <= 0:
        raise ValueError("La corriente nominal debe ser mayor que cero")
    if factor_ia <= 0:
        raise ValueError("El factor de arranque debe ser mayor que cero")
    return round(in_a * factor_ia, 2)


def metodo_arranque(potencia_kw: float, tension_v: float = 380) -> dict:
    """
    Recomienda metodo de arranque segun potencia.
    Criterios BT Chile:
        <= 7.5 kW      -> DOL (directo), reduccion_corriente_pct = 0
        7.5 < P <= 30  -> Estrella-Triangulo, reduccion_corriente_pct = 33
        > 30 kW        -> Variador de frecuencia, reduccion_corriente_pct = 70
    Retorna metodo, justificacion y reduccion de corriente.
    """
    if potencia_kw <= 0:
        raise ValueError("La potencia debe ser mayor que cero")
    if tension_v <= 0:
        raise ValueError("La tension debe ser mayor que cero")

    if potencia_kw <= 7.5:
        return {
            "metodo": "DOL",
            "justificacion": "Motor pequeno BT; arranque directo admisible segun criterio de potencia",
            "reduccion_corriente_pct": 0.0,
        }
    if potencia_kw <= 30:
        return {
            "metodo": "Estrella-Triangulo",
            "justificacion": "Potencia media BT; se recomienda reducir corriente de partida",
            "reduccion_corriente_pct": 33.0,
        }
    return {
        "metodo": "Variador de frecuencia",
        "justificacion": "Potencia alta BT; se recomienda rampa controlada con VFD",
        "reduccion_corriente_pct": 70.0,
    }


def seleccionar_guardamotor(in_a: float) -> dict:
    """
    Selecciona rango de guardamotor segun In.
    Retorna rango_min, rango_max y ajuste_recomendado.
    Raise ValueError si in_a <= 0 o queda fuera de tabla.
    """
    if in_a <= 0:
        raise ValueError("La corriente nominal debe ser mayor que cero")

    for rango_min, rango_max in RANGOS_GUARDAMOTOR:
        if rango_min <= in_a <= rango_max:
            return {
                "rango_min": rango_min,
                "rango_max": rango_max,
                "ajuste_recomendado": round(in_a, 2),
            }

    raise ValueError("Corriente fuera de tabla de guardamotores")


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
