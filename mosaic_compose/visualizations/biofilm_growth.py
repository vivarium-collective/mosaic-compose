"""BiofilmColonyGrowth — colony size over time for the agent-based biofilm.

The number of cells in the pymunk colony as it grows and divides, on a log axis
so the exponential growth phase reads as a straight line. This is the scalar
projection of a spatial agent-based model: each division is a step up in the
count, and the slope is the colony's effective doubling rate.
"""
from __future__ import annotations

import json
import math

from process_bigraph.visualization import Visualization

_COLOR = "#7c3aed"  # violet — colony size


def _downsample(xs, ys, cap=600):
    n = len(xs)
    if n <= cap:
        return list(xs), list(ys)
    step = max(1, n // cap)
    return list(xs[::step]), list(ys[::step])


class BiofilmColonyGrowth(Visualization):
    """Colony size (cell count) over time for the agent-based biofilm."""

    def inputs(self):
        return {"cell_count": "list[float]", "time": "list[float]"}

    @staticmethod
    def generate_state(config=None):
        return {
            "time": [0, 20, 40, 60, 80, 100, 120, 140, 160],
            "cell_count": [3, 6, 9, 16, 20, 26, 38, 44, 55],
        }

    def update(self, state):
        t = list(state.get("time") or [])
        c = list(state.get("cell_count") or [])
        n = min(len(t), len(c)) or 0
        t, c = t[:n], c[:n]
        t, c = _downsample(t, c)
        c = [max(float(v), 1.0) for v in c]  # log axis needs > 0

        c_end = int(c[-1]) if c else 0
        c0 = c[0] if c else 1.0
        # Effective doublings over the run (log2 of the fold increase).
        doublings = math.log2(c_end / c0) if c0 and c_end else 0.0

        traces = [{
            "x": t, "y": c, "type": "scatter", "mode": "lines+markers",
            "name": "colony size",
            "line": {"color": _COLOR, "width": 3, "shape": "hv"},
            "marker": {"size": 4, "color": _COLOR},
            "hovertemplate": "t=%{x:.0f}<br>%{y:.0f} cells<extra></extra>",
        }]
        hi = math.ceil(math.log10(max(c + [10])))
        layout = {
            "title": {
                "text": "Agent-based biofilm: the colony grows and divides<br>"
                        "<span style='font-size:12px;color:#64748b'>pymunk rod cells grow, divide, and pack a 2-D chamber (viva-munk); count on a log axis</span>",
                "x": 0.02, "xanchor": "left", "font": {"size": 17},
            },
            "xaxis": {"title": {"text": "time (arb. units)"}, "zeroline": False,
                      "gridcolor": "rgba(148,163,184,0.18)"},
            "yaxis": {"title": {"text": "colony size (cells, log)"}, "type": "log",
                      "range": [0, hi], "gridcolor": "rgba(148,163,184,0.18)"},
            "showlegend": False,
            "margin": {"l": 60, "r": 20, "t": 64, "b": 55},
            "plot_bgcolor": "rgba(0,0,0,0)", "paper_bgcolor": "rgba(0,0,0,0)",
            "annotations": [{
                "xref": "paper", "yref": "paper", "x": 0.98, "y": 0.08, "xanchor": "right",
                "text": f"{int(c0)} → {c_end} cells  (~{doublings:.1f} doublings)",
                "showarrow": False, "font": {"size": 12, "color": "#334155"},
                "bgcolor": "rgba(255,255,255,0.7)",
            }],
        }
        caption = (
            "Each rod cell grows by an adder rule and divides when it adds a fixed "
            "increment; pymunk resolves the physical packing as the colony fills the "
            "chamber. The colony store is spatial (per-cell positions, map[pymunk_agent]); "
            "a small CountCells step projects it to this emittable colony-size trajectory."
        )
        return {"html": (
            '<div id="biofilm_growth" style="height:380px"></div>'
            f'<p style="font-size:12px;color:#64748b;margin:6px 10px 0;line-height:1.4">{caption}</p>'
            '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'
            '<script>Plotly.newPlot("biofilm_growth",'
            + json.dumps(traces) + "," + json.dumps(layout)
            + ", {responsive:true, displayModeBar:false});</script>"
        )}
