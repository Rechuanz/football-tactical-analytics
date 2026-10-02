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
    "player_label": "Jogador", "team": "Time", "matches": "Jogos", "shots": "Chutes",
    "goals": "Gols", "xg": "xG", "npxg": "np-xG", "key_passes": "Passes-chave",
    "assists": "Assist.", "xa": "xA", "npxg_plus_xa": "np-xG+xA",
    "npxg_xa_per_match": "np-xG+xA / jogo", "progressive_passes": "Passes prog.",
    "progressive_carries": "Carries prog.", "progressions_per_match": "Progressões / jogo",
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


@st.cache_data(show_spinner=False)
def season_bundle(competition_id: int, season_id: int, _progress=None) -> dict:
    events, matches, failed = pipeline.load_season_events(
        competition_id, season_id, progress=_progress)
    return {"failed": failed, "n_matches": events["match_id"].nunique(), **_bundle(events)}


def show_fig(fig):
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def table(df: pd.DataFrame, columns: dict, **kwargs):
    cols = [c for c in columns if c in df.columns]
    st.dataframe(df[cols].rename(columns=columns), hide_index=True, use_container_width=True, **kwargs)


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

    tabs = st.tabs(["Jogadores", "Passes progressivos", "Carries progressivos",
                    "Passes-chave", "Rede de passes"])
    with tabs[0]:
        table(b["players"], PLAYER_COLS)
    maps = [
        (tabs[1], viz.plot_progressive_passes, b["tables"]["progressive_passes"]),
        (tabs[2], viz.plot_progressive_carries, b["tables"]["progressive_carries"]),
        (tabs[3], viz.plot_key_passes, b["tables"]["key_passes"]),
    ]
    for tab, plot, df in maps:
        with tab:
            team = st.radio("Time", teams, horizontal=True, key=f"{plot.__name__}")
            show_fig(plot(df, team, title))
    with tabs[4]:
        team = st.radio("Time", teams, horizontal=True, key="network_team")
        show_fig(viz.plot_pass_network(b["nodes"], b["edges"], team, title))
        st.caption("Posição média dos passes de cada jogador até a primeira substituição do time; "
                   "espessura = passes completos entre a dupla (mín. 3).")


# ---------- visão: temporada inteira ----------
def season_view(competition: str, season: str, cid: int, sid: int, n_total: int):
    st.subheader(f"{competition} {season} — campeonato inteiro")
    bar = st.progress(0.0, text="Baixando partidas…")

    def progress(i, n, text):
        bar.progress(i / n, text=f"[{i}/{n}] {text}")

    b = season_bundle(cid, sid, _progress=progress)
    bar.empty()
    st.caption(f"{b['n_matches']} jogos analisados"
               + (f" · {len(b['failed'])} sem eventos abertos" if b["failed"] else ""))

    tabs = st.tabs(["Jogadores", "Times"])
    with tabs[0]:
        players = b["players"]
        c1, c2, c3 = st.columns([2, 1, 1])
        teams = c1.multiselect("Times", sorted(players["team"].unique()))
        max_m = int(players["matches"].max())
        min_m = c2.slider("Mínimo de jogos", 1, max_m, min(3, max_m))
        metrics = {v: k for k, v in PLAYER_COLS.items()
                   if k not in ("player_label", "team", "matches")}
        sort_label = c3.selectbox("Ordenar por", list(metrics), index=list(metrics).index("np-xG+xA"))
        df = players[players["matches"] >= min_m]
        if teams:
            df = df[df["team"].isin(teams)]
        df = df.sort_values(metrics[sort_label], ascending=False)
        top = df.head(15).set_index("player_label")[metrics[sort_label]]
        st.bar_chart(top.rename(sort_label), horizontal=True, sort=False)
        table(df, PLAYER_COLS)
        st.download_button("Baixar CSV", df.to_csv(index=False), "jogadores.csv", "text/csv")
    with tabs[1]:
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
    season_view(competition, season, cid, sid, len(matches))
else:
    st.write("Clique em **Analisar campeonato** na barra lateral para carregar a temporada.")
