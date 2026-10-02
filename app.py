"""Front end Streamlit: escolhe campeonato → temporada → partida (ou temporada inteira).

    streamlit run app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from football_analytics import extract, pipeline, queries, transform, viz

st.set_page_config(page_title="Football Tactical Analytics", page_icon="⚽", layout="wide")

PLAYER_COLS = {
    "player_label": "Jogador", "team": "Time", "matches": "Jogos", "minutes": "Minutos", "shots": "Chutes",
    "goals": "Gols", "xg": "xG", "npxg": "np-xG", "key_passes": "Passes-chave",
    "assists": "Assist.", "xa": "xA", "npxg_plus_xa": "np-xG+xA",
    "npxg_xa_per90": "np-xG+xA / 90", "progressive_passes": "Passes prog.",
    "progressive_carries": "Carries prog.", "progressions_per90": "Progressões / 90",
}
TEAM_COLS = {
    "team": "Time", "matches": "Jogos", "goals": "Gols", "shots": "Chutes", "xg": "xG",
    "npxg": "np-xG", "passes": "Passes", "pass_pct": "Precisão de passe (%)",
    "progressive_passes": "Passes prog.", "progressive_carries": "Carries prog.",
}


# ---------- dados (em cache) ----------
@st.cache_data(show_spinner=False)
def get_competitions() -> pd.DataFrame:
    return extract.list_competitions()


@st.cache_data(show_spinner=False)
def get_matches(competition_id: int, season_id: int) -> pd.DataFrame:
    return extract.list_matches(competition_id, season_id)


def _bundle(events: pd.DataFrame) -> dict:
    """Roda todas as queries sobre `events` e devolve só DataFrames (cacheáveis)."""
    con = transform.load_to_duckdb(events)
    tables = pipeline.analysis_tables(con)
    out = {
        "tables": tables,
        "players": queries.tournament_summary(con),
        "teams": queries.team_summary(con),
        "nodes": queries.pass_network_nodes(con),
        "edges": queries.pass_network_edges(con),
    }
    con.close()
    return out


@st.cache_data(show_spinner="Carregando partida…")
def match_bundle(match_id: int) -> dict:
    events = extract.fetch_events(match_id)
    return {"events": events, **_bundle(events)}


def season_bundle(competition_id: int, season_id: int, progress=None) -> dict:
    """Sem @st.cache: o progresso é um elemento da página, que não pode ser reexecutado
    a partir do cache. O resultado fica em st.session_state (ver season_view)."""
    events, matches, failed = pipeline.load_season_events(
        competition_id, season_id, progress=progress)
    return {"failed": failed, "n_matches": events["match_id"].nunique(), **_bundle(events)}


def show_fig(fig):
    st.pyplot(fig, width='stretch')
    plt.close(fig)


def table(df: pd.DataFrame, columns: dict, **kwargs):
    cols = [c for c in columns if c in df.columns]
    st.dataframe(df[cols].rename(columns=columns), hide_index=True, width='stretch', **kwargs)


# ---------- visão: partida ----------
def match_view(match_row: pd.Series):
    title = (f"{match_row.home_team} {match_row.home_score} x {match_row.away_score} "
             f"{match_row.away_team} — {match_row.match_date}")
    st.subheader(title)
    b = match_bundle(int(match_row.match_id))
    teams = list(b["teams"]["team"])

    cols = st.columns(len(teams))
    for col, t in zip(cols, b["teams"].itertuples()):
        with col:
            st.markdown(f"**{t.team}**")
            a, c, d = st.columns(3)
            a.metric("Gols", t.goals)
            c.metric("xG", t.xg)
            d.metric("np-xG", t.npxg)
            a, c, d = st.columns(3)
            a.metric("Chutes", t.shots)
            c.metric("Precisão de passe", f"{t.pass_pct}%")
            d.metric("Prog. (passes+carries)", t.progressive_passes + t.progressive_carries)

    tabs = st.tabs(["Jogadores", "Chutes", "Passes progressivos", "Carries progressivos",
                    "Passes-chave", "Rede de passes"])
    with tabs[0]:
        table(b["players"], PLAYER_COLS)
    maps = [
        (tabs[1], viz.plot_shot_map, b["tables"]["shots"]),
        (tabs[2], viz.plot_progressive_passes, b["tables"]["progressive_passes"]),
        (tabs[3], viz.plot_progressive_carries, b["tables"]["progressive_carries"]),
        (tabs[4], viz.plot_key_passes, b["tables"]["key_passes"]),
    ]
    for tab, plot, df in maps:
        with tab:
            team = st.radio("Time", teams, horizontal=True, key=f"{plot.__name__}")
            show_fig(plot(df, team, title))
    with tabs[5]:
        team = st.radio("Time", teams, horizontal=True, key="network_team")
        show_fig(viz.plot_pass_network(b["nodes"], b["edges"], team, title))
        st.caption("Posição média dos passes de cada jogador até a primeira substituição do time; "
                   "espessura = passes completos entre a dupla (mín. 3).")


# ---------- visão: temporada inteira ----------
def season_view(competition: str, season: str, cid: int, sid: int, cov: dict):
    st.subheader(f"{competition} {season} — campeonato inteiro")
    key = ("season", cid, sid)
    if key not in st.session_state:
        bar = st.progress(0.0, text="Baixando partidas…")

        def progress(i, n, text):
            bar.progress(i / n, text=f"[{i}/{n}] {text}")

        st.session_state[key] = season_bundle(cid, sid, progress)
        bar.empty()
    b = st.session_state[key]
    st.caption(f"{b['n_matches']} jogos analisados"
               + (f" · {len(b['failed'])} sem eventos abertos" if b["failed"] else ""))

    if cov["focal_team"]:
        st.warning(
            f"Só os jogos do **{cov['focal_team']}** estão disponíveis ({cov['focal_games']} jogos). "
            "Jogadores e totais dos demais times cobrem apenas os jogos contra ele, "
            "então não são comparáveis. Os filtros de mínimo de jogos e minutos já vêm ajustados "
            "para mostrar só o elenco com cobertura completa.")

    tabs = st.tabs(["Jogadores", "Times"])
    with tabs[0]:
        players = b["players"]
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        teams = c1.multiselect("Times", sorted(players["team"].unique()))
        max_m = int(players["matches"].max())
        has_minutes = bool(players["minutes"].notna().any())  # escalações ausentes em jogos antigos
        max_min = int(players["minutes"].max()) if has_minutes else 0
        focal = cov["focal_team"] is not None
        default_min = max(3, cov["focal_games"] // 2) if focal else 3
        min_m = c2.slider("Mínimo de jogos", 1, max_m, min(default_min, max_m),
                          key=f"min_{cid}_{sid}")
        default_minutes = (max_min // 2 // 30) * 30 if focal else 180
        min_minutes = 0
        if has_minutes:
            min_minutes = c3.slider("Mínimo de minutos", 0, max_min, min(default_minutes, max_min),
                                    step=30, key=f"minutes_{cid}_{sid}")
        else:
            c3.caption("Minutos indisponíveis nesta temporada.")
        metrics = {v: k for k, v in PLAYER_COLS.items()
                   if k not in ("player_label", "team", "matches", "minutes")}
        sort_label = c4.selectbox("Ordenar por", list(metrics), index=list(metrics).index("np-xG+xA"))
        df = players[(players["matches"] >= min_m) & (players["minutes"].fillna(0) >= min_minutes)]
        if teams:
            df = df[df["team"].isin(teams)]
        df = df.sort_values(metrics[sort_label], ascending=False)
        top = df.head(15).set_index("player_label")[metrics[sort_label]]
        st.bar_chart(top.rename(sort_label), horizontal=True, sort=False)
        table(df, PLAYER_COLS)
        st.download_button("Baixar CSV", df.to_csv(index=False), "jogadores.csv", "text/csv")
    with tabs[1]:
        if cov["focal_team"]:
            st.caption(f"Apenas o {cov['focal_team']} tem a temporada completa; os demais times "
                       "têm só os jogos contra ele.")
        table(b["teams"], TEAM_COLS)


# ---------- layout ----------
st.title("⚽ Football Tactical Analytics")
st.caption("StatsBomb Open Data · DuckDB · mplsoccer")

comps = get_competitions()
with st.sidebar:
    st.header("Seleção")
    competition = st.selectbox("Campeonato", sorted(comps["competition_name"].unique()),
                               index=sorted(comps["competition_name"].unique()).index("FIFA World Cup"))
    seasons = comps[comps["competition_name"] == competition].sort_values("season_name", ascending=False)
    season = st.selectbox("Temporada", list(seasons["season_name"]))
    srow = seasons[seasons["season_name"] == season].iloc[0]
    cid, sid = int(srow.competition_id), int(srow.season_id)

    matches = get_matches(cid, sid)
    cov = pipeline.coverage(matches)
    if cov["focal_team"]:
        st.warning(
            f"**Cobertura parcial:** nesta temporada o StatsBomb só liberou os jogos do "
            f"**{cov['focal_team']}** ({cov['focal_games']} de {cov['n_matches']} jogos). "
            f"Os outros {cov['n_teams'] - 1} times aparecem apenas nos jogos contra ele.")
    scope = st.radio("Escopo", ["Partida", "Campeonato inteiro"])
    match_row = None
    if scope == "Partida":
        labels = [f"{r.match_date}  {r.home_team} {r.home_score}x{r.away_score} {r.away_team}"
                  for r in matches.itertuples()]
        match_row = matches.iloc[labels.index(st.selectbox("Partida", labels, index=len(labels) - 1))]
    else:
        st.info(f"{len(matches)} jogos. A primeira carga baixa todos os eventos "
                "(depois fica em cache local).")
        go_season = st.button("Analisar campeonato", type="primary")

if scope == "Partida":
    match_view(match_row)
elif go_season or st.session_state.get("season_key") == (cid, sid):
    st.session_state["season_key"] = (cid, sid)
    season_view(competition, season, cid, sid, cov)
else:
    st.write("Clique em **Analisar campeonato** na barra lateral para carregar a temporada.")
