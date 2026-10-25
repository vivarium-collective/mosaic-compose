"""GLVPhasePortrait — the gLV community trajectory in (Gardnerella, Lactobacillus) phase space.

A 2D trajectory colored by time, flowing from the initial community to the
Lactobacillus-dominant fixed point. A phase portrait makes the competitive
*exclusion* geometry obvious: the state is pulled to one corner of the simplex.
"""
from __future__ import annotations

import json

from process_bigraph.visualization import Visualization


def _downsample(xs, ys, cap=600):
    n = len(xs)
    if n <= cap:
        return list(xs), list(ys)
    step = max(1, n // cap)
    return list(xs[::step]), list(ys[::step])


class GLVPhasePortrait(Visualization):
    """(Gardnerella, Lactobacillus) phase-space trajectory colored by time."""

    def inputs(self):
        return {"lactobacillus": "list[float]", "gardnerella": "list[float]"}

    @staticmethod
    def generate_state(config=None):
        return {
            "lactobacillus": [0.45, 0.58, 0.70, 0.82, 0.90, 0.95, 0.98, 0.997, 0.9997, 1.0],
            "gardnerella": [0.08, 0.14, 0.15, 0.11, 0.06, 0.03, 0.012, 0.002, 2e-4, 2e-5],
        }

    def update(self, state):
        L = list(state.get("lactobacillus") or [])
        G = list(state.get("gardnerella") or [])
        n = min(len(L), len(G)) or 0
        L, G = L[:n], G[:n]
        G, L = _downsample(G, L)
        steps = list(range(len(L)))

        traces = [{
            "x": G, "y": L, "type": "scatter", "mode": "lines+markers", "name": "trajectory",
            "line": {"color": "rgba(100,116,139,0.55)", "width": 2},
            "marker": {"size": 6, "color": steps, "colorscale": "Viridis",
                       "showscale": True,
                       "colorbar": {"title": {"text": "step"}, "thickness": 12}},
            "hovertemplate": "Gardnerella=%{x:.3f}<br>Lactobacillus=%{y:.3f}<extra></extra>",
        }]
        if L and G:
            traces.append({
                "x": [G[0]], "y": [L[0]], "type": "scatter", "mode": "markers+text",
                "name": "start", "text": ["start"], "textposition": "top right",
                "marker": {"size": 13, "color": "#0ea5e9", "symbol": "circle",
                           "line": {"color": "#fff", "width": 1.5}},
                "hovertemplate": "start<br>G=%{x:.3f} L=%{y:.3f}<extra></extra>"})
            traces.append({
                "x": [G[-1]], "y": [L[-1]], "type": "scatter", "mode": "markers+text",
                "name": "fixed point", "text": ["L-dominant"], "textposition": "bottom left",
                "marker": {"size": 15, "color": "#0d9488", "symbol": "star",
                           "line": {"color": "#fff", "width": 1.5}},
                "hovertemplate": "fixed point<br>G=%{x:.3f} L=%{y:.3f}<extra></extra>"})

        layout = {
            "title": {
                "text": "Phase portrait: the community is pulled to the Lactobacillus corner<br>"
                        "<span style='font-size:12px;color:#64748b'>trajectory in (Gardnerella, Lactobacillus) space, colored by time</span>",
                "x": 0.02, "xanchor": "left", "font": {"size": 17},
            },
            "xaxis": {"title": {"text": "Gardnerella (relative abundance)"},
                      "gridcolor": "rgba(148,163,184,0.18)", "zeroline": False},
            "yaxis": {"title": {"text": "Lactobacillus (relative abundance)"},
                      "gridcolor": "rgba(148,163,184,0.18)", "zeroline": False,
                      "scaleanchor": "x", "scaleratio": 1},
            "showlegend": False,
            "margin": {"l": 60, "r": 20, "t": 64, "b": 55},
            "plot_bgcolor": "rgba(0,0,0,0)", "paper_bgcolor": "rgba(0,0,0,0)",
        }
        caption = (
            "Each point is the community state at one time step; color runs early→late. "
            "The flow leaves the mixed start and converges on the Lactobacillus-dominant "
            "fixed point (Gardnerella → 0) — competitive exclusion, not coexistence."
        )
        return {"html": (
            '<div id="glv_phase" style="height:400px"></div>'
            f'<p style="font-size:12px;color:#64748b;margin:6px 10px 0;line-height:1.4">{caption}</p>'
            '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'
            '<script>Plotly.newPlot("glv_phase",'
            + json.dumps(traces) + "," + json.dumps(layout)
            + ", {responsive:true, displayModeBar:false});</script>"
        )}
