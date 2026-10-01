import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from football_analytics import config, extract, queries, transform, viz


def main():
    info = extract.get_match_info()
    title = f"{info.home_team} x {info.away_team} — {info.competition} {info.season}"
    print(title)

    events = extract.fetch_events()
    events.to_parquet(config.DATA_DIR / f"events_{config.MATCH_ID}.parquet")
    con = transform.load_to_duckdb(events)
    print(con.execute("SELECT type, count(*) n FROM events GROUP BY 1 ORDER BY 2 DESC LIMIT 5").df())

    prog = queries.progressive_passes(con)
    con.register("progressive_passes_view", prog)
    print(queries.progressive_passes_by_player(con).head(10))

    config.OUTPUT_DIR.mkdir(exist_ok=True)
    for team in prog["team"].unique():
        viz.plot_progressive_passes(prog, team, title,
                                    config.OUTPUT_DIR / f"progressive_passes_{team}.png")
    print("Mapas salvos em outputs/")


if __name__ == "__main__":
    main()
