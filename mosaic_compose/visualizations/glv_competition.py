"""GLVCompetition — Lactobacillus vs Gardnerella community dynamics over time.

A shared-axis view of the two species' relative abundances, with filled areas
and an annotation of the protective state the community resolves into. Makes the
competitive outcome (Lactobacillus excludes Gardnerella → low-pH "healthy"
state) undeniable at a glance.
"""
from __future__ import annotations

import json

from process_bigraph.visualization import Visualization

# Consistent MOSAIC community palette (reused by the phase portrait):
#   Lactobacillus = protective teal; Gardnerella = BV rose.
_L_COLOR = "#0d9488"
_G_COLOR = "#e11d48"


def _downsample(xs, ys, cap=800):
    """Keep ~cap evenly-spaced points so long runs stay light without losing shape."""
    n = len(xs)
    if n <= cap:
        return list(xs), list(ys)
    step = max(1, n // cap)
    return list(xs[::step]), list(ys[::step])


class GLVCompetition(Visualization):
    """Lactobacillus vs Gardnerella relative abundance over time (gLV competition)."""

    def inputs(self):
        return {
            "lactobacillus": "list[float]",
            "gardnerella": "list[float]",
            "time": "list[float]",
        }

    @staticmethod
    def generate_state(config=None):
        return {
            "time": [0, 10, 20, 30, 40, 50, 60, 80, 100, 120],
            "lactobacillus": [0.45, 0.58, 0.70, 0.82, 0.90, 0.95, 0.98, 0.997, 0.9997, 1.0],
            "gardnerella": [0.08, 0.14, 0.15, 0.11, 0.06, 0.03, 0.012, 0.002, 2e-4, 2e-5],
        }

    def update(self, state):
        t = list(state.get("time") or [])
        L = list(state.get("lactobacillus") or [])
        G = list(state.get("gardnerella") or [])
        n = min(len(t), len(L), len(G)) or 0
        t, L, G = t[:n], L[:n], G[:n]
        t, L = _downsample(t, L)
        _, G = _downsample(state.get("time") or [], G)

        L_end = L[-1] if L else 0.0
        G_end = G[-1] if G else 0.0
        winner = ("Lactobacillus-dominant (protective)" if L_end >= G_end
                  else "Gardnerella-dominant (BV)")
        win_color = _L_COLOR if L_end >= G_end else _G_COLOR

        traces = [
            {"x": t, "y": L, "type": "scatter", "mode": "lines",
             "name": "Lactobacillus (protective)",
             "line": {"color": _L_COLOR, "width": 3, "shape": "spline"},
             "fill": "tozeroy", "fillcolor": "rgba(13,148,136,0.12)",
             "hovertemplate": "t=%{x:.1f}<br>Lactobacillus=%{y:.3f}<extra></extra>"},
            {"x": t, "y": G, "type": "scatter", "mode": "lines",
             "name": "Gardnerella (BV)",
             "line": {"color": _G_COLOR, "width": 3, "shape": "spline"},
             "fill": "tozeroy", "fillcolor": "rgba(225,29,72,0.10)",
             "hovertemplate": "t=%{x:.1f}<br>Gardnerella=%{y:.3f}<extra></extra>"},
        ]
        layout = {
            "title": {
                "text": "Lactobacillus competitively excludes Gardnerella<br>"
                        "<span style='font-size:12px;color:#64748b'>generalized Lotka-Volterra community; resolves to the protective low-pH state</span>",
                "x": 0.02, "xanchor": "left", "font": {"size": 17},
            },
            "xaxis": {"title": {"text": "time (arb. units)"}, "zeroline": False,
                      "gridcolor": "rgba(148,163,184,0.18)"},
            "yaxis": {"title": {"text": "relative abundance"}, "rangemode": "tozero",
                      "gridcolor": "rgba(148,163,184,0.18)"},
            "legend": {"orientation": "h", "y": -0.2, "x": 0},
            "margin": {"l": 60, "r": 20, "t": 64, "b": 70},
            "plot_bgcolor": "rgba(0,0,0,0)", "paper_bgcolor": "rgba(0,0,0,0)",
            "annotations": [{
                "xref": "paper", "yref": "paper", "x": 0.98, "y": 0.5,
                "xanchor": "right", "text": f"→ {winner}",
                "showarrow": False, "font": {"size": 12, "color": win_color},
            }],
        }
        caption = (
            "Starting from a Lactobacillus-leaning community (L=0.45, G=0.08), "
            "asymmetric competition drives the system to the protective "
            "Lactobacillus-dominant state as Gardnerella is excluded."
        )
        return {"html": (
            '<div id="glv_competition" style="height:380px"></div>'
            f'<p style="font-size:12px;color:#64748b;margin:6px 10px 0;line-height:1.4">{caption}</p>'
            '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'
            '<script>Plotly.newPlot("glv_competition",'
            + json.dumps(traces) + "," + json.dumps(layout)
            + ", {responsive:true, displayModeBar:false});</script>"
        )}
