"""
GUI Grupo 3 - Ventana para generar memoria explicativa.
Toplevel no modal. Consume src/generador_memoria.py.
"""
import threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog

from src.generador_memoria import generar_memoria


BG_MAIN = "#1a1a1a"
BG_PANEL = "#242424"
FG_TEXT = "#d0d0d0"
FG_LABEL = "#00CC44"
FG_VALOR = "#FFFFFF"
FG_ERROR = "#FF4444"
FG_SUCCESS = "#00FF66"
BORDE = "#333333"
FONT_MAIN = ("Consolas", 10)
FONT_TITLE = ("Consolas", 13, "bold")
FONT_LABEL = ("Consolas", 9)


class ReporteWindow(tk.Toplevel):
    """
    Ventana Toplevel no modal para generar memoria explicativa.
    Tiene formulario administrativo y resumen de datos de calculo.
    """

    def __init__(self, parent, datos_calculo: dict | None = None):
        """Inicializa la ventana con datos de calculo opcionales."""
        super().__init__(parent)
        self.datos_calculo = datos_calculo or {}
        self.title("Memoria Explicativa SEC - Motor BT")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self._construir_ui()

    def _construir_ui(self):
        """Construye formulario, resumen y botones."""
        contenedor = tk.Frame(self, bg=BG_MAIN, padx=18, pady=16)
        contenedor.pack(fill="both", expand=True)
        tk.Label(contenedor, text="G3 - MEMORIA EXPLICATIVA SEC", bg=BG_MAIN, fg=FG_LABEL, font=FONT_TITLE).pack(anchor="w", pady=(0, 12))

        cuerpo = tk.Frame(contenedor, bg=BG_MAIN)
        cuerpo.pack(fill="both")
        izquierdo = tk.Frame(cuerpo, bg=BG_PANEL, highlightbackground=BORDE, highlightthickness=1, padx=12, pady=10)
        izquierdo.pack(side="left", fill="both", padx=(0, 10))
        derecho = tk.Frame(cuerpo, bg=BG_PANEL, highlightbackground=BORDE, highlightthickness=1, padx=12, pady=10, width=260)
        derecho.pack(side="left", fill="both")
        derecho.pack_propagate(False)

        self._crear_formulario(izquierdo)
        self._crear_resumen(derecho)

        botones = tk.Frame(contenedor, bg=BG_MAIN)
        botones.pack(fill="x", pady=(12, 0))
        self._boton(botones, "GENERAR MEMORIA", self._generar).pack(side="left")
        self._boton(botones, "CANCELAR", self.destroy, color=BG_PANEL, fg=FG_TEXT).pack(side="left", padx=(8, 0))
        self._label_estado = tk.Label(contenedor, text="", bg=BG_MAIN, fg=FG_TEXT, font=FONT_MAIN, wraplength=640, justify="left")
        self._label_estado.pack(anchor="w", pady=(10, 0))

    def _crear_formulario(self, parent):
        """Crea campos de datos del proyecto."""
        tk.Label(parent, text="Datos del proyecto", bg=BG_PANEL, fg=FG_LABEL, font=FONT_LABEL).pack(anchor="w", pady=(0, 8))
        self._entry_nombre = self._entry(parent, "Nombre proyecto")
        self._entry_direccion = self._entry(parent, "Direccion")
        self._entry_comuna = self._entry(parent, "Comuna")
        self._entry_propietario = self._entry(parent, "Propietario")
        self._entry_rut = self._entry(parent, "RUT propietario")
        self._entry_instalador = self._entry(parent, "Instalador")
        self._entry_licencia = self._entry(parent, "Licencia SEC")
        self._clase_var = tk.StringVar(value="A")
        tk.OptionMenu(parent, self._clase_var, "A", "B").pack(anchor="w", fill="x", pady=3)
        self._entry_fecha = self._entry(parent, "Fecha AAAA-MM", datetime.now().strftime("%Y-%m"))
        self._entry_tierra = self._entry(parent, "Resist. tierra ohm", "25")
        tk.Label(parent, text="Descripcion obra", bg=BG_PANEL, fg=FG_LABEL, font=FONT_LABEL).pack(anchor="w", pady=(6, 2))
        self._text_descripcion = tk.Text(parent, height=3, width=44, bg=BG_MAIN, fg=FG_TEXT, insertbackground=FG_SUCCESS, relief="flat", font=FONT_MAIN)
        self._text_descripcion.pack(fill="x")

    def _crear_resumen(self, parent):
        """Muestra resumen de datos de calculo disponibles."""
        tk.Label(parent, text="Datos de calculo", bg=BG_PANEL, fg=FG_LABEL, font=FONT_LABEL).pack(anchor="w", pady=(0, 8))
        resumen = [
            f"Tension: {self.datos_calculo.get('tension_v', 'N/D')} V",
            f"Potencia: {self.datos_calculo.get('potencia_total_kw', 'N/D')} kW",
            f"Circuitos: {len(self.datos_calculo.get('circuitos', []))}",
            f"Alimentador: {'si' if self.datos_calculo.get('alimentador') else 'no'}",
            f"Emergencia: {'si' if self.datos_calculo.get('emergencia') else 'no'}",
            f"Arranque: {'si' if self.datos_calculo.get('arranque') else 'no'}",
        ]
        for linea in resumen:
            tk.Label(parent, text=linea, bg=BG_PANEL, fg=FG_VALOR, font=FONT_MAIN, anchor="w").pack(fill="x", pady=2)

    def _generar(self):
        """
        Valida campos obligatorios, pide ruta de salida y genera memoria en thread.
        No abre el archivo generado.
        """
        try:
            datos_proyecto = self._leer_datos_proyecto()
        except ValueError as error:
            self._set_estado(str(error), error=True)
            return
        faltantes = [campo for campo in ["nombre_proyecto", "direccion", "instalador", "licencia"] if not datos_proyecto.get(campo)]
        if faltantes:
            self._set_estado(f"Faltan campos obligatorios: {', '.join(faltantes)}", error=True)
            return
        if not self.datos_calculo.get("circuitos"):
            self._set_estado("No hay datos de calculo suficientes para generar memoria.", error=True)
            return

        ruta = filedialog.asksaveasfilename(parent=self, defaultextension=".docx", filetypes=[("Word", "*.docx")])
        if not ruta:
            return
        self._set_estado("Generando...")
        thread = threading.Thread(target=self._worker_generar, args=(datos_proyecto, ruta), daemon=True)
        thread.start()

    def _worker_generar(self, datos_proyecto, ruta):
        """Ejecuta generacion en segundo plano y actualiza estado."""
        resultado = generar_memoria(datos_proyecto, self.datos_calculo, ruta)
        self.after(0, self._mostrar_resultado_generacion, resultado)

    def _mostrar_resultado_generacion(self, resultado):
        """Muestra resultado final de generacion."""
        if resultado.get("ok"):
            self._set_estado(f"Generado en {resultado['ruta']}", error=False)
        else:
            self._set_estado(resultado.get("motivo", "Error generando memoria"), error=True)

    def _leer_datos_proyecto(self):
        """Lee campos del formulario y retorna dict de proyecto."""
        return {
            "nombre_proyecto": self._entry_nombre.get().strip(),
            "direccion": self._entry_direccion.get().strip(),
            "comuna": self._entry_comuna.get().strip(),
            "propietario": self._entry_propietario.get().strip(),
            "rut_propietario": self._entry_rut.get().strip(),
            "instalador": self._entry_instalador.get().strip(),
            "licencia": self._entry_licencia.get().strip(),
            "clase_licencia": self._clase_var.get(),
            "fecha": self._entry_fecha.get().strip(),
            "resistencia_tierra_ohm": self._leer_float(self._entry_tierra, "Resistencia de tierra"),
            "descripcion_obra": self._text_descripcion.get("1.0", tk.END).strip(),
        }

    def _leer_float(self, entry, nombre):
        """Lee un float desde Entry y levanta ValueError con contexto."""
        try:
            return float(entry.get() or 0)
        except ValueError as error:
            raise ValueError(f"{nombre} debe ser numerico") from error

    def _entry(self, parent, etiqueta, valor=""):
        """Crea fila de formulario con etiqueta y Entry."""
        fila = tk.Frame(parent, bg=BG_PANEL)
        fila.pack(fill="x", pady=3)
        tk.Label(fila, text=etiqueta, bg=BG_PANEL, fg=FG_LABEL, font=FONT_LABEL, width=20, anchor="w").pack(side="left")
        entry = tk.Entry(fila, bg=BG_MAIN, fg=FG_TEXT, insertbackground=FG_SUCCESS, relief="flat", font=FONT_MAIN, width=24)
        entry.insert(0, valor)
        entry.pack(side="left")
        return entry

    def _boton(self, parent, texto, comando, color=FG_LABEL, fg=BG_MAIN):
        """Crea boton del formulario de reporte."""
        return tk.Button(parent, text=texto, command=comando, bg=color, fg=fg, activebackground=FG_SUCCESS, activeforeground=BG_MAIN, relief="flat", bd=0, padx=10, pady=6, cursor="hand2", font=FONT_MAIN)

    def _set_estado(self, texto, error=False):
        """Actualiza label de estado con color de error o exito."""
        self._label_estado.config(text=texto, fg=FG_ERROR if error else FG_SUCCESS)
