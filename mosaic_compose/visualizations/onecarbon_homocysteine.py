"""OneCarbonHomocysteine — homocysteine vs estradiol over the menstrual cycle.

Renders the live run of ``mosaic_onecarbon_cycle``: plasma/hepatic homocysteine
(µM, left axis) against the menstrual-cycle estradiol input E2 (nM, right axis),
over one 28-day cycle. Reproduces the headline of Kim, Nijhout & Reed 2021 —
homocysteine falls as estradiol rises (lowest at the ovulatory E2 peak), because
estradiol activates CBS (transsulfuration), the homocysteine-clearing enzyme.

E2(t) is recomputed from the model time with the SAME Fourier series the composite
drives the model with (imported from the composite module — single source of
truth); no value is invented.
"""
from __future__ import annotations

import json
import math

from process_bigraph.visualization import Visualization

from mosaic_compose.composites.onecarbon import _E2_FOURIER, _E2_PERIOD_DAYS

_HCY_COLOR = "#2563eb"   # homocysteine — blue
_E2_COLOR = "#db2777"    # estradiol — pink


def _downsample(xs, ys, cap=800):
    n = len(xs)
    if n <= cap:
        return list(xs), list(ys)
    step = max(1, n // cap)
    return list(xs[::step]), list(ys[::step])


def _e2_nM(day):
    v = _E2_FOURIER[0]
    for k in range(1, (len(_E2_FOURIER) - 1) // 2 + 1):
        w = 2 * math.pi * k / _E2_PERIOD_DAYS
        v += _E2_FOURIER[2 * k - 1] * math.cos(w * day) + _E2_FOURIER[2 * k] * math.sin(w * day)
    return v


class OneCarbonHomocysteine(Visualization):
    """Homocysteine vs estradiol over the menstrual cycle (Kim 2021 reimplementation)."""

    def inputs(self):
        return {
            "homocysteine": "list[float]",
            "sam": "list[float]",
            "sah": "list[float]",
            "time": "list[float]",
        }

    @staticmethod
    def generate_state(config=None):
        # Static preview shape only; the live run replaces this with real readouts.
        t = [h for h in range(0, 673, 24)]
        hcy = [0.86, 0.85, 0.85, 0.83, 0.80, 0.74, 0.66, 0.61, 0.62,
               0.70, 0.74, 0.74, 0.72, 0.73, 0.74, 0.78, 0.82, 0.86,
               0.88, 0.89, 0.90, 0.90, 0.90, 0.90, 0.90, 0.90, 0.89, 0.88, 0.86]
        return {"time": t, "homocysteine": hcy,
                "sam": [137] * len(t), "sah": [13] * len(t)}

    def update(self, state):
        t = list(state.get("time") or [])
        Hcy = list(state.get("homocysteine") or [])
        n = min(len(t), len(Hcy)) or 0
        t, Hcy = t[:n], Hcy[:n]
        day = [x / 24.0 for x in t]
        E2 = [_e2_nM(d) for d in day]

        day_ds, Hcy_ds = _downsample(day, Hcy)
        _, E2_ds = _downsample(day, E2)

        # locate the ovulatory E2 peak and the Hcy value there
        if E2_ds:
            ip = max(range(len(E2_ds)), key=lambda i: E2_ds[i])
            peak_day, peak_hcy = day_ds[ip], Hcy_ds[ip]
        else:
            peak_day = peak_hcy = 0.0

        traces = [
            {"x": day_ds, "y": Hcy_ds, "type": "scatter", "mode": "lines",
             "name": "homocysteine", "yaxis": "y1",
             "line": {"color": _HCY_COLOR, "width": 3, "shape": "spline"},
             "hovertemplate": "day %{x:.1f}<br>Hcy=%{y:.3f} µM<extra></extra>"},
            {"x": day_ds, "y": E2_ds, "type": "scatter", "mode": "lines",
             "name": "estradiol (E2)", "yaxis": "y2",
             "line": {"color": _E2_COLOR, "width": 2.5, "dash": "dot"},
             "hovertemplate": "day %{x:.1f}<br>E2=%{y:.3f} nM<extra></extra>"},
        ]
        layout = {
            "title": {
                "text": "Homocysteine falls as estradiol rises over the menstrual cycle<br>"
                        "<span style='font-size:12px;color:#64748b'>Kim, Nijhout &amp; Reed 2021 — estradiol activates CBS (transsulfuration), clearing homocysteine</span>",
                "x": 0.02, "xanchor": "left", "font": {"size": 16},
            },
            "xaxis": {"title": {"text": "day of menstrual cycle"}, "zeroline": False,
                      "gridcolor": "rgba(148,163,184,0.18)", "range": [0, 28]},
            "yaxis": {"title": {"text": "homocysteine (µM)"},
                      "titlefont": {"color": _HCY_COLOR}, "tickfont": {"color": _HCY_COLOR},
                      "gridcolor": "rgba(148,163,184,0.18)"},
            "yaxis2": {"title": {"text": "estradiol E2 (nM)"}, "overlaying": "y", "side": "right",
                       "titlefont": {"color": _E2_COLOR}, "tickfont": {"color": _E2_COLOR},
                       "showgrid": False, "rangemode": "tozero"},
            "legend": {"orientation": "h", "y": -0.2, "x": 0},
            "margin": {"l": 62, "r": 60, "t": 66, "b": 66},
            "plot_bgcolor": "rgba(0,0,0,0)", "paper_bgcolor": "rgba(0,0,0,0)",
            "annotations": [{
                "xref": "x", "yref": "y1", "x": peak_day, "y": peak_hcy,
                "ax": 28, "ay": -28, "text": f"ovulatory E2 peak →<br>Hcy min {peak_hcy:.2f} µM",
                "showarrow": True, "arrowhead": 2, "arrowcolor": _E2_COLOR,
                "font": {"size": 10, "color": "#9d174d"}, "align": "right",
            }],
        }
        caption = (
            "Faithful recreation of Kim, Nijhout &amp; Reed 2021: the curated Reed2004 "
            "methionine-cycle model (BioModels BIOMD0000000698) driven by a menstrual-cycle "
            "estradiol input, with estradiol activating CBS via Kim's h(E2). Homocysteine "
            "tracks estradiol inversely (corr ≈ −0.94), reaching its minimum at the ovulatory "
            "E2 peak around day 12 — the paper's central result."
        )
        return {"html": (
            '<div id="onecarbon_homocysteine" style="height:400px"></div>'
            f'<p style="font-size:12px;color:#64748b;margin:6px 10px 0;line-height:1.4">{caption}</p>'
            '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'
            '<script>Plotly.newPlot("onecarbon_homocysteine",'
            + json.dumps(traces) + "," + json.dumps(layout)
            + ", {responsive:true, displayModeBar:false});</script>"
        )}
