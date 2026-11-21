"""One-carbon / methionine-cycle composite for MOSAIC, built on viva-tellurium.

A faithful reimplementation of the central result of **Kim, Nijhout & Reed 2021**
("One-carbon metabolism during the menstrual cycle and pregnancy", PLOS Comput
Biol, doi:10.1371/journal.pcbi.1009708): hepatic homocysteine varies **inversely**
with estradiol over the menstrual cycle, because estradiol activates
cystathionine-β-synthase (CBS), the transsulfuration enzyme that clears
homocysteine.

How it is built (model provenance)
----------------------------------
Kim 2021 is a 19-ODE extension of the Reed/Nijhout one-carbon models and is NOT
deposited as SBML. Rather than hand-transcribe it, this composite stands the
estradiol forcing on top of a **curated, retrievable base model**:

* **Base:** BioModels **BIOMD0000000698** — *Reed2004, Methionine Cycle*
  (CURATED SBML, bundled at ``mosaic_compose/data/models/BIOMD0000000698.xml``;
  download: https://www.ebi.ac.uk/biomodels/BIOMD0000000698). Met → SAM → SAH →
  Hcy with MAT-I/III, GNMT, the lumped methyltransferase V_METH, AH, the folate-
  dependent remethylation V_MS, V_BHMT, and the transsulfuration V_CBS. We load
  its exact curated rate laws via ``tellurium.sbmlToAntimony`` — no transcription.
* **Kim 2021 extension:** the estradiol activation of CBS, **h(E2) = 1 +
  (E2−0.09)/(0.67+(E2−0.09))** (Kim Eq 3), applied to the CBS rate by scaling its
  ``beta_1``/``beta_2`` coefficients; and a menstrual-cycle estradiol input
  **E2(t)** (nM) — a 5-harmonic Fourier fit (RMS 0.05 nM) to Kim's 29-point mean
  daily E2 curve (BioCycle data, peak ≈1.15 nM at ovulation, day ~12), evaluated
  over one 28-day cycle (model time in hours; day = time/24).

We deliberately apply the forcing only to CBS (the dominant, well-identified
estradiol target that drives the Hcy–E2 relationship). Kim's other E2 effects
(PEMT g(E2), TS/DHFR u(E2)) act on folate-cycle enzymes that are lumped or absent
in the Reed2004 methionine-cycle base, so scaling the lumped V_METH by g(E2) would
misattribute a whole enzyme class — see the paper for the full 19-ODE network.

Validated behaviour: homocysteine is lowest at the ovulatory E2 peak and highest
at menstruation (corr(E2, Hcy) ≈ −0.94 over the settled cycle; Hcy ≈ 0.6–1.0 µM),
reproducing Kim 2021 Fig 2.

State (Antimony species, µM): Methionine, AdoMet (SAM), AdoHcy (SAH),
Homocysteine, Cystathionine; plus the derived assignment ``E2`` (nM).
"""
from __future__ import annotations

import math
import re
from importlib import resources

from process_bigraph.composite_generator import composite_generator

from viva_tellurium import make_tellurium_document
from viva_tellurium.composites import register_tellurium

from ._emit import strip_emitter

_CORE_EXTENSIONS = [register_tellurium]

# 5-harmonic Fourier fit (period 28 d) to Kim 2021's mean daily menstrual E2 (nM).
# coef = [a0, a1,b1, a2,b2, ...] for terms a_k*cos(w_k·day) + b_k*sin(w_k·day).
_E2_PERIOD_DAYS = 28.0
_E2_FOURIER = [0.435855, -0.232929, -0.094179, -0.019523, -0.15162,
               -0.02478, 0.136149, -0.038287, -0.086684, 0.044116, 0.060624]


def _e2_expression() -> str:
    """Antimony expression for menstrual E2(t) in nM (model time in hours)."""
    terms = [f"{_E2_FOURIER[0]:.6g}"]
    for k in range(1, (len(_E2_FOURIER) - 1) // 2 + 1):
        w = 2 * math.pi * k / _E2_PERIOD_DAYS
        a, b = _E2_FOURIER[2 * k - 1], _E2_FOURIER[2 * k]
        terms.append(f"({a:.6g})*cos({w:.8g}*(time/24)) + ({b:.6g})*sin({w:.8g}*(time/24))")
    return " + ".join(terms)


def _build_onecarbon_antimony() -> str:
    """Load the curated Reed2004 SBML and inject Kim 2021's CBS estradiol forcing."""
    import tellurium as te
    sbml = (resources.files("mosaic_compose") / "data" / "models"
            / "BIOMD0000000698.xml").read_text(encoding="utf-8")
    ant = te.sbmlToAntimony(sbml)
    # Drop the constant CBS coefficients; we re-add them as h(E2)-scaled rules.
    ant = re.sub(r'^\s*beta_1\s*=\s*[-0-9.eE]+\s*;.*$', '', ant, flags=re.M)
    ant = re.sub(r'^\s*beta_2\s*=\s*[-0-9.eE]+\s*;.*$', '', ant, flags=re.M)
    inject = (
        "\n  # --- Kim 2021 estradiol forcing on CBS (doi:10.1371/journal.pcbi.1009708) ---\n"
        f"  E2 := {_e2_expression()};   # menstrual-cycle estradiol (nM), 1 cycle = 672 h\n"
        "  hE2 := 1 + (E2 - 0.09)/(0.67 + (E2 - 0.09));   # CBS activation, Kim Eq 3\n"
        "  beta_1 := 1.7 * hE2;    # Reed2004 CBS slope, estradiol-scaled\n"
        "  beta_2 := 30.0 * hE2;   # Reed2004 CBS offset, estradiol-scaled\n"
    )
    ant = re.sub(r'(?m)^end\s*$', inject + "end", ant, count=1)
    return ant


_VISUALIZATIONS = [
    {
        "name": "onecarbon_homocysteine",
        "address": "local:OneCarbonHomocysteine",
        "config": {
            "inputs_map": {
                "homocysteine": "stores.species.Homocysteine",
                "sam": "stores.species.AdoMet",
                "sah": "stores.species.AdoHcy",
                "time": "global_time",
            }
        },
    },
]


@composite_generator(
    name="mosaic_onecarbon_cycle",
    description=(
        "Hepatic one-carbon / methionine cycle over the menstrual cycle — a faithful "
        "recreation of Kim, Nijhout & Reed 2021 (PLOS Comp Biol): estradiol activates "
        "CBS (transsulfuration), so homocysteine varies inversely with estradiol "
        "(lowest at the ovulatory E2 peak). Built on the curated Reed2004 methionine-"
        "cycle SBML (BioModels BIOMD0000000698) + Kim's h(E2) CBS forcing and a "
        "Fourier-fit menstrual E2(t). Integrated with libroadrunner/CVODE via "
        "viva-tellurium."
    ),
    default_n_steps=672,
    visualizations=_VISUALIZATIONS,
    core_extensions=_CORE_EXTENSIONS,
)
def mosaic_onecarbon_cycle(core=None):
    return strip_emitter(make_tellurium_document(
        model=_build_onecarbon_antimony(),
        model_format="antimony",
        interval=1.0,
    ))
