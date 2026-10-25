"""Spatial Cellular-Potts colonic crypt — a second spatial/ABM study.

STATUS: prototype, NOT yet wired into the workspace (not imported in
``composites/__init__.py``, so not discovered/registered). It builds and runs
fast and the Wnt-driven differentiation is real (goblet cells 38 -> 101 over a
short run), but two viva-cpm-side issues block a shippable study:
  * ``positions`` only populates a real centroid for ~1-5 of the ~119 cells (the
    rest come back ``[0, 0, 0]``), so the CryptSpatialMap scatter can't render
    the lattice — this needs a fix in viva-cpm's CPMProcess position output.
  * the CryptCensus counts are correct per tick but the scalar stores ACCUMULATE
    across ticks (need overwrite semantics) — a smaller, fixable wiring issue.
Enable by adding ``from . import crypt`` to ``composites/__init__.py`` once the
positions output is fixed upstream. The capture-the-state wrapper + the inline
spatial-snapshot viz step pattern below are reusable and already validated on
the biofilm colony.


Built on viva-cpm's Rust Cellular-Potts engine over the HRA colonic-crypt FTU:
epithelial stem cells at the crypt base secrete a Wnt morphogen, and progenitor
cells adopt goblet / absorptive fates along the Wnt gradient (an ODE → Boolean →
cell-type coupling). This is a *lattice* spatial model — distinct from the
off-lattice pymunk biofilm colony.

viva-cpm ships `build_crypt_composite(core, …)` but returns a *built* Composite
(not a document) and ships no visualization. Here we: capture the document's
state dict (the function wraps it in a Composite internally), author a
`CryptSpatialMap` inline Visualization step that renders the lattice cells as a
scatter colored by cell type (surfaced to the study's native gallery via the
spatial-snapshot path), and a `CryptCensus` step that emits per-type cell counts
as scalars (the `positions`/`types` lists are spatial and not xarray-emittable).
"""
from __future__ import annotations

import json

import process_bigraph as pb
from process_bigraph.composite import Step
from process_bigraph.composite_generator import composite_generator
from process_bigraph.visualization import Visualization

import viva_cpm.composites.crypt as _crypt_mod

# Cell-type palette (by HRA type name). Medium (background) is never drawn.
_TYPE_COLOR = {
    "Epithelial Stem Cells": "#7c3aed",   # violet — the Wnt-secreting niche
    "Goblet Cells": "#0d9488",            # teal — secretory fate
    "Absorptive Cells": "#ea580c",        # orange — absorptive fate
    "Enteroendocrine Cells": "#eab308",   # amber
    "Tuft Cell": "#64748b",               # slate
}
_DOWNSCALE = 0.25


class CryptSpatialMap(Visualization):
    """Scatter of the Potts crypt cells, colored by cell type (spatial snapshot)."""

    def inputs(self):
        return {"positions": "list", "types": "list"}

    def update(self, state):
        positions = state.get("positions") or []
        types = state.get("types") or []
        names = (getattr(self, "config", None) or {}).get("type_names") or []
        n = min(len(positions), len(types))
        # Group cells by type name, skipping Medium (background) + unplaced (0,0).
        by_type: dict[str, dict] = {}
        for i in range(n):
            p = positions[i]
            if not (isinstance(p, (list, tuple)) and len(p) >= 2):
                continue
            x, y = float(p[0]), float(p[1])
            tid = int(types[i])
            name = names[tid] if 0 <= tid < len(names) else str(tid)
            if name == "Medium" or (x == 0.0 and y == 0.0):
                continue
            d = by_type.setdefault(name, {"x": [], "y": []})
            d["x"].append(x)
            d["y"].append(y)
        traces = []
        for name, d in sorted(by_type.items(), key=lambda kv: -len(kv[1]["x"])):
            traces.append({
                "x": d["x"], "y": d["y"], "type": "scatter", "mode": "markers",
                "name": f"{name} ({len(d['x'])})",
                "marker": {"size": 9, "color": _TYPE_COLOR.get(name, "#94a3b8"),
                           "line": {"color": "rgba(255,255,255,0.6)", "width": 0.5}},
                "hovertemplate": name + "<br>(%{x:.0f}, %{y:.0f})<extra></extra>",
            })
        layout = {
            "title": {
                "text": "Colonic crypt (Cellular-Potts): cells by fate<br>"
                        "<span style='font-size:12px;color:#64748b'>HRA crypt FTU; stem niche at the base, goblet/absorptive progeny along the Wnt gradient (viva-cpm)</span>",
                "x": 0.02, "xanchor": "left", "font": {"size": 16},
            },
            "xaxis": {"title": {"text": "x (lattice)"}, "zeroline": False, "scaleanchor": "y", "scaleratio": 1},
            "yaxis": {"title": {"text": "y (lattice)"}, "zeroline": False},
            "legend": {"orientation": "h", "y": -0.18, "x": 0},
            "margin": {"l": 55, "r": 20, "t": 60, "b": 60},
            "plot_bgcolor": "rgba(248,250,252,0.6)", "paper_bgcolor": "rgba(0,0,0,0)",
        }
        return {"html": (
            '<div id="crypt_map" style="height:440px"></div>'
            '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'
            '<script>Plotly.newPlot("crypt_map",'
            + json.dumps(traces) + "," + json.dumps(layout)
            + ", {responsive:true, displayModeBar:false});</script>"
        )}


class CryptCensus(Step):
    """Emit per-fate cell counts (stem / goblet / absorptive) as scalars each tick."""

    def inputs(self):
        return {"types": "list"}

    def outputs(self):
        return {"stem_count": "integer", "goblet_count": "integer",
                "absorptive_count": "integer"}

    def update(self, state):
        types = state.get("types") or []
        cfg = getattr(self, "config", None) or {}
        stem, goblet, absorp = cfg.get("stem_type"), cfg.get("goblet_type"), cfg.get("absorptive_type")
        return {
            "stem_count": sum(1 for t in types if t == stem),
            "goblet_count": sum(1 for t in types if t == goblet),
            "absorptive_count": sum(1 for t in types if t == absorp),
        }


def _register_crypt(core):
    core.register_link("CryptSpatialMap", CryptSpatialMap)
    core.register_link("CryptCensus", CryptCensus)
    return core


def _capture_crypt_state(core):
    """Capture the document state + meta from viva-cpm's build_crypt_composite.

    The function assembles a ``state`` dict then wraps it in a ``pb.Composite``
    and returns the built object; intercept that wrap to grab the (unrealized)
    state we need for a ``@composite_generator``.
    """
    captured: dict = {}

    class _Capture:
        def __init__(self, doc, core=None):
            captured["state"] = doc["state"]

    orig = _crypt_mod.pb.Composite
    try:
        _crypt_mod.pb.Composite = _Capture
        ret = _crypt_mod.build_crypt_composite(
            core, downscale=_DOWNSCALE, mcs_per_update=8, subcell_every=1)
        meta = ret[1] if isinstance(ret, tuple) and len(ret) > 1 else {}
    finally:
        _crypt_mod.pb.Composite = orig
    return captured.get("state", {}), (meta or {})


@composite_generator(
    name="mosaic_crypt_cpm",
    description=(
        "Spatial Cellular-Potts colonic crypt (viva-cpm) over the HRA crypt FTU: "
        "Wnt-secreting stem niche at the base, goblet/absorptive differentiation "
        "along the gradient. Lattice spatial model. Renders a cell-type map "
        "(spatial snapshot) and emits per-fate cell counts."
    ),
    default_n_steps=40,
    core_extensions=[_register_crypt],
)
def mosaic_crypt_cpm(core=None):
    from mosaic_compose.core import build_core
    state, meta = _capture_crypt_state(core or build_core())
    stores = state.get("stores")
    if not isinstance(stores, dict):
        stores = {}
        state["stores"] = stores
    # Scalar per-fate census (xarray-emittable), seeded from meta's initial counts.
    ic = meta.get("initial_counts") or {}
    state["stem_count"] = int(ic.get("stem", 0))
    state["goblet_count"] = int(ic.get("goblet", 0))
    state["absorptive_count"] = int(ic.get("absorptive", 0))
    state["census"] = {
        "_type": "step", "address": "local:CryptCensus",
        "config": {"stem_type": meta.get("stem_type"),
                   "goblet_type": meta.get("goblet_type"),
                   "absorptive_type": meta.get("absorptive_type")},
        "inputs": {"types": ["types"]},
        "outputs": {"stem_count": ["stem_count"], "goblet_count": ["goblet_count"],
                    "absorptive_count": ["absorptive_count"]},
    }
    # Spatial snapshot: inline Visualization step (surfaced via the native gallery).
    state["crypt_map"] = {
        "_type": "step", "address": "local:CryptSpatialMap",
        "config": {"type_names": meta.get("type_names") or []},
        "inputs": {"positions": ["positions"], "types": ["types"]},
        "outputs": {"html": ["stores", "crypt_viz_html"]},
    }
    return {"state": state}
