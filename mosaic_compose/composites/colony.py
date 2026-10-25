"""Spatial agent-based biofilm colony — the ABM arm of the Foundations demo.

Built on viva-munk's pymunk multibody physics: rod-shaped cells grow and divide
in a 2-D chamber, pushing on each other as the colony packs. This is the spatial
/ agent-based model TYPE — distinct from the ODE, FBA, and composition arms.

viva-munk ships the physics (`PymunkProcess`), the adder growth+division
(`AdderGrowDivide`), and a spatial colony renderer (`MultibodyVizStep`), but its
`biofilm_document()` builder seeds cells from an uncontrolled RNG and uses a
growth rate too low to divide in a short run. Here we assemble the document
ourselves: a seeded initial placement of small rod cells, a high adder growth
rate so the colony visibly divides, and a tiny `CountCells` step that emits the
scalar colony size each tick (the `cells` map itself is spatial and not
xarray-emittable, so the growth CURVE needs a scalar readout).
"""
from __future__ import annotations

from process_bigraph.composite import Step
from process_bigraph.composite_generator import composite_generator

from viva_munk.composites import _register_pymunk_types, _register_processes
from viva_munk.processes.grow_divide import add_adder_grow_divide_to_agents
from viva_munk.processes.multibody import make_initial_state
from viva_munk.visualizations import make_multibody_viz_step, make_viz_stores


class CountCells(Step):
    """Emit the colony size (number of cells) as a scalar each tick.

    The `cells` store is a ``map[pymunk_agent]`` (spatial, variable-length), which
    the XArrayEmitter drops; this projects it to a scalar so the colony-growth
    trajectory is emittable + plottable.
    """

    def inputs(self):
        return {"cells": "map[pymunk_agent]"}

    def outputs(self):
        return {"cell_count": "integer"}

    def update(self, state):
        cells = state.get("cells") or {}
        return {"cell_count": len(cells)}


def _register_colony(core):
    # viva-munk's register helpers mutate the core in place and may return None,
    # so call them for side effect and keep our handle on `core`.
    _register_pymunk_types(core)
    _register_processes(core)
    core.register_link("CountCells", CountCells)
    return core


_ENV = 30.0
# Finer physics/emit interval so the colony-growth trajectory is well sampled
# (the per-hour growth rate is time-based, so a smaller step just yields more,
# smaller updates over the same simulated time — same final colony, denser curve).
_INTERVAL = 6.0


@composite_generator(
    name="mosaic_biofilm_colony",
    description=(
        "Spatial agent-based biofilm: rod-shaped cells grow, divide, and push on "
        "each other via pymunk physics (viva-munk), packing a 2-D colony. The ABM "
        "/ spatial model type. Emits colony size (cell count) per tick; the "
        "MultibodyViz step renders the spatial colony."
    ),
    default_n_steps=60,
    core_extensions=[_register_colony],
)
def mosaic_biofilm_colony(core=None):
    state = make_initial_state(
        n_microbes=3, n_particles=0, env_size=_ENV, seed=7,
        microbe_length_range=(2.0, 2.0), microbe_radius_range=(0.5, 0.5),
        microbe_mass_density=0.02,
    )
    # High adder growth rate so the colony visibly divides within a short run.
    # Zero the stochastic CVs so the colony grows deterministically (exponential
    # growth otherwise amplifies per-cell rate noise into huge run-to-run
    # variance in the final count).
    add_adder_grow_divide_to_agents(
        state, agents_key="cells",
        config={"agents_key": "cells", "alpha_mean_per_h": 150.0,
                "alpha_cv": 0.0, "delta_cv": 0.0, "division_noise_cv": 0.0},
    )
    # pymunk physics integrator: resolve cell-cell overlap each tick.
    state["multibody"] = {
        "_type": "process", "address": "local:PymunkProcess",
        "config": {"env_size": _ENV}, "interval": _INTERVAL,
        "inputs": {"segment_cells": ["cells"], "circle_particles": ["particles"]},
        "outputs": {"segment_cells": ["cells"], "circle_particles": ["particles"]},
    }
    # Project the spatial colony to a scalar size each tick (xarray-emittable).
    state["cell_count"] = 3
    state["count_cells"] = {
        "_type": "step", "address": "local:CountCells",
        "inputs": {"cells": ["cells"]},
        "outputs": {"cell_count": ["cell_count"]},
    }
    # Spatial SNAPSHOT: viva-munk's MultibodyVizStep renders the live colony
    # (cell positions/orientations) to HTML directly from the state tree — no
    # emitter involved, so the spatial `cells` map is rendered in full. The run's
    # _render_viz (render_results) collects it into viz.json → the study's native
    # gallery (which now also accepts the step's {'html': ...} payload shape).
    state["stores"] = make_viz_stores()
    state["colony_snapshot"] = make_multibody_viz_step(
        title="Biofilm colony", env_width=_ENV, env_height=_ENV, has_particles=False)
    return {"state": state}
