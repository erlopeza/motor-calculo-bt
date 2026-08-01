# Diseño — GUI Plan 3-A: render de resultados no tabulares

**Fecha:** 2026-07-12 · **Rama base:** `main` (se creará rama de trabajo) · **Estado:** aprobado para plan
**Ámbito:** capa visual `gui/` sobre el núcleo `gui_core` ya existente. NO toca `gui_core`, ni el motor, ni fase 5 (emergencia).

---

## 1. Objetivo

Cinco módulos de la GUI (`icc_trafo`, `balance`, `demanda`, `flujo_nodal`, `reporte`) ya calculan y registran resultado, pero al pulsar **Calcular** el panel solo cambia el badge: no muestra los valores. Esto rompe la usabilidad — el usuario no ve el Icc del transformador, el balance por tablero, la demanda, las tensiones por barra ni dónde quedó el reporte generado. Plan 3-A completa el render para que **todo módulo con presentador muestre su resultado en pantalla**.

Contexto verificado (2026-07-12): la GUI y el `.exe` empaquetado funcionan end-to-end; los 8 módulos tabulares (dv, capacidad, sugerencia, icc_punto, aporte_motores, protecciones, coordinacion, arc_flash) ya renderizan tabla vía `_COLUMNAS`. Este plan cubre el hueco de los 5 no tabulares.

## 2. Alcance (aprobado)

- **Dentro:** render de los 5 módulos no tabulares; botón "Abrir carpeta" para el reporte.
- **Fuera:** fase 5 (emergencia: generador/ats/ups/sts/trafo_iso/arranque) → plan aparte; edición de datos en la GUI; elección de carpeta de salida del reporte.

## 3. Enfoque

Extender el mecanismo de render existente, no reemplazarlo. Hoy `gui/app.py` tiene un dict `_COLUMNAS` (id → columnas + extractor de fila) y `PanelModulo.mostrar_tabla`. Se generaliza a un **registro de adaptadores** `RENDER[id] = fn(panel, resultado)` y `PanelModulo` gana dos primitivas nuevas. Alternativas descartadas: render "mágico" que introspecciona cualquier dict (impredecible); panel custom por módulo (rompe uniformidad, duplica estilo).

## 4. Componentes

### 4.1 `PanelModulo` (en `gui/componentes.py`) — primitivas nuevas, aditivas
- `mostrar_fichas(pares: list[tuple[str, str, str|None]])` — tarjetas clave-valor; cada par es `(etiqueta, valor, rol)` donde `rol ∈ {None, "ok", "alerta", "precaucion"}` decide el color del valor (desde `COLORES`). Etiqueta en `texto_tenue`.
- `agregar_accion(texto: str, comando) -> BotonAccion` — botón secundario bajo los resultados; reutiliza `BotonAccion`.
- `mostrar_tabla(columnas, filas)` se mantiene sin cambios.
- El `contenedor_resultados` apila en orden: fichas (resumen) → tabla (detalle) → acciones. Cada `ejecutar_modulo` limpia el contenedor antes de recomponer (ya lo hace `mostrar_tabla`; se extrae la limpieza a un paso previo común para no borrar entre fichas y tabla).

### 4.2 Registro de adaptadores (en `gui/app.py`) — reemplaza `_COLUMNAS`
`RENDER: dict[str, Callable[[PanelModulo, dict], None]]`. Cada adaptador recibe el panel y el `resultado` del presentador y llama a las primitivas. Migración de los 8 tabulares: adaptadores que solo llaman `mostrar_tabla(columnas, [extractor(f) for f in resultado["filas"]])` — sin cambio visible. Los 5 nuevos:

| Módulo | Render (formas reales verificadas) |
|---|---|
| `icc_trafo` | fichas: `Icc (kA)=Icc_kA`, `Zt (Ω)=Zt_ohm` |
| `flujo_nodal` | fichas resumen: `Convergió=convergido` (rol ok/alerta), `Pérdidas (kW)=perdidas_kW`; + tabla barras (`id`, `V_pu`, `V_kV`, `P_kW`) desde `buses` |
| `balance` | tabla por tablero (Tablero, S dem (kVA)=`S_total_kva`, Uso %=`uso_pct`, Deseq. %=`desequilibrio_pct`, Estado=`estado`) desde `resultado["tableros"]`; + ficha resumen trafo (`Uso trafo %=uso_trafo_pct`, `Estado=estado_trafo`) |
| `demanda` | fichas desde `resultado`: `P total (kW)=P_total_kw`, `S total (kVA)=S_total_kva`, `I alim (A)=I_alim_A`, `Factor crecimiento=factor_crecimiento`, `Tipo=tipo_instalacion` |
| `reporte` | fichas: `Nivel=nivel` (rol: FINAL→ok, BORRADOR→precaucion, INCOMPLETO→alerta), `DOCX/PDF/JSON=` nombre de archivo (basename, no ruta completa); + acción "Abrir carpeta" |

Reglas de robustez del adaptador: usar `.get(...)` con default y formateo seguro (redondeo de floats, `"—"` si falta); nunca lanzar por clave ausente (coherente con el resto de `gui/`).

### 4.3 Reporte — carpeta de salida
`AppBT` define `self.carpeta_reportes = os.path.join(os.getcwd(), "salida_reportes")`, la crea si falta antes de generar, y la pasa a `presentar_reporte(sesion, carpeta_salida=...)`. El botón "Abrir carpeta" hace `os.startfile(self.carpeta_reportes)` en Windows, envuelto en try/except (no-op con aviso en barra si el SO no lo soporta). La ruta se conoce siempre (no depende de lo que devuelva el presentador).

## 5. Flujo de datos

`ejecutar_modulo(id)` (sin cambios estructurales): llama `PRESENTADOR[id](sesion)` → `sesion.registrar(...)` → si `id in RENDER`, limpia el contenedor del panel correspondiente y llama `RENDER[id](panel, resultado)` → `refrescar_estado()` de todos los paneles → `riel.refrescar()`. El caso `reporte` sigue recibiendo `carpeta_salida` como hoy.

## 6. Manejo de errores

- Adaptadores tolerantes a claves faltantes (`.get` + defaults).
- El try/except ya presente en `ejecutar_modulo` (imprime traceback + muestra error en barra) cubre fallos del presentador; los adaptadores no deben lanzar, pero si lo hicieran, quedan bajo el mismo paraguas.
- "Abrir carpeta": try/except alrededor de `os.startfile`.

## 7. Estrategia de pruebas

1. **Componentes (headless-skip):** `mostrar_fichas` inserta N tarjetas; `agregar_accion` crea un botón invocable; apilado fichas+tabla no se pisan.
2. **Wiring (headless-skip):** para cada uno de los 5 módulos, tras cargar `circuitos.xlsx` y `ejecutar_modulo`, el `contenedor_resultados` del panel queda con ≥1 hijo (no vacío).
3. **Regresión:** los 8 tabulares siguen renderizando tabla; suite completa (766) verde.
4. **`gui_core` intacto:** sin cambios en su código ni en sus tests.

## 8. Decisiones registradas

1. Alcance solo A (los 5 no tabulares); fase 5 a plan aparte.
2. Reporte: mostrar rutas + nivel + botón "Abrir carpeta" (sin elección de carpeta).
3. Carpeta de salida fija `<cwd>/salida_reportes/`.
4. Registro de adaptadores `RENDER` reemplaza `_COLUMNAS`; `PanelModulo` gana `mostrar_fichas` + `agregar_accion`.
5. `gui_core` no se toca; colores solo desde `COLORES`; `gui/` importa `gui_core`, nunca al revés.
