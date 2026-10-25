"""Spatial agent-based biofilm colony — the ABM arm of the Foundations demo.

Based directly on viva-munk's own biofilm experiment (its
``EXPERIMENT_REGISTRY['with_particles']`` entry): rod-shaped cells grow by an
adder rule (~40-min doubling) and divide, pushing on each other and on a bath of
passive particles via pymunk physics, packing a 2-D chamber. This is the
spatial / agent-based model TYPE — distinct from the ODE, FBA, and composition
arms.

We take viva-munk's real document + config unchanged (so the dynamics are theirs,
not hand-tuned) and only add a tiny ``CountCells`` step that projects the spatial
``cells`` map (``map[pymunk_agent]``, not xarray-emittable) to a scalar colony
size each tick — written with ``overwrite`` so it records the CURRENT count, not
a running sum. viva-munk's ``MultibodyVizStep`` (already in the document) renders
the live colony spatially; the run surfaces it to the study's native gallery.
"""
from __future__ import annotations

from process_bigraph.composite import Step
from process_bigraph.composite_generator import composite_generator

from viva_munk.composites import _register_pymunk_types, _register_processes
from viva_munk.experiments.documents.biofilm import biofilm_document


class CountCells(Step):
    """Emit the colony size (number of cells) as a scalar each tick.

    ``cells`` is a ``map[pymunk_agent]`` (spatial, variable-length), dropped by
    the XArrayEmitter; this projects it to a scalar. ``overwrite[integer]`` so the
    store holds the current count rather than accumulating it across ticks.
    """

    def inputs(self):
        return {"cells": "map[pymunk_agent]"}

    def outputs(self):
        return {"cell_count": "overwrite[integer]"}

    def update(self, state):
        return {"cell_count": len(state.get("cells") or {})}


def _register_colony(core):
    # Register viva-munk's pymunk types (pymunk_agent, …) + processes + viz onto
    # the run core (they mutate in place and may return None, so don't reassign),
    # then add our projection step.
    _register_pymunk_types(core)
    _register_processes(core)
    core.register_link("CountCells", CountCells)
    return core


# viva-munk's biofilm document with its real adder growth + pymunk physics,
# configured as a clean dividing colony (no passive-particle bath — it only
# clutters the figure and bloats the snapshot GIF). The GROWTH dynamics are
# viva-munk's, unchanged; only the chamber size + seed count are set here.
_N_CELLS = 5
_ENV_SIZE = 50
_EXPT_TIME = 10800.0  # 3 h of simulated growth → a well-grown colony
_CELL_COUNT_SEED = _N_CELLS


@composite_generator(
    name="mosaic_biofilm_colony",
    description=(
        "Spatial agent-based biofilm (viva-munk's biofilm_document): rod cells "
        "grow by an adder rule (~40-min doubling) and divide, pushing on each "
        "other via pymunk physics as the colony packs a 2-D chamber. The ABM / "
        "spatial model type. Emits colony size (cell count); viva-munk's "
        "MultibodyViz renders the spatial colony."
    ),
    default_n_steps=_EXPT_TIME,
    core_extensions=[_register_colony],
)
def mosaic_biofilm_colony(core=None):
    doc = biofilm_document({
        "env_size": _ENV_SIZE, "n_cells": _N_CELLS, "n_initial_particles": 0,
    })
    state = doc.get("state", doc)
    # Rename the viz step key for a cleaner native-gallery panel title.
    if "multibody_viz" in state:
        state["colony_snapshot"] = state.pop("multibody_viz")
    # Drop viva-munk's per-cell mass-traces panel to keep the figure set focused
    # (colony snapshot + colony-size curve); the dynamics are unchanged.
    state.pop("cell_mass_traces", None)
    # Scalar colony-size projection (xarray-emittable).
    state["cell_count"] = _CELL_COUNT_SEED
    state["count_cells"] = {
        "_type": "step", "address": "local:CountCells",
        "inputs": {"cells": ["cells"]},
        "outputs": {"cell_count": ["cell_count"]},
    }
    return {"state": state}
