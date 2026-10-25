"""The viva-cobra dFBA metabolic-arm composites build + run on the workspace core.

Skipped cleanly if viva-cobra / cobra are not installed (e.g. a deps-light env),
so a fresh checkout without the optional metabolic stack still passes.
"""
from __future__ import annotations

import pytest

pytest.importorskip("viva_cobra", reason="viva-cobra (COBRApy stack) not installed")
pytest.importorskip("cobra", reason="cobra not installed")


def _run_final_state(gen, duration=1.0):
    """Build + run a dFBA composite and return its final state.

    The composites no longer carry a standalone emitter node (``_emit.strip_emitter``
    removes the library builder's RAM emitter so the workbench injects its
    configured sink — xarray — instead). So we assert on the final state directly
    rather than reading an emitter history; the composite's own ``biomass`` /
    ``substrates`` stores hold the outcome.
    """
    from process_bigraph import Composite

    from mosaic_compose.core import build_core

    comp = Composite(gen(), core=build_core())
    comp.run(duration)
    return comp.state


def test_ecoli_core_dfba_grows_and_consumes_glucose():
    from mosaic_compose.composites.dfba import mosaic_dfba_ecoli_core

    state = _run_final_state(mosaic_dfba_ecoli_core, duration=1.5)
    assert state["biomass"] > 0.01  # grew from the 0.01 seed
    assert state["substrates"]["glucose"] < 11.1  # glucose consumed


def test_lactobacillus_dfba_builds_and_grows():
    from mosaic_compose.composites.dfba import mosaic_dfba_lactobacillus

    state = _run_final_state(mosaic_dfba_lactobacillus, duration=1.0)
    assert state["biomass"] >= 0.01


def test_importing_the_workspace_registers_the_composites():
    # Importing the package must not raise even with the metabolic stack present,
    # and the composites subpackage loads.
    import mosaic_compose

    assert mosaic_compose._composites is not None
