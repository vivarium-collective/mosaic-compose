"""Hormone PK-PD composites for MOSAIC, built on viva-tellurium.

Estrogen enterohepatic recycling authored INLINE as Antimony — the model source
lives in the composite's ``config.model`` field, so it is authored and shown
directly in a study's Model tab. Runs through libroadrunner/CVODE.

This is the hormone-homeostasis core of MOSAIC's thesis: hepatic conjugation
secretes estrogen-glucuronide into the gut, where microbial beta-glucuronidase
(the "estrobolome") deconjugates it back to free estrogen for reabsorption
(enterohepatic recirculation). Gut-microbial GUS activity therefore tunes
systemic estrogen exposure — the mechanistic link between the microbiome and
sex-specific hormone levels.
"""
from __future__ import annotations

from process_bigraph.composite_generator import composite_generator

from viva_tellurium import make_tellurium_document
from viva_tellurium.composites import register_tellurium

_CORE_EXTENSIONS = [register_tellurium]

# Three-compartment estrogen PK with microbial deconjugation:
#   E_blood  — systemic free estrogen (the clinically relevant exposure)
#   EG_gut   — conjugated estrogen-glucuronide delivered to the gut via bile
#   E_gut    — free estrogen in the gut lumen after microbial deconjugation
# gus (beta-glucuronidase / estrobolome activity) is the knob that reroutes
# conjugated estrogen back into circulation instead of being excreted.
_ESTROGEN_EHC = """\
model estrogen_enterohepatic
  species E_blood, EG_gut, E_gut;
  E_blood = 1.0;
  EG_gut  = 0.0;
  E_gut   = 0.0;

  k_conj  = 0.30;   # hepatic conjugation + biliary secretion: E_blood -> EG_gut
  gus     = 0.50;   # microbial beta-glucuronidase (estrobolome): EG_gut -> E_gut
  k_reabs = 0.40;   # enterohepatic reabsorption: E_gut -> E_blood
  k_excr  = 0.20;   # fecal excretion of conjugate EG_gut (lost from the loop)
  k_clear = 0.10;   # systemic clearance of free estrogen

  E_blood' = -k_conj*E_blood + k_reabs*E_gut - k_clear*E_blood;
  EG_gut'  =  k_conj*E_blood - gus*EG_gut - k_excr*EG_gut;
  E_gut'   =  gus*EG_gut - k_reabs*E_gut;
end
"""


@composite_generator(
    name="mosaic_estrogen_enterohepatic",
    description=(
        "Estrogen enterohepatic recycling as a kinetic / PK-PD ODE — hepatic "
        "conjugation, biliary delivery, microbial beta-glucuronidase "
        "deconjugation (estrobolome), and reabsorption. Model authored inline "
        "as Antimony (shown in the study's Model tab); the `gus` parameter tunes "
        "how strongly the gut microbiome raises systemic estrogen exposure."
    ),
    default_n_steps=120,
    core_extensions=_CORE_EXTENSIONS,
)
def mosaic_estrogen_enterohepatic(core=None):
    return make_tellurium_document(
        model=_ESTROGEN_EHC,
        model_format="antimony",
        interval=0.25,
    )
