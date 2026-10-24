"""EstrogenEnterohepatic — three-compartment estrogen PK over time.

Overlays the systemic (E_blood), biliary-conjugate (EG_gut), and gut-lumen
(E_gut) compartments so the enterohepatic recirculation + clearance dynamics are
visible in one view. Systemic exposure (the clinically relevant signal) is filled.
"""
from __future__ import annotations

import json

from process_bigraph.visualization import Visualization

_BLOOD = "#7c3aed"   # violet — systemic free estrogen
_CONJ = "#f59e0b"    # amber — conjugated EG in gut (biliary delivery)
_GUT = "#0d9488"     # teal — free E in gut lumen (after microbial deconjugation)


def _downsample(xs, ys, cap=800):
    n = len(xs)
    if n <= cap:
        return list(xs), list(ys)
    step = max(1, n // cap)
    return list(xs[::step]), list(ys[::step])


class EstrogenEnterohepatic(Visualization):
    """Systemic / conjugate / gut-lumen estrogen compartments over time."""

    def inputs(self):
        return {
            "e_blood": "list[float]",
            "eg_gut": "list[float]",
            "e_gut": "list[float]",
            "time": "list[float]",
        }

    @staticmethod
    def generate_state(config=None):
        return {
            "time": [0, 2, 4, 6, 8, 12, 18, 24, 36, 48],
            "e_blood": [1.0, 0.72, 0.55, 0.44, 0.36, 0.25, 0.15, 0.09, 0.03, 0.012],
            "eg_gut": [0.0, 0.17, 0.22, 0.22, 0.20, 0.15, 0.10, 0.06, 0.02, 0.008],
            "e_gut": [0.0, 0.08, 0.13, 0.14, 0.14, 0.11, 0.07, 0.045, 0.016, 0.006],
        }

    def update(self, state):
        t = list(state.get("time") or [])
        eb = list(state.get("e_blood") or [])
        eg = list(state.get("eg_gut") or [])
        eu = list(state.get("e_gut") or [])
        n = min(len(t), len(eb), len(eg), len(eu)) or 0
        t, eb, eg, eu = t[:n], eb[:n], eg[:n], eu[:n]
        src_t = state.get("time") or []
        t, eb = _downsample(t, eb)
        _, eg = _downsample(src_t, eg)
        _, eu = _downsample(src_t, eu)

        traces = [
            {"x": t, "y": eb, "type": "scatter", "mode": "lines", "name": "E_blood (systemic)",
             "line": {"color": _BLOOD, "width": 3}, "fill": "tozeroy",
             "fillcolor": "rgba(124,58,237,0.10)",
             "hovertemplate": "t=%{x:.1f}<br>E_blood=%{y:.3f}<extra></extra>"},
            {"x": t, "y": eg, "type": "scatter", "mode": "lines", "name": "EG_gut (conjugate)",
             "line": {"color": _CONJ, "width": 2.5},
             "hovertemplate": "t=%{x:.1f}<br>EG_gut=%{y:.3f}<extra></extra>"},
            {"x": t, "y": eu, "type": "scatter", "mode": "lines", "name": "E_gut (deconjugated)",
             "line": {"color": _GUT, "width": 2.5},
             "hovertemplate": "t=%{x:.1f}<br>E_gut=%{y:.3f}<extra></extra>"},
        ]
        layout = {
            "title": {
                "text": "Estrogen enterohepatic recycling<br>"
                        "<span style='font-size:12px;color:#64748b'>bile delivers conjugate to the gut; microbial β-glucuronidase (gus) deconjugates it for reabsorption</span>",
                "x": 0.02, "xanchor": "left", "font": {"size": 17},
            },
            "xaxis": {"title": {"text": "time (arb. units)"},
                      "gridcolor": "rgba(148,163,184,0.18)", "zeroline": False},
            "yaxis": {"title": {"text": "relative concentration"}, "rangemode": "tozero",
                      "gridcolor": "rgba(148,163,184,0.18)"},
            "legend": {"orientation": "h", "y": -0.2, "x": 0},
            "margin": {"l": 60, "r": 20, "t": 64, "b": 70},
            "plot_bgcolor": "rgba(0,0,0,0)", "paper_bgcolor": "rgba(0,0,0,0)",
        }
        caption = (
            "A bolus of systemic estrogen (E_blood=1) is conjugated and secreted into the gut "
            "(EG_gut), where microbial β-glucuronidase deconjugates it to free E_gut for "
            "reabsorption. The gus knob sets how much is recycled vs excreted — raising gus "
            "slows systemic clearance."
        )
        return {"html": (
            '<div id="estrogen_ehc" style="height:380px"></div>'
            f'<p style="font-size:12px;color:#64748b;margin:6px 10px 0;line-height:1.4">{caption}</p>'
            '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'
            '<script>Plotly.newPlot("estrogen_ehc",'
            + json.dumps(traces) + "," + json.dumps(layout)
            + ", {responsive:true, displayModeBar:false});</script>"
        )}
