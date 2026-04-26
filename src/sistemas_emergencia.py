"""
Modulo M9 - Sistemas de emergencia segun RIC-N08.
Clasificacion de grupo, autonomia requerida y
dimensionamiento de grupo electrogeno.
"""
import math


# Tabla de grupos segun RIC-N08 7.1
GRUPOS = {
    0: {
        "descripcion": "Interrupcion tolerable <= 15 minutos",
        "tiempo_max_interrupcion_seg": 900,
    },
    1: {
        "descripcion": "Interrupcion tolerable <= 15 segundos",
        "tiempo_max_interrupcion_seg": 15,
    },
    2: {
        "descripcion": "Sin interrupcion tolerable",
        "tiempo_max_interrupcion_seg": 0,
    },
}


# Tipos de consumo y su grupo RIC-N08 6.3 y 8.11.2
CONSUMOS_GRUPO = {
    "iluminacion_evacuacion": 0,
    "iluminacion_antipanico": 0,
    "alarma_incendio": 1,
    "bomba_incendio": 1,
    "extraccion_humos": 1,
    "ascensor_rescate": 1,
    "ups_servidores": 2,
    "sala_cirugia": 2,
    "sistemas_medicos": 2,
    "centro_datos": 2,
}


RECINTOS_120_MIN = {"asistencial", "educacional", "cine_teatro", "mall", "aeropuerto"}


def clasificar_grupo(tipo_consumo: str) -> dict:
    """
    Clasifica el grupo de emergencia segun tipo de consumo.
    RIC-N08 7.1 y 6.3.
    Parametros:
        tipo_consumo: clave de CONSUMOS_GRUPO
    Retorna grupo, descripcion y tiempo maximo de interrupcion.
    Raise ValueError si tipo_consumo no esta en tabla.
    """
    clave = _normalizar_clave(tipo_consumo)
    if clave not in CONSUMOS_GRUPO:
        raise ValueError(f"Tipo de consumo no reconocido: {tipo_consumo}")

    grupo = CONSUMOS_GRUPO[clave]
    return {
        "grupo": grupo,
        "descripcion": GRUPOS[grupo]["descripcion"],
        "tiempo_max_interrupcion_seg": GRUPOS[grupo]["tiempo_max_interrupcion_seg"],
    }


def autonomia_requerida(grupo: int, num_pisos: int = 1, tipo_recinto: str = "general") -> dict:
    """
    Calcula autonomia requerida segun grupo, pisos y tipo de recinto.
    RIC-N08 8.7.1.c y 8.10.2.

    Reglas:
        Grupo 0:
            <=5 pisos, general      -> 60 min
            >5 pisos                -> 120 min
            asistencial/educacional -> 120 min
        Grupo 1:
            autonomia minima        -> 120 min
        Grupo 2:
            autonomia               -> -1, hasta entrada de generador

    Retorna autonomia_min, fuente_recomendada y articulo_ric.
    Raise ValueError si grupo no es 0, 1 o 2.
    """
    if grupo not in GRUPOS:
        raise ValueError("El grupo debe ser 0, 1 o 2")
    if num_pisos <= 0:
        raise ValueError("El numero de pisos debe ser mayor que cero")

    recinto = _normalizar_clave(tipo_recinto)
    if grupo == 0:
        autonomia_min = 120 if num_pisos > 5 or recinto in RECINTOS_120_MIN else 60
        return {
            "autonomia_min": autonomia_min,
            "fuente_recomendada": "baterias",
            "articulo_ric": "RIC-N08 8.7.1.c",
        }
    if grupo == 1:
        return {
            "autonomia_min": 120,
            "fuente_recomendada": "generador",
            "articulo_ric": "RIC-N08 8.8.2",
        }
    return {
        "autonomia_min": -1,
        "fuente_recomendada": "ups",
        "articulo_ric": "RIC-N08 8.11",
    }


def potencia_generador(cargas_kw: list[float], fp: float = 0.8, margen_pct: float = 25.0) -> dict:
    """
    Calcula potencia minima requerida para grupo electrogeno.
    RIC-N08 8.8.3: debe soportar todas las cargas conectadas.

    Formula:
        P_total = suma(cargas_kw)
        P_con_margen = P_total x (1 + margen_pct/100)
        S_kva = P_con_margen / fp
    Retorna p_total_kw, p_con_margen_kw, s_requerido_kva y margen_pct.
    Raise ValueError si lista vacia, fp fuera de (0,1], margen < 0.
    """
    if not cargas_kw:
        raise ValueError("La lista de cargas no puede estar vacia")
    if not 0 < fp <= 1:
        raise ValueError("El factor de potencia debe estar en rango (0, 1]")
    if margen_pct < 0:
        raise ValueError("El margen no puede ser negativo")

    cargas = [float(carga) for carga in cargas_kw]
    if any(carga < 0 for carga in cargas):
        raise ValueError("Las cargas no pueden ser negativas")

    p_total = math.fsum(cargas)
    p_con_margen = p_total * (1 + margen_pct / 100.0)
    s_kva = p_con_margen / fp
    return {
        "p_total_kw": round(p_total, 2),
        "p_con_margen_kw": round(p_con_margen, 2),
        "s_requerido_kva": round(s_kva, 2),
        "margen_pct": float(margen_pct),
    }


def calcular_emergencia_completo(
    tipo_consumo: str,
    num_pisos: int,
    cargas_kw: list[float],
    tipo_recinto: str = "general",
    fp: float = 0.8,
    margen_pct: float = 25.0,
) -> dict:
    """
    Orquestador: clasifica grupo, determina autonomia y dimensiona generador.
    Retorna dict con claves grupo, autonomia y generador.
    """
    grupo = clasificar_grupo(tipo_consumo)
    autonomia = autonomia_requerida(grupo["grupo"], num_pisos, tipo_recinto)
    generador = potencia_generador(cargas_kw, fp, margen_pct)
    return {
        "grupo": grupo,
        "autonomia": autonomia,
        "generador": generador,
    }


def _normalizar_clave(valor: str) -> str:
    """Normaliza claves de consumo y recinto para busqueda estable."""
    return str(valor or "").strip().lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
