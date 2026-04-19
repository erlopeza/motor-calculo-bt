import pandas as pd
import streamlit as st

from persistencia import obtener_ejecuciones


def _normalizar_dataframe(ruta_db: str = "motor_bt.db") -> pd.DataFrame:
    runs = obtener_ejecuciones(ruta_db=ruta_db)
    if not runs:
        return pd.DataFrame()

    df = pd.DataFrame(runs)
    df["timestamp_dt"] = pd.to_datetime(df.get("timestamp"), errors="coerce", utc=True)
    df = df.sort_values("timestamp_dt", ascending=False, na_position="last").reset_index(drop=True)
    return df


def _fmt_val(value):
    if value is None:
        return "â€”"
    if isinstance(value, float) and pd.isna(value):
        return "â€”"
    if isinstance(value, str) and value.strip() == "":
        return "â€”"
    return value


def _tabla_presentacion(df: pd.DataFrame, columnas):
    vista = df[columnas].copy()
    for c in vista.columns:
        vista[c] = vista[c].apply(_fmt_val)
    return vista


def _estado_gantt_desde_status(status):
    mapa = {
        "OK": "COMPLETADO",
        "CON_FALLAS": "EN_REVISIÃ“N",
        "CON_ADVERTENCIAS": "EN_REVISIÃ“N",
        "ERROR": "BLOQUEADO",
    }
    return mapa.get(status, "EN_REVISIÃ“N")


def main():
    st.set_page_config(page_title="Motor BT - Dashboard", layout="wide")
    st.title("Dashboard tÃ©cnico - Motor BT")

    ruta_db = st.sidebar.text_input("Ruta DB", value="motor_bt.db")
    df = _normalizar_dataframe(ruta_db=ruta_db)

    if df.empty:
        st.info("sin ejecuciones registradas")
        return

    tab_resumen, tab_proyecto, tab_detalle, tab_estado = st.tabs(
        ["Resumen global", "Por proyecto", "Detalle de ejecuciÃ³n", "Estado tÃ©cnico"]
    )

    with tab_resumen:
        total_runs = len(df)
        ultima_ejecucion = _fmt_val(df.iloc[0].get("timestamp"))
        proyectos_activos = df["project_id"].dropna().astype(str).str.strip()
        proyectos_activos = (proyectos_activos != "").sum() if len(proyectos_activos) else 0

        n_ok = (df["status"] == "OK").sum() if "status" in df else 0
        tasa_ok = (n_ok / total_runs * 100.0) if total_runs else 0.0
        fallas_acumuladas = pd.to_numeric(df.get("n_fallas"), errors="coerce").fillna(0).sum()
        max_dv = pd.to_numeric(df.get("max_dv_pct"), errors="coerce").max()
        max_icc = pd.to_numeric(df.get("max_icc_ka"), errors="coerce").max()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total runs", total_runs)
        c2.metric("Ãšltima ejecuciÃ³n", str(ultima_ejecucion))
        c3.metric("Proyectos activos", int(df["project_id"].dropna().nunique()))

        c4, c5, c6, c7 = st.columns(4)
        c4.metric("Tasa OK", f"{tasa_ok:.1f}%")
        c5.metric("Fallas acumuladas", int(fallas_acumuladas))
        c6.metric("Î”V mÃ¡ximo", "â€”" if pd.isna(max_dv) else f"{float(max_dv):.3f}%")
        c7.metric("Icc mÃ¡ximo", "â€”" if pd.isna(max_icc) else f"{float(max_icc):.3f} kA")

        st.subheader("Ãšltimas 10 ejecuciones")
        cols = [
            "timestamp", "run_id", "project_id", "revision", "status",
            "n_ok", "n_fallas", "max_dv_pct", "max_icc_ka",
        ]
        cols = [c for c in cols if c in df.columns]
        st.dataframe(_tabla_presentacion(df.head(10), cols), use_container_width=True)

    with tab_proyecto:
        proyectos = sorted(
            [p for p in df["project_id"].dropna().astype(str).unique() if p.strip() != ""]
        )
        if not proyectos:
            st.info("sin ejecuciones registradas")
        else:
            proyecto_sel = st.selectbox("project_id", options=proyectos, index=0)
            df_p = df[df["project_id"] == proyecto_sel].copy()
            df_p = df_p.sort_values("timestamp_dt", ascending=True, na_position="last")

            st.subheader("EvoluciÃ³n por revisiÃ³n")
            if "revision" in df_p.columns:
                evo = df_p[["revision", "max_dv_pct", "n_fallas"]].copy()
                evo["revision"] = evo["revision"].apply(_fmt_val)
                evo["max_dv_pct"] = pd.to_numeric(evo["max_dv_pct"], errors="coerce")
                evo["n_fallas"] = pd.to_numeric(evo["n_fallas"], errors="coerce")
                evo = evo.groupby("revision", dropna=False, as_index=False).agg(
                    max_dv_pct=("max_dv_pct", "max"),
                    n_fallas=("n_fallas", "max"),
                )
                st.line_chart(evo.set_index("revision")[["max_dv_pct", "n_fallas"]])
            else:
                st.info("sin revisiones disponibles")

            st.subheader("Runs del proyecto")
            cols = [
                "timestamp", "run_id", "revision", "status", "norma",
                "n_circuitos", "n_ok", "n_fallas", "max_dv_pct", "max_icc_ka",
            ]
            cols = [c for c in cols if c in df_p.columns]
            st.dataframe(_tabla_presentacion(df_p, cols), use_container_width=True)

    with tab_detalle:
        opciones = df[["run_id", "timestamp"]].copy()
        opciones["label"] = opciones.apply(
            lambda r: f"{_fmt_val(r['run_id'])} | {_fmt_val(r['timestamp'])}", axis=1
        )
        seleccion = st.selectbox("run_id", options=opciones["label"].tolist(), index=0)
        run_id_sel = seleccion.split(" | ")[0]
        fila = df[df["run_id"] == run_id_sel].iloc[0].to_dict()

        st.subheader("Campos del registro")
        items = [{"campo": k, "valor": _fmt_val(v)} for k, v in fila.items() if k != "timestamp_dt"]
        st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)

        st.subheader("Rutas de reporte")
        st.text(f"ruta_reporte_txt: {_fmt_val(fila.get('ruta_reporte_txt'))}")
        st.text(f"ruta_reporte_xlsx: {_fmt_val(fila.get('ruta_reporte_xlsx'))}")

    with tab_estado:
        st.subheader("DistribuciÃ³n status")
        status_counts = df["status"].fillna("â€”").astype(str).value_counts().sort_index()
        st.bar_chart(status_counts)

        st.subheader("DistribuciÃ³n norma")
        norma_counts = df["norma"].fillna("â€”").astype(str).value_counts().sort_index()
        st.bar_chart(norma_counts)

        st.subheader("Ãšltimo control de versiÃ³n")
        ultimo = df.iloc[0].to_dict()
        st.text(f"commit_hash: {_fmt_val(ultimo.get('commit_hash'))}")
        st.text(f"branch: {_fmt_val(ultimo.get('branch'))}")
        st.text(f"estado_gantt (mapeado): {_estado_gantt_desde_status(ultimo.get('status'))}")


if __name__ == "__main__":
    main()


