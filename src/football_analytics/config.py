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

# Exceções manuais aos rótulos (o padrão vem do player_nickname das escalações).
SHORT_NAMES = {
    "Lionel Andrés Messi Cuccittini": "Messi",
    "Ángel Fabián Di María Hernández": "Di María",
    "Nahuel Molina Lucero": "Molina",
    "Alexis Mac Allister": "Mac Allister",
    "Theo Bernard François Hernández": "Theo",
    "Kylian Mbappé Lottin": "Mbappé",
    "Antoine Griezmann": "Griezmann",
    "Olivier Giroud": "Giroud",
    "Ousmane Dembélé": "Dembélé",
    "Randal Kolo Muani": "Kolo Muani",
    "Rodrigo Javier De Paul": "De Paul",
    "Marcos Javier Acuña": "Acuña",
    "Enzo Fernandez": "Enzo",
    "Nicolás Hernán Otamendi": "Otamendi",
    "Cristian Gabriel Romero": "Romero",
    "Nicolás Alejandro Tagliafico": "Tagliafico",
    "Julián Álvarez": "J. Álvarez",
    "Neymar da Silva Santos Junior": "Neymar",
    "Raphael Dias Belloli": "Raphinha",
    "Hugo Lloris": "Lloris",
    "Raphaël Varane": "Varane",
    "Dayotchanculle Upamecano": "Upamecano",
    "Jules Koundé": "Koundé",
    "Adrien Rabiot": "Rabiot",
    "Aurélien Djani Tchouaméni": "Tchouaméni",
}


def short_name(player: str, nickname=None) -> str:
    """Rótulo curto: exceção manual > último token do apelido > último token do nome."""
    if player in SHORT_NAMES:
        return SHORT_NAMES[player]
    source = nickname if isinstance(nickname, str) and nickname.strip() else player
    return source.split()[-1]
