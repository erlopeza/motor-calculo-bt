# ============================================================
# protecciones.py
# Responsabilidad: verificación de protecciones eléctricas
# Normativa: IEC 60898 (doméstico) / IEC 60947-2 (industrial)
#            IEC 60364-4-41 (protección contra choque eléctrico)
# Razón para cambiar: actualización de criterios o curvas
# Referencia: SIMARIS Design — proyecto ENERQUIMICA Rev02
# ============================================================

# --- FACTORES DE DISPARO MAGNÉTICO POR CURVA ---
# Umbral mínimo y máximo según IEC 60898 / IEC 60947-2
# Se usa el mínimo para verificar el peor caso (conservador)

CURVAS_DISPARO = {
    "B":   {"Im_min": 3,  "Im_max": 5,  "uso": "cables largos, resistivas puras"},
    "C":   {"Im_min": 5,  "Im_max": 10, "uso": "uso general, iluminacion, enchufes"},
    "D":   {"Im_min": 10, "Im_max": 20, "uso": "motores, transformadores, arranques"},
    "K":   {"Im_min": 8,  "Im_max": 12, "uso": "motores industriales"},
    "TM":  {"Im_min": 6,  "Im_max": 10, "uso": "MCCB termomagnético — motores medianos"},
    "ETU": {"Im_min": 4,  "Im_max": 10, "uso": "disparador electrónico — ajustable"},
}

# --- TIEMPO MÁXIMO DE DESCONEXIÓN — IEC 60364-4-41 ---
# Protección contra choque eléctrico en sistema TN
# Voltaje de contacto tolerable: 50V
# Depende de la tensión de fase del sistema

TIEMPO_MAX_DESCONEXION = {
    # Vn (V) : ta_max (s)
    220: 0.4,   # circuitos finales 1F ≤ 32A
    230: 0.4,   # circuitos finales 1F ≤ 32A (IEC nominal)
    380: 5.0,   # circuitos de distribución 3F
    400: 5.0,   # circuitos de distribución 3F (IEC nominal)
}

def calcular_umbral_magnetico(In_A, curva):
    """
    Calcula el umbral de disparo magnético mínimo y máximo.
    Usa el mínimo para verificación conservadora (peor caso).

    Parámetros:
        In_A  : corriente nominal del disyuntor en Amperios
        curva : "B", "C", "D", "K", "TM" o "ETU"

    Retorna:
        Im_min : umbral mínimo de disparo en A
        Im_max : umbral máximo de disparo en A
    """
    datos = CURVAS_DISPARO.get(curva.upper())
    if not datos:
        return None, None
    Im_min = round(In_A * datos["Im_min"], 1)
    Im_max = round(In_A * datos["Im_max"], 1)
    return Im_min, Im_max

def verificar_disparo(Icc_punto_A, In_A, curva):
    """
    Verifica si la Icc disponible en el punto garantiza
    el disparo magnético del disyuntor.

    Criterio IEC 60898: Icc_punto ≥ Im_mínimo (peor caso)

    Retorna:
        puede_disparar : True / False
        margen_pct     : margen sobre el umbral en %
        Im_min         : umbral mínimo de disparo en A
    """
    Im_min, Im_max = calcular_umbral_magnetico(In_A, curva)
    if Im_min is None:
        return None, None, None

    puede_disparar = Icc_punto_A >= Im_min
    margen_pct     = round(((Icc_punto_A / Im_min) - 1) * 100, 1)
    return puede_disparar, margen_pct, Im_min

def verificar_poder_de_corte(Icc_punto_kA, poder_de_corte_kA):
    """
    Verifica si el poder de corte es suficiente.
    Criterio IEC 60947-2: Icu ≥ Icc_punto

    Retorna:
        es_suficiente : True / False
        margen_kA     : margen en kA
    """
    es_suficiente = poder_de_corte_kA >= Icc_punto_kA
    margen_kA     = round(poder_de_corte_kA - Icc_punto_kA, 2)
    return es_suficiente, margen_kA

def clasificar_margen_disparo(margen_pct):
    """
    Clasifica el margen de disparo.
    Margen bajo puede ser problemático con variaciones de red.
    Criterio basado en práctica SIMARIS — c_min=0.9 reduce Icc 10%.
    """
    if margen_pct < 0:
        return "NO DISPARA — cambiar curva o aumentar sección"
    elif margen_pct < 10:
        return "MARGEN CRÍTICO — Icc mínima puede no disparar"
    elif margen_pct < 50:
        return "MARGEN ACEPTABLE"
    else:
        return "MARGEN AMPLIO"

def verificar_tiempo_desconexion(Icc_punto_A, In_A, curva, Vn):
    """
    Verifica el tiempo de desconexión para protección
    contra choque eléctrico según IEC 60364-4-41.

    El tiempo de desconexión real depende de la curva y la
    relación Icc / In. A mayor relación → menor tiempo.

    Retorna:
        cumple     : True / False
        ta_req     : tiempo máximo requerido en s
        relacion   : Icc_punto / In (múltiplo de In)
    """
    ta_req   = TIEMPO_MAX_DESCONEXION.get(Vn, 5.0)
    relacion = round(Icc_punto_A / In_A, 1)

    # Estimación conservadora del tiempo de disparo
    # basada en los múltiplos de la curva
    Im_min, Im_max = calcular_umbral_magnetico(In_A, curva)

    if Im_min and Icc_punto_A >= Im_min:
        # Disparo magnético garantizado — tiempo < 0.1s
        cumple = True
    else:
        # Solo disparo térmico — tiempo puede superar ta_req
        cumple = False

    return cumple, ta_req, relacion

def verificar_circuito_completo(nombre, In_A, curva, poder_corte_kA,
                                 Icc_punto_kA, Vn=380):
    """
    Verificación completa de una protección.
    Integra IEC 60898, IEC 60947-2 e IEC 60364-4-41.
    Retorna diccionario con todos los resultados.
    """
    Icc_punto_A = Icc_punto_kA * 1000

    # 1. Verificar disparo magnético
    puede_disparar, margen_pct, Im_min = verificar_disparo(
        Icc_punto_A, In_A, curva
    )

    # 2. Verificar poder de corte
    es_suficiente, margen_kA = verificar_poder_de_corte(
        Icc_punto_kA, poder_corte_kA
    )

    # 3. Verificar tiempo de desconexión IEC 60364-4-41
    cumple_tiempo, ta_req, relacion = verificar_tiempo_desconexion(
        Icc_punto_A, In_A, curva, Vn
    )

    # 4. Estado general — orden de prioridad
    if not puede_disparar:
        estado = "FALLA DISPARO — protección no garantizada"
    elif not es_suficiente:
        estado = "FALLA PODER CORTE — riesgo de destrucción"
    elif not cumple_tiempo:
        estado = "PRECAUCIÓN — tiempo desconexión excede IEC 60364-4-41"
    elif margen_pct < 10:
        estado = "PRECAUCIÓN — margen de disparo crítico"
    else:
        estado = "OK"

    return {
        "nombre":          nombre,
        "In_A":            In_A,
        "curva":           curva,
        "poder_corte_kA":  poder_corte_kA,
        "Icc_punto_kA":    Icc_punto_kA,
        "Icc_punto_A":     round(Icc_punto_A, 1),
        "Im_min_A":        Im_min,
        "puede_disparar":  puede_disparar,
        "margen_pct":      margen_pct,
        "clasif_margen":   clasificar_margen_disparo(margen_pct),
        "poder_ok":        es_suficiente,
        "margen_kA":       margen_kA,
        "cumple_tiempo":   cumple_tiempo,
        "ta_req":          ta_req,
        "relacion_Icc_In": relacion,
        "estado":          estado,
    }


def leer_protecciones_excel(libro_openpyxl):
    """
    Lee la hoja 'protecciones' del libro Excel ya abierto.
    Estructura: nombre | curva | In_A | poder_corte_kA

    Retorna diccionario indexado por nombre de circuito.
    Si la hoja no existe retorna diccionario vacío.
    """
    protecciones = {}

    # Buscar hoja — insensible a mayúsculas
    hoja_nombre = None
    for nombre in libro_openpyxl.sheetnames:
        if nombre.lower() == "protecciones":
            hoja_nombre = nombre
            break

    if not hoja_nombre:
        return protecciones

    hoja = libro_openpyxl[hoja_nombre]

    for fila in hoja.iter_rows(min_row=2, values_only=True):
        if not fila[0]:
            continue
        nombre        = str(fila[0]).strip()
        curva         = str(fila[1]).strip().upper() if fila[1] else "C"
        In_A          = float(fila[2]) if fila[2] else None
        poder_corte   = float(fila[3]) if fila[3] else None

        if In_A and poder_corte:
            protecciones[nombre] = {
                "curva":          curva,
                "In_A":           In_A,
                "poder_corte_kA": poder_corte,
            }

    return protecciones