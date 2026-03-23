# ============================================================
# balance.py
# Responsabilidad: balance de carga por tablero y por fase
# Normativa: IEC 60364 / SEC RIC N°10
# Razón para cambiar: nuevos tipos de carga o factores
# ============================================================

# --- FACTORES DE SIMULTANEIDAD POR TIPO DE CARGA ---
# Fuente: práctica ingeniería eléctrica industrial
# El usuario puede usar hvac o critica para cargas 24/7

FACTORES_SIMULTANEIDAD = {
    "critica":       1.00,   # UPS, CRAC, servidores — siempre activos
    "hvac":          1.00,   # CRAC / climatización crítica — 24/7
    "iluminacion":   1.00,   # luminarias — siempre encendidas
    "motor":         0.75,   # bombas, compresores — arranques escalonados
    "tomacorriente": 0.50,   # enchufes de uso general
}

# Umbral de alerta del transformador
ALERTA_USO_TRAFO = 80.0   # % — recomendación operacional


def obtener_fs(tipo_carga):
    """
    Retorna el factor de simultaneidad para un tipo de carga.
    Insensible a mayúsculas. Usa 'critica' como fallback.
    """
    tipo = str(tipo_carga).strip().lower()
    return FACTORES_SIMULTANEIDAD.get(tipo, 1.00)


def calcular_potencia_circuito(I_diseno, cos_phi, sistema, Vn_sistema):
    """
    Calcula potencia activa y aparente del circuito.
    Usa los mismos parámetros que la hoja circuitos.
    """
    if sistema == "3F":
        P_w  = round(1.732 * Vn_sistema * I_diseno * cos_phi)
        S_va = round(1.732 * Vn_sistema * I_diseno)
    else:
        P_w  = round(Vn_sistema * I_diseno * cos_phi)
        S_va = round(Vn_sistema * I_diseno)
    return P_w, S_va


def calcular_balance_tableros(circuitos, balance_datos, tableros_datos,
                               kVA_trafo, Vn_sistema=380):
    """
    Calcula el balance de carga por tablero y por fase.

    Parámetros:
        circuitos      : lista de circuitos (de leer_circuitos_excel)
        balance_datos  : dict {nombre: {tablero, fase, tipo_carga}}
        tableros_datos : dict {nombre_tablero: capacidad_kva}
        kVA_trafo      : potencia nominal del transformador en kVA
        Vn_sistema     : tensión de referencia para cálculo

    Retorna:
        resultado : dict con balance por tablero y resumen total
    """
    # Índice de circuitos por nombre
    circ_idx = {c["nombre"]: c for c in circuitos}

    # Acumuladores por tablero
    tableros = {}

    for nombre, bd in balance_datos.items():
        if nombre not in circ_idx:
            continue

        c          = circ_idx[nombre]
        tablero    = bd["tablero"]
        fase       = bd["fase"].upper()
        tipo_carga = bd["tipo_carga"]
        fs         = obtener_fs(tipo_carga)

        # Potencia del circuito
        from conductores import TENSION_SISTEMA
        Vn = TENSION_SISTEMA.get(c["sistema"], 380)
        P_w, S_va = calcular_potencia_circuito(
            c["I_diseno"], c["cos_phi"], c["sistema"], Vn
        )

        P_kw  = P_w  / 1000
        S_kva = S_va / 1000

        # Potencia demandada con factor de simultaneidad
        P_dem  = round(P_kw  * fs, 3)
        S_dem  = round(S_kva * fs, 3)

        # Inicializar tablero si no existe
        if tablero not in tableros:
            tableros[tablero] = {
                "circuitos":    [],
                "P_total_kw":   0.0,
                "S_total_kva":  0.0,
                "fases": {
                    "L1": 0.0,
                    "L2": 0.0,
                    "L3": 0.0,
                },
                "capacidad_kva": tableros_datos.get(tablero, 0),
            }

        # Acumular al tablero
        tableros[tablero]["P_total_kw"]  = round(
            tableros[tablero]["P_total_kw"] + P_dem, 3
        )
        tableros[tablero]["S_total_kva"] = round(
            tableros[tablero]["S_total_kva"] + S_dem, 3
        )

        # Distribuir por fase
        if c["sistema"] == "3F":
            # Circuito trifásico — carga distribuida en L1/L2/L3
            P_por_fase = round(P_dem / 3, 3)
            for f in ["L1", "L2", "L3"]:
                tableros[tablero]["fases"][f] = round(
                    tableros[tablero]["fases"][f] + P_por_fase, 3
                )
        else:
            # Circuito monofásico — carga en la fase asignada
            if fase in tableros[tablero]["fases"]:
                tableros[tablero]["fases"][fase] = round(
                    tableros[tablero]["fases"][fase] + P_dem, 3
                )

        # Registrar circuito en el tablero
        tableros[tablero]["circuitos"].append({
            "nombre":     nombre,
            "tablero":    tablero,
            "fase":       fase,
            "tipo_carga": tipo_carga,
            "fs":         fs,
            "P_kw":       P_kw,
            "P_dem_kw":   P_dem,
            "S_kva":      S_kva,
            "S_dem_kva":  S_dem,
        })

    # Calcular métricas por tablero
    for nombre_t, t in tableros.items():
        cap = t["capacidad_kva"]

        # Porcentaje de uso
        t["uso_pct"] = round(
            (t["S_total_kva"] / cap * 100) if cap > 0 else 0, 1
        )

        # Estado del tablero
        if t["uso_pct"] > 100:
            t["estado"] = "FALLA — supera capacidad nominal"
        elif t["uso_pct"] > ALERTA_USO_TRAFO:
            t["estado"] = "PRECAUCIÓN — supera 80%"
        else:
            t["estado"] = "OK"

        # Desequilibrio de fases
        fases_kw = list(t["fases"].values())
        f_max    = max(fases_kw)
        f_min    = min(fases_kw)
        f_prom   = sum(fases_kw) / 3 if sum(fases_kw) > 0 else 1
        t["desequilibrio_pct"] = round(
            (f_max - f_min) / f_prom * 100, 1
        )

        # Estado del desequilibrio
        # IEC 60038: desequilibrio tolerable < 2% en sistemas TN
        # Práctica industrial: alerta > 10%, problema > 20%
        if t["desequilibrio_pct"] > 20:
            t["estado_fases"] = "DESEQUILIBRIO SEVERO — redistribuir cargas"
        elif t["desequilibrio_pct"] > 10:
            t["estado_fases"] = "DESEQUILIBRIO MODERADO — revisar distribución"
        else:
            t["estado_fases"] = "EQUILIBRADO"

    # Resumen total sobre transformador
    S_total_kva = sum(t["S_total_kva"] for t in tableros.values())
    uso_trafo   = round(S_total_kva / kVA_trafo * 100, 1) if kVA_trafo > 0 else 0

    if uso_trafo > 100:
        estado_trafo = "FALLA — transformador sobrecargado"
    elif uso_trafo > ALERTA_USO_TRAFO:
        estado_trafo = "PRECAUCIÓN — supera 80% del transformador"
    else:
        estado_trafo = "OK"

    resultado = {
        "tableros":      tableros,
        "S_total_kva":   round(S_total_kva, 2),
        "kVA_trafo":     kVA_trafo,
        "uso_trafo_pct": uso_trafo,
        "estado_trafo":  estado_trafo,
    }

    return resultado


def reporte_balance(resultado):
    """
    Genera líneas del reporte de balance.
    Retorna lista de strings.
    """
    lineas = []
    lineas.append("=" * 60)
    lineas.append("  BALANCE DE CARGA POR TABLERO")
    lineas.append("=" * 60)

    for nombre_t, t in resultado["tableros"].items():
        lineas.append("")
        lineas.append(f"  Tablero   : {nombre_t}")
        lineas.append(f"  Capacidad : {t['capacidad_kva']} kVA")
        lineas.append(f"  Demanda   : {t['S_total_kva']} kVA "
                      f"({t['P_total_kw']} kW)")
        lineas.append(f"  Uso       : {t['uso_pct']}% -> {t['estado']}")
        lineas.append(f"  Fases     : "
                      f"L1={t['fases']['L1']}kW  "
                      f"L2={t['fases']['L2']}kW  "
                      f"L3={t['fases']['L3']}kW")
        lineas.append(f"  Desequilib: {t['desequilibrio_pct']}% "
                      f"-> {t['estado_fases']}")

    lineas.append("")
    lineas.append("-" * 60)
    lineas.append(f"  Transformador : {resultado['kVA_trafo']} kVA")
    lineas.append(f"  Total demanda : {resultado['S_total_kva']} kVA")
    lineas.append(f"  Uso trafo     : {resultado['uso_trafo_pct']}% "
                  f"-> {resultado['estado_trafo']}")
    lineas.append("=" * 60)

    return lineas