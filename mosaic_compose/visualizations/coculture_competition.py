"""CocultureCompetition — two dFBA organisms competing for a shared substrate.

Two biomass trajectories (left axis) against the shared glucose pool (right axis)
so the composition's coupling is undeniable: both organisms draw from one
glucose store, and the faster glucose specialist (E. coli core) outgrows
Lactobacillus as the shared pool is exhausted.
"""
from __future__ import annotations

import json

from process_bigraph.visualization import Visualization

_ECOLI = "#1d4ed8"   # blue — E. coli core
_LACTO = "#0d9488"   # teal — Lactobacillus
_GLC = "#ea580c"     # orange — shared glucose


def _downsample(xs, ys, cap=800):
    n = len(xs)
    if n <= cap:
        return list(xs), list(ys)
    step = max(1, n // cap)
    return list(xs[::step]), list(ys[::step])


class CocultureCompetition(Visualization):
    """Two organisms' biomass + the shared glucose pool over time (co-culture)."""

    def inputs(self):
        return {
            "biomass_ecoli": "list[float]",
            "biomass_lacto": "list[float]",
            "glucose": "list[float]",
            "time": "list[float]",
        }

    @staticmethod
    def generate_state(config=None):
        return {
            "time": [0, 20, 40, 60, 80, 100, 120, 150, 180, 200],
            "biomass_ecoli": [0.01, 0.03, 0.09, 0.24, 0.55, 0.95, 1.22, 1.34, 1.35, 1.355],
            "biomass_lacto": [0.01, 0.012, 0.014, 0.016, 0.017, 0.018, 0.018, 0.018, 0.018, 0.018],
            "glucose": [15.0, 13.8, 11.2, 7.6, 3.9, 1.2, 0.2, 0.0, 0.0, 0.0],
        }

    def update(self, state):
        t = list(state.get("time") or [])
        be = list(state.get("biomass_ecoli") or [])
        bl = list(state.get("biomass_lacto") or [])
        g = list(state.get("glucose") or [])
        n = min(len(t), len(be), len(bl), len(g)) or 0
        t, be, bl, g = t[:n], be[:n], bl[:n], g[:n]
        src_t = state.get("time") or []
        t, be = _downsample(t, be)
        _, bl = _downsample(src_t, bl)
        _, g = _downsample(src_t, g)

        g0 = g[0] if g else 0.0
        exhaust_t = next((ti for ti, gv in zip(t, g) if g0 and gv < 0.05 * g0), None)

        traces = [
            {"x": t, "y": be, "type": "scatter", "mode": "lines", "name": "E. coli core",
             "line": {"color": _ECOLI, "width": 3}, "yaxis": "y",
             "hovertemplate": "t=%{x:.1f}<br>E. coli=%{y:.3f} gDW/L<extra></extra>"},
            {"x": t, "y": bl, "type": "scatter", "mode": "lines", "name": "Lactobacillus",
             "line": {"color": _LACTO, "width": 3}, "yaxis": "y",
             "hovertemplate": "t=%{x:.1f}<br>Lactobacillus=%{y:.3f} gDW/L<extra></extra>"},
            {"x": t, "y": g, "type": "scatter", "mode": "lines", "name": "shared glucose",
             "line": {"color": _GLC, "width": 2.5, "dash": "dot"}, "yaxis": "y2", "fill": "tozeroy",
             "fillcolor": "rgba(234,88,12,0.06)",
             "hovertemplate": "t=%{x:.1f}<br>glucose=%{y:.2f} mM<extra></extra>"},
        ]
        shapes, annotations = [], []
        if exhaust_t is not None:
            shapes.append({"type": "line", "xref": "x", "yref": "paper",
                           "x0": exhaust_t, "x1": exhaust_t, "y0": 0, "y1": 1,
                           "line": {"dash": "dash", "color": "#94a3b8", "width": 1}})
            annotations.append({"xref": "x", "yref": "paper", "x": exhaust_t, "y": 1.02,
                                "text": "shared glucose exhausted", "showarrow": False,
                                "font": {"size": 11, "color": "#64748b"}, "xanchor": "center"})

        layout = {
            "title": {
                "text": "Composition: two dFBA organisms compete for one glucose pool<br>"
                        "<span style='font-size:12px;color:#64748b'>E. coli core outgrows Lactobacillus as the shared substrate is exhausted</span>",
                "x": 0.02, "xanchor": "left", "font": {"size": 17},
            },
            "xaxis": {"title": {"text": "time (arb. units)"},
                      "gridcolor": "rgba(148,163,184,0.18)", "zeroline": False},
            "yaxis": {"title": {"text": "biomass (gDW/L)"}, "rangemode": "tozero",
                      "gridcolor": "rgba(148,163,184,0.18)"},
            "yaxis2": {"title": {"text": "glucose (mM)", "font": {"color": _GLC}},
                       "tickfont": {"color": _GLC}, "overlaying": "y", "side": "right",
                       "rangemode": "tozero", "showgrid": False},
            "legend": {"orientation": "h", "y": -0.2, "x": 0},
            "margin": {"l": 60, "r": 60, "t": 64, "b": 70},
            "plot_bgcolor": "rgba(0,0,0,0)", "paper_bgcolor": "rgba(0,0,0,0)",
            "shapes": shapes, "annotations": annotations,
        }
        caption = (
            "Both organisms are independent viva-cobra dFBA models wired into one "
            "composite through a shared `substrates` store. The FBA solves write "
            "consumption as deltas, so competition for glucose composes additively "
            "— the faster glucose specialist (E. coli core) wins the shared pool."
        )
        return {"html": (
            '<div id="coculture_competition" style="height:380px"></div>'
            f'<p style="font-size:12px;color:#64748b;margin:6px 10px 0;line-height:1.4">{caption}</p>'
            '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'
            '<script>Plotly.newPlot("coculture_competition",'
            + json.dumps(traces) + "," + json.dumps(layout)
            + ", {responsive:true, displayModeBar:false});</script>"
        )}
