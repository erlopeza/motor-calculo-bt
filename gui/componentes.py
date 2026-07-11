"""Componentes Tkinter reutilizables, estilizados con la paleta Tokyo Night."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui_core.estado import COLORES, Estado, color_de_estado
from gui_core.fases import FASES, estado_fase, estado_modulo, PRESENTADOR

_ETIQUETA = {
    Estado.SIN_DATOS: "sin datos",
    Estado.LISTO: "listo",
    Estado.CALCULADO: "calculado",
    Estado.ALERTA: "alerta",
}


class BadgeEstado(tk.Label):
    """Punto + etiqueta de estado, coloreado."""

    def __init__(self, master, estado: Estado):
        super().__init__(master)
        self.set_estado(estado)

    def set_estado(self, estado: Estado) -> None:
        self.color = color_de_estado(estado)
        self.configure(text=f"● {_ETIQUETA[estado]}", fg=self.color,
                       bg=COLORES["panel"], font=("Segoe UI", 9))


class BotonAccion(tk.Button):
    """Botón azul relleno; gris cuando se deshabilita."""

    def __init__(self, master, texto: str, comando):
        super().__init__(
            master, text=texto, command=comando,
            bg=COLORES["acento"], fg=COLORES["fondo"], relief="flat",
            activebackground=COLORES["acento"], activeforeground=COLORES["fondo"],
            disabledforeground=COLORES["texto_tenue"],
            font=("Segoe UI", 10, "bold"),
            padx=14, pady=6, cursor="hand2", bd=0,
        )

    def set_habilitado(self, habilitado: bool) -> None:
        if habilitado:
            self.configure(state="normal", bg=COLORES["acento"], fg=COLORES["fondo"])
        else:
            self.configure(state="disabled", bg=COLORES["borde"], fg=COLORES["texto_tenue"])


class TablaResultados(tk.Frame):
    """Tabla ttk.Treeview con encabezado Tokyo Night."""

    def __init__(self, master, columnas: list[str]):
        super().__init__(master, bg=COLORES["fondo"])
        self.columnas = columnas

        style = ttk.Style(self)
        # "clam" honra background/foreground de ttk.Style; el tema nativo de Windows
        # ("vista") renderiza heading y fieldbackground via UxTheme e ignora estos colores.
        style.theme_use("clam")
        style.configure("TokyoNight.Treeview",
                        background=COLORES["panel"], fieldbackground=COLORES["panel"],
                        foreground=COLORES["texto"], borderwidth=0)
        style.configure("TokyoNight.Treeview.Heading",
                        background=COLORES["seleccion"], foreground=COLORES["texto"],
                        relief="flat")
        style.map("TokyoNight.Treeview",
                  background=[("selected", COLORES["seleccion"])],
                  foreground=[("selected", COLORES["texto"])])

        self.tree = ttk.Treeview(self, columns=columnas, show="headings", height=8,
                                  style="TokyoNight.Treeview")
        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=110)
        self.tree.pack(fill="both", expand=True)

    def set_filas(self, filas: list[list]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for fila in filas:
            self.tree.insert("", "end", values=fila)

    def num_filas(self) -> int:
        return len(self.tree.get_children())


class RielFases(tk.Frame):
    """Lista vertical de las 7 fases con badge de estado; notifica selección."""

    def __init__(self, master, sesion, on_seleccion):
        super().__init__(master, bg=COLORES["panel"], width=200)
        self.pack_propagate(False)
        self.sesion = sesion
        self.on_seleccion = on_seleccion
        self.items: dict[int, tk.Frame] = {}
        self._puntos: dict[int, tk.Label] = {}
        for n, nombre in FASES.items():
            fila = tk.Frame(self, bg=COLORES["panel"], cursor="hand2")
            fila.pack(fill="x")
            punto = tk.Label(fila, text="●", bg=COLORES["panel"], fg=COLORES["texto_tenue"])
            punto.pack(side="left", padx=(12, 8), pady=6)
            lbl = tk.Label(fila, text=f"{n} · {nombre}", bg=COLORES["panel"],
                           fg=COLORES["texto"], font=("Segoe UI", 10), anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            for w in (fila, punto, lbl):
                w.bind("<Button-1>", lambda e, k=n: self.seleccionar(k))
            self.items[n] = fila
            self._puntos[n] = punto
        self.refrescar()

    def seleccionar(self, fase: int) -> None:
        for n, fila in self.items.items():
            bg = COLORES["seleccion"] if n == fase else COLORES["panel"]
            fila.configure(bg=bg)
            for hijo in fila.winfo_children():
                hijo.configure(bg=bg)
        self.on_seleccion(fase)

    def refrescar(self) -> None:
        for n, punto in self._puntos.items():
            punto.configure(fg=color_de_estado(estado_fase(n, self.sesion)))


class BarraSuperior(tk.Frame):
    """Barra superior: proyecto · perfil · [Cargar Excel] · estado."""

    def __init__(self, master, on_cargar):
        super().__init__(master, bg=COLORES["panel"], height=44)
        self.pack_propagate(False)
        self._proyecto = tk.StringVar(value="Proyecto: —")
        self._perfil = tk.StringVar(value="perfil: —")
        self._estado = tk.StringVar(value="")
        tk.Label(self, textvariable=self._proyecto, bg=COLORES["panel"],
                 fg=COLORES["texto"], font=("Segoe UI", 10, "bold")).pack(side="left", padx=12)
        tk.Label(self, textvariable=self._perfil, bg=COLORES["panel"],
                 fg=COLORES["texto_tenue"], font=("Segoe UI", 9)).pack(side="left")
        BotonAccion(self, "Cargar Excel", on_cargar).pack(side="right", padx=12, pady=6)
        self._lbl_estado = tk.Label(self, textvariable=self._estado, bg=COLORES["panel"],
                 fg=COLORES["ok"], font=("Segoe UI", 9))
        self._lbl_estado.pack(side="right", padx=8)

    def set_info(self, proyecto: str, perfil: str, estado: str, es_error: bool = False) -> None:
        self._proyecto.set(f"Proyecto: {proyecto}")
        self._perfil.set(f"perfil: {perfil}")
        self._estado.set(estado)
        self._lbl_estado.configure(fg=COLORES["alerta"] if es_error else COLORES["ok"])

    def texto_proyecto(self) -> str:
        return self._proyecto.get()


class PanelModulo(tk.Frame):
    """Anatomía uniforme: encabezado+norma+badge, aplicabilidad, acción, resultados."""

    def __init__(self, master, modulo, sesion, on_calcular):
        super().__init__(master, bg=COLORES["fondo"], padx=16, pady=12)
        self.modulo = modulo
        self.sesion = sesion

        cab = tk.Frame(self, bg=COLORES["fondo"]); cab.pack(fill="x")
        self._titulo = tk.Label(cab, text=modulo.nombre, bg=COLORES["fondo"],
                                fg=COLORES["texto"], font=("Segoe UI", 13, "bold"))
        self._titulo.pack(side="left")
        self._norma = tk.Label(cab, text=modulo.norma, bg=COLORES["fondo"],
                               fg=COLORES["texto_tenue"], font=("Segoe UI", 9))
        self._norma.pack(side="left", padx=10)
        self.badge = BadgeEstado(cab, estado_modulo(modulo, sesion))
        self.badge.configure(bg=COLORES["fondo"])
        self.badge.pack(side="right")

        tk.Label(self, text=f"Requiere: {modulo.requiere}", bg=COLORES["fondo"],
                 fg=COLORES["texto_tenue"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 8))

        self.boton = BotonAccion(self, "Calcular", lambda: on_calcular(modulo.id))
        self.boton.pack(anchor="w")
        habilitado = modulo.prereq(sesion) and modulo.id in PRESENTADOR
        self.boton.set_habilitado(habilitado)

        self.contenedor_resultados = tk.Frame(self, bg=COLORES["fondo"])
        self.contenedor_resultados.pack(fill="both", expand=True, pady=(10, 0))

    def titulo_texto(self) -> str:
        return self._titulo.cget("text")

    def norma_texto(self) -> str:
        return self._norma.cget("text")

    def refrescar_estado(self) -> None:
        self.badge.set_estado(estado_modulo(self.modulo, self.sesion))
        self.badge.configure(bg=COLORES["fondo"])
        habilitado = self.modulo.prereq(self.sesion) and self.modulo.id in PRESENTADOR
        self.boton.set_habilitado(habilitado)

    def mostrar_tabla(self, columnas: list[str], filas: list[list]) -> None:
        for w in self.contenedor_resultados.winfo_children():
            w.destroy()
        tabla = TablaResultados(self.contenedor_resultados, columnas)
        tabla.configure(bg=COLORES["fondo"])
        tabla.set_filas(filas)
        tabla.pack(fill="both", expand=True)
