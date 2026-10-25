"""Two-organism dynamic-FBA co-culture — process-bigraph COMPOSITION.

The Foundations composition demo: two independent viva-cobra dynamic-FBA models
(E. coli core + Lactobacillus iNF517) wired into **one** composite that share a
single substrate pool. Each organism has its own biomass + uptake + FBA solve,
but both draw glucose from the same environment — so they *compete*, and the
shared pool couples their fates.

Why this composes cleanly: the FBAStep writes substrate changes as DELTAS
(``map[count]``: ``flux * biomass * dt``, clamped to the available pool), so two
organisms' consumption of the shared ``substrates`` store applies additively —
no custom coupling process needed, just shared topology. This is exactly what
process-bigraph composition buys you: take two models that each run standalone
(see the dFBA studies) and couple them through a shared store.
"""
from __future__ import annotations

import copy

from process_bigraph.composite_generator import composite_generator

from viva_cobra import dfba_document, get_model_spec
from viva_cobra.core import register_processes, register_types

from ._emit import strip_emitter

_CORE_EXTENSIONS = [register_types, register_processes]
_DT = 0.05

# The private (per-organism) store names in a single dfba_document. ``substrates``
# is deliberately NOT here: it is the SHARED environment both organisms wire to.
_PRIVATE = ("biomass", "uptakes", "interval")


def _cfg(model_key: str, kinetic_params: dict) -> dict:
    spec = get_model_spec(model_key)
    return {
        "model_file": spec["model_file"],
        "substrate_update_reactions": dict(spec["substrate_update_reactions"]),
        "bounds": dict(spec["default_bounds"]),
        "biomass_reaction": spec["biomass_reaction"],
        "kinetic_params": kinetic_params,
    }


def _suffix_path(path, suffix):
    """Rewrite a dfba wiring path for one organism: private stores get the suffix,
    the shared ``substrates`` store is left untouched."""
    if isinstance(path, list) and len(path) == 1 and path[0] in _PRIVATE:
        return [f"{path[0]}_{suffix}"]
    return path


def _remap_ports(node, suffix):
    """Deep-copy a process/step node, suffixing its private input/output paths."""
    node = copy.deepcopy(node)
    for side in ("inputs", "outputs"):
        wires = node.get(side) or {}
        node[side] = {port: _suffix_path(p, suffix) for port, p in wires.items()}
    return node


def _add_organism(state, schema, doc, suffix):
    """Fold one organism's dFBA document into the shared co-culture state/schema."""
    st = doc["state"]
    sch = doc["schema"]
    # Shared substrate pool: union the organisms' initial concentrations (glucose
    # is shared; each may also bring its own extra substrate).
    shared = state.setdefault("substrates", {})
    for k, v in (st.get("substrates") or {}).items():
        shared.setdefault(k, v)
    schema.setdefault("substrates", sch.get("substrates", "map[concentration]"))
    # Private stores + processes, suffixed per organism.
    for key in _PRIVATE:
        state[f"{key}_{suffix}"] = st[key]
        schema[f"{key}_{suffix}"] = sch[key]
    state[f"uptake_{suffix}"] = _remap_ports(st["uptake"], suffix)
    state[f"fba_{suffix}"] = _remap_ports(st["fba"], suffix)


@composite_generator(
    name="mosaic_dfba_coculture",
    description=(
        "Process-bigraph COMPOSITION: two dynamic-FBA organisms (E. coli core + "
        "Lactobacillus iNF517) sharing one substrate pool and competing for "
        "glucose. Each model runs standalone in its own study; here they are "
        "coupled through a shared `substrates` store (FBA writes consumption "
        "deltas, so competition composes additively — no custom coupling process)."
    ),
    default_n_steps=200,
    core_extensions=_CORE_EXTENSIONS,
)
def mosaic_dfba_coculture(core=None):
    # Deliberately MODERATE, comparable uptake kinetics (lower Vmax, higher Km)
    # so neither organism instantly monopolizes the glucose: the competition
    # unfolds gradually over the run instead of a one-tick blow-out. E. coli is a
    # slightly faster glucose specialist; Lactobacillus is a hair slower but holds
    # a private glutamate niche — so it persists rather than being wiped out.
    ecoli = dfba_document(
        _cfg("ecoli_core", {"glucose": [1.0, 2.6], "acetate": [0.5, 2.0]}),
        dt=_DT, initial_substrates={"glucose": 10.0, "acetate": 0.0},
        initial_biomass=0.004,
    )
    lacto = dfba_document(
        _cfg("iNF517", {"glucose": [1.0, 2.2], "glutamate": [0.5, 5.0]}),
        dt=_DT, initial_substrates={"glucose": 10.0, "glutamate": 8.0},
        initial_biomass=0.004,
    )
    state: dict = {"interval": _DT}
    schema: dict = {"interval": "overwrite[float]"}
    _add_organism(state, schema, ecoli, "ecoli")
    _add_organism(state, schema, lacto, "lacto")
    return strip_emitter({"schema": schema, "state": state})
