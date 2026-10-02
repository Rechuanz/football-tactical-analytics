"""Orquestração: análise de uma partida e de uma competição/temporada inteira."""
import pandas as pd

from . import config, extract, queries, transform, viz


def _teams(events: pd.DataFrame):
    return events["team"].dropna().unique()


def match_title(events: pd.DataFrame, matches: pd.DataFrame = None, match_id=None) -> str:
    if matches is not None:
        row = matches[matches["match_id"] == match_id]
        if not row.empty:
            r = row.iloc[0]
            return f"{r.home_team} {r.home_score} x {r.away_score} {r.away_team} — {r.match_date}"
    return " x ".join(_teams(events))


def coverage(matches: pd.DataFrame) -> dict:
    """Cobertura do Open Data numa temporada: algumas só liberam jogos de um time.

    `focal_team` é o time presente em mais de 60% dos jogos (None em torneios normais).
    """
    teams = pd.concat([matches["home_team"], matches["away_team"]]).value_counts()
    n = len(matches)
    focal = teams.index[0] if n and teams.iloc[0] / n > 0.6 else None
    return {"n_matches": n, "n_teams": len(teams), "max_games": int(teams.iloc[0]) if n else 0,
            "focal_team": focal, "focal_games": int(teams.iloc[0]) if focal else 0}


def analysis_tables(con) -> dict:
    """Roda as queries analíticas e registra os resultados como views."""
    tables = {
        "progressive_passes": queries.progressive_passes(con),
        "progressive_carries": queries.progressive_carries(con),
        "key_passes": queries.key_passes(con),
        "shot_participation": queries.shot_participation(con),
        "shots": queries.shots(con),
    }
    for name in ("progressive_passes", "progressive_carries", "shot_participation"):
        con.register(f"{name}_view", tables[name])
    return tables


def plot_match_maps(con, events, tables, title, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    nodes, edges = queries.pass_network_nodes(con), queries.pass_network_edges(con)
    for team in _teams(events):
        viz.plot_progressive_passes(tables["progressive_passes"], team, title,
                                    out_dir / f"progressive_passes_{team}.png")
        viz.plot_progressive_carries(tables["progressive_carries"], team, title,
                                     out_dir / f"progressive_carries_{team}.png")
        viz.plot_key_passes(tables["key_passes"], team, title, out_dir / f"key_passes_{team}.png")
        viz.plot_shot_map(tables["shots"], team, title, out_dir / f"shot_map_{team}.png")
        viz.plot_pass_network(nodes, edges, team, title, out_dir / f"pass_network_{team}.png")


def analyze_match(match_id: int, matches: pd.DataFrame = None, refresh=False):
    events = extract.fetch_events(match_id, use_cache=not refresh)
    title = match_title(events, matches, match_id)
    print(title)
    con = transform.load_to_duckdb(events)
    tables = analysis_tables(con)
    print(queries.progressive_passes_by_player(con).head(10))
    print(tables["shot_participation"].head(10))
    out = config.OUTPUT_DIR / str(match_id)
    plot_match_maps(con, events, tables, title, out)
    print(f"Mapas salvos em {out}")


def load_season_events(competition_id: int, season_id: int, limit=None, refresh=False,
                       progress=None):
    """Baixa (ou lê do cache) os eventos de todos os jogos; devolve (events, matches, failed).

    `progress(i, total, texto)` é chamado a cada jogo (usado pelo CLI e pelo app).
    """
    matches = extract.list_matches(competition_id, season_id)
    if limit:
        matches = matches.head(limit)
    frames, failed = [], []
    for i, m in enumerate(matches.itertuples(), 1):
        text = f"{m.home_team} x {m.away_team} ({m.match_id})"
        if progress:
            progress(i, len(matches), text)
        try:
            frames.append(extract.fetch_events(m.match_id, use_cache=not refresh))
        except Exception as exc:  # jogo sem eventos abertos
            failed.append(m.match_id)
            print(f"  ignorado {text}: {exc}")
    return pd.concat(frames, ignore_index=True), matches, failed


def analyze_season(competition_id: int, season_id: int, maps=False, limit=None,
                   min_matches=1, refresh=False):
    """Agrega todos os jogos da temporada numa única tabela `events` e resume por jogador."""
    events, matches, failed = load_season_events(
        competition_id, season_id, limit, refresh,
        progress=lambda i, n, t: print(f"[{i}/{n}] {t}"))
    label = f"competição {competition_id} / temporada {season_id} ({events['match_id'].nunique()} jogos)"
    con = transform.load_to_duckdb(events)
    tables = analysis_tables(con)

    summary = queries.tournament_summary(con)
    summary = summary[summary["matches"] >= min_matches]
    out = config.OUTPUT_DIR / f"season_{competition_id}_{season_id}"
    out.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out / "player_summary.csv", index=False)
    viz.plot_tournament_leaders(summary, label, out / "xg_xa_leaders.png")
    print(summary.head(15).to_string(index=False))
    print(f"Resumo salvo em {out}" + (f"; falharam: {failed}" if failed else ""))

    if maps:
        for mid, ev in events.groupby("match_id"):
            mcon = transform.load_to_duckdb(ev)
            plot_match_maps(mcon, ev, analysis_tables(mcon), match_title(ev, matches, mid),
                            config.OUTPUT_DIR / str(mid))
        print("Mapas por jogo salvos em outputs/<match_id>/")
