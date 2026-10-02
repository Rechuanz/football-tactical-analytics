"""CLI do pipeline StatsBomb Open Data.

    python main.py                                  # final da Copa 2022
    python main.py pick                             # escolhe campeonato/temporada/jogo interativamente
    python main.py competitions [--search copa]
    python main.py matches COMPETITION_ID SEASON_ID
    python main.py analyze [MATCH_ID] [--competition-id N --season-id N] [--refresh]
    python main.py analyze-season COMPETITION_ID SEASON_ID [--maps] [--limit N] [--min-matches N]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd

from football_analytics import config, extract, pipeline

pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 500)


def choose(label: str, options: list) -> int:
    """Lista opções numeradas; aceita número ou texto para filtrar."""
    shown = list(enumerate(options))
    while True:
        for i, text in shown:
            print(f"  {i:>3}  {text}")
        answer = input(f"{label} (número, ou texto para filtrar): ").strip()
        if answer.isdigit() and int(answer) < len(options):
            return int(answer)
        shown = [(i, t) for i, t in enumerate(options) if answer.lower() in t.lower()] or shown


def pick():
    comps = extract.list_competitions()
    names = sorted(comps["competition_name"].unique())
    name = names[choose("Campeonato", names)]
    seasons = comps[comps["competition_name"] == name].reset_index(drop=True)
    row = seasons.iloc[choose("Temporada", list(seasons["season_name"]))]
    cid, sid = int(row.competition_id), int(row.season_id)

    action = choose("O que fazer", ["Analisar um jogo", "Resumo da temporada inteira",
                                    "Resumo da temporada + mapas de todos os jogos"])
    if action:
        pipeline.analyze_season(cid, sid, maps=action == 2)
        return
    matches = extract.list_matches(cid, sid).reset_index(drop=True)
    labels = [f"{r.match_date}  {r.home_team} {r.home_score}x{r.away_score} {r.away_team}"
              for r in matches.itertuples()]
    match_id = int(matches.iloc[choose("Jogo", labels)].match_id)
    pipeline.analyze_match(match_id, matches)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("pick", help="seleção interativa")

    c = sub.add_parser("competitions", help="lista competições/temporadas")
    c.add_argument("--search", help="filtra por texto")

    m = sub.add_parser("matches", help="lista jogos de uma competição/temporada")
    m.add_argument("competition_id", type=int)
    m.add_argument("season_id", type=int)

    a = sub.add_parser("analyze", help="analisa uma partida (padrão: final da Copa 2022)")
    a.add_argument("match_id", type=int, nargs="?", default=config.MATCH_ID)
    a.add_argument("--competition-id", type=int, help="opcional: título com placar/data")
    a.add_argument("--season-id", type=int)
    a.add_argument("--refresh", action="store_true", help="ignora o cache em data/")

    s = sub.add_parser("analyze-season", help="resumo por jogador de uma temporada inteira")
    s.add_argument("competition_id", type=int)
    s.add_argument("season_id", type=int)
    s.add_argument("--maps", action="store_true", help="também gera mapas de cada jogo (lento)")
    s.add_argument("--limit", type=int, help="só os N primeiros jogos")
    s.add_argument("--min-matches", type=int, default=1, help="mínimo de jogos por jogador")
    s.add_argument("--refresh", action="store_true")

    args = ap.parse_args(sys.argv[1:] or ["analyze"])
    if args.cmd == "pick":
        pick()
    elif args.cmd == "competitions":
        df = extract.list_competitions()
        if args.search:
            mask = df.astype(str).apply(lambda col: col.str.contains(args.search, case=False)).any(axis=1)
            df = df[mask]
        print(df.to_string(index=False))
    elif args.cmd == "matches":
        print(extract.list_matches(args.competition_id, args.season_id).to_string(index=False))
    elif args.cmd == "analyze-season":
        pipeline.analyze_season(args.competition_id, args.season_id, args.maps, args.limit,
                                args.min_matches, args.refresh)
    else:
        matches = None
        if args.competition_id is not None and args.season_id is not None:
            matches = extract.list_matches(args.competition_id, args.season_id)
        pipeline.analyze_match(args.match_id, matches, args.refresh)


if __name__ == "__main__":
    main()
