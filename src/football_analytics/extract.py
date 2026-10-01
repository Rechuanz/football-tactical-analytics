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
    "shot_outcome", "shot_statsbomb_xg", "under_pressure",
]


def get_match_info(competition_id=config.COMPETITION_ID,
                   season_id=config.SEASON_ID,
                   match_id=config.MATCH_ID) -> pd.Series:
    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    return matches.loc[matches["match_id"] == match_id].iloc[0]


def fetch_events(match_id: int = config.MATCH_ID) -> pd.DataFrame:
    """Baixa os eventos de uma partida e devolve um DataFrame enxuto."""
    events = sb.events(match_id=match_id)
    return events.reindex(columns=KEEP_COLUMNS)
