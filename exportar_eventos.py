import csv
import json
from datetime import datetime

from persistencia import obtener_ejecuciones


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
        "OBSERVACIONES": "EN_REVISION",
        "ERROR": "BLOQUEADO",
    }
    estado = estado_map.get(status, "EN_REVISION")

    if n_fallas > 0:
        observaciones = f"{n_fallas} circuito(s) en falla"
    elif status == "OK":
        observaciones = "sin observaciones"
    else:
        observaciones = "revisión técnica requerida"

    return {
        "run_id": run.get("run_id"),
        "project_id": run.get("project_id"),
        "revision": run.get("revision"),
        "timestamp": run.get("timestamp"),
        "event_type": event_type,
        "estado": estado,
        "disciplina": "ELC",
        "WBS_ID": None,
        "ITEM_ID": None,
        "observaciones": observaciones,
    }


def exportar_json(ruta_salida: str, ruta_db: str = "motor_bt.db") -> None:
    runs = obtener_ejecuciones(ruta_db=ruta_db)
    eventos = [derivar_evento(run) for run in runs]
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(eventos, f, ensure_ascii=False, indent=2)


def exportar_csv(ruta_salida: str, ruta_db: str = "motor_bt.db") -> None:
    runs = obtener_ejecuciones(ruta_db=ruta_db)
    eventos = [derivar_evento(run) for run in runs]
    campos = [
        "run_id", "project_id", "revision", "timestamp",
        "event_type", "estado", "disciplina",
        "WBS_ID", "ITEM_ID", "observaciones",
    ]
    with open(ruta_salida, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(eventos)


if __name__ == "__main__":
    marca = datetime.now().strftime("%Y%m%d_%H%M")
    archivo_json = f"eventos_{marca}.json"
    archivo_csv = f"eventos_{marca}.csv"
    exportar_json(archivo_json)
    exportar_csv(archivo_csv)
    print(f"JSON generado: {archivo_json}")
    print(f"CSV generado: {archivo_csv}")
