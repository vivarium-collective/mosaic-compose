"""AmineCrossfeeding — BV biogenic-amine cross-feeding dynamics over time.

Renders the live run of ``mosaic_amine_crossfeeding``: Lactobacillus & Gardnerella
relative abundance and the biogenic-amine pool (normalised by its ~mM cap) on the
left axis, with the derived vaginal pH on the right axis. Makes the coupled
mechanism legible at a glance — as Lactobacillus takes over it degrades the amine
pool and acidifies (pH falls toward the protective <4.5 range), or, in the BV
basin, amines accumulate to ~mM and pH climbs.

pH is derived from the Lactate readout with the SAME assignment rule the model
uses (pH = 7.0 - 3.1*Lac/(Lac+0.25)); no value is invented.
"""
from __future__ import annotations

import json

from process_bigraph.visualization import Visualization

_L_COLOR = "#0d9488"   # Lactobacillus — protective teal
_G_COLOR = "#e11d48"   # Gardnerella — BV rose
_A_COLOR = "#9333ea"   # amines — violet
_PH_COLOR = "#f59e0b"  # pH — amber

_A_MAX = 6000.0        # amine normalisation cap (uM), matches the model's A_max


def _downsample(xs, ys, cap=800):
    n = len(xs)
    if n <= cap:
        return list(xs), list(ys)
    step = max(1, n // cap)
    return list(xs[::step]), list(ys[::step])


def _ph_from_lactate(lac):
    return 7.0 - 3.1 * lac / (lac + 0.25)


class AmineCrossfeeding(Visualization):
    """Lactobacillus/Gardnerella/amine-pool/pH dynamics of the BV amine cross-feeding ODE."""

    def inputs(self):
        return {
            "lactobacillus": "list[float]",
            "gardnerella": "list[float]",
            "amines": "list[float]",
            "lactate": "list[float]",
            "time": "list[float]",
        }

    @staticmethod
    def generate_state(config=None):
        # Illustrative shape for a static preview only (recovery trajectory);
        # the live run replaces this with real readouts.
        t = [0, 5, 10, 15, 20, 25, 30, 35, 42]
        return {
            "time": t,
            "lactobacillus": [0.30, 0.38, 0.52, 0.70, 0.85, 0.93, 0.96, 0.97, 0.98],
            "gardnerella": [0.30, 0.31, 0.26, 0.18, 0.10, 0.06, 0.04, 0.03, 0.03],
            "amines": [2000, 2100, 1500, 800, 350, 150, 70, 45, 31],
            "lactate": [0.15, 0.25, 0.55, 1.00, 1.45, 1.63, 1.69, 1.71, 1.71],
        }

    def update(self, state):
        t = list(state.get("time") or [])
        L = list(state.get("lactobacillus") or [])
        G = list(state.get("gardnerella") or [])
        A = list(state.get("amines") or [])
        Lac = list(state.get("lactate") or [])
        n = min(len(t), len(L), len(G), len(A), len(Lac)) or 0
        t, L, G, A, Lac = t[:n], L[:n], G[:n], A[:n], Lac[:n]

        pH = [_ph_from_lactate(x) for x in Lac]
        A_norm = [a / _A_MAX for a in A]

        t_ds, L = _downsample(t, L)
        _, G = _downsample(t, G)
        _, A_norm_ds = _downsample(t, A_norm)
        _, A_raw_ds = _downsample(t, A)
        _, pH_ds = _downsample(t, pH)

        L_end = L[-1] if L else 0.0
        G_end = G[-1] if G else 0.0
        ph_end = pH_ds[-1] if pH_ds else 7.0
        a_end = A_raw_ds[-1] if A_raw_ds else 0.0
        protective = L_end >= G_end
        state_label = (
            f"→ protective (L-dominant, pH {ph_end:.1f}, amines {a_end:.0f} µM)"
            if protective else
            f"→ BV (G-dominant, pH {ph_end:.1f}, amines {a_end:.0f} µM)"
        )
        state_color = _L_COLOR if protective else _G_COLOR

        # amine hover shows real uM even though it is drawn on the normalised axis
        amine_custom = [[a] for a in A_raw_ds]

        traces = [
            {"x": t_ds, "y": A_norm_ds, "type": "scatter", "mode": "lines",
             "name": "amine pool (µM)", "yaxis": "y1",
             "line": {"color": _A_COLOR, "width": 0},
             "fill": "tozeroy", "fillcolor": "rgba(147,51,234,0.12)",
             "customdata": amine_custom,
             "hovertemplate": "t=%{x:.1f}<br>amines=%{customdata[0]:.0f} µM<extra></extra>"},
            {"x": t_ds, "y": L, "type": "scatter", "mode": "lines",
             "name": "Lactobacillus (protective)", "yaxis": "y1",
             "line": {"color": _L_COLOR, "width": 3, "shape": "spline"},
             "hovertemplate": "t=%{x:.1f}<br>Lactobacillus=%{y:.3f}<extra></extra>"},
            {"x": t_ds, "y": G, "type": "scatter", "mode": "lines",
             "name": "Gardnerella (BV)", "yaxis": "y1",
             "line": {"color": _G_COLOR, "width": 3, "shape": "spline"},
             "hovertemplate": "t=%{x:.1f}<br>Gardnerella=%{y:.3f}<extra></extra>"},
            {"x": t_ds, "y": pH_ds, "type": "scatter", "mode": "lines",
             "name": "vaginal pH", "yaxis": "y2",
             "line": {"color": _PH_COLOR, "width": 2.5, "dash": "dot"},
             "hovertemplate": "t=%{x:.1f}<br>pH=%{y:.2f}<extra></extra>"},
        ]
        layout = {
            "title": {
                "text": "Biogenic-amine cross-feeding drives the community + pH<br>"
                        "<span style='font-size:12px;color:#64748b'>Gardnerella amines inhibit Lactobacillus (Borgogna 2021); "
                        "Lactobacillus degrades amines &amp; acidifies (Puebla-Barragan 2021)</span>",
                "x": 0.02, "xanchor": "left", "font": {"size": 16},
            },
            "xaxis": {"title": {"text": "time (arb. units)"}, "zeroline": False,
                      "gridcolor": "rgba(148,163,184,0.18)"},
            "yaxis": {"title": {"text": "relative abundance · amine pool (÷6000 µM)"},
                      "rangemode": "tozero", "gridcolor": "rgba(148,163,184,0.18)",
                      "range": [0, 1.05]},
            "yaxis2": {"title": {"text": "vaginal pH"}, "overlaying": "y", "side": "right",
                       "range": [3.8, 7.1], "showgrid": False,
                       "titlefont": {"color": _PH_COLOR}, "tickfont": {"color": _PH_COLOR}},
            "legend": {"orientation": "h", "y": -0.22, "x": 0},
            "margin": {"l": 62, "r": 58, "t": 66, "b": 76},
            "plot_bgcolor": "rgba(0,0,0,0)", "paper_bgcolor": "rgba(0,0,0,0)",
            "shapes": [{
                "type": "line", "xref": "paper", "x0": 0, "x1": 1,
                "yref": "y2", "y0": 4.5, "y1": 4.5,
                "line": {"color": "rgba(245,158,11,0.5)", "width": 1, "dash": "dash"},
            }],
            "annotations": [
                {"xref": "paper", "yref": "y2", "x": 0.012, "y": 4.5, "xanchor": "left",
                 "yanchor": "bottom", "text": "pH 4.5 (BV threshold)",
                 "showarrow": False, "font": {"size": 10, "color": "#b45309"}},
                {"xref": "paper", "yref": "paper", "x": 0.98, "y": 0.5, "xanchor": "right",
                 "text": state_label, "showarrow": False,
                 "font": {"size": 12, "color": state_color}},
            ],
        }
        caption = (
            "Mechanistic ODE coupling the Lactobacillus–Gardnerella community to the "
            "biogenic-amine pool and pH. Amine growth-inhibition is anchored to Borgogna "
            "2021 (putrescine 3,179 µM → ~25% slower Lactobacillus doubling); amine "
            "degradation and pH-dependent growth from Puebla-Barragan 2021. The loop is "
            "bistable — a protective acidic state vs a BV state with a ~mM amine pool."
        )
        return {"html": (
            '<div id="amine_crossfeeding" style="height:400px"></div>'
            f'<p style="font-size:12px;color:#64748b;margin:6px 10px 0;line-height:1.4">{caption}</p>'
            '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'
            '<script>Plotly.newPlot("amine_crossfeeding",'
            + json.dumps(traces) + "," + json.dumps(layout)
            + ", {responsive:true, displayModeBar:false});</script>"
        )}
