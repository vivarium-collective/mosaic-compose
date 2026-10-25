"""Microbiome-community composites for MOSAIC, built on viva-tellurium.

A generalized Lotka-Volterra (gLV) community authored INLINE as Antimony — the
model source lives in the composite's ``config.model`` field, so it is authored
and shown directly in a study's Model tab (viva-tellurium: model_format
'antimony'). Runs through libroadrunner/CVODE via ``register_tellurium``.

gLV form (Stein et al. 2013): dNi/dt = Ni * (r_i + sum_j a_ij * Nj).
"""
from __future__ import annotations

from process_bigraph.composite_generator import composite_generator

from viva_tellurium import make_tellurium_document
from viva_tellurium.composites import register_tellurium

from ._emit import strip_emitter

# Register viva-tellurium's TelluriumProcess + UTC step + the species-time-series
# visualization onto whatever core realizes the composite. (The RAM emitter it
# also registers is unused here — Foundations composites emit via XArray; see
# ._emit.)
_CORE_EXTENSIONS = [register_tellurium]

# Vaginal microbiome gLV — Lactobacillus crispatus (protective, lactic-acid /
# low-pH) vs Gardnerella vaginalis (BV-associated). The off-diagonal interaction
# terms are asymmetric: Lactobacillus strongly suppresses Gardnerella (via lactic
# acid / H2O2 / bacteriocins), while Gardnerella only weakly suppresses it. That
# asymmetry makes Lactobacillus the competitive dominant — starting from a
# Lactobacillus-leaning community, L competitively excludes G and the system
# settles into the protective, low-pH "healthy" state.
#
# (Illustrative demo parameters — not calibrated to a specific clinical dataset.
# They are chosen so L can invade a G-dominant state while G cannot invade an
# L-dominant one: r_L + a_LG·G* > 0 and r_G + a_GL·L* < 0, with carrying
# capacities K_i = r_i/|a_ii|.)
_VAGINAL_GLV = """\
model vaginal_glv
  # species = relative community abundance (0-1 scale)
  species Lactobacillus, Gardnerella;
  Lactobacillus = 0.45;
  Gardnerella   = 0.08;

  # intrinsic growth rates
  r_L = 1.0;
  r_G = 0.85;

  # interaction matrix a_ij (self-limitation on the diagonal; asymmetric
  # off-diagonal inhibition -> Lactobacillus competitively excludes Gardnerella).
  # a_GL strongly negative: L strongly suppresses G; a_LG weakly negative: G only
  # weakly suppresses L.
  a_LL = -1.0;   a_LG = -0.6;
  a_GL = -1.5;   a_GG = -1.0;

  # generalized Lotka-Volterra rate rules
  Lactobacillus' = Lactobacillus * (r_L + a_LL*Lactobacillus + a_LG*Gardnerella);
  Gardnerella'   = Gardnerella   * (r_G + a_GL*Lactobacillus + a_GG*Gardnerella);
end
"""


@composite_generator(
    name="mosaic_glv_vaginal",
    description=(
        "Vaginal microbiome community dynamics as a generalized Lotka-Volterra "
        "(gLV) ODE — Lactobacillus vs Gardnerella competitive bistability (BV). "
        "Model authored inline as Antimony (shown in the study's Model tab); "
        "integrated with libroadrunner/CVODE via viva-tellurium."
    ),
    default_n_steps=120,
    core_extensions=_CORE_EXTENSIONS,
)
def mosaic_glv_vaginal(core=None):
    return strip_emitter(make_tellurium_document(
        model=_VAGINAL_GLV,
        model_format="antimony",
        interval=0.2,
    ))
