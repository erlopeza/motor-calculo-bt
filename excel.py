# ============================================================
# excel.py
# Responsabilidad: lectura de entrada y exportación de reportes
# Razón para cambiar: modificar formato o estructura de archivos
# ============================================================

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.exceptions import InvalidFileException
from conductores import CONDUCTORES, FACTOR_SISTEMA, TENSION_SISTEMA, LIMITE_DV, FACTORES_TEMP
from calculos import (
    capacidad_corregida, calcular_potencia,
    calcular_caida_tension, clasificar_caida, sugerir_conductor
)

def leer_circuitos_excel(nombre_archivo):
    """
    Lee circuitos desde Excel con manejo de errores por tipo.
    Cada tipo de error da un mensaje específico y útil.
    """
    circuitos = []
    errores   = []

    # --- NIVEL 1: verificar que el archivo existe y es válido ---
    try:
        libro = openpyxl.load_workbook(nombre_archivo, data_only=True)
    except FileNotFoundError:
        # El archivo no existe en la carpeta
        raise FileNotFoundError(
            f"No se encontró '{nombre_archivo}'.\n"
            f"Verifica que el archivo está en la misma carpeta que el programa."
        )
    except openpyxl.utils.exceptions.InvalidFileException:
        # El archivo no es un Excel válido o está corrupto
        raise ValueError(
            f"'{nombre_archivo}' no es un archivo Excel válido.\n"
            f"Verifica que el archivo tiene extensión .xlsx y no está dañado."
        )
    except PermissionError:
        # El archivo está abierto en Excel u otro programa
        raise PermissionError(
            f"No se puede leer '{nombre_archivo}'.\n"
            f"Cierra el archivo en Excel antes de ejecutar el programa."
        )

    hoja = libro.active

    print(f"\n  Leyendo: {nombre_archivo}")
    print(f"  Circuitos encontrados: {hoja.max_row - 1}")

    # --- NIVEL 2: verificar cada fila de datos ---
    for num_fila, fila in enumerate(
        hoja.iter_rows(min_row=2, values_only=True), start=2
    ):
        nombre    = fila[0]
        sistema   = fila[1]
        conductor = fila[2]
        paralelos = fila[3]
        I_diseno  = fila[4]
        cos_phi   = fila[5]
        L_m       = fila[6]
        temp_amb  = fila[7]

        # Saltar filas vacías
        if nombre is None:
            continue

        sistema   = str(sistema).strip().upper()
        conductor = str(conductor).strip().upper()

        # Validar sistema
        if sistema not in FACTOR_SISTEMA:
            errores.append(
                f"Fila {num_fila} '{nombre}': "
                f"sistema '{sistema}' inválido — usar 1F, 2F o 3F"
            )
            continue

        # Validar conductor
        if conductor not in CONDUCTORES:
            errores.append(
                f"Fila {num_fila} '{nombre}': "
                f"conductor '{conductor}' no existe en tabla"
            )
            continue

        # Validar que los valores numéricos sean números
        try:
            paralelos = int(paralelos)
            I_diseno  = float(I_diseno)
            cos_phi   = float(cos_phi)
            L_m       = float(L_m)
            temp_amb  = float(temp_amb)
        except (TypeError, ValueError):
            errores.append(
                f"Fila {num_fila} '{nombre}': "
                f"valor no numérico en columnas D-H — "
                f"verifica que no hay texto donde debe ir un número"
            )
            continue

        # Validar rangos lógicos
        if I_diseno <= 0:
            errores.append(
                f"Fila {num_fila} '{nombre}': "
                f"corriente debe ser mayor a 0A"
            )
            continue

        if not 0 < cos_phi <= 1:
            errores.append(
                f"Fila {num_fila} '{nombre}': "
                f"factor de potencia debe estar entre 0 y 1"
            )
            continue

        if L_m <= 0:
            errores.append(
                f"Fila {num_fila} '{nombre}': "
                f"longitud debe ser mayor a 0 metros"
            )
            continue

        if int(temp_amb) not in FACTORES_TEMP:
            errores.append(
                f"Fila {num_fila} '{nombre}': "
                f"temperatura {temp_amb}°C no está en tabla — "
                f"usar 25, 30, 35, 40, 45 o 50"
            )
            continue

        circuitos.append({
            "nombre":    str(nombre).strip(),
            "sistema":   sistema,
            "conductor": conductor,
            "S_mm2":     CONDUCTORES[conductor]["mm2"],
            "I_max":     CONDUCTORES[conductor]["I_max"],
            "paralelos": paralelos,
            "I_diseno":  I_diseno,
            "cos_phi":   cos_phi,
            "L_m":       L_m,
            "temp_amb":  temp_amb,
        })

    # Mostrar advertencias sin detener el programa
    if errores:
        print(f"\n  ADVERTENCIAS ({len(errores)} filas con problemas):")
        for e in errores:
            print(f"  ⚠ {e}")

    return circuitos

def guardar_txt(lineas, nombre_archivo):
    """Guarda lista de líneas en archivo .txt"""
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        for linea in lineas:
            f.write(linea + "\n")
    print(f"  TXT guardado : {nombre_archivo}")

def exportar_excel(nombre_proyecto, circuitos, fecha, nombre_archivo):
    """
    Exporta resultados a Excel con formato profesional.
    Colores por estado: verde ÓPTIMO, amarillo ACEPTABLE,
    naranja PRECAUCIÓN, rojo FALLA.
    """
    COLORES = {
        "ÓPTIMO":     "FF92D050",
        "ACEPTABLE":  "FFFFFF00",
        "PRECAUCIÓN": "FFFFC000",
        "FALLA":      "FFFF0000",
        "SUPERA":     "FFFF0000",
    }

    borde = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"),  bottom=Side(style="thin")
    )

    libro = openpyxl.Workbook()
    hoja  = libro.active
    hoja.title = "Resultados"

    # Título
    hoja.merge_cells("A1:L1")
    hoja["A1"] = f"REPORTE BT — {nombre_proyecto}"
    hoja["A1"].font      = Font(bold=True, size=13, color="FFFFFFFF")
    hoja["A1"].alignment = Alignment(horizontal="center")
    hoja["A1"].fill      = PatternFill("solid", fgColor="FF1F3864")

    # Info
    hoja.merge_cells("A2:L2")
    hoja["A2"] = f"Fecha: {fecha}  |  Normativa: SEC RIC N°10 / NEC / IEC 60364  |  Límite ΔV: {LIMITE_DV}%"
    hoja["A2"].alignment = Alignment(horizontal="center")
    hoja["A2"].fill      = PatternFill("solid", fgColor="FFD6E4F7")

    # Encabezados
    encabezados = [
        "Circuito", "Sistema", "Conductor", "Paralelos",
        "I_diseño(A)", "I_cap(A)", "Estado_I",
        "Potencia(W)", "ΔV(V)", "ΔV(%)", "Estado_dV", "Sugerencia"
    ]

    for col, texto in enumerate(encabezados, start=1):
        celda = hoja.cell(row=3, column=col, value=texto)
        celda.font      = Font(bold=True, color="FFFFFFFF")
        celda.fill      = PatternFill("solid", fgColor="FF2E75B6")
        celda.alignment = Alignment(horizontal="center")
        celda.border    = borde

    # Datos
    for i, c in enumerate(circuitos):
        fila_num = 4 + i

        I_cap        = capacidad_corregida(c["I_max"], c["paralelos"], c["temp_amb"])
        P_watts      = calcular_potencia(c["I_diseno"], c["cos_phi"], c["sistema"])
        dV_V, dV_pct = calcular_caida_tension(
            c["L_m"], c["S_mm2"], c["I_diseno"], c["paralelos"], c["sistema"]
        )
        estado_dV = clasificar_caida(dV_pct)
        estado_I  = "OK" if c["I_diseno"] <= I_cap else "SUPERA"

        sugerencia = ""
        if estado_dV == "FALLA" or estado_I == "SUPERA":
            cond, mm2, dv = sugerir_conductor(
                c["L_m"], c["I_diseno"], c["paralelos"],
                c["sistema"], c["temp_amb"]
            )
            if cond:
                sugerencia = f"→ Usar {cond} ({dv}%)"

        desc_cond = f"{c['paralelos']}x{c['conductor']}" if c["paralelos"] > 1 else c["conductor"]

        valores = [
            c["nombre"], c["sistema"], desc_cond, c["paralelos"],
            c["I_diseno"], I_cap, estado_I,
            P_watts, dV_V, dV_pct, estado_dV, sugerencia
        ]

        for col, valor in enumerate(valores, start=1):
            celda = hoja.cell(row=fila_num, column=col, value=valor)
            celda.border    = borde
            celda.alignment = Alignment(horizontal="center")

        hoja.cell(row=fila_num, column=7).fill  = PatternFill("solid", fgColor=COLORES.get(estado_I,  "FFFFFFFF"))
        hoja.cell(row=fila_num, column=11).fill = PatternFill("solid", fgColor=COLORES.get(estado_dV, "FFFFFFFF"))

        if sugerencia:
            hoja.cell(row=fila_num, column=12).font = Font(bold=True, color="FFFF0000")

    # Anchos de columna
    anchos = [28, 8, 14, 10, 12, 10, 10, 12, 8, 8, 12, 22]
    for col, ancho in enumerate(anchos, start=1):
        hoja.column_dimensions[openpyxl.utils.get_column_letter(col)].width = ancho

    libro.save(nombre_archivo)
    print(f"  Excel guardado: {nombre_archivo}")