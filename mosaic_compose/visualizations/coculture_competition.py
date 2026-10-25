"""CocultureCompetition — two dFBA organisms competing for a shared substrate.

Both organisms' biomass on a LOG axis (so the fast winner and the suppressed
competitor are both legible) against the shared glucose pool, with the x-axis
focused on the active growth window (the batch run plateaus once glucose is
gone, so the flat tail is trimmed). Makes the composition's coupling readable:
both draw from one glucose store and the faster specialist pulls ahead.
"""
from __future__ import annotations

import json
import math

from process_bigraph.visualization import Visualization

_ECOLI = "#1d4ed8"   # blue — E. coli core
_LACTO = "#0d9488"   # teal — Lactobacillus
_GLC = "#ea580c"     # orange — shared glucose


def _downsample(xs, ys, cap=600):
    n = len(xs)
    if n <= cap:
        return list(xs), list(ys)
    step = max(1, n // cap)
    return list(xs[::step]), list(ys[::step])


class CocultureCompetition(Visualization):
    """Two organisms' biomass (log) + the shared glucose pool over the active window."""

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
            "time": [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0],
            "biomass_ecoli": [0.004, 0.012, 0.033, 0.089, 0.24, 0.52, 0.76, 0.81, 0.812, 0.812],
            "biomass_lacto": [0.004, 0.006, 0.010, 0.016, 0.025, 0.037, 0.045, 0.046, 0.046, 0.046],
            "glucose": [10.0, 9.4, 8.3, 6.5, 4.1, 1.7, 0.3, 0.02, 0.02, 0.02],
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

        # Active window: a little past the point glucose is effectively exhausted
        # (the batch run is flat after that). Fall back to the full range.
        g0 = g[0] if g else 0.0
        exhaust_t = next((ti for ti, gv in zip(t, g) if g0 and gv < 0.02 * g0), None)
        x_max = (exhaust_t * 1.25) if exhaust_t else (t[-1] if t else 1.0)

        # Log y needs strictly-positive values; clamp a floor just for display.
        floor = 1e-3
        be_p = [max(v, floor) for v in be]
        bl_p = [max(v, floor) for v in bl]
        be_end = be[-1] if be else 0.0
        bl_end = bl[-1] if bl else 0.0
        ratio = (be_end / bl_end) if bl_end else float("inf")

        traces = [
            {"x": t, "y": be_p, "type": "scatter", "mode": "lines", "name": "E. coli core",
             "line": {"color": _ECOLI, "width": 3}, "yaxis": "y",
             "hovertemplate": "t=%{x:.2f}<br>E. coli=%{y:.3g} gDW/L<extra></extra>"},
            {"x": t, "y": bl_p, "type": "scatter", "mode": "lines", "name": "Lactobacillus",
             "line": {"color": _LACTO, "width": 3}, "yaxis": "y",
             "hovertemplate": "t=%{x:.2f}<br>Lactobacillus=%{y:.3g} gDW/L<extra></extra>"},
            {"x": t, "y": g, "type": "scatter", "mode": "lines", "name": "shared glucose",
             "line": {"color": _GLC, "width": 2.5, "dash": "dot"}, "yaxis": "y2", "fill": "tozeroy",
             "fillcolor": "rgba(234,88,12,0.06)",
             "hovertemplate": "t=%{x:.2f}<br>glucose=%{y:.2f} mM<extra></extra>"},
        ]
        shapes, annotations = [], []
        if exhaust_t is not None:
            shapes.append({"type": "line", "xref": "x", "yref": "paper",
                           "x0": exhaust_t, "x1": exhaust_t, "y0": 0, "y1": 1,
                           "line": {"dash": "dash", "color": "#94a3b8", "width": 1}})
            annotations.append({"xref": "x", "yref": "paper", "x": exhaust_t, "y": 1.03,
                                "text": "shared glucose exhausted", "showarrow": False,
                                "font": {"size": 11, "color": "#64748b"}, "xanchor": "center"})
        # Outcome label: final biomass ratio (the "who won, by how much").
        if math.isfinite(ratio) and ratio > 0:
            annotations.append({
                "xref": "paper", "yref": "paper", "x": 0.98, "y": 0.06, "xanchor": "right",
                "text": f"E. coli : Lactobacillus ≈ {ratio:.0f} : 1 at glucose exhaustion",
                "showarrow": False, "font": {"size": 11, "color": "#334155"},
                "bgcolor": "rgba(255,255,255,0.7)",
            })

        # log-axis tick range from the data
        lo = math.floor(math.log10(max(min(be_p + bl_p), floor)))
        hi = math.ceil(math.log10(max(be_p + bl_p + [floor * 10])))
        layout = {
            "title": {
                "text": "Composition: two dFBA organisms share one glucose pool<br>"
                        "<span style='font-size:12px;color:#64748b'>biomass on a log axis; E. coli core pulls ahead of Lactobacillus as the shared substrate runs out</span>",
                "x": 0.02, "xanchor": "left", "font": {"size": 17},
            },
            "xaxis": {"title": {"text": "time (arb. units)"}, "range": [0, x_max],
                      "gridcolor": "rgba(148,163,184,0.18)", "zeroline": False},
            "yaxis": {"title": {"text": "biomass (gDW/L, log)"}, "type": "log",
                      "range": [lo, hi], "gridcolor": "rgba(148,163,184,0.18)"},
            "yaxis2": {"title": {"text": "glucose (mM)", "font": {"color": _GLC}},
                       "tickfont": {"color": _GLC}, "overlaying": "y", "side": "right",
                       "rangemode": "tozero", "showgrid": False},
            "legend": {"orientation": "h", "y": -0.2, "x": 0},
            "margin": {"l": 64, "r": 60, "t": 64, "b": 70},
            "plot_bgcolor": "rgba(0,0,0,0)", "paper_bgcolor": "rgba(0,0,0,0)",
            "shapes": shapes, "annotations": annotations,
        }
        caption = (
            "Both organisms are independent viva-cobra dFBA models wired into one composite "
            "through a shared `substrates` store (FBA writes consumption as deltas, so the draw "
            "on glucose composes additively — no custom coupling process). On the shared pool the "
            "faster glucose specialist (E. coli core) outgrows Lactobacillus; the log axis keeps "
            "both growth curves legible, and the view is trimmed to the active growth window."
        )
        return {"html": (
            '<div id="coculture_competition" style="height:380px"></div>'
            f'<p style="font-size:12px;color:#64748b;margin:6px 10px 0;line-height:1.4">{caption}</p>'
            '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'
            '<script>Plotly.newPlot("coculture_competition",'
            + json.dumps(traces) + "," + json.dumps(layout)
            + ", {responsive:true, displayModeBar:false});</script>"
        )}
