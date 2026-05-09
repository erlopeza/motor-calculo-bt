---
tipo: decision-arquitectural
area: python
proyecto: motor-calculo-bt
tags: [ciclo-0, blindaje, parametrico, usa_defaults, presets, stamford]
fecha: 2026-05-08
estado: cerrado
commit: ver hash del commit que contiene esta nota
tests: 437 passed -> 441 passed / 5 skipped / 0 failed
---

# Ciclo 0 — Blindaje Paramétrico del Motor Universal

## Regla oficial

Ningún fabricante, modelo comercial, datasheet o marca puede ser
fundamento del motor de cálculo.

Los datos de fabricante solo pueden existir como:
1. entrada del usuario
2. preset trazable (presets/)
3. fixture de validación (tests/)
4. catálogo externo opcional

Nunca como constante obligatoria del núcleo de cálculo.

## Cambios ejecutados

| Brief | Módulo | Cambio |
|---|---|---|
| 0-AUDIT | — | inventario 4 módulos, 85 constantes clasificadas |
| 0-B | generador.py | Stamford -> presets/, usa_defaults propagado |
| 0-C | ats.py | elimina duplicación, importa generador.calcular_icc_ge |
| 0-D | ups.py | usa_defaults + defaults_aplicados |
| 0-E | motores.py | usa_defaults + defaults_aplicados + factor_arranque_efectivo |
| 0-F | suite | tests anti-hardcode globales |

## Estructura presets

```text
presets/
    alternadores/
        stamford_hci544d.py  <- único preset de alternador actualmente
```

## Patrón usa_defaults

Todos los módulos del ciclo retornan:

```python
"usa_defaults": bool
"defaults_aplicados": list[str]
```

Regla: si `usa_defaults=True`, el resultado debe revisarse contra
parámetros reales del equipo antes de usar en memoria SEC.

## Deuda técnica registrada

| ID | Descripción | Prioridad |
|---|---|---|
| DT-C0-01 | `_curve_multiplier` duplicado en generador/ats/motores | baja |
| DT-C0-02 | `FACTOR_TEMP_BAT` en ups.py sin cita normativa | baja |
| DT-C0-03 | derrateo altitud en generador.py sin cita normativa | baja |
| DT-C0-04 | arranque_motores.py no propaga usa_defaults (API GUI simplificada) | baja |
| DT-C0-05 | sugerencias.py, coordinacion.py y simulaciones/analizador.py mantienen referencias comerciales como fuente/limitación, fuera del alcance de módulos blindados | media |

## Próximo ciclo

Ciclo 1 — Normativa base:

```text
A-3 ΔV acumulada alimentador + circuito
A-4 Fd alumbrado real RIC N°03 Tabla N°3
A-5 Icc fase-neutro mínima IEC 60364-4-41
```
