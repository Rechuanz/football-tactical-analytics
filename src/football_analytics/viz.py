"""Etapa 4: visualizações táticas com mplsoccer."""
import matplotlib.pyplot as plt
import pandas as pd
from mplsoccer import Pitch


def plot_progressive_passes(df: pd.DataFrame, team: str, title: str, path=None):
    d = df[df["team"] == team]
    pitch = Pitch(pitch_type="statsbomb", pitch_color="#1b1f2a", line_color="#c7d5cc")
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor("#1b1f2a")
    pitch.lines(d.start_x, d.start_y, d.pass_end_x, d.pass_end_y,
                lw=2, comet=True, transparent=True, color="#4cc9f0", ax=ax)
    pitch.scatter(d.pass_end_x, d.pass_end_y, s=40, color="#4cc9f0",
                  edgecolors="white", zorder=3, ax=ax)
    ax.set_title(f"{team} — passes progressivos ({len(d)})\n{title}",
                 color="white", fontsize=15, pad=12)
    if path:
        fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    return fig
