"""The viva-cobra dFBA metabolic-arm composites build + run on the workspace core.

Skipped cleanly if viva-cobra / cobra are not installed (e.g. a deps-light env),
so a fresh checkout without the optional metabolic stack still passes.
"""
from __future__ import annotations

import pytest

pytest.importorskip("viva_cobra", reason="viva-cobra (COBRApy stack) not installed")
pytest.importorskip("cobra", reason="cobra not installed")


def _run(gen, duration=1.0):
    from process_bigraph import Composite
    from process_bigraph.emitter import gather_emitter_results

    from mosaic_compose.core import build_core

    comp = Composite(gen(), core=build_core())
    comp.run(duration)
    return gather_emitter_results(comp)[("emitter",)]


def test_ecoli_core_dfba_grows_and_consumes_glucose():
    from mosaic_compose.composites.dfba import mosaic_dfba_ecoli_core

    history = _run(mosaic_dfba_ecoli_core, duration=1.5)
    assert history
    first, last = history[0], history[-1]
    assert last["biomass"] > first["biomass"]
    assert last["substrates"]["glucose"] < 11.1


def test_lactobacillus_dfba_builds_and_grows():
    from mosaic_compose.composites.dfba import mosaic_dfba_lactobacillus

    history = _run(mosaic_dfba_lactobacillus, duration=1.0)
    assert history
    assert history[-1]["biomass"] >= history[0]["biomass"]


def test_importing_the_workspace_registers_the_composites():
    # Importing the package must not raise even with the metabolic stack present,
    # and the composites subpackage loads.
    import mosaic_compose

    assert mosaic_compose._composites is not None
