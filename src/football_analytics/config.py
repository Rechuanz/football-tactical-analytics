from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
SQL_DIR = ROOT / "sql"
OUTPUT_DIR = ROOT / "outputs"

# Final da Copa do Mundo 2022: Argentina 3(4) x 3(2) França
COMPETITION_ID = 43
SEASON_ID = 106
MATCH_ID = 3869685

# Campo StatsBomb: 120 x 80, gol atacado em (120, 40)
PITCH_LENGTH = 120
PITCH_WIDTH = 80
