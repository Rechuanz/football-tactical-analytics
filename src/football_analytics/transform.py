"""Etapa 2: limpeza e carga dos eventos em DuckDB (em memória)."""
import duckdb
import numpy as np
import pandas as pd


def _split_xy(df: pd.DataFrame, col: str, prefix: str) -> pd.DataFrame:
    """Converte colunas [x, y] (listas) em duas colunas numéricas."""
    coords = df[col].apply(lambda v: v if isinstance(v, (list, tuple, np.ndarray)) else [None, None])
    df[f"{prefix}_x"] = coords.str[0].astype("float64")
    df[f"{prefix}_y"] = coords.str[1].astype("float64")
    return df.drop(columns=[col])


def clean_events(events: pd.DataFrame) -> pd.DataFrame:
    df = events.copy()
    for col, prefix in [("location", "start"),
                        ("pass_end_location", "pass_end"),
                        ("carry_end_location", "carry_end")]:
        df = _split_xy(df, col, prefix)
    df["under_pressure"] = df["under_pressure"].fillna(False).astype(bool)
    df["pass_goal_assist"] = df["pass_goal_assist"].fillna(False).astype(bool)
    df["pass_shot_assist"] = df["pass_shot_assist"].fillna(False).astype(bool)
    return df


def load_to_duckdb(events: pd.DataFrame) -> duckdb.DuckDBPyConnection:
    """Cria a conexão em memória e registra a tabela `events`."""
    con = duckdb.connect(":memory:")
    df = clean_events(events)
    con.register("events_df", df)
    con.execute("CREATE TABLE events AS SELECT * FROM events_df")
    return con
