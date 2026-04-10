# ============================================================
# gui.py
# Responsabilidad: interfaz gráfica — Motor de Cálculo BT
# Estructura: panel lateral + área de resultados con tabs
# Razón para cambiar: modificar layout o agregar tabs
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import openpyxl
import threading
import sys
import os

# --- IMPORTS DE MÓDULOS DEL PROYECTO ---
from conductores import CONDUCTORES, TENSION_SISTEMA, LIMITE_DV
from calculos import (
    capacidad_corregida, calcular_potencia,
    calcular_caida_tension, clasificar_caida, sugerir_conductor
)
from excel import (
    leer_circuitos_excel, leer_transformador_excel,
    leer_balance_excel, leer_tableros_excel,
    guardar_txt, exportar_excel
)
from transformador import calcular_icc_transformador, icc_desde_tabla, clasificar_icc
from icc_punto import calcular_icc_todos_circuitos
from protecciones import verificar_circuito_completo, leer_protecciones_excel
from balance import calcular_balance_tableros, obtener_fs
from demanda import (
    calcular_demanda, seleccionar_transformador,
    dimensionar_acometida_sec, reporte_demanda
)
from excel import leer_demanda_excel, leer_cadena_excel
from coordinacion import verificar_cadena, reporte_coordinacion
from perfiles import (PERFILES, PERFIL_DEFAULT, obtener_perfil, lista_perfiles,
    validar_perfil_vs_datos, hay_bloqueo, NIVEL_OK, NIVEL_ADVERTENCIA, NIVEL_BLOQUEO)
from datetime import datetime

# ============================================================
# COLORES Y ESTILOS — TEMA INDUSTRIAL
# ============================================================

COLORES = {
    "fondo":        "#1E1E2E",   # fondo principal
    "panel":        "#2A2A3E",   # panel lateral
    "tab_fondo":    "#252535",   # fondo tabs
    "encabezado":   "#3A3A5C",   # encabezado de tabla
    "fila_par":     "#1E1E2E",   # filas pares
    "fila_impar":   "#252535",   # filas impares
    "texto":        "#E0E0F0",   # texto principal
    "texto_gris":   "#8888AA",   # texto secundario
    "acento":       "#5E81F4",   # azul acento
    "ok":           "#4CAF50",   # verde OK
    "falla":        "#F44336",   # rojo FALLA
    "precaucion":   "#FF9800",   # naranja PRECAUCIÓN
    "optimo":       "#4CAF50",   # verde ÓPTIMO
    "aceptable":    "#FFC107",   # amarillo ACEPTABLE
    "boton":        "#5E81F4",   # botón principal
    "boton_hover":  "#7B9FF7",   # botón hover
    "borde":        "#3A3A5C",   # bordes
}

FUENTES = {
    "titulo":   ("Consolas", 11, "bold"),
    "subtitulo":("Consolas", 9, "bold"),
    "normal":   ("Consolas", 9),
    "pequeño":  ("Consolas", 8),
    "mono":     ("Courier New", 9),
}

# ============================================================
# AUTOTEST — verificar módulos antes de abrir ventana
# ============================================================

def ejecutar_autotest():
    """
    Verifica que todos los módulos críticos funcionan
    antes de abrir la interfaz.
    Retorna lista de (nombre, ok, mensaje).
    """
    from calculos import calcular_caida_tension
    from transformador import calcular_icc_transformador
    from icc_punto import calcular_zt_cable
    from protecciones import verificar_disparo
    from balance import obtener_fs

    tests = []

    # Test 1 — conductores
    try:
        assert len(CONDUCTORES) > 10
        tests.append(("conductores.py", True, f"{len(CONDUCTORES)} conductores cargados"))
    except Exception as e:
        tests.append(("conductores.py", False, str(e)))

    # Test 2 — caída de tensión
    try:
        dV_V, dV_pct = calcular_caida_tension(10, 13.3, 63, 1, "3F")
        assert dV_V == 1.436 and dV_pct == 0.378
        tests.append(("calculos.py", True, f"CRAC 1-A → {dV_V}V / {dV_pct}%"))
    except Exception as e:
        tests.append(("calculos.py", False, str(e)))

    # Test 3 — transformador
    try:
        Icc_kA, _, _ = calcular_icc_transformador(1000, 380, 5.0)
        assert 30.0 <= Icc_kA <= 31.0
        tests.append(("transformador.py", True, f"1000kVA → {Icc_kA} kA"))
    except Exception as e:
        tests.append(("transformador.py", False, str(e)))

    # Test 4 — impedancia cable
    try:
        Zt = calcular_zt_cable(10, 13.3, 1)
        assert Zt > 0
        tests.append(("icc_punto.py", True, f"6AWG 10m → {Zt} Ω"))
    except Exception as e:
        tests.append(("icc_punto.py", False, str(e)))

    # Test 5 — protecciones
    try:
        puede, margen, Im = verificar_disparo(10000, 63, "C")
        assert puede == True
        tests.append(("protecciones.py", True, f"C63A / 10kA → dispara OK"))
    except Exception as e:
        tests.append(("protecciones.py", False, str(e)))

    # Test 6 — balance
    try:
        fs = obtener_fs("critica")
        assert fs == 1.0
        tests.append(("balance.py", True, f"fs critica = {fs}"))
    except Exception as e:
        tests.append(("balance.py", False, str(e)))

    return tests

# ============================================================
# CLASE PRINCIPAL — VENTANA
# ============================================================

class MotorCalculoBT:

    def __init__(self, root):
        self.root = root
        self.root.title("Motor de Cálculo BT  v3.0")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 600)
        self.root.configure(bg=COLORES["fondo"])

        # Estado de la aplicación
        self.archivo_excel   = tk.StringVar(value="")
        self.nombre_proyecto = tk.StringVar(value="")
        self.estado_texto    = tk.StringVar(value="● Listo — carga un archivo Excel")
        self.var_perfil      = tk.StringVar(value=PERFIL_DEFAULT)
        self.perfil_activo   = obtener_perfil(PERFIL_DEFAULT)

        # Datos calculados
        self.circuitos        = []
        self.datos_trafo      = None
        self.protecciones     = {}
        self.balance_datos    = {}
        self.tableros_datos   = {}
        self.resultado_calc   = None
        self.params_demanda    = None
        self.resultado_demanda = None
        self.cadena_datos      = []
        self.resultados_m7     = {}

        # Contadores resumen
        self.var_circ_ok     = tk.StringVar(value="—")
        self.var_circ_falla  = tk.StringVar(value="—")
        self.var_icc         = tk.StringVar(value="—")
        self.var_trafo_uso   = tk.StringVar(value="—")
        self.var_prot_ok     = tk.StringVar(value="—")

        self._construir_ui()
        self._mostrar_autotest()

    # ----------------------------------------------------------
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ----------------------------------------------------------

    def _construir_ui(self):
        """Construye el layout principal: panel lateral + área tabs."""

        # Frame raíz con dos columnas
        self.frame_principal = tk.Frame(self.root, bg=COLORES["fondo"])
        self.frame_principal.pack(fill="both", expand=True)

        # Panel lateral (fijo 240px)
        self._construir_panel_lateral()

        # Separador vertical
        sep = tk.Frame(self.frame_principal, bg=COLORES["borde"], width=1)
        sep.pack(side="left", fill="y")

        # Área de resultados (expansible)
        self._construir_area_resultados()

    def _construir_panel_lateral(self):
        """Panel izquierdo: proyecto, archivo, resumen, botones."""
        panel = tk.Frame(
            self.frame_principal,
            bg=COLORES["panel"],
            width=240
        )
        panel.pack(side="left", fill="y")
        panel.pack_propagate(False)

        # Título
        tk.Label(
            panel, text="⚡ MOTOR BT",
            bg=COLORES["panel"], fg=COLORES["acento"],
            font=FUENTES["titulo"], pady=12
        ).pack(fill="x")

        tk.Frame(panel, bg=COLORES["borde"], height=1).pack(fill="x", padx=10)

        # --- PERFIL DE PROYECTO ---
        self._seccion_label(panel, "PERFIL")

        self.rb_perfil_widgets = []   # guardar refs para bloquear/liberar
        for clave, label in lista_perfiles():
            rb = tk.Radiobutton(
                panel,
                text=label,
                variable=self.var_perfil,
                value=clave,
                command=self._cambiar_perfil,
                bg=COLORES["panel"],
                fg=COLORES["texto"],
                selectcolor=COLORES["acento"],
                activebackground=COLORES["panel"],
                activeforeground=COLORES["texto"],
                font=FUENTES["pequeño"],
                anchor="w",
                cursor="hand2"
            )
            rb.pack(fill="x", padx=14, pady=1)
            self.rb_perfil_widgets.append(rb)

        # Descripción del perfil activo
        self.lbl_perfil_desc = tk.Label(
            panel,
            text=self.perfil_activo["descripcion"],
            bg=COLORES["panel"], fg=COLORES["texto_gris"],
            font=FUENTES["pequeño"], wraplength=200,
            anchor="w", justify="left"
        )
        self.lbl_perfil_desc.pack(fill="x", padx=14, pady=(2, 2))

        # Etiqueta de estado del selector (bloqueado/libre)
        self.lbl_perfil_lock = tk.Label(
            panel, text="",
            bg=COLORES["panel"], fg=COLORES["texto_gris"],
            font=FUENTES["pequeño"], wraplength=200,
            anchor="w", justify="left"
        )
        self.lbl_perfil_lock.pack(fill="x", padx=14, pady=(0, 6))

        tk.Frame(panel, bg=COLORES["borde"], height=1).pack(fill="x", padx=10)

        # --- PROYECTO ---
        self._seccion_label(panel, "PROYECTO")

        tk.Label(panel, text="Nombre:", bg=COLORES["panel"],
                 fg=COLORES["texto_gris"], font=FUENTES["pequeño"],
                 anchor="w").pack(fill="x", padx=14, pady=(4,0))
        tk.Entry(
            panel, textvariable=self.nombre_proyecto,
            bg=COLORES["fondo"], fg=COLORES["texto"],
            font=FUENTES["normal"], relief="flat",
            insertbackground=COLORES["texto"], bd=0,
            highlightthickness=1, highlightbackground=COLORES["borde"],
            highlightcolor=COLORES["acento"]
        ).pack(fill="x", padx=14, pady=(2,8))

        # --- ARCHIVO ---
        self._seccion_label(panel, "ARCHIVO EXCEL")

        self.lbl_archivo = tk.Label(
            panel, text="Sin archivo cargado",
            bg=COLORES["panel"], fg=COLORES["texto_gris"],
            font=FUENTES["pequeño"], wraplength=200,
            anchor="w", justify="left"
        )
        self.lbl_archivo.pack(fill="x", padx=14, pady=(4,4))

        self._boton(panel, "📂  Cargar Excel", self._cargar_excel,
                    color=COLORES["encabezado"]).pack(fill="x", padx=14, pady=2)

        tk.Frame(panel, bg=COLORES["borde"], height=1).pack(fill="x", padx=10, pady=8)

        # --- RESUMEN EJECUTIVO ---
        self._seccion_label(panel, "RESUMEN")

        self._fila_resumen(panel, "Circuitos OK",  self.var_circ_ok,   COLORES["ok"])
        self._fila_resumen(panel, "Circuitos FALLA", self.var_circ_falla, COLORES["falla"])
        self._fila_resumen(panel, "Icc bornes BT", self.var_icc,       COLORES["acento"])
        self._fila_resumen(panel, "Uso transf.",   self.var_trafo_uso, COLORES["precaucion"])
        self._fila_resumen(panel, "Protec. OK",    self.var_prot_ok,   COLORES["ok"])

        tk.Frame(panel, bg=COLORES["borde"], height=1).pack(fill="x", padx=10, pady=8)

        # --- BOTONES ACCIÓN ---
        self._boton(panel, "▶  CALCULAR", self._calcular,
                    color=COLORES["boton"]).pack(fill="x", padx=14, pady=2)
        self._boton(panel, "💾  EXPORTAR REPORTE", self._exportar,
                    color=COLORES["encabezado"]).pack(fill="x", padx=14, pady=2)
        self.btn_demanda = self._boton(
                    panel, "📊  DEMANDA M6", self._abrir_ventana_demanda,
                    color=COLORES["encabezado"])
        self.btn_demanda.pack(fill="x", padx=14, pady=2)
        self.btn_demanda.config(state="disabled")   # habilitado tras calcular
        self.btn_coord = self._boton(
                    panel, "⚡  COORDINACIÓN M7", self._abrir_ventana_coordinacion,
                    color=COLORES["encabezado"])
        self.btn_coord.pack(fill="x", padx=14, pady=2)
        self.btn_coord.config(state="disabled")     # habilitado tras calcular

        tk.Frame(panel, bg=COLORES["borde"], height=1).pack(fill="x", padx=10, pady=8)

        # --- ESTADO ---
        tk.Label(
            panel, textvariable=self.estado_texto,
            bg=COLORES["panel"], fg=COLORES["texto_gris"],
            font=FUENTES["pequeño"], wraplength=210,
            anchor="w", justify="left"
        ).pack(fill="x", padx=14, pady=4)

    def _construir_area_resultados(self):
        """Área derecha con Notebook de tabs."""
        area = tk.Frame(self.frame_principal, bg=COLORES["fondo"])
        area.pack(side="left", fill="both", expand=True)

        # Estilo del Notebook
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "BT.TNotebook",
            background=COLORES["fondo"],
            borderwidth=0
        )
        style.configure(
            "BT.TNotebook.Tab",
            background=COLORES["panel"],
            foreground=COLORES["texto_gris"],
            font=FUENTES["normal"],
            padding=[14, 6]
        )
        style.map(
            "BT.TNotebook.Tab",
            background=[("selected", COLORES["acento"])],
            foreground=[("selected", "#FFFFFF")]
        )

        self.notebook = ttk.Notebook(area, style="BT.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=0, pady=0)

        # Crear tabs
        self.tab_dv    = self._crear_tab("⚡  Caída ΔV")
        self.tab_icc   = self._crear_tab("⚡  Transf / Icc")
        self.tab_prot  = self._crear_tab("🛡  Protecciones")
        self.tab_bal   = self._crear_tab("⚖  Balance")
        self.tab_test  = self._crear_tab("🔧  Sistema")

    def _crear_tab(self, titulo):
        """Crea un frame dentro del notebook y retorna el frame scrollable."""
        frame_outer = tk.Frame(self.notebook, bg=COLORES["fondo"])
        self.notebook.add(frame_outer, text=titulo)

        canvas = tk.Canvas(frame_outer, bg=COLORES["fondo"],
                          highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_outer, orient="vertical",
                                  command=canvas.yview)
        frame_inner = tk.Frame(canvas, bg=COLORES["fondo"])

        frame_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scroll con rueda del mouse
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            int(-1*(e.delta/120)), "units"))

        return frame_inner

    # ----------------------------------------------------------
    # COMPONENTES REUTILIZABLES
    # ----------------------------------------------------------

    def _seccion_label(self, parent, texto):
        tk.Label(
            parent, text=texto,
            bg=COLORES["panel"], fg=COLORES["acento"],
            font=FUENTES["pequeño"], anchor="w", pady=2
        ).pack(fill="x", padx=14)

    def _boton(self, parent, texto, comando, color=None):
        color = color or COLORES["boton"]
        btn = tk.Button(
            parent, text=texto, command=comando,
            bg=color, fg="#FFFFFF",
            font=FUENTES["normal"],
            relief="flat", cursor="hand2",
            activebackground=COLORES["boton_hover"],
            activeforeground="#FFFFFF",
            pady=6
        )
        return btn

    def _fila_resumen(self, parent, etiqueta, variable, color):
        f = tk.Frame(parent, bg=COLORES["panel"])
        f.pack(fill="x", padx=14, pady=1)
        tk.Label(f, text=etiqueta, bg=COLORES["panel"],
                 fg=COLORES["texto_gris"],
                 font=FUENTES["pequeño"], anchor="w",
                 width=16).pack(side="left")
        tk.Label(f, textvariable=variable, bg=COLORES["panel"],
                 fg=color, font=FUENTES["subtitulo"],
                 anchor="e").pack(side="right")

    def _limpiar_tab(self, tab_frame):
        for widget in tab_frame.winfo_children():
            widget.destroy()

    def _encabezado_tab(self, parent, titulo, subtitulo=""):
        tk.Label(
            parent, text=titulo,
            bg=COLORES["fondo"], fg=COLORES["acento"],
            font=FUENTES["titulo"], anchor="w", pady=8, padx=16
        ).pack(fill="x")
        if subtitulo:
            tk.Label(
                parent, text=subtitulo,
                bg=COLORES["fondo"], fg=COLORES["texto_gris"],
                font=FUENTES["pequeño"], anchor="w", padx=16
            ).pack(fill="x")
        tk.Frame(parent, bg=COLORES["borde"], height=1).pack(
            fill="x", padx=16, pady=4)

    def _tabla(self, parent, columnas, datos, colores_fila=None):
        """
        Crea una tabla con Treeview estilizado.
        colores_fila: función que recibe la fila y retorna color de fondo.
        """
        style = ttk.Style()
        style.configure(
            "BT.Treeview",
            background=COLORES["fila_par"],
            foreground=COLORES["texto"],
            fieldbackground=COLORES["fila_par"],
            font=FUENTES["mono"],
            rowheight=22
        )
        style.configure(
            "BT.Treeview.Heading",
            background=COLORES["encabezado"],
            foreground=COLORES["texto"],
            font=FUENTES["subtitulo"],
            relief="flat"
        )
        style.map("BT.Treeview",
                  background=[("selected", COLORES["acento"])],
                  foreground=[("selected", "#FFFFFF")])

        frame = tk.Frame(parent, bg=COLORES["fondo"])
        frame.pack(fill="both", expand=True, padx=16, pady=8)

        tree = ttk.Treeview(
            frame,
            columns=list(columnas.keys()),
            show="headings",
            style="BT.Treeview"
        )

        for col, ancho in columnas.items():
            tree.heading(col, text=col)
            tree.column(col, width=ancho, anchor="center")

        # Colores de etiquetas
        tree.tag_configure("ok",        background="#1A3A1A", foreground=COLORES["ok"])
        tree.tag_configure("falla",     background="#3A1A1A", foreground=COLORES["falla"])
        tree.tag_configure("precaucion",background="#3A2A0A", foreground=COLORES["precaucion"])
        tree.tag_configure("aceptable", background="#2A2A1A", foreground=COLORES["aceptable"])
        tree.tag_configure("normal",    background=COLORES["fila_par"])
        tree.tag_configure("impar",     background=COLORES["fila_impar"])

        for i, fila in enumerate(datos):
            tag = "impar" if i % 2 else "normal"
            if colores_fila:
                tag = colores_fila(fila) or tag
            tree.insert("", "end", values=fila, tags=(tag,))

        # Scrollbar horizontal
        scroll_x = ttk.Scrollbar(frame, orient="horizontal",
                                  command=tree.xview)
        tree.configure(xscrollcommand=scroll_x.set)

        tree.pack(fill="both", expand=True)
        scroll_x.pack(fill="x")

        return tree

    # ----------------------------------------------------------
    # ACCIONES
    # ----------------------------------------------------------

    def _cargar_excel(self):
        """Abre selector de archivo, carga datos y detecta perfil."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Excel", "*.xlsx"), ("Todos", "*.*")]
        )
        if not ruta:
            return

        self.archivo_excel.set(ruta)
        nombre = os.path.basename(ruta)
        self.lbl_archivo.config(text=nombre, fg=COLORES["texto"])

        # --- DETECCIÓN AUTOMÁTICA DE PERFIL ---
        try:
            libro = openpyxl.load_workbook(ruta, data_only=True)
            from excel import leer_perfil_excel
            datos_perfil = leer_perfil_excel(libro)

            if datos_perfil:
                perfil_clave = datos_perfil["perfil"]
                perfil_obj   = obtener_perfil(perfil_clave)

                # Sincronizar selector de perfil en la GUI
                self.var_perfil.set(perfil_clave)
                self.perfil_activo = perfil_obj
                self.lbl_perfil_desc.config(
                    text=perfil_obj["descripcion"],
                    fg=COLORES["ok"]
                )
                self.root.after(3000, lambda: self.lbl_perfil_desc.config(
                    fg=COLORES["texto_gris"]
                ))

                # Nombre del proyecto desde la hoja perfil
                nombre_proy = datos_perfil.get("nombre_proyecto", "")
                if nombre_proy:
                    self.nombre_proyecto.set(nombre_proy.upper())

                # Bloquear selector — perfil definido por el Excel
                self._bloquear_perfil(perfil_obj["label"])

                self._set_estado(
                    f"✓ Perfil detectado: {perfil_obj['label']} "
                    f"— {nombre_proy.upper()}"
                )
            else:
                # Sin hoja perfil — liberar selector
                self._liberar_perfil()
                if not self.nombre_proyecto.get():
                    self.nombre_proyecto.set(
                        os.path.splitext(nombre)[0].upper()
                    )
                self._set_estado(
                    f"● Archivo cargado: {nombre} "
                    f"(sin hoja 'perfil' — perfil libre)"
                )
        except Exception as e:
            self._liberar_perfil()
            if not self.nombre_proyecto.get():
                self.nombre_proyecto.set(
                    os.path.splitext(nombre)[0].upper()
                )
            self._set_estado(f"● Archivo cargado: {nombre}")

    def _bloquear_perfil(self, label_perfil):
        """
        Deshabilita el selector de perfil cuando el Excel
        tiene hoja 'perfil'. El perfil lo define el Excel.
        """
        for rb in self.rb_perfil_widgets:
            rb.config(state="disabled", cursor="arrow",
                      fg=COLORES["texto_gris"])
        self.lbl_perfil_lock.config(
            text="🔒 Definido en hoja 'perfil'",
            fg=COLORES["acento"]
        )

    def _liberar_perfil(self):
        """
        Habilita el selector cuando no hay hoja perfil en el Excel.
        """
        for rb in self.rb_perfil_widgets:
            rb.config(state="normal", cursor="hand2",
                      fg=COLORES["texto"])
        self.lbl_perfil_lock.config(text="", fg=COLORES["texto_gris"])

    def _cambiar_perfil(self):
        """Actualiza el perfil activo. No toca los tabs."""
        clave = self.var_perfil.get()
        self.perfil_activo = obtener_perfil(clave)
        self.lbl_perfil_desc.config(
            text=self.perfil_activo["descripcion"]
        )
        self._set_estado(f"● Perfil: {self.perfil_activo['label']}")

    def _calcular(self):
        """Lee datos, valida perfil y abre ventana de confirmación."""
        if not self.archivo_excel.get():
            messagebox.showwarning("Sin archivo",
                "Carga un archivo Excel antes de calcular.")
            return

        self._set_estado("⏳ Leyendo datos...")
        self.root.update()

        # Leer datos primero para poder validar
        archivo = self.archivo_excel.get()
        try:
            self.datos_trafo    = leer_transformador_excel(archivo)
            libro               = openpyxl.load_workbook(archivo, data_only=True)
            self.protecciones   = leer_protecciones_excel(libro)
            self.balance_datos  = leer_balance_excel(libro)
            self.tableros_datos = leer_tableros_excel(libro)
            self.circuitos      = leer_circuitos_excel(archivo)
            self.params_demanda = leer_demanda_excel(libro)
            self.cadena_datos   = leer_cadena_excel(libro)
        except Exception as e:
            self._set_estado(f"✗ Error al leer: {e}")
            return

        # Validar perfil vs datos
        perfil_clave = self.var_perfil.get()
        resultados   = validar_perfil_vs_datos(
            perfil_clave, self.circuitos, self.datos_trafo,
            self.protecciones, self.balance_datos, self.tableros_datos
        )

        # Mostrar ventana de validación
        self._mostrar_ventana_validacion(resultados)

    def _mostrar_ventana_validacion(self, resultados):
        """
        Ventana modal con resumen de validación.
        Si hay BLOQUEO → solo CANCELAR disponible.
        Si solo hay ADVERTENCIAS → puede continuar.
        """
        bloqueado = hay_bloqueo(resultados)
        perfil    = self.perfil_activo

        # Crear ventana modal
        ventana = tk.Toplevel(self.root)
        ventana.title("Validación de datos")
        ventana.geometry("500x420")
        ventana.configure(bg=COLORES["fondo"])
        ventana.resizable(False, False)
        ventana.grab_set()   # modal — bloquea la ventana principal

        # Centrar respecto a la ventana principal
        x = self.root.winfo_x() + (self.root.winfo_width() - 500) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 420) // 2
        ventana.geometry(f"500x420+{x}+{y}")

        # --- Encabezado ---
        tk.Label(
            ventana,
            text="VALIDACIÓN DE DATOS",
            bg=COLORES["fondo"], fg=COLORES["acento"],
            font=FUENTES["titulo"], pady=12
        ).pack(fill="x")

        tk.Label(
            ventana,
            text=f"Perfil: {perfil['label']}  |  "
                 f"Circuitos: {len(self.circuitos)}",
            bg=COLORES["fondo"], fg=COLORES["texto_gris"],
            font=FUENTES["pequeño"]
        ).pack()

        tk.Frame(ventana, bg=COLORES["borde"],
                 height=1).pack(fill="x", padx=16, pady=8)

        # --- Resultados de validación ---
        frame_scroll = tk.Frame(ventana, bg=COLORES["fondo"])
        frame_scroll.pack(fill="both", expand=True, padx=16)

        for i, (nivel, mensaje) in enumerate(resultados):
            if nivel == NIVEL_BLOQUEO:
                icono = "✗"
                color = COLORES["falla"]
                bg    = "#3A1A1A"
            elif nivel == NIVEL_ADVERTENCIA:
                icono = "⚠"
                color = COLORES["precaucion"]
                bg    = "#2A1A0A"
            else:
                icono = "✓"
                color = COLORES["ok"]
                bg    = "#1A3A1A"

            fila = tk.Frame(frame_scroll, bg=bg,
                            relief="flat", bd=0)
            fila.pack(fill="x", pady=2)

            # Icono
            tk.Label(
                fila, text=f"  {icono}  ",
                bg=bg, fg=color,
                font=FUENTES["subtitulo"]
            ).pack(side="left", anchor="n", pady=6)

            # Mensaje (puede tener saltos de línea)
            tk.Label(
                fila, text=mensaje,
                bg=bg, fg=COLORES["texto"],
                font=FUENTES["pequeño"],
                justify="left", anchor="w",
                wraplength=400
            ).pack(side="left", fill="x", pady=6, padx=(0, 8))

        tk.Frame(ventana, bg=COLORES["borde"],
                 height=1).pack(fill="x", padx=16, pady=8)

        # --- Botones ---
        frame_btns = tk.Frame(ventana, bg=COLORES["fondo"])
        frame_btns.pack(pady=8)

        def continuar():
            ventana.destroy()
            self._set_estado("⏳ Calculando...")
            self.root.update()
            hilo = threading.Thread(
                target=self._ejecutar_calculos_post_validacion,
                daemon=True
            )
            hilo.start()

        def cancelar():
            ventana.destroy()
            self._set_estado("● Cálculo cancelado")

        if not bloqueado:
            tk.Button(
                frame_btns,
                text="▶  CONTINUAR",
                command=continuar,
                bg=COLORES["boton"], fg="#FFFFFF",
                font=FUENTES["normal"],
                relief="flat", cursor="hand2",
                padx=20, pady=6
            ).pack(side="left", padx=8)

        tk.Button(
            frame_btns,
            text="✗  CANCELAR",
            command=cancelar,
            bg=COLORES["encabezado"], fg="#FFFFFF",
            font=FUENTES["normal"],
            relief="flat", cursor="hand2",
            padx=20, pady=6
        ).pack(side="left", padx=8)

    def _ejecutar_calculos_post_validacion(self):
        """
        Ejecuta los cálculos. Los datos ya fueron leídos en _calcular().
        Solo procesa los cálculos matemáticos y actualiza la GUI.
        """
        try:
            if not self.circuitos:
                self.root.after(0, lambda: self._set_estado(
                    "✗ No se encontraron circuitos válidos"))
                return

            # Calcular Icc por punto si hay transformador
            if self.datos_trafo:
                if self.datos_trafo["modo"] == "A":
                    _, Zt_ohm, _ = calcular_icc_transformador(
                        self.datos_trafo["kVA"],
                        self.datos_trafo["Vn_BT"],
                        self.datos_trafo["Ucc_pct"]
                    )
                else:
                    _, Ucc_pct, _ = icc_desde_tabla(self.datos_trafo["kVA"])
                    Zt_ohm = (Ucc_pct/100) * (
                        self.datos_trafo["Vn_BT"]**2 /
                        (self.datos_trafo["kVA"]*1000)
                    )
                self.circuitos = calcular_icc_todos_circuitos(
                    Zt_ohm, self.circuitos
                )

            # Balance
            self.resultado_balance = None
            if self.balance_datos and self.tableros_datos:
                kVA = self.datos_trafo["kVA"] if self.datos_trafo else 1000
                self.resultado_balance = calcular_balance_tableros(
                    self.circuitos, self.balance_datos,
                    self.tableros_datos, kVA
                )

            # Demanda M6
            self.resultado_demanda = None
            if self.params_demanda and self.balance_datos:
                self.resultado_demanda = calcular_demanda(
                    self.circuitos, self.balance_datos, self.params_demanda
                )

            # Coordinación TCC — M7
            self.resultados_m7 = {}
            if self.cadena_datos:
                modos = {}
                for d in self.cadena_datos:
                    m = d.get("modo", "red")
                    modos.setdefault(m, []).append(d)
                for modo, dispositivos in modos.items():
                    dispositivos_ord = sorted(dispositivos, key=lambda x: x["nivel"])
                    Icc_A = 0
                    for d in reversed(dispositivos_ord):
                        if d.get("Icc_kA"):
                            Icc_A = d["Icc_kA"] * 1000
                            break
                    if Icc_A > 0:
                        self.resultados_m7[modo] = verificar_cadena(
                            dispositivos_ord, Icc_A, sistema="3F_380"
                        )

            # Actualizar GUI desde el hilo principal
            self.root.after(0, self._actualizar_gui)

        except Exception as e:
            self.root.after(0, lambda: self._set_estado(f"✗ Error: {e}"))

    def _actualizar_gui(self):
        """Actualiza todos los tabs con los resultados calculados."""
        self._poblar_tab_dv()
        self._poblar_tab_icc()
        self._poblar_tab_protecciones()
        self._poblar_tab_balance()
        self._actualizar_resumen()
        # Habilitar botón Demanda M6 si hay datos
        if self.resultado_demanda:
            self.btn_demanda.config(state="normal")
        if self.resultados_m7:
            self.btn_coord.config(state="normal")
        self._set_estado("✓ Cálculo completado")

    def _exportar(self):
        """Exporta reporte TXT y Excel con selector de carpeta."""
        if not self.circuitos:
            messagebox.showwarning("Sin datos",
                "Ejecuta el cálculo antes de exportar.")
            return

        from main import generar_reporte_txt

        fecha         = datetime.now().strftime("%d/%m/%Y %H:%M")
        fecha_archivo = datetime.now().strftime("%Y%m%d_%H%M")
        nombre        = self.nombre_proyecto.get() or "PROYECTO"
        nombre_base   = f"REPORTE_{nombre.upper()}_{fecha_archivo}"

        carpeta = filedialog.askdirectory(
            title="Seleccionar carpeta de destino"
        )
        if not carpeta:
            return

        nombre_txt  = os.path.join(carpeta, f"{nombre_base}.txt")
        nombre_xlsx = os.path.join(carpeta, f"{nombre_base}.xlsx")

        lineas, _, _ = generar_reporte_txt(
            nombre, self.circuitos, fecha,
            self.datos_trafo, self.protecciones,
            self.balance_datos, self.tableros_datos
        )

        guardar_txt(lineas, nombre_txt)
        exportar_excel(nombre, self.circuitos, fecha, nombre_xlsx)

        messagebox.showinfo("Exportado",
            f"Archivos guardados en:\n{carpeta}\n\n"
            f"{nombre_base}.txt\n"
            f"{nombre_base}.xlsx")
        self._set_estado(f"✓ Exportado en: {os.path.basename(carpeta)}")

    # ----------------------------------------------------------
    # POBLAR TABS
    # ----------------------------------------------------------

    def _poblar_tab_dv(self):
        self._limpiar_tab(self.tab_dv)
        self._encabezado_tab(
            self.tab_dv,
            "CAÍDA DE TENSIÓN POR CIRCUITO",
            f"Límite: {LIMITE_DV}%  |  Normativa: SEC RIC N°10 / NEC / IEC 60364"
        )

        columnas = {
            "Circuito": 200, "Sistema": 60, "Conductor": 100,
            "I_dis(A)": 70, "I_cap(A)": 70, "Estado_I": 80,
            "ΔV(V)": 70, "ΔV(%)": 70, "Estado_dV": 100,
            "Sugerencia": 160
        }

        datos = []
        for c in self.circuitos:
            I_cap = capacidad_corregida(c["I_max"], c["paralelos"], c["temp_amb"])
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
                    sugerencia = f"→ {cond} ({dv}%)"

            desc = (f"{c['paralelos']}x{c['conductor']}"
                    if c["paralelos"] > 1 else c["conductor"])

            datos.append((
                c["nombre"], c["sistema"], desc,
                c["I_diseno"], I_cap, estado_I,
                dV_V, dV_pct, estado_dV, sugerencia
            ))

        def color_fila(fila):
            estado_dv = fila[8]
            estado_i  = fila[5]
            if estado_dv == "FALLA" or estado_i == "SUPERA":
                return "falla"
            elif estado_dv == "PRECAUCIÓN":
                return "precaucion"
            elif estado_dv == "ACEPTABLE":
                return "aceptable"
            return "ok"

        self._tabla(self.tab_dv, columnas, datos, color_fila)

    def _poblar_tab_icc(self):
        self._limpiar_tab(self.tab_icc)
        self._encabezado_tab(
            self.tab_icc,
            "TRANSFORMADOR E Icc POR PUNTO",
            "Método: impedancias IEC 60909"
        )

        if not self.datos_trafo:
            tk.Label(self.tab_icc, text="No se encontró hoja 'Transformador'",
                     bg=COLORES["fondo"], fg=COLORES["texto_gris"],
                     font=FUENTES["normal"], pady=20).pack()
            return

        # Datos del transformador
        modo = self.datos_trafo["modo"]
        if modo == "A":
            Icc_kA, Zt_ohm, info = calcular_icc_transformador(
                self.datos_trafo["kVA"],
                self.datos_trafo["Vn_BT"],
                self.datos_trafo["Ucc_pct"]
            )
        else:
            Icc_kA, Ucc_pct, _ = icc_desde_tabla(self.datos_trafo["kVA"])
            Zt_ohm = 0
            info = {"In_A": 0, "Zt_ohm": 0}

        # Panel info transformador
        f_info = tk.Frame(self.tab_icc, bg=COLORES["panel"],
                          relief="flat", bd=0)
        f_info.pack(fill="x", padx=16, pady=8)

        datos_trafo_display = [
            ("Nombre",      self.datos_trafo.get("nombre", "—")),
            ("Modo",        f"{'A — datos de placa' if modo=='A' else 'B — tabla típica'}"),
            ("Potencia",    f"{self.datos_trafo['kVA']} kVA"),
            ("Tensión BT",  f"{self.datos_trafo['Vn_BT']} V"),
            ("Ucc%",        f"{self.datos_trafo.get('Ucc_pct','—')} %"),
            ("In BT",       f"{info.get('In_A','—')} A"),
            ("Zt",          f"{info.get('Zt_ohm','—')} Ω"),
            ("Icc bornes",  f"{Icc_kA} kA"),
            ("Nivel Icc",   clasificar_icc(Icc_kA)),
        ]

        for i, (campo, valor) in enumerate(datos_trafo_display):
            fila = tk.Frame(f_info,
                            bg=COLORES["fila_impar"] if i%2 else COLORES["panel"])
            fila.pack(fill="x")
            tk.Label(fila, text=f"  {campo}", width=14, anchor="w",
                     bg=fila["bg"], fg=COLORES["texto_gris"],
                     font=FUENTES["pequeño"]).pack(side="left", pady=3)
            color_val = COLORES["acento"] if "Icc" in campo else COLORES["texto"]
            tk.Label(fila, text=valor, anchor="w",
                     bg=fila["bg"], fg=color_val,
                     font=FUENTES["normal"]).pack(side="left", pady=3)

        # Tabla Icc por circuito
        tk.Label(self.tab_icc, text="Icc en cada punto del sistema",
                 bg=COLORES["fondo"], fg=COLORES["texto_gris"],
                 font=FUENTES["pequeño"], anchor="w",
                 padx=16, pady=8).pack(fill="x")

        columnas = {
            "Circuito": 200, "Sistema": 60, "Conductor": 100,
            "L(m)": 60, "Zt_cable(Ω)": 100,
            "Icc(kA)": 80, "Reducción(%)": 100, "Nivel": 180
        }

        datos = []
        for c in self.circuitos:
            if "Icc_kA" not in c:
                continue
            from icc_punto import reduccion_icc
            red = reduccion_icc(Icc_kA, c["Icc_kA"])
            datos.append((
                c["nombre"], c["sistema"], c["conductor"],
                c["L_m"], c.get("Zt_cable", "—"),
                c["Icc_kA"], f"{red}%", c["nivel_icc"]
            ))

        def color_icc(fila):
            nivel = str(fila[7])
            if "MUY BAJO" in nivel:  return "falla"
            if "BAJO"    in nivel:   return "precaucion"
            return "ok"

        self._tabla(self.tab_icc, columnas, datos, color_icc)

    def _poblar_tab_protecciones(self):
        self._limpiar_tab(self.tab_prot)
        self._encabezado_tab(
            self.tab_prot,
            "VERIFICACIÓN DE PROTECCIONES",
            "IEC 60898 | IEC 60947-2 | IEC 60364-4-41"
        )

        if not self.protecciones:
            tk.Label(self.tab_prot,
                     text="No se encontró hoja 'Protecciones'",
                     bg=COLORES["fondo"], fg=COLORES["texto_gris"],
                     font=FUENTES["normal"], pady=20).pack()
            return

        columnas = {
            "Circuito": 180, "Curva": 60, "In(A)": 60,
            "Pdc(kA)": 70, "Icc(kA)": 70,
            "Im_min(A)": 80, "Margen(%)": 80,
            "Estado": 220
        }

        datos = []
        for c in self.circuitos:
            if c["nombre"] not in self.protecciones:
                continue
            p = self.protecciones[c["nombre"]]
            Vn = TENSION_SISTEMA[c["sistema"]]
            r = verificar_circuito_completo(
                c["nombre"], p["In_A"], p["curva"],
                p["poder_corte_kA"], c.get("Icc_kA", 0), Vn
            )
            datos.append((
                c["nombre"], p["curva"], int(p["In_A"]),
                int(p["poder_corte_kA"]), c.get("Icc_kA","—"),
                r["Im_min_A"], r["margen_pct"], r["estado"]
            ))

        def color_prot(fila):
            estado = str(fila[7])
            if "FALLA"     in estado: return "falla"
            if "PRECAUCIÓN" in estado: return "precaucion"
            return "ok"

        self._tabla(self.tab_prot, columnas, datos, color_prot)

    def _poblar_tab_balance(self):
        self._limpiar_tab(self.tab_bal)
        self._encabezado_tab(
            self.tab_bal,
            "BALANCE DE CARGA POR TABLERO",
            "Factores de simultaneidad | Equilibrio L1/L2/L3 | IEC 60038"
        )

        if not self.resultado_balance:
            tk.Label(self.tab_bal,
                     text="No se encontraron hojas 'balance' y 'tableros'",
                     bg=COLORES["fondo"], fg=COLORES["texto_gris"],
                     font=FUENTES["normal"], pady=20).pack()
            return

        for nombre_t, t in self.resultado_balance["tableros"].items():
            # Encabezado del tablero
            color_estado = (COLORES["falla"] if "FALLA" in t["estado"]
                           else COLORES["precaucion"] if "PRECAUCIÓN" in t["estado"]
                           else COLORES["ok"])

            f_header = tk.Frame(self.tab_bal, bg=COLORES["panel"])
            f_header.pack(fill="x", padx=16, pady=(12,2))

            tk.Label(f_header, text=f"  {nombre_t}",
                     bg=COLORES["panel"], fg=COLORES["acento"],
                     font=FUENTES["subtitulo"]).pack(side="left", pady=6)
            tk.Label(f_header,
                     text=f"  {t['uso_pct']}%  {t['estado']}  ",
                     bg=COLORES["panel"], fg=color_estado,
                     font=FUENTES["subtitulo"]).pack(side="right", pady=6)

            # Datos del tablero
            datos_t = [
                ("Capacidad",   f"{t['capacidad_kva']} kVA"),
                ("Demanda",     f"{t['S_total_kva']} kVA  ({t['P_total_kw']} kW)"),
                ("Uso",         f"{t['uso_pct']}%"),
                ("L1",          f"{t['fases']['L1']} kW"),
                ("L2",          f"{t['fases']['L2']} kW"),
                ("L3",          f"{t['fases']['L3']} kW"),
                ("Desequilibrio", f"{t['desequilibrio_pct']}%  →  {t['estado_fases']}"),
            ]

            f_datos = tk.Frame(self.tab_bal, bg=COLORES["fondo"])
            f_datos.pack(fill="x", padx=16, pady=2)

            for i, (campo, valor) in enumerate(datos_t):
                fila = tk.Frame(f_datos,
                                bg=COLORES["fila_impar"] if i%2 else COLORES["fila_par"])
                fila.pack(fill="x")
                tk.Label(fila, text=f"  {campo}", width=16, anchor="w",
                         bg=fila["bg"], fg=COLORES["texto_gris"],
                         font=FUENTES["pequeño"]).pack(side="left", pady=2)
                tk.Label(fila, text=valor, anchor="w",
                         bg=fila["bg"], fg=COLORES["texto"],
                         font=FUENTES["normal"]).pack(side="left", pady=2)

        # Resumen transformador
        r = self.resultado_balance
        color_trafo = (COLORES["falla"] if "FALLA" in r["estado_trafo"]
                      else COLORES["precaucion"] if "PRECAUCIÓN" in r["estado_trafo"]
                      else COLORES["ok"])

        tk.Frame(self.tab_bal, bg=COLORES["borde"],
                 height=1).pack(fill="x", padx=16, pady=8)

        f_trafo = tk.Frame(self.tab_bal, bg=COLORES["panel"])
        f_trafo.pack(fill="x", padx=16, pady=4)
        tk.Label(f_trafo, text="  TRANSFORMADOR",
                 bg=COLORES["panel"], fg=COLORES["acento"],
                 font=FUENTES["subtitulo"]).pack(side="left", pady=6)
        tk.Label(f_trafo,
                 text=f"  {r['uso_trafo_pct']}% de {r['kVA_trafo']} kVA"
                      f"  →  {r['estado_trafo']}  ",
                 bg=COLORES["panel"], fg=color_trafo,
                 font=FUENTES["subtitulo"]).pack(side="right", pady=6)

    def _mostrar_autotest(self):
        """Muestra resultados del autotest en el tab Sistema."""
        self._limpiar_tab(self.tab_test)
        self._encabezado_tab(
            self.tab_test,
            "VERIFICACIÓN DEL SISTEMA",
            "Test automático al arranque — verifica integridad de todos los módulos"
        )

        tests = ejecutar_autotest()
        todos_ok = all(ok for _, ok, _ in tests)

        for nombre, ok, msg in tests:
            f = tk.Frame(self.tab_test,
                         bg=COLORES["fila_impar"] if tests.index(
                             (nombre,ok,msg))%2 else COLORES["fila_par"])
            f.pack(fill="x", padx=16, pady=1)

            icono = "✓" if ok else "✗"
            color = COLORES["ok"] if ok else COLORES["falla"]

            tk.Label(f, text=f"  {icono}  {nombre}",
                     bg=f["bg"], fg=color,
                     font=FUENTES["normal"], width=22,
                     anchor="w").pack(side="left", pady=4)
            tk.Label(f, text=msg,
                     bg=f["bg"], fg=COLORES["texto_gris"],
                     font=FUENTES["pequeño"],
                     anchor="w").pack(side="left", pady=4)

        tk.Frame(self.tab_test, bg=COLORES["borde"],
                 height=1).pack(fill="x", padx=16, pady=8)

        resumen_color = COLORES["ok"] if todos_ok else COLORES["falla"]
        resumen_texto = ("✓  Todos los módulos operativos"
                         if todos_ok else
                         "✗  Hay módulos con errores — revisar instalación")
        tk.Label(self.tab_test, text=resumen_texto,
                 bg=COLORES["fondo"], fg=resumen_color,
                 font=FUENTES["subtitulo"], pady=8, padx=16,
                 anchor="w").pack(fill="x")

    # ----------------------------------------------------------
    # RESUMEN EJECUTIVO
    # ----------------------------------------------------------

    def _actualizar_resumen(self):
        """Actualiza los contadores del panel lateral."""
        total_ok = total_falla = 0
        for c in self.circuitos:
            I_cap = capacidad_corregida(c["I_max"], c["paralelos"], c["temp_amb"])
            _, dV_pct = calcular_caida_tension(
                c["L_m"], c["S_mm2"], c["I_diseno"], c["paralelos"], c["sistema"]
            )
            estado_dV = clasificar_caida(dV_pct)
            estado_I  = "OK" if c["I_diseno"] <= I_cap else "SUPERA"
            if estado_dV == "FALLA" or estado_I == "SUPERA":
                total_falla += 1
            else:
                total_ok += 1

        self.var_circ_ok.set(str(total_ok))
        self.var_circ_falla.set(str(total_falla))

        if self.datos_trafo:
            if self.datos_trafo["modo"] == "A":
                Icc_kA, _, _ = calcular_icc_transformador(
                    self.datos_trafo["kVA"],
                    self.datos_trafo["Vn_BT"],
                    self.datos_trafo["Ucc_pct"]
                )
            else:
                Icc_kA, _, _ = icc_desde_tabla(self.datos_trafo["kVA"])
            self.var_icc.set(f"{Icc_kA} kA")

        if self.resultado_balance:
            self.var_trafo_uso.set(
                f"{self.resultado_balance['uso_trafo_pct']}%")

        prot_ok = sum(
            1 for c in self.circuitos
            if c["nombre"] in self.protecciones
            and verificar_circuito_completo(
                c["nombre"],
                self.protecciones[c["nombre"]]["In_A"],
                self.protecciones[c["nombre"]]["curva"],
                self.protecciones[c["nombre"]]["poder_corte_kA"],
                c.get("Icc_kA", 0),
                TENSION_SISTEMA[c["sistema"]]
            )["estado"] == "OK"
        )
        self.var_prot_ok.set(f"{prot_ok}/{len(self.protecciones)}")


    def _abrir_ventana_demanda(self):
        """
        Abre ventana separada con resultados de demanda M6.
        No modal — coexiste con la ventana principal.
        Se recrea cada vez — evita estados inconsistentes.
        """
        if not self.resultado_demanda:
            return

        r   = self.resultado_demanda
        p   = self.params_demanda

        # Calcular trafo o SEC según tipo
        resultado_trafo = None
        resultado_sec   = None
        if p.get("tipo_alimentador") == "transformador":
            resultado_trafo = seleccionar_transformador(r["S_futuro_kva"])
        else:
            resultado_sec = dimensionar_acometida_sec(
                r["S_futuro_kva"],
                p["tension_alim"],
                p["sistema_alim"],
                p.get("zona_sec", "urbana")
            )

        # --- Crear ventana ---
        ventana = tk.Toplevel(self.root)
        ventana.title(f"Demanda M6 — {self.nombre_proyecto.get()}")
        ventana.geometry("860x620")
        ventana.configure(bg=COLORES["fondo"])
        ventana.resizable(True, True)
        # No grab_set() — no modal, coexiste con ventana principal

        # Centrar
        x = self.root.winfo_x() + (self.root.winfo_width()  - 860) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 620) // 2
        ventana.geometry(f"860x620+{x}+{y}")

        # Título
        tk.Label(
            ventana,
            text="DEMANDA MÁXIMA Y DIMENSIONAMIENTO — M6",
            bg=COLORES["fondo"], fg=COLORES["acento"],
            font=FUENTES["titulo"], pady=10
        ).pack(fill="x")
        tk.Label(
            ventana,
            text=f"Instalación: {r['tipo_instalacion'].upper()}  |  "
                 f"Normativa: RIC N°03 SEC / IEC 60076",
            bg=COLORES["fondo"], fg=COLORES["texto_gris"],
            font=FUENTES["pequeño"]
        ).pack()
        tk.Frame(ventana, bg=COLORES["borde"],
                 height=1).pack(fill="x", padx=16, pady=6)

        # Notebook interno
        style = ttk.Style()
        style.configure("M6.TNotebook",
                         background=COLORES["fondo"], borderwidth=0)
        style.configure("M6.TNotebook.Tab",
                         background=COLORES["panel"],
                         foreground=COLORES["texto_gris"],
                         font=FUENTES["pequeño"], padding=[12, 5])
        style.map("M6.TNotebook.Tab",
                  background=[("selected", COLORES["acento"])],
                  foreground=[("selected", "#FFFFFF")])

        nb = ttk.Notebook(ventana, style="M6.TNotebook")
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        # --- TAB 1: Detalle por circuito ---
        tab_det = tk.Frame(nb, bg=COLORES["fondo"])
        nb.add(tab_det, text="📋  Detalle circuitos")

        cols_det = {
            "Circuito": 200, "Tipo_carga": 130,
            "Fd": 50, "P_inst(kW)": 90,
            "P_dem(kW)": 90, "S_dem(kVA)": 90
        }
        self._tabla_en_frame(tab_det, cols_det, [
            (d["nombre"], d["tipo_carga"], d["Fd"],
             d["P_inst_kw"], d["P_dem_kw"], d["S_dem_kva"])
            for d in r["detalle"]
        ])

        # --- TAB 2: Resumen ejecutivo ---
        tab_res = tk.Frame(nb, bg=COLORES["fondo"])
        nb.add(tab_res, text="📊  Resumen")

        filas_res = [
            ("Tipo instalación",  r["tipo_instalacion"].upper()),
            ("Demanda total",     f"{r['S_total_kva']} kVA  ({r['P_total_kw']} kW)"),
            ("Corriente alim.",   f"{r['I_alim_A']} A  ({r['sistema_alim']} / {r['Vn_alim']} V)"),
            ("Factor crecimiento",f"×{r['factor_crecimiento']}"),
            ("Demanda futura",    f"{r['S_futuro_kva']} kVA  →  {r['I_futuro_A']} A"),
        ]
        self._filas_info(tab_res, filas_res)

        # --- TAB 3: Transformador o SEC ---
        tab_dim = tk.Frame(nb, bg=COLORES["fondo"])
        tipo_alim = p.get("tipo_alimentador", "transformador")
        nb.add(tab_dim, text="🔌  Transformador" if tipo_alim == "transformador" else "🔌  Acometida SEC")

        if resultado_trafo:
            t = resultado_trafo
            color_t = (COLORES["falla"]     if "FALLA" in t["estado"] else
                       COLORES["precaucion"] if "PRECAUCIÓN" in t["estado"] else
                       COLORES["ok"])
            filas_t = [
                ("kVA mínimo requerido", f"{t['kVA_minimo']} kVA"),
                ("kVA seleccionado",     f"{t['kVA_seleccionado']} kVA  (estándar IEC 60076)"),
                ("Uso del transformador",f"{t['uso_pct']}%"),
                ("Estado",               t["estado"]),
                ("",                     ""),
                ("Transformador actual",
                 f"{self.datos_trafo['kVA']} kVA  →  "
                 f"{'SUFICIENTE' if self.datos_trafo['kVA'] >= t['kVA_minimo'] else 'INSUFICIENTE para demanda futura'}"
                 if self.datos_trafo else "—"),
            ]
            self._filas_info(tab_dim, filas_t, color_estado=color_t)

        elif resultado_sec:
            s = resultado_sec
            filas_s = [
                ("Corriente alimentador", f"{s['I_alim_A']} A"),
                ("Icc empalme SEC",       f"{s['Icc_kA']} kA  (zona {s['zona']})"),
                ("Protección mínima",     f"{s['I_prot_min_A']} A  (125% I_alim — RIC N°03)"),
                ("Nota",                  s["nota"]),
            ]
            self._filas_info(tab_dim, filas_s)

        # Botón cerrar
        tk.Frame(ventana, bg=COLORES["borde"],
                 height=1).pack(fill="x", padx=16, pady=6)
        self._boton(ventana, "✗  Cerrar", ventana.destroy,
                    color=COLORES["encabezado"]).pack(pady=8)

    def _tabla_en_frame(self, parent, columnas, datos):
        """Crea Treeview dentro de un frame."""
        frame = tk.Frame(parent, bg=COLORES["fondo"])
        frame.pack(fill="both", expand=True, padx=16, pady=8)

        style = ttk.Style()
        style.configure("M6.Treeview",
            background=COLORES["fila_par"],
            foreground=COLORES["texto"],
            fieldbackground=COLORES["fila_par"],
            font=FUENTES["mono"], rowheight=22)
        style.configure("M6.Treeview.Heading",
            background=COLORES["encabezado"],
            foreground=COLORES["texto"],
            font=FUENTES["subtitulo"], relief="flat")

        tree = ttk.Treeview(frame,
            columns=list(columnas.keys()),
            show="headings", style="M6.Treeview")
        for col, ancho in columnas.items():
            tree.heading(col, text=col)
            tree.column(col, width=ancho, anchor="center")
        tree.tag_configure("par",  background=COLORES["fila_par"])
        tree.tag_configure("impar",background=COLORES["fila_impar"])

        for i, fila in enumerate(datos):
            tree.insert("", "end", values=fila,
                        tags=("impar" if i % 2 else "par",))

        scroll_x = ttk.Scrollbar(frame, orient="horizontal",
                                  command=tree.xview)
        tree.configure(xscrollcommand=scroll_x.set)
        tree.pack(fill="both", expand=True)
        scroll_x.pack(fill="x")

    def _filas_info(self, parent, filas, color_estado=None):
        """Muestra pares campo/valor como filas estilizadas."""
        for i, (campo, valor) in enumerate(filas):
            if not campo:
                tk.Frame(parent, bg=COLORES["borde"],
                         height=1).pack(fill="x", padx=16, pady=4)
                continue
            f = tk.Frame(parent,
                         bg=COLORES["fila_impar"] if i % 2 else COLORES["fila_par"])
            f.pack(fill="x", padx=16, pady=1)
            tk.Label(f, text=f"  {campo}", width=22, anchor="w",
                     bg=f["bg"], fg=COLORES["texto_gris"],
                     font=FUENTES["pequeño"]).pack(side="left", pady=5)
            # Color especial para fila Estado
            color_val = (color_estado if campo == "Estado" and color_estado
                         else COLORES["texto"])
            tk.Label(f, text=valor, anchor="w",
                     bg=f["bg"], fg=color_val,
                     font=FUENTES["normal"]).pack(side="left", pady=5)


    def _abrir_ventana_coordinacion(self):
        """
        Abre ventana separada con resultados de coordinación TCC M7.
        Patrón idéntico a _abrir_ventana_demanda — Toplevel no modal.
        """
        if not self.resultados_m7:
            return

        ventana = tk.Toplevel(self.root)
        ventana.title(f"Coordinación TCC M7 — {self.nombre_proyecto.get()}")
        ventana.geometry("900x640")
        ventana.configure(bg=COLORES["fondo"])
        ventana.resizable(True, True)

        x = self.root.winfo_x() + (self.root.winfo_width()  - 900) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 640) // 2
        ventana.geometry(f"900x640+{x}+{y}")

        # Título
        tk.Label(
            ventana,
            text="COORDINACIÓN TCC — M7",
            bg=COLORES["fondo"], fg=COLORES["acento"],
            font=FUENTES["titulo"], pady=10
        ).pack(fill="x")
        tk.Label(
            ventana,
            text="Normativa: IEC 60947-2 / IEC 60898-1 / IEC 60364-4-41  |  "
                 "Limitación: región térmica ETU no modelada → usar SIMARIS",
            bg=COLORES["fondo"], fg=COLORES["texto_gris"],
            font=FUENTES["pequeño"]
        ).pack()
        tk.Frame(ventana, bg=COLORES["borde"],
                 height=1).pack(fill="x", padx=16, pady=6)

        # Notebook por modo
        style = ttk.Style()
        style.configure("M7.TNotebook",
                         background=COLORES["fondo"], borderwidth=0)
        style.configure("M7.TNotebook.Tab",
                         background=COLORES["panel"],
                         foreground=COLORES["texto_gris"],
                         font=FUENTES["pequeño"], padding=[12, 5])
        style.map("M7.TNotebook.Tab",
                  background=[("selected", COLORES["acento"])],
                  foreground=[("selected", "#FFFFFF")])

        nb = ttk.Notebook(ventana, style="M7.TNotebook")
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        for modo, resultado in self.resultados_m7.items():
            tab = tk.Frame(nb, bg=COLORES["fondo"])
            icono = "🔌" if modo == "red" else "⚡"
            nb.add(tab, text=f"{icono}  Modo {modo.capitalize()}")
            self._construir_tab_coordinacion(tab, resultado, modo)

        # Botón cerrar
        tk.Frame(ventana, bg=COLORES["borde"],
                 height=1).pack(fill="x", padx=16, pady=6)
        self._boton(ventana, "✗  Cerrar", ventana.destroy,
                    color=COLORES["encabezado"]).pack(pady=8)

    def _construir_tab_coordinacion(self, parent, resultado, modo):
        """Construye el contenido de un tab de coordinación."""

        # --- Resumen global ---
        sel = resultado["selectividad_global"]
        iec = resultado["iec60364_final"]
        color_sel = (COLORES["ok"]        if sel == "TOTAL" else
                     COLORES["precaucion"] if sel in ("PARCIAL","INDETERMINADA") else
                     COLORES["falla"])
        color_iec = (COLORES["ok"]   if iec["cumple"] == True else
                     COLORES["falla"] if iec["cumple"] == False else
                     COLORES["precaucion"])

        frame_res = tk.Frame(parent, bg=COLORES["panel"])
        frame_res.pack(fill="x", padx=16, pady=8)

        tk.Label(frame_res,
                 text=f"  Selectividad global: {sel}",
                 bg=COLORES["panel"], fg=color_sel,
                 font=FUENTES["subtitulo"], anchor="w"
                 ).pack(side="left", padx=8, pady=6)
        tk.Label(frame_res,
                 text=f"  IEC 60364-4-41: {iec['estado']}  ({iec['nota']})",
                 bg=COLORES["panel"], fg=color_iec,
                 font=FUENTES["pequeño"], anchor="w"
                 ).pack(side="left", padx=8, pady=6)

        # --- Tabla tiempos de disparo ---
        tk.Label(parent, text="  Tiempos de disparo",
                 bg=COLORES["fondo"], fg=COLORES["texto_gris"],
                 font=FUENTES["pequeño"], anchor="w"
                 ).pack(fill="x", padx=16, pady=(8, 2))

        cols_disp = {
            "Dispositivo": 180, "Nivel": 55,
            "t_disparo(s)": 100, "Región": 160, "Nota": 350
        }
        filas_disp = []
        for d in resultado["resultados_disparo"]:
            t_str = f"{d['t_s']:.3f}" if d["t_s"] is not None else "—"
            filas_disp.append((
                d["nombre"], d["nivel"], t_str,
                d["region"], d["nota"]
            ))
        self._tabla_en_frame(parent, cols_disp, filas_disp)

        # --- Tabla selectividad por par ---
        tk.Label(parent, text="  Selectividad por par",
                 bg=COLORES["fondo"], fg=COLORES["texto_gris"],
                 font=FUENTES["pequeño"], anchor="w"
                 ).pack(fill="x", padx=16, pady=(8, 2))

        cols_par = {
            "Inferior": 160, "Superior": 160,
            "Selectividad": 120, "Nota": 380
        }
        filas_par = []
        for p in resultado["selectividad_pares"]:
            filas_par.append((
                p["inferior"], p["superior"],
                p["selectividad"], p["nota"]
            ))
        self._tabla_en_frame(parent, cols_par, filas_par)

    def _set_estado(self, texto):
        self.estado_texto.set(texto)

# ============================================================
# PUNTO DE ENTRADA
# ============================================================

def main():
    root = tk.Tk()
    app = MotorCalculoBT(root)
    root.mainloop()

if __name__ == "__main__":
    main()