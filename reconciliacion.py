# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from datetime import datetime

# Columnas esperadas
MAYOR_COLS = [
    "Código", "Cuenta", "Fecha", "Tipo", "Nro. Comp", "Subcuenta",
    "Detalle", "CUIT", "Razon Social", "Débito", "Crédito", "Saldo", "Importe"
]
BANCO_COLS = [
    "NUM", "FECHA", "COMBTE", "DESCRIPCION", "DEBITO", "CREDITO", "SALDO", "IMPORTE"
]

# --- Utilidades ---

def _coerce_datetime64(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas Fecha_norm* a datetime64 para compatibilidad con Streamlit/Arrow."""
    out = df.copy()
    for c in list(out.columns):
        if isinstance(c, str) and c.startswith("Fecha_norm"):
            out[c] = pd.to_datetime(out[c], errors="coerce")
    return out


def _parse_fecha(series: pd.Series) -> pd.Series:
    """Acepta dd/mm/yyyy o ya datetime/date."""
    ser = pd.to_datetime(series, format="%d/%m/%Y", errors="coerce").dt.date
    return ser


def _parse_importe(series: pd.Series) -> pd.Series:
    """Parsea importes con separador de miles (.) y decimales (,)."""
    s = series.copy()
    if s.dtype == object:
        s = s.astype(str).str.replace(".", "", regex=False)  # separador de miles
        s = s.str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _validar_headers(df: pd.DataFrame, esperadas: list[str], nombre: str):
    """Valida que estén presentes las columnas esperadas."""
    faltantes = [c for c in esperadas if c not in df.columns]
    if faltantes:
        raise ValueError(f"{nombre}: faltan columnas {faltantes}. Presentes: {list(df.columns)}")


def _normalizar_mayor(df_mayor: pd.DataFrame) -> pd.DataFrame:
    """Normaliza el DataFrame del Mayor."""
    _validar_headers(df_mayor, MAYOR_COLS, "Mayor")
    df = df_mayor.copy()
    df["Fecha_norm"] = _parse_fecha(df["Fecha"])
    df["Importe_norm"] = _parse_importe(df["Importe"])
    df = df[~df["Importe_norm"].isna() & ~df["Fecha_norm"].isna()].copy()
    df["origen"] = "MAYOR"
    df["row_id"] = np.arange(len(df))
    return df


def _normalizar_banco(df_banco: pd.DataFrame) -> pd.DataFrame:
    """Normaliza el DataFrame del Banco."""
    _validar_headers(df_banco, BANCO_COLS, "Banco")
    df = df_banco.copy()
    df["Fecha_norm"] = _parse_fecha(df["FECHA"])
    df["Importe_norm"] = _parse_importe(df["IMPORTE"])
    df = df[~df["Importe_norm"].isna() & ~df["Fecha_norm"].isna()].copy()
    df["origen"] = "BANCO"
    df["row_id"] = np.arange(len(df))
    return df


def _diferencia_dias(d1, d2) -> int:
    """Calcula diferencia absoluta en días entre dos fechas."""
    return abs((d1 - d2).days)


def _diferencia_dias_series(fecha_series: pd.Series, pivot_date) -> pd.Series:
    """Calcula diferencia en días para una serie completa."""
    return fecha_series.apply(lambda d: abs((d - pivot_date).days))


# --- Heurística MVP de conciliación ---

def conciliacion_mvp(
    df_mayor_in: pd.DataFrame,
    df_banco_in: pd.DataFrame,
    tolerancia_dias: int,
    max_items_grupo: int,
    direccion: str = "MAYOR→BANCO",
):
    """
    Conciliación bancaria con estrategia MVP:
    1. One-to-one exacto con tolerancia de fechas
    2. Many-to-one (agrupación) si max_items_grupo > 1
    """
    mayor = _normalizar_mayor(df_mayor_in)
    banco = _normalizar_banco(df_banco_in)

    # Signo para acelerar búsquedas
    mayor["signo"] = np.sign(mayor["Importe_norm"]).astype(int)
    banco["signo"] = np.sign(banco["Importe_norm"]).astype(int)

    mayor_idx = mayor.set_index("row_id")
    banco_idx = banco.set_index("row_id")

    usados_mayor: set[int] = set()
    usados_banco: set[int] = set()
    matches: list[dict] = []

    # --- One-to-one exacto con tolerancia de fechas ---
    mayor_map: dict[tuple[float, int], list[tuple[int, datetime]]] = {}
    for rid, r in mayor_idx.iterrows():
        key = (r["Importe_norm"], r["signo"])
        mayor_map.setdefault(key, []).append((rid, r["Fecha_norm"]))

    for bid, b in banco_idx.iterrows():
        if bid in usados_banco:
            continue
        key = (b["Importe_norm"], b["signo"])
        cand = mayor_map.get(key, [])
        if not cand:
            continue
        cand_validos = [
            (rid, f)
            for (rid, f) in cand
            if rid not in usados_mayor and _diferencia_dias(f, b["Fecha_norm"]) <= tolerancia_dias
        ]
        if not cand_validos:
            continue
        cand_validos.sort(key=lambda x: (_diferencia_dias(x[1], b["Fecha_norm"]), x[1]))
        rid_sel, f_sel = cand_validos[0]
        usados_mayor.add(rid_sel)
        usados_banco.add(bid)
        diff_days = _diferencia_dias(f_sel, b["Fecha_norm"])
        estado = "Conciliado exacto" if diff_days == 0 else "Conciliado por tolerancia"
        matches.append({
            "row_id_mayor": rid_sel,
            "row_id_banco": bid,
            "estado": estado,
            "regla": "one_to_one",
            "diferencia_dias": diff_days,
            "grupo_id": None,
        })

    # --- Many-to-one (Mayor → Banco) ---
    if max_items_grupo and max_items_grupo > 1 and direccion.startswith("MAYOR"):
        no_usados_mayor = mayor_idx.drop(index=list(usados_mayor), errors="ignore")
        no_usados_banco = banco_idx.drop(index=list(usados_banco), errors="ignore")

        mayor_por_signo = {
            -1: no_usados_mayor[no_usados_mayor["signo"] < 0],
            0: no_usados_mayor[no_usados_mayor["signo"] == 0],
            1: no_usados_mayor[no_usados_mayor["signo"] > 0],
        }

        grupo_seq = 1

        for bid, b in no_usados_banco.iterrows():
            sign_key = int(np.sign(b["Importe_norm"]))
            candidatos = mayor_por_signo.get(sign_key, pd.DataFrame())
            if candidatos.empty:
                continue

            cand = candidatos[_diferencia_dias_series(candidatos["Fecha_norm"], b["Fecha_norm"]) <= tolerancia_dias]
            if cand.empty:
                continue

            cand = cand.assign(diff_days=cand["Fecha_norm"].apply(lambda d: _diferencia_dias(d, b["Fecha_norm"])))
            cand = cand.sort_values(by=["diff_days", "Importe_norm"], ascending=[True, False])
            cand = cand.head(60)

            objetivo = b["Importe_norm"]
            rids = cand.index.tolist()
            importes = cand["Importe_norm"].values
            fechas = cand["Fecha_norm"].values
            diffs = cand["diff_days"].values

            mejor_sol = None  # (indices, max_diff, len)
            visited_limit = 5000
            visited = 0

            def backtrack(start, curr_sum, indices):
                nonlocal mejor_sol, visited
                if visited > visited_limit:
                    return
                visited += 1

                if len(indices) > max_items_grupo:
                    return
                if abs(curr_sum - objetivo) < 1e-9 and len(indices) >= 1:
                    max_diff = max(diffs[i] for i in indices) if indices else 0
                    cand_tuple = (tuple(indices), max_diff, len(indices))
                    if mejor_sol is None:
                        mejor_sol = cand_tuple
                    else:
                        curr_best = mejor_sol
                        curr_oldest = min(fechas[i] for i in curr_best[0])
                        new_oldest = min(fechas[i] for i in indices)
                        if (cand_tuple[1], cand_tuple[2], new_oldest) < (curr_best[1], curr_best[2], curr_oldest):
                            mejor_sol = cand_tuple
                    return
                if sign_key >= 0 and curr_sum > objetivo + 1e-9:
                    return
                if sign_key < 0 and curr_sum < objetivo - 1e-9:
                    return

                for i in range(start, len(rids)):
                    idx = i
                    backtrack(i + 1, curr_sum + importes[idx], indices + [idx])

            backtrack(0, 0.0, [])

            if mejor_sol:
                sel = mejor_sol[0]
                grupo_id = f"G{grupo_seq}"
                grupo_seq += 1
                for idx in sel:
                    rid_sel = rids[idx]
                    usados_mayor.add(rid_sel)
                    matches.append({
                        "row_id_mayor": rid_sel,
                        "row_id_banco": bid,
                        "estado": "Conciliado por agrupación",
                        "regla": f"many_to_one<={max_items_grupo}",
                        "diferencia_dias": int(diffs[idx]),
                        "grupo_id": grupo_id,
                    })
                usados_banco.add(bid)

    # --- Construcción de salida ---
    m_df = pd.DataFrame(matches)

    solo_mayor_ids = [rid for rid in mayor_idx.index if rid not in usados_mayor]
    solo_banco_ids = [bid for bid in banco_idx.index if bid not in usados_banco]

    # Detalle conciliado
    if not m_df.empty:
        joined = (
            m_df
            .merge(mayor_idx.reset_index().rename(columns={"row_id": "row_id_mayor"}), on="row_id_mayor", how="left")
            .merge(
                banco_idx.reset_index().rename(columns={"row_id": "row_id_banco"}),
                on="row_id_banco",
                how="left",
                suffixes=("_MAYOR", "_BANCO"),
            )
        )
        mayor_cols = [c for c in mayor.columns if c in MAYOR_COLS] + ["Fecha_norm", "Importe_norm"]
        banco_cols = [c for c in banco.columns if c in BANCO_COLS] + ["Fecha_norm", "Importe_norm"]
        rename_map = {}
        for c in mayor_cols:
            rename_map[c] = f"{c}_MAYOR"
        for c in banco_cols:
            rename_map[c] = f"{c}_BANCO"
        detalle_ok = joined.rename(columns=rename_map)
    else:
        detalle_ok = pd.DataFrame(columns=[])

    # Solo en Mayor
    solo_mayor = mayor_idx.loc[solo_mayor_ids].copy()
    if not solo_mayor.empty:
        solo_mayor["estado"] = "Solo en Mayor"
        solo_mayor["regla"] = ""
        solo_mayor["diferencia_dias"] = np.nan
        solo_mayor["grupo_id"] = ""
        for c in BANCO_COLS + ["Fecha_norm", "Importe_norm"]:
            solo_mayor[f"{c}_BANCO"] = np.nan
        for c in MAYOR_COLS + ["Fecha_norm", "Importe_norm"]:
            if c in solo_mayor.columns:
                solo_mayor[f"{c}_MAYOR"] = solo_mayor[c]
        detalle_mayor_only = solo_mayor[[
            col for col in solo_mayor.columns if col.endswith("_MAYOR") or col.endswith("_BANCO")
        ] + ["estado", "regla", "diferencia_dias", "grupo_id"]]
    else:
        detalle_mayor_only = pd.DataFrame(columns=detalle_ok.columns if not detalle_ok.empty else None)

    # Solo en Banco
    solo_banco = banco_idx.loc[solo_banco_ids].copy()
    if not solo_banco.empty:
        solo_banco["estado"] = "Solo en Banco"
        solo_banco["regla"] = ""
        solo_banco["diferencia_dias"] = np.nan
        solo_banco["grupo_id"] = ""
        for c in MAYOR_COLS + ["Fecha_norm", "Importe_norm"]:
            solo_banco[f"{c}_MAYOR"] = np.nan
        for c in BANCO_COLS + ["Fecha_norm", "Importe_norm"]:
            if c in solo_banco.columns:
                solo_banco[f"{c}_BANCO"] = solo_banco[c]
        detalle_banco_only = solo_banco[[
            col for col in solo_banco.columns if col.endswith("_MAYOR") or col.endswith("_BANCO")
        ] + ["estado", "regla", "diferencia_dias", "grupo_id"]]
    else:
        detalle_banco_only = pd.DataFrame(columns=detalle_ok.columns if not detalle_ok.empty else None)

    # Combinar todos los detalles
    frames = [df for df in [detalle_ok, detalle_mayor_only, detalle_banco_only] if df is not None and not df.empty]
    detalle = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    # Ordenar columnas
    mayor_out = [f"{c}_MAYOR" for c in MAYOR_COLS if f"{c}_MAYOR" in detalle.columns] + [c for c in ["Fecha_norm_MAYOR", "Importe_norm_MAYOR"] if c in detalle.columns]
    banco_out = [f"{c}_BANCO" for c in BANCO_COLS if f"{c}_BANCO" in detalle.columns] + [c for c in ["Fecha_norm_BANCO", "Importe_norm_BANCO"] if c in detalle.columns]
    meta_out = [c for c in ["estado", "regla", "diferencia_dias", "grupo_id"] if c in detalle.columns]
    col_order = mayor_out + banco_out + meta_out
    if not detalle.empty:
        detalle = detalle.reindex(columns=col_order)
        detalle = _coerce_datetime64(detalle)

    # Resumen
    resumen = (
        detalle["estado"].value_counts().rename_axis("estado").reset_index(name="cantidad")
        if not detalle.empty else pd.DataFrame(columns=["estado", "cantidad"])
    )

    return detalle, resumen


# --- Helpers para usar "resultado previo" en la app ---

def is_previous_result(df: pd.DataFrame) -> bool:
    """Detecta si el DataFrame es un resultado previo de conciliación."""
    cols = set(df.columns)
    has_mayor = any(c.endswith("_MAYOR") for c in cols)
    has_banco = any(c.endswith("_BANCO") for c in cols)
    return has_mayor and has_banco and "estado" in cols


def extract_mayor_from_previous(df: pd.DataFrame) -> pd.DataFrame:
    """Reconstruye columnas base del Mayor a partir de un Detalle exportado."""
    # Mapeo de aliases comunes
    alias_map = {
        "Nro. Comp": ["Nro.Comp", "Nro Comp", "NroComp"],
        "Razon Social": ["Razon,Social", "RazonSocial", "Razón Social"],
    }
    
    # Buscar columnas del Mayor presentes
    mayor_cols_present = []
    for base_col in MAYOR_COLS:
        col_mayor = f"{base_col}_MAYOR"
        if col_mayor in df.columns:
            mayor_cols_present.append(base_col)
        else:
            # Buscar aliases
            aliases = alias_map.get(base_col, [])
            for alias in aliases:
                alias_col = f"{alias}_MAYOR"
                if alias_col in df.columns:
                    mayor_cols_present.append(base_col)
                    break
    
    out = pd.DataFrame()
    for c in mayor_cols_present:
        col_mayor = f"{c}_MAYOR"
        if col_mayor in df.columns:
            out[c] = df[col_mayor]
        else:
            # Buscar en aliases
            aliases = alias_map.get(c, [])
            for alias in aliases:
                alias_col = f"{alias}_MAYOR"
                if alias_col in df.columns:
                    out[c] = df[alias_col]
                    break
    
    # Completar columnas faltantes con NA
    for col in MAYOR_COLS:
        if col not in out.columns:
            out[col] = pd.NA
    
    # Si no existe Importe original, intentar con Importe_norm_MAYOR
    if "Importe" not in out.columns and "Importe_norm_MAYOR" in df.columns:
        out["Importe"] = df["Importe_norm_MAYOR"]
    if "Fecha" not in out.columns and "Fecha_norm_MAYOR" in df.columns:
        out["Fecha"] = pd.to_datetime(df["Fecha_norm_MAYOR"]).dt.strftime("%d/%m/%Y")
    
    return out


def merge_with_previous(prev_detalle: pd.DataFrame, nuevo_detalle: pd.DataFrame) -> pd.DataFrame:
    """Une resultado previo con nuevo resultado, eliminando duplicados."""
    # Remover duplicados en cada DataFrame por separado
    if prev_detalle.columns.duplicated().any():
        prev_detalle = prev_detalle.loc[:, ~prev_detalle.columns.duplicated()].copy()
    if nuevo_detalle.columns.duplicated().any():
        nuevo_detalle = nuevo_detalle.loc[:, ~nuevo_detalle.columns.duplicated()].copy()
    
    # Unir columnas
    cols = list(set(prev_detalle.columns) | set(nuevo_detalle.columns))
    prev_al = prev_detalle.reindex(columns=cols)
    nuevo_al = nuevo_detalle.reindex(columns=cols)
    combinado = pd.concat([prev_al, nuevo_al], ignore_index=True)
    combinado = combinado.drop_duplicates()
    
    # Normalizar fechas para Arrow/Streamlit
    combinado = _coerce_datetime64(combinado)
    return combinado
