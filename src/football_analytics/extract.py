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


def _player_labels(match_id: int) -> dict:
    """player_name -> rótulo curto, via apelidos das escalações (vazio se indisponível)."""
    try:
        lineups = sb.lineups(match_id=match_id)
    except Exception:
        return {}
    return {r.player_name: config.short_name(r.player_name, r.player_nickname)
            for df in lineups.values() for r in df.itertuples()}


def fetch_events(match_id: int = config.MATCH_ID, use_cache: bool = True) -> pd.DataFrame:
    """Eventos de uma partida (enxutos, com `match_id`); usa o parquet em data/ se existir."""
    cache = config.DATA_DIR / f"events_{match_id}.parquet"
    if use_cache and cache.exists():
        events = pd.read_parquet(cache)
        if {"match_id", "player_label", *KEEP_COLUMNS} <= set(events.columns):
            return events
        events = sb.events(match_id=match_id).reindex(columns=KEEP_COLUMNS)
    else:
        events = sb.events(match_id=match_id).reindex(columns=KEEP_COLUMNS)
    labels = _player_labels(match_id)
    events["player_label"] = [
        labels.get(p) or config.short_name(p) if isinstance(p, str) else None
        for p in events["player"]
    ]
    events["match_id"] = match_id
    config.DATA_DIR.mkdir(exist_ok=True)
    events.to_parquet(cache)
    return events
