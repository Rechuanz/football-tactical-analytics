"""Etapa 1: extração dos eventos brutos via statsbombpy (dados abertos)."""
import warnings

import pandas as pd
from statsbombpy import sb

from . import config

warnings.filterwarnings("ignore", category=UserWarning, module="statsbombpy")

# Colunas usadas nas análises; as demais (centenas, esparsas) são descartadas.
KEEP_COLUMNS = [
    "id", "index", "period", "minute", "second", "timestamp", "type",
    "team", "team_id", "player", "player_id", "position", "play_pattern",
    "possession", "possession_team",
    "location", "pass_end_location", "carry_end_location",
    "pass_outcome", "pass_type", "pass_recipient", "pass_height",
    "pass_length", "pass_angle", "pass_goal_assist", "pass_shot_assist",
    "shot_outcome", "shot_type", "shot_statsbomb_xg", "shot_key_pass_id", "under_pressure",
]


def get_match_info(competition_id=config.COMPETITION_ID,
                   season_id=config.SEASON_ID,
                   match_id=config.MATCH_ID) -> pd.Series:
    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    return matches.loc[matches["match_id"] == match_id].iloc[0]


def list_competitions() -> pd.DataFrame:
    cols = ["competition_id", "season_id", "competition_name", "season_name", "country_name"]
    return sb.competitions()[cols].sort_values(["competition_name", "season_name"])


def list_matches(competition_id: int, season_id: int) -> pd.DataFrame:
    cols = ["match_id", "match_date", "home_team", "away_team", "home_score", "away_score"]
    return sb.matches(competition_id=competition_id, season_id=season_id)[cols] \
        .sort_values("match_date")


PERIOD_START = {1: 0, 2: 45, 3: 90, 4: 105}  # relógio do jogo no início de cada período


def _clock(text: str) -> float:
    minutes, seconds = text.split(":")
    return int(minutes) + int(seconds) / 60


def _stint_minutes(positions: list, elapsed, match_end: float) -> float:
    """Soma o tempo em campo de um jogador a partir das posições (entrada/saída).

    A disputa de pênaltis vem com o relógio reiniciado (período 1 de novo): uma saída
    anterior à entrada significa "até o fim do jogo", e entradas que voltam no tempo
    são ignoradas.
    """
    total, cursor = 0.0, 0.0
    for pos in positions:
        if pos["from_period"] > 4:
            continue
        start = elapsed(pos["from_period"], _clock(pos["from"]))
        if start < cursor - 0.5:
            continue
        end = match_end if pos["to"] is None else elapsed(pos["to_period"], _clock(pos["to"]))
        if end < start - 0.5:
            end = match_end
        end = min(end, match_end)
        total += end - start
        cursor = end
    return total


def _lineup_info(match_id: int, events: pd.DataFrame):
    """(rótulos, minutos) por player_name, via escalações; vazios se indisponíveis."""
    try:
        lineups = sb.lineups(match_id=match_id)
    except Exception:
        return {}, {}
    regular = events[events["period"] <= 4]
    ends = (regular["minute"] + regular["second"] / 60).groupby(regular["period"]).max()

    def elapsed(period: int, clock: float) -> float:
        before = sum(ends[q] - PERIOD_START[q] for q in ends.index if q < period)
        return before + clock - PERIOD_START[period]

    last = ends.index.max()
    match_end = elapsed(last, ends[last])
    labels, minutes = {}, {}
    for df in lineups.values():
        for r in df.itertuples():
            labels[r.player_name] = config.short_name(r.player_name, r.player_nickname)
            if r.positions:
                minutes[r.player_name] = round(_stint_minutes(r.positions, elapsed, match_end), 1)
    return labels, minutes


def fetch_events(match_id: int = config.MATCH_ID, use_cache: bool = True) -> pd.DataFrame:
    """Eventos de uma partida (enxutos, com `match_id`); usa o parquet em data/ se existir."""
    cache = config.DATA_DIR / f"events_{match_id}.parquet"
    if use_cache and cache.exists():
        events = pd.read_parquet(cache)
        if {"match_id", "player_label", "minutes_played", *KEEP_COLUMNS} <= set(events.columns):
            return events
        events = sb.events(match_id=match_id).reindex(columns=KEEP_COLUMNS)
    else:
        events = sb.events(match_id=match_id).reindex(columns=KEEP_COLUMNS)
    labels, minutes = _lineup_info(match_id, events)
    events["player_label"] = [
        labels.get(p) or config.short_name(p) if isinstance(p, str) else None
        for p in events["player"]
    ]
    events["minutes_played"] = events["player"].map(minutes)
    events["match_id"] = match_id
    config.DATA_DIR.mkdir(exist_ok=True)
    events.to_parquet(cache)
    return events
