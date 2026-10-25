"""Dynamic-FBA metabolic-arm composites for MOSAIC, built on viva-cobra.

MOSAIC's metabolic arm couples a genome-scale metabolic model (GEM) to its
environment via **dynamic FBA**: a Michaelis-Menten uptake process turns the
current substrate concentrations into exchange-flux bounds, the COBRApy FBA solve
returns the growth rate + realized fluxes, and the shared substrate pools +
biomass update each step (all from the ``viva_cobra`` library).

These ``@composite_generator`` functions expose runnable dFBA composites in the
workbench Composites tab. They are the reusable pattern for the metabolic module
of each Aim — swap ``model_file`` for a tissue or microbe GEM (e.g. a hepatic
model, or a Lactobacillus/Gardnerella reconstruction via Reconstructor / ftINIT)
to specialize the arm. See the Resources tab for the GEM tooling + datasets.
"""
from __future__ import annotations

from process_bigraph.composite_generator import composite_generator

from viva_cobra import dfba_document, get_model_spec
from viva_cobra.core import register_processes, register_types

from ._emit import strip_emitter

# Register viva-cobra's domain types (concentration/mass/count/bounds) + process
# links onto whatever core realizes the composite.
_CORE_EXTENSIONS = [register_types, register_processes]

_DT = 0.05


def _cfg(model_key: str, kinetic_params: dict) -> dict:
    """Assemble a viva-cobra dFBA config from a bundled GEM's registry metadata."""
    spec = get_model_spec(model_key)
    return {
        "model_file": spec["model_file"],
        "substrate_update_reactions": dict(spec["substrate_update_reactions"]),
        "bounds": dict(spec["default_bounds"]),
        "biomass_reaction": spec["biomass_reaction"],
        "kinetic_params": kinetic_params,
    }


@composite_generator(
    name="mosaic_dfba_ecoli_core",
    description=(
        "Dynamic-FBA metabolic-arm template: Michaelis-Menten uptake constraining "
        "COBRApy FBA on the E. coli core GEM (diauxic glucose -> acetate overflow). "
        "The reusable MOSAIC metabolic-module pattern — swap in a tissue/microbe GEM."
    ),
    default_n_steps=200,
    core_extensions=_CORE_EXTENSIONS,
)
def mosaic_dfba_ecoli_core(core=None):
    return strip_emitter(dfba_document(
        _cfg("ecoli_core", {"glucose": [0.5, 10.0], "acetate": [0.5, 2.0]}),
        dt=_DT,
        initial_substrates={"glucose": 11.1, "acetate": 0.0},
        initial_biomass=0.01,
    ))


@composite_generator(
    name="mosaic_dfba_lactobacillus",
    description=(
        "Dynamic-FBA of a lactic-acid bacterium (L. lactis iNF517) as a "
        "vaginal-microbiome metabolic proxy for Aim 1 (Lactobacillus-dominant, "
        "lactate-producing states): Michaelis-Menten uptake constraining COBRApy "
        "FBA on glucose + glutamate."
    ),
    default_n_steps=200,
    core_extensions=_CORE_EXTENSIONS,
)
def mosaic_dfba_lactobacillus(core=None):
    return strip_emitter(dfba_document(
        _cfg("iNF517", {"glucose": [0.5, 10.0], "glutamate": [0.5, 5.0]}),
        dt=_DT,
        initial_substrates={"glucose": 20.0, "glutamate": 5.0},
        initial_biomass=0.01,
    ))
