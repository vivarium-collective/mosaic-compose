"""DFBAGrowth — dynamic-FBA growth curve with substrate depletion (dual axis).

Biomass accumulation (left axis, filled) against the shared substrate pools
(right axis) so the coupling is obvious: the cell grows while it draws down
glucose, and growth slows as the preferred substrate is exhausted.
"""
from __future__ import annotations

import json

from process_bigraph.visualization import Visualization

_BIO = "#1d4ed8"     # blue — biomass
_GLC = "#ea580c"     # orange — glucose (preferred)
_GLU = "#16a34a"     # green — glutamate


def _downsample(xs, ys, cap=800):
    n = len(xs)
    if n <= cap:
        return list(xs), list(ys)
    step = max(1, n // cap)
    return list(xs[::step]), list(ys[::step])


class DFBAGrowth(Visualization):
    """Biomass growth + substrate depletion over time (dynamic FBA), dual y-axis."""

    def inputs(self):
        return {
            "biomass": "list[float]",
            "glucose": "list[float]",
            "glutamate": "list[float]",
            "time": "list[float]",
        }

    @staticmethod
    def generate_state(config=None):
        return {
            "time": [0, 5, 10, 15, 20, 25, 30, 40, 50, 60],
            "biomass": [0.01, 0.03, 0.08, 0.18, 0.33, 0.48, 0.60, 0.69, 0.71, 0.711],
            "glucose": [20.0, 17.5, 13.8, 9.2, 4.9, 1.8, 0.5, 0.08, 0.04, 0.039],
            "glutamate": [5.0, 4.6, 4.1, 3.5, 2.9, 2.5, 2.2, 1.95, 1.84, 1.813],
        }

    def update(self, state):
        t = list(state.get("time") or [])
        bio = list(state.get("biomass") or [])
        glc = list(state.get("glucose") or [])
        glu = list(state.get("glutamate") or [])
        n = min(len(t), len(bio), len(glc), len(glu)) or 0
        t, bio, glc, glu = t[:n], bio[:n], glc[:n], glu[:n]
        src_t = state.get("time") or []
        t, bio = _downsample(t, bio)
        _, glc = _downsample(src_t, glc)
        _, glu = _downsample(src_t, glu)

        glc0 = glc[0] if glc else 0.0
        exhaust_t = None
        for ti, g in zip(t, glc):
            if glc0 and g < 0.05 * glc0:
                exhaust_t = ti
                break

        traces = [
            {"x": t, "y": bio, "type": "scatter", "mode": "lines", "name": "biomass",
             "line": {"color": _BIO, "width": 3}, "fill": "tozeroy",
             "fillcolor": "rgba(29,78,216,0.10)", "yaxis": "y",
             "hovertemplate": "t=%{x:.1f}<br>biomass=%{y:.3f} gDW/L<extra></extra>"},
            {"x": t, "y": glc, "type": "scatter", "mode": "lines", "name": "glucose",
             "line": {"color": _GLC, "width": 2.5}, "yaxis": "y2",
             "hovertemplate": "t=%{x:.1f}<br>glucose=%{y:.2f} mM<extra></extra>"},
            {"x": t, "y": glu, "type": "scatter", "mode": "lines", "name": "glutamate",
             "line": {"color": _GLU, "width": 2.5, "dash": "dot"}, "yaxis": "y2",
             "hovertemplate": "t=%{x:.1f}<br>glutamate=%{y:.2f} mM<extra></extra>"},
        ]
        shapes, annotations = [], []
        if exhaust_t is not None:
            shapes.append({"type": "line", "xref": "x", "yref": "paper",
                           "x0": exhaust_t, "x1": exhaust_t, "y0": 0, "y1": 1,
                           "line": {"dash": "dash", "color": "#94a3b8", "width": 1}})
            annotations.append({"xref": "x", "yref": "paper", "x": exhaust_t, "y": 1.02,
                                "text": "glucose exhausted", "showarrow": False,
                                "font": {"size": 11, "color": "#64748b"}, "xanchor": "center"})

        layout = {
            "title": {
                "text": "Dynamic FBA: biomass grows as substrates are drawn down<br>"
                        "<span style='font-size:12px;color:#64748b'>Lactobacillus GEM (iNF517) under Michaelis-Menten uptake → COBRApy FBA</span>",
                "x": 0.02, "xanchor": "left", "font": {"size": 17},
            },
            "xaxis": {"title": {"text": "time (arb. units)"},
                      "gridcolor": "rgba(148,163,184,0.18)", "zeroline": False},
            "yaxis": {"title": {"text": "biomass (gDW/L)", "font": {"color": _BIO}},
                      "tickfont": {"color": _BIO}, "rangemode": "tozero",
                      "gridcolor": "rgba(148,163,184,0.18)"},
            "yaxis2": {"title": {"text": "substrate (mM)", "font": {"color": _GLC}},
                       "tickfont": {"color": _GLC}, "overlaying": "y", "side": "right",
                       "rangemode": "tozero", "showgrid": False},
            "legend": {"orientation": "h", "y": -0.2, "x": 0},
            "margin": {"l": 60, "r": 60, "t": 64, "b": 70},
            "plot_bgcolor": "rgba(0,0,0,0)", "paper_bgcolor": "rgba(0,0,0,0)",
            "shapes": shapes, "annotations": annotations,
        }
        caption = (
            "Michaelis-Menten uptake turns substrate concentrations into FBA exchange bounds; "
            "the COBRApy solve returns growth rate + fluxes, and the shared pools update each step. "
            "Biomass rises as glucose (preferred) is consumed, then growth slows."
        )
        return {"html": (
            '<div id="dfba_growth" style="height:380px"></div>'
            f'<p style="font-size:12px;color:#64748b;margin:6px 10px 0;line-height:1.4">{caption}</p>'
            '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'
            '<script>Plotly.newPlot("dfba_growth",'
            + json.dumps(traces) + "," + json.dumps(layout)
            + ", {responsive:true, displayModeBar:false});</script>"
        )}
