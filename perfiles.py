# ============================================================
# perfiles.py
# Responsabilidad: definición de perfiles y validación
# Razón para cambiar: agregar perfil o ajustar reglas
# ============================================================

import math

PERFILES = {
    "domestico": {
        "label":            "Doméstico",
        "descripcion":      "Viviendas — 220V monofásico / empalme SEC",
        "tension":          220,
        "sistema":          "1F",
        "cos_phi":          0.95,
        "conductor":        "12AWG",
        "norma":            "MM2",
        "Icc_kA":           6.0,
        "curva":            "C",
        "temp_amb":         30,
        "limite_dv":        3.0,
        "requiere_trafo":   False,
        "requiere_balance": False,
        "requiere_prot":    False,
        "entrada_watts":    True,
        "icc_referencia":   "Empalme SEC — 6 kA zona urbana (tabla SEC)",
        "cargas_tipicas": {
            "iluminacion":  200,
            "enchufe":      1500,
            "cocina":       5000,
            "lavadora":     2000,
            "calefon":      3000,
            "aire_acond":   2500,
        },
    },
    "comercial": {
        "label":            "Comercial",
        "descripcion":      "Oficinas, locales, edificios — 380V trifásico",
        "tension":          380,
        "sistema":          "3F",
        "cos_phi":          0.90,
        "conductor":        "10AWG",
        "norma":            "MM2",
        "Icc_kA":           None,
        "curva":            "C",
        "temp_amb":         30,
        "limite_dv":        3.0,
        "requiere_trafo":   False,
        "requiere_balance": True,
        "requiere_prot":    True,
        "entrada_watts":    False,
        "icc_referencia":   "Calcular desde transformador (Modo B si no hay datos)",
        "cargas_tipicas":   {},
    },
    "industrial": {
        "label":            "Industrial / Telecom",
        "descripcion":      "Plantas, datacenters, telecom — datos completos",
        "tension":          380,
        "sistema":          "3F",
        "cos_phi":          0.85,
        "conductor":        "6AWG",
        "norma":            "AWG",
        "Icc_kA":           None,
        "curva":            "C",
        "temp_amb":         30,
        "limite_dv":        3.0,
        "requiere_trafo":   True,
        "requiere_balance": True,
        "requiere_prot":    True,
        "entrada_watts":    False,
        "icc_referencia":   "Datos de placa del transformador obligatorios",
        "cargas_tipicas":   {},
    },
}

PERFIL_DEFAULT = "industrial"


def obtener_perfil(nombre):
    return PERFILES.get(nombre, PERFILES[PERFIL_DEFAULT])


def lista_perfiles():
    return [(k, v["label"]) for k, v in PERFILES.items()]


def convertir_watts_a_amperes(watts, cos_phi, sistema, tension):
    if watts <= 0 or cos_phi <= 0:
        return 0.0
    if sistema == "3F":
        I = watts / (math.sqrt(3) * tension * cos_phi)
    else:
        I = watts / (tension * cos_phi)
    return round(I, 2)


def icc_empalme_sec(zona="urbana"):
    tabla = {
        "urbana":    6.0,
        "suburbana": 4.0,
        "rural":     2.0,
    }
    return tabla.get(zona, 6.0)


# ============================================================
# VALIDACIÓN DE PERFIL VS DATOS
# ============================================================

# Niveles de validación
NIVEL_OK        = "ok"
NIVEL_ADVERTENCIA = "advertencia"
NIVEL_BLOQUEO   = "bloqueo"


def validar_perfil_vs_datos(perfil_clave, circuitos, datos_trafo,
                             protecciones, balance_datos, tableros_datos):
    """
    Valida que los datos cargados son coherentes con el perfil.

    Retorna lista de (nivel, mensaje) ordenada por severidad.
    Si hay algún BLOQUEO → no se puede calcular.
    Si hay ADVERTENCIAS → puede continuar con aviso.
    """
    resultados = []
    perfil = obtener_perfil(perfil_clave)

    # --- VALIDACIONES COMUNES ---

    # Sin circuitos — bloqueo en todos los perfiles
    if not circuitos:
        resultados.append((NIVEL_BLOQUEO,
            "No se encontraron circuitos válidos en la hoja 'circuitos'"))
        return resultados   # no tiene sentido seguir validando

    # --- VALIDACIONES POR PERFIL ---

    if perfil_clave == "domestico":

        # Circuitos 3F en perfil doméstico — bloqueo
        circ_3F = [c["nombre"] for c in circuitos if c["sistema"] == "3F"]
        if circ_3F:
            nombres = ", ".join(circ_3F[:3])
            if len(circ_3F) > 3:
                nombres += f" (+{len(circ_3F)-3} más)"
            resultados.append((NIVEL_BLOQUEO,
                f"Perfil Doméstico no admite circuitos 3F.\n"
                f"Circuitos afectados: {nombres}\n"
                f"Cambia a perfil Comercial o Industrial."))

        # Transformador cargado — advertencia
        if datos_trafo:
            resultados.append((NIVEL_ADVERTENCIA,
                "Se encontró hoja 'Transformador' pero el perfil\n"
                "Doméstico usa Icc de empalme SEC (6 kA).\n"
                "Los datos del transformador serán ignorados."))

        # Balance cargado — advertencia
        if balance_datos:
            resultados.append((NIVEL_ADVERTENCIA,
                "Se encontró hoja 'balance' pero el perfil\n"
                "Doméstico no calcula balance de fases.\n"
                "Los datos de balance serán ignorados."))

    elif perfil_clave == "comercial":

        # Sin transformador — advertencia (Modo B)
        if not datos_trafo:
            resultados.append((NIVEL_ADVERTENCIA,
                "No se encontró hoja 'Transformador'.\n"
                "Se usará Modo B (tabla típica IEC 60076).\n"
                "Para mayor precisión, agrega datos de placa."))

        # Sin protecciones — advertencia
        if not protecciones:
            resultados.append((NIVEL_ADVERTENCIA,
                "No se encontró hoja 'Protecciones'.\n"
                "Se omitirá la verificación de protecciones."))

        # Sin balance — advertencia
        if not balance_datos or not tableros_datos:
            resultados.append((NIVEL_ADVERTENCIA,
                "No se encontraron hojas 'balance' y/o 'tableros'.\n"
                "Se omitirá el balance de carga."))

        # Circuitos 1F en perfil comercial — advertencia
        circ_1F = [c["nombre"] for c in circuitos
                   if c["sistema"] in ("1F", "2F")]
        if circ_1F:
            resultados.append((NIVEL_ADVERTENCIA,
                f"Se encontraron {len(circ_1F)} circuito(s) monofásicos.\n"
                f"El perfil Comercial es principalmente trifásico.\n"
                f"Verifica que la asignación de fases es correcta."))

    elif perfil_clave == "industrial":

        # Sin transformador — bloqueo
        if not datos_trafo:
            resultados.append((NIVEL_BLOQUEO,
                "El perfil Industrial requiere datos del transformador.\n"
                "Agrega la hoja 'Transformador' al Excel con:\n"
                "kVA, Vn_BT, Ucc% y modo=A."))

        # Sin protecciones — advertencia
        if not protecciones:
            resultados.append((NIVEL_ADVERTENCIA,
                "No se encontró hoja 'Protecciones'.\n"
                "Se omitirá la verificación de protecciones."))

        # Sin balance — advertencia
        if not balance_datos or not tableros_datos:
            resultados.append((NIVEL_ADVERTENCIA,
                "No se encontraron hojas 'balance' y/o 'tableros'.\n"
                "Se omitirá el balance de carga."))

    # Si no hay problemas, agregar OK general
    if not resultados:
        resultados.append((NIVEL_OK,
            f"Datos coherentes con perfil {perfil['label']}.\n"
            f"{len(circuitos)} circuitos listos para calcular."))

    return resultados


def hay_bloqueo(resultados_validacion):
    """Retorna True si alguna validación tiene nivel BLOQUEO."""
    return any(nivel == NIVEL_BLOQUEO for nivel, _ in resultados_validacion)
