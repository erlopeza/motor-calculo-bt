"""
GUI M8 - Ventana de calculo de arranque de motores.
Toplevel no modal. Consume src/arranque_motores.py.
"""
import tkinter as tk
from tkinter import ttk

from src.arranque_motores import calcular_arranque_completo


# Paleta oscuro industrial
BG_MAIN = "#1a1a1a"
BG_PANEL = "#242424"
FG_TEXT = "#d0d0d0"
FG_LABEL = "#00CC44"
FG_VALOR = "#FFFFFF"
FG_ERROR = "#FF4444"
FG_WARNING = "#FFAA00"
FG_SUCCESS = "#00FF66"
BORDE = "#333333"
FONT_MAIN = ("Consolas", 10)
FONT_TITLE = ("Consolas", 13, "bold")
FONT_LABEL = ("Consolas", 9)


class ArranqueWindow(tk.Toplevel):
    """
    Ventana Toplevel no modal para calculo de arranque de motores.
    No usa grab_set(). Se abre desde la ventana principal.
    """

    def __init__(self, parent):
        """
        Inicializa la ventana con formulario y panel de resultados.
        parent: ventana tkinter padre.
        """
        super().__init__(parent)
        self.title("Arranque de Motores - Motor BT")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self._construir_ui()

    def _construir_ui(self):
        """Construye el formulario de entrada y el panel de resultados."""
        contenedor = tk.Frame(self, bg=BG_MAIN, padx=18, pady=16)
        contenedor.pack(fill="both", expand=True)

        tk.Label(
            contenedor,
            text="M8 - ARRANQUE DE MOTORES",
            bg=BG_MAIN,
            fg=FG_LABEL,
            font=FONT_TITLE,
        ).pack(anchor="w", pady=(0, 12))

        frame_inputs = tk.Frame(
            contenedor,
            bg=BG_PANEL,
            highlightbackground=BORDE,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        frame_inputs.pack(fill="x")

        self._entry_potencia = self._crear_fila_input(frame_inputs, "Potencia (kW)", "")
        self._entry_tension = self._crear_fila_input(frame_inputs, "Tension (V)", "380")
        self._entry_fp = self._crear_fila_input(frame_inputs, "Factor de potencia", "0.85")
        self._entry_rend = self._crear_fila_input(frame_inputs, "Rendimiento (eta)", "0.92")
        self._entry_factor_ia = self._crear_fila_input(frame_inputs, "Factor Ia (Ia/In)", "6.0")

        tk.Button(
            contenedor,
            text="CALCULAR",
            command=self._calcular,
            bg=FG_LABEL,
            fg=BG_MAIN,
            activebackground=FG_SUCCESS,
            activeforeground=BG_MAIN,
            font=FONT_MAIN,
            relief="flat",
            bd=0,
            padx=10,
            pady=7,
            cursor="hand2",
        ).pack(fill="x", pady=12)

        self._frame_resultados = tk.Frame(
            contenedor,
            bg=BG_PANEL,
            highlightbackground=BORDE,
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        self._frame_resultados.pack(fill="x")

    def _calcular(self):
        """
        Lee entradas, llama a calcular_arranque_completo(),
        muestra resultados o error dentro de la ventana.
        """
        try:
            potencia_kw = float(self._entry_potencia.get())
            tension_v = float(self._entry_tension.get())
            fp = float(self._entry_fp.get())
            rendimiento = float(self._entry_rend.get())
            factor_ia = float(self._entry_factor_ia.get())
            resultado = calcular_arranque_completo(
                potencia_kw,
                tension_v,
                fp,
                rendimiento,
                factor_ia,
            )
        except ValueError as error:
            self._mostrar_error(str(error))
            return

        self._mostrar_resultados(resultado)

    def _mostrar_resultados(self, resultado: dict):
        """
        Puebla el frame de resultados con los valores calculados.
        Limpia resultados anteriores antes de poblar.
        """
        self._limpiar_resultados()
        metodo = resultado["metodo"]
        guardamotor = resultado["guardamotor"]
        filas = [
            ("In (A)", f"{resultado['in_a']:.2f}"),
            ("Ia arranque (A)", f"{resultado['ia_arranque_a']:.2f}"),
            ("Metodo", metodo["metodo"]),
            ("Justificacion", metodo["justificacion"]),
            ("Reduccion corriente", f"{metodo['reduccion_corriente_pct']:.2f} %"),
            ("Guardamotor rango", f"{guardamotor['rango_min']:.2f} - {guardamotor['rango_max']:.2f} A"),
            ("Ajuste recomendado", f"{guardamotor['ajuste_recomendado']:.2f} A"),
        ]

        for etiqueta, valor in filas:
            self._crear_fila_resultado(etiqueta, valor)

    def _mostrar_error(self, mensaje: str):
        """
        Limpia resultados y muestra mensaje de error en FG_ERROR
        dentro del frame de resultados.
        """
        self._limpiar_resultados()
        tk.Label(
            self._frame_resultados,
            text=mensaje,
            bg=BG_PANEL,
            fg=FG_ERROR,
            font=FONT_MAIN,
            wraplength=360,
            justify="left",
        ).pack(anchor="w")

    def _crear_fila_input(self, parent, etiqueta: str, valor_default: str):
        """Crea una fila Label + Entry y retorna el Entry."""
        fila = tk.Frame(parent, bg=BG_PANEL)
        fila.pack(fill="x", pady=4)
        tk.Label(
            fila,
            text=etiqueta,
            bg=BG_PANEL,
            fg=FG_LABEL,
            font=FONT_LABEL,
            width=24,
            anchor="w",
        ).pack(side="left")
        entry = tk.Entry(
            fila,
            bg=BG_MAIN,
            fg=FG_TEXT,
            insertbackground=FG_SUCCESS,
            relief="flat",
            font=FONT_MAIN,
            width=16,
        )
        entry.insert(0, valor_default)
        entry.pack(side="right")
        return entry

    def _crear_fila_resultado(self, etiqueta: str, valor: str):
        """Crea una fila de resultado con etiqueta y valor."""
        fila = tk.Frame(self._frame_resultados, bg=BG_PANEL)
        fila.pack(fill="x", pady=3)
        tk.Label(
            fila,
            text=etiqueta,
            bg=BG_PANEL,
            fg=FG_LABEL,
            font=FONT_LABEL,
            anchor="w",
            width=22,
        ).pack(side="left")
        tk.Label(
            fila,
            text=valor,
            bg=BG_PANEL,
            fg=FG_SUCCESS if etiqueta == "Metodo" else FG_VALOR,
            font=FONT_MAIN,
            anchor="w",
            justify="left",
            wraplength=250,
        ).pack(side="left", fill="x", expand=True)

    def _limpiar_resultados(self):
        """Elimina widgets anteriores del frame de resultados."""
        for widget in self._frame_resultados.winfo_children():
            widget.destroy()
