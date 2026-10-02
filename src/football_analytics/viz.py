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


def plot_progressive_carries(df: pd.DataFrame, team: str, title: str, path=None):
    d = df[df["team"] == team]
    pitch = Pitch(pitch_type="statsbomb", pitch_color="#1b1f2a", line_color="#c7d5cc")
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor("#1b1f2a")
    pitch.arrows(d.start_x, d.start_y, d.carry_end_x, d.carry_end_y,
                 width=2.5, headwidth=5, headlength=5, color="#f9c74f", ax=ax)
    pitch.scatter(d.start_x, d.start_y, s=25, color="#f9c74f", ax=ax)
    ax.set_title(f"{team} — carries progressivos ({len(d)})\n{title}",
                 color="white", fontsize=15, pad=12)
    if path:
        fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    return fig


def plot_key_passes(df: pd.DataFrame, team: str, title: str, path=None):
    d = df[df["team"] == team].fillna({"xa": 0})
    pitch = Pitch(pitch_type="statsbomb", pitch_color="#1b1f2a", line_color="#c7d5cc")
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor("#1b1f2a")
    for goal, color in [(False, "#90be6d"), (True, "#f94144")]:
        g = d[d["goal_assist"] == goal]
        pitch.arrows(g.start_x, g.start_y, g.pass_end_x, g.pass_end_y,
                     width=2, headwidth=5, headlength=5, color=color, ax=ax,
                     label="assistência" if goal else "passe para chute")
        pitch.scatter(g.pass_end_x, g.pass_end_y, s=g.xa * 1500 + 30, color=color,
                      edgecolors="white", alpha=0.9, zorder=3, ax=ax)
    ax.legend(loc="lower left", facecolor="#1b1f2a", labelcolor="white", edgecolor="none")
    ax.set_title(f"{team} — passes que geram chute ({len(d)}; tamanho = xG)\n{title}",
                 color="white", fontsize=15, pad=12)
    if path:
        fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    return fig


def plot_pass_network(nodes: pd.DataFrame, edges: pd.DataFrame, team: str, title: str,
                      path=None):
    n = nodes[nodes["team"] == team].set_index("player")
    e = edges[(edges["team"] == team) & edges.player_a.isin(n.index)
              & edges.player_b.isin(n.index)]
    pitch = Pitch(pitch_type="statsbomb", pitch_color="#1b1f2a", line_color="#c7d5cc")
    fig, ax = pitch.draw(figsize=(12, 8))
    fig.set_facecolor("#1b1f2a")
    for r in e.itertuples():
        a, b = n.loc[r.player_a], n.loc[r.player_b]
        pitch.lines(a.x, a.y, b.x, b.y, lw=r.passes * 0.6, color="#4cc9f0",
                    alpha=0.6, zorder=2, ax=ax)
    pitch.scatter(n.x, n.y, s=n.passes * 12, color="#f9c74f", edgecolors="white",
                  zorder=3, ax=ax)
    for player, r in n.iterrows():
        pitch.annotate(r.player_label, (r.x, r.y - 4), color="white",
                       fontsize=9, ha="center", va="center", zorder=4, ax=ax)
    ax.set_title(f"{team} — rede de passes até a 1ª substituição\n{title}",
                 color="white", fontsize=15, pad=12)
    if path:
        fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    return fig


def plot_tournament_leaders(summary: pd.DataFrame, title: str, path=None, top: int = 15):
    d = summary.head(top).iloc[::-1]
    labels = list(d["player_label"])
    for i, (lab, full) in enumerate(zip(labels, d["player"])):
        if labels.count(lab) > 1:  # sobrenome repetido: desambigua com a inicial
            labels[i] = f"{full[0]}. {lab}"
    fig, ax = plt.subplots(figsize=(10, 0.45 * len(d) + 2))
    fig.set_facecolor("#1b1f2a")
    ax.set_facecolor("#1b1f2a")
    ax.barh(labels, d["npxg"], color="#f94144", label="np-xG")
    ax.barh(labels, d["xa"], left=d["npxg"], color="#4cc9f0", label="xA")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.legend(facecolor="#1b1f2a", labelcolor="white", edgecolor="none")
    ax.set_title(f"Participação em finalizações (np-xG + xA)\n{title}", color="white", fontsize=14)
    if path:
        fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    return fig
