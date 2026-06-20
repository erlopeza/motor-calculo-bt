# 02 — Git, commits y ramas

## Resumen

| Aspecto | Dato |
|---|---|
| Commits totales | 76 |
| Rango temporal | 2026-03-21 → 2026-05-09 (~7 semanas) |
| Ramas locales | `main` |
| Ramas remotas | `origin/main` |
| **Ramas activas adicionales** | **Ninguna** |
| Tags / releases | 0 |
| Remoto | `https://github.com/erlopeza/motor-calculo-bt.git` |
| Pull requests fusionados | 1 (PR #1, rama `codex/check-and-configure-remote-origin`) |
| Working tree (inicio) | limpio |

## Autoría

| Autor | Email | Commits |
|---|---|---|
| user007 | javierlopez.araya@gmail.com | 74 |
| erlopeza | javierlopez.araya@gmail.com | 2 |

🟡 **H-09 (parcial):** dos nombres de autor (`user007`, `erlopeza`) comparten el mismo email. Es la misma persona con dos configuraciones `user.name`. No es un problema de seguridad, pero ensucia `git shortlog`/blame. Recomendación: unificar `git config user.name`.

## Convención de commits

El historial es **trazable y descriptivo**, organizado por **módulos (M1–M12), grupos y ciclos**:

- Etapas tempranas: prosa en español por bloques (`Bloque 3:`, `Etapa 3 M2:`).
- Etapa media: adopción parcial de **Conventional Commits** (`feat:`, `fix:`, `chore:`, `test:`) — p. ej. `feat(A-8): keys MM2...`, `fix(A-7): validar conductor...`.
- Etapa reciente: vuelve a prosa por ciclos (`Ciclo 1 A-5 Icc fase-neutro IEC 60364-4-41`).

🟡 **Hallazgo (Bajo):** convención **inconsistente** (mezcla de Conventional Commits y prosa libre). No bloquea, pero dificulta el changelog automatizado. Recomendación: fijar un estilo (Conventional Commits) de aquí en adelante.

✅ **Fortaleza:** el patrón `chore: baseline pre-X` antes de cada módulo grande (M8, M9, GUI-M8, G3, FASE-F) es una **buena práctica** que crea puntos de retorno claros.

## Cobertura de mensajes vs. normativa

Los mensajes citan normas concretas (IEC 60364-4-41, IEC 60909, NCh 4-2003 12.28, RIC-N08, TIA-942), lo que da **trazabilidad normativa del cambio** — práctica destacable para un proyecto de ingeniería eléctrica.

## Recomendaciones

| Acción | Prioridad |
|---|---|
| Unificar `user.name` en git config | Baja |
| Adoptar Conventional Commits de forma consistente | Baja |
| Crear tags de release (`v1.0`, `v2.0`) para hitos | Media |
| Considerar ramas de feature en lugar de trabajar siempre sobre `main` | Media |
