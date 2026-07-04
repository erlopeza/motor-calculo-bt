# Diseño — Rediseño de GUI: flujo por fases SEC + Tokyo Night

**Fecha:** 2026-06-24 · **Rama:** `main` (se creará rama de trabajo) · **Estado:** aprobado para plan
**Ámbito:** GUI de escritorio del Motor de Cálculo BT. UI de dashboard (`dashboard.py` Streamlit) fuera de alcance.

---

## 1. Objetivo

Rediseñar la GUI Tkinter existente para que **comunique cómo y cuándo se aplica cada módulo** del motor, exponga las capacidades nuevas (Arc Flash, TCC, coordinación, flujo nodal, aporte de motores) que hoy no tienen superficie, y unifique la experiencia con un sistema visual coherente (paleta Tokyo Night). Evolución, no reescritura ni cambio de framework.

**Decisiones marco (aprobadas en brainstorming):**
1. **Framework:** seguir en Tkinter (sin dependencias nuevas), evolucionando el `MotorCalculoBT` actual.
2. **Navegación:** flujo por **fases del proceso SEC** (no tabs planos, no wizard rígido).
3. **Guía:** **blanda navegable** — el usuario entra a cualquier fase; cada fase/módulo muestra su estado y avisa prerrequisitos faltantes, sin bloquear.
4. **Paleta:** Tokyo Night.

## 2. Arquitectura y shell (Sección A)

Ventana única reorganizada:

```
┌───────────────────────────────────────────────────────────┐
│  BarraSuperior: proyecto · perfil · [Cargar Excel] · estado  │
├──────────────┬────────────────────────────────────────────┤
│  RielFases    │   Área de contenido (fase seleccionada)     │
│  (7 fases +   │   PanelModulo × N (los módulos de la fase)  │
│   badges)     │                                             │
└──────────────┴────────────────────────────────────────────┘
```

- **RielFases** (izquierda): las 7 fases, cada una con `BadgeEstado`. Reemplaza los tabs planos.
- **Área de contenido**: los `PanelModulo` de la fase activa.
- **`SesionProyecto`**: objeto de estado único que guarda datos cargados + resultados calculados. El estado de cada fase/módulo se **deriva** de él. Única fuente de verdad, desacoplada de los widgets (testeable sin abrir ventanas).
- **Sub-ventanas actuales** (`arranque`, `emergencia`, `guiada`, `reporte`) se **absorben** como paneles dentro de sus fases (5 y 6); se eliminan los `Toplevel` dispersos.

### Separación lógica/vista (para testabilidad)
- **Modelo:** `SesionProyecto` (datos + resultados + derivación de estado + chequeo de prerrequisitos). Pura, sin Tkinter.
- **Presentadores:** una clase por módulo que toma entradas de UI, llama a la función del motor correspondiente y devuelve resultados estructurados. Sin Tkinter.
- **Vistas:** widgets Tkinter delgados que renderizan modelo/presentador.

## 3. Modelo de estado y anatomía de módulo (Sección B)

**4 estados** (derivados de `SesionProyecto`), con color Tokyo Night:

| Estado | Color | Significado |
|---|---|---|
| sin datos | `#565f89` | faltan prerrequisitos o entrada no cargada |
| listo | `#7aa2f7` | prerrequisitos presentes, aún no calculado |
| calculado | `#9ece6a` | ejecutado sin hallazgos |
| alerta | `#f7768e` / `#ff9e64` | calculado con hallazgos (ΔV falla, no dispara, Cat EPP alta, no converge) |

**Anatomía uniforme del `PanelModulo`:**
1. Encabezado: nombre + **norma de referencia** + `BadgeEstado`.
2. Aplicabilidad (el "cuándo"): línea "Requiere: …"; si falta algo, se indica en gris.
3. Entradas/parámetros: campos con defaults normativos, o "usa datos cargados".
4. Acción: `BotonAccion` [Calcular], deshabilitado si faltan prereqs (tooltip explica).
5. Resultados: `TablaResultados`/fichas; filas coloreadas por estado.
6. Trazabilidad: nota de norma/supuestos al pie.

## 4. Sistema visual Tokyo Night (Sección C)

**Paleta → roles** (constante `COLORES` reescrita):

| Rol | Hex |
|---|---|
| fondo | `#1a1b26` |
| panel/riel | `#16161e` |
| selección/encabezado | `#292e42` |
| borde | `#3b4261` |
| texto | `#c0caf5` |
| texto tenue | `#565f89` |
| acento / listo | `#7aa2f7` |
| ok / calculado | `#9ece6a` |
| alerta | `#f7768e` |
| precaución | `#ff9e64` |
| dato normativo | `#e0af68` (amarillo) / `#bb9af7` (violeta) |

**Tipografía:** una sola familia sans del sistema; jerarquía por tamaño/peso (título módulo 15/500, norma 12, cuerpo 13, notas 11). Sentence case.

**Componentes reutilizables** (estilizados una vez):
`BadgeEstado`, `PanelModulo`, `BotonAccion`, `TablaResultados`, `RielFases`, `BarraSuperior`.

## 5. Inventario de módulos por fase (Sección D)

Cada módulo es un `PanelModulo` con norma y prerrequisitos. Fuente = módulo del motor existente (la GUI no recalcula, solo orquesta).

**0 · Datos** — `excel.py`: cargador de todas las hojas + reporte de hojas detectadas y validaciones por fila. *Prereq: —*

**1 · Cálculo base** — `calculos.py`, `sugerencias.py`:
- Caída de tensión ΔV. *Prereq: circuitos*
- Capacidad de conductor (I_max corregida vs I_diseño). *Prereq: circuitos*
- Sugerencia de sección mínima (opcional). *Prereq: circuitos*

**2 · Cortocircuito** — `transformador.py`, `icc_punto.py`, `motores.py`:
- Icc bornes trafo (modo A/B). *Prereq: trafo*
- Icc por punto + fase-neutro (R+jX). *Prereq: trafo + circuitos*
- Aporte de motores al Icc. *Prereq: Icc + motores*

**3 · Protección** — `protecciones.py`, `coordinacion.py`, `tcc_curvas.py`, `arc_flash.py`:
- Verificación de protecciones (disparo, poder de corte, tiempo IEC 60364-4-41). *Prereq: Icc + protecciones*
- Coordinación TCC / selectividad M7 (márgenes, back-up). *Prereq: cadena*
- Curvas TCC (catálogo tiempo-corriente). *Soporte*
- Arc Flash (energía, frontera, Cat EPP). *Prereq: Icc + protección*

**4 · Carga y red** — `balance.py`, `demanda.py`, `red_desde_cadena.py`+`flujo_nodal.py`:
- Balance por tablero (desequilibrio, uso trafo). *Prereq: circuitos + balance/tableros*
- Demanda máxima M6 (FD, dimensionamiento). *Prereq: circuitos + params demanda*
- Flujo de carga nodal (tensiones por barra, pérdidas). *Prereq: cadena + trafo*

**5 · Emergencia** — `generador.py`, `ats.py`, `trafo_iso.py`, `ups.py`, `sts.py`, `motores.py`:
- Grupo electrógeno + ATS + autonomía (RIC N°08). *Prereq: demanda/cargas*
- Transformador de aislamiento · UPS · STS. *Prereq: cargas*
- Arranque de motores (DOL/Y-Δ/VFD, caída en arranque). *Prereq: motores*

**6 · Reporte** — `reporteria_sec.py`:
- Gate de completitud (TIPO-A default → borrador/final). *Prereq: cálculos*
- Memoria DOCX + PDF + JSON EPC. *Prereq: cálculos*

## 6. Estrategia de pruebas (Sección E)

1. **`SesionProyecto` (unit, sin Tkinter):** carga de datos setea flags; derivación de estado por fase; chequeo de prerrequisitos por módulo.
2. **Presentadores (unit, sin Tkinter):** cada uno llama al motor correcto y arma resultados a partir de entradas.
3. **Smoke de render (headless-skip):** instanciar la app bajo `Tk()` oculto; se omite si no hay display (CI), como los tests GUI actuales.
4. **Constantes visuales:** `COLORES` contiene los hex Tokyo Night; el set de componentes existe.

Regla: toda decisión lógica es testeable sin display; los widgets son vistas delgadas. La suite completa (740+) se mantiene verde.

## 7. Fuera de alcance (YAGNI)

- Cambio de framework (Qt/web).
- `dashboard.py` (Streamlit) — se aborda por separado si se decide.
- Edición de datos dentro de la GUI (la entrada sigue siendo el Excel; la GUI orquesta y muestra).
- Persistencia de sesión entre corridas más allá de lo que ya hace `persistencia.py`.

## 8. Bug conocido a corregir en el camino

`gui.py:1034` referencia `undefined name 'e'` fuera de su `except` (detectado por pyflakes) — corregir al reescribir esa zona.

## 9. Decisiones registradas

1. Evolucionar Tkinter (sin deps nuevas).
2. Navegación por fases del proceso SEC (7 fases).
3. Guía blanda navegable con estado (no wizard rígido).
4. Paleta Tokyo Night mapeada a roles semánticos.
5. Estado único `SesionProyecto` con derivación; lógica desacoplada de widgets.
6. Sub-ventanas actuales absorbidas como paneles de fase.
7. La GUI orquesta el motor existente; no recalcula ni duplica lógica.
