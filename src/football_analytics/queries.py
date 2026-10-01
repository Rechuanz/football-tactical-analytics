"""Etapa 3: execução das consultas SQL analíticas."""
import duckdb
import pandas as pd

from . import config


def run_sql_file(con: duckdb.DuckDBPyConnection, name: str) -> pd.DataFrame:
    return con.execute((config.SQL_DIR / f"{name}.sql").read_text(encoding="utf-8")).df()


def progressive_passes(con) -> pd.DataFrame:
    return run_sql_file(con, "progressive_passes")


def progressive_passes_by_player(con) -> pd.DataFrame:
    return con.execute("""
        SELECT team, player, count(*) AS progressive_passes
        FROM progressive_passes_view
        GROUP BY ALL ORDER BY progressive_passes DESC
    """).df()
