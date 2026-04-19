import csv
import json
from datetime import datetime

from persistencia import obtener_ejecuciones, obtener_eventos, registrar_evento


def derivar_evento(run: dict) -> dict:
    status = run.get("status")
    n_fallas = run.get("n_fallas") or 0
    ruta_reporte_txt = run.get("ruta_reporte_txt")

    event_type = "CALCULO_BT"
    if n_fallas > 0:
        event_type = "ALERTA"
    if ruta_reporte_txt is not None:
        event_type = "REPORTE"

    estado_map = {
        "OK": "COMPLETADO",
        "CON_FALLAS": "EN_REVISION",
        "CON_ADVERTENCIAS": "EN_REVISION",
        "OBSERVACIONES": "EN_REVISION",
        "ERROR": "BLOQUEADO",
    }
    estado = estado_map.get(status, "EN_REVISION")

    if n_fallas > 0:
        observaciones = f"{n_fallas} circuito(s) en falla"
    elif status == "OK":
        observaciones = "sin observaciones"
    else:
        observaciones = "revision tecnica requerida"

    project_id = run.get("project_id")
    revision = run.get("revision")

    return {
        "run_id": run.get("run_id"),
        "project_id": project_id,
        "revision": revision,
        "timestamp": run.get("timestamp"),
        "event_type": event_type,
        "title": f"Calculo BT - {project_id} {revision}",
        "estado": estado,
        "disciplina": "ELC",
        "WBS_ID": None,
        "ITEM_ID": None,
        "frente_id": None,
        "description": run.get("observaciones") or observaciones,
        "observaciones": observaciones,
    }


def exportar_json(ruta_salida: str, ruta_db: str = "motor_bt.db") -> None:
    eventos = obtener_eventos(ruta_db=ruta_db)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(eventos, f, ensure_ascii=False, indent=2)


def exportar_csv(ruta_salida: str, ruta_db: str = "motor_bt.db") -> None:
    eventos = obtener_eventos(ruta_db=ruta_db)
    campos = [
        "event_id",
        "run_id",
        "project_id",
        "revision",
        "timestamp",
        "event_type",
        "title",
        "estado",
        "disciplina",
        "WBS_ID",
        "ITEM_ID",
        "frente_id",
        "description",
        "observaciones",
    ]
    with open(ruta_salida, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(eventos)


def persistir_eventos(ruta_db: str = "motor_bt.db") -> int:
    runs = obtener_ejecuciones(ruta_db=ruta_db)
    eventos = obtener_eventos(ruta_db=ruta_db)
    run_ids_con_evento = {evento.get("run_id") for evento in eventos}

    insertados = 0
    for run in runs:
        run_id = run.get("run_id")
        if run_id in run_ids_con_evento:
            continue

        evento = derivar_evento(run)
        event_id = registrar_evento(run_id, evento, ruta_db=ruta_db)
        if event_id:
            insertados += 1

    return insertados


if __name__ == "__main__":
    marca = datetime.now().strftime("%Y%m%d_%H%M")
    archivo_json = f"eventos_{marca}.json"
    archivo_csv = f"eventos_{marca}.csv"
    n = persistir_eventos()
    exportar_json(archivo_json)
    exportar_csv(archivo_csv)
    print(f"Eventos persistidos: {n}")
    print(f"JSON generado: {archivo_json}")
    print(f"CSV generado: {archivo_csv}")


