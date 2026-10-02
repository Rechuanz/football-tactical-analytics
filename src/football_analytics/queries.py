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


def progressive_carries(con) -> pd.DataFrame:
    return run_sql_file(con, "progressive_carries")


def key_passes(con) -> pd.DataFrame:
    return run_sql_file(con, "key_passes")


def shot_participation(con) -> pd.DataFrame:
    return run_sql_file(con, "shot_participation")


def pass_network_nodes(con) -> pd.DataFrame:
    return run_sql_file(con, "pass_network_nodes")


def pass_network_edges(con) -> pd.DataFrame:
    return run_sql_file(con, "pass_network_edges")


def tournament_summary(con) -> pd.DataFrame:
    """Resumo por jogador. Requer as views *_view já registradas (ver pipeline)."""
    return run_sql_file(con, "tournament_summary")


def team_summary(con) -> pd.DataFrame:
    """Resumo por time. Requer as views progressive_*_view registradas (ver pipeline)."""
    return run_sql_file(con, "team_summary")


def shots(con) -> pd.DataFrame:
    return run_sql_file(con, "shots")
