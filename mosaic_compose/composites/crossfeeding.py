"""BV amine cross-feeding composite for MOSAIC, built on viva-tellurium.

A mechanistic ODE of the **biogenic-amine cross-feeding loop** that couples the
vaginal microbial community to the metabolite pool and to pH — authored INLINE
as Antimony (the model source lives in the composite's ``config.model`` field,
so it is shown directly in a study's Model tab). Runs through
libroadrunner/CVODE via ``register_tellurium``.

Biology / data provenance
--------------------------
This extends the plain Lactobacillus–Gardnerella gLV arm (``community.py``) with
the biogenic-amine mechanism two BV papers quantify:

* **Borgogna et al. 2021** (Appl. Environ. Microbiol., doi:10.1128/aem.03068-20):
  Gardnerella-associated biogenic amines INHIBIT Lactobacillus growth and SUPPRESS
  lactic-acid production. Putrescine at 3,179 uM lengthened L. crispatus/gasseri/
  iners doubling time by ~22-33% (we anchor the growth-inhibition half-constant
  ``Ki_A`` to the midpoint: a ~25% growth-rate reduction at 3,179 uM -> Ki_A ~
  11,300 uM). Cadaverine (4,990 uM) gave a smaller +7.5-13% effect.
* **Puebla-Barragan et al. 2021** (Int. J. Mol. Sci., doi:10.3390/ijms222212279):
  L. crispatus strains DEGRADE cadaverine/putrescine/tyramine (>=40% removal), and
  their growth is pH-dependent (faster at lower pH). This supplies the reverse arm
  (a Lactobacillus amine sink) and the pH coupling.

Together they close a two-way loop with a pH feedback:
  Gardnerella -> amines -> (inhibit Lactobacillus growth + suppress lactate) -> pH rises -> favours Gardnerella   [BV cycle]
  Lactobacillus -> lactate -> low pH (+ faster amine degradation) -> clears amines -> favours Lactobacillus       [protective cycle]
which makes the system **bistable**: it settles into a protective, acidic,
amine-cleared Lactobacillus state OR a BV-like Gardnerella state with a ~mM amine
pool and higher pH, depending on the starting community.

The amine half-constant ``Ki_A`` is anchored to Borgogna's measured effect size;
the community growth/competition and lactate/pH terms are illustrative scaffold
parameters (as in the gLV arm), chosen so the bistable structure the two papers
describe is reproduced — they are NOT a fit to a specific clinical dataset.

State (Antimony species): Lactobacillus, Gardnerella (relative abundance);
Amines (biogenic-amine pool, uM, putrescine-equivalent); Lactate (lactic-acid /
acidification proxy, arb.). pH is derived from Lactate (an assignment rule).
"""
from __future__ import annotations

from process_bigraph.composite_generator import composite_generator

from viva_tellurium import make_tellurium_document
from viva_tellurium.composites import register_tellurium

from ._emit import strip_emitter

_CORE_EXTENSIONS = [register_tellurium]

_BV_AMINE_CROSSFEEDING = """\
model bv_amine_crossfeeding
  # community abundances (relative, 0-1); Amines in uM (putrescine-equiv);
  # Lactate = lactic-acid / acidification proxy (arb.)
  species Lactobacillus, Gardnerella, Amines, Lactate;
  Lactobacillus = 0.30;
  Gardnerella   = 0.30;
  Amines        = 2000.0;   # perturbed / contested starting amine load (uM)
  Lactate       = 0.15;

  # pH derived from lactate (acidification): maps Lactate 0..large -> pH 7.0 .. ~3.9
  pH := 7.0 - 3.1 * Lactate/(Lactate + 0.25);

  # --- community growth / competition (illustrative scaffold, cf. gLV arm) ---
  r_L = 1.0;  K_L = 1.0;
  r_G = 0.9;  K_G = 1.0;
  c_GL = 1.3;   # Lactobacillus competitive pressure on Gardnerella (acid/low pH)
  c_LG = 0.6;   # Gardnerella pressure on Lactobacillus

  # --- amine inhibition of Lactobacillus growth (Borgogna 2021) ---
  # putrescine 3,179 uM -> ~+25% doubling time -> growth factor ~0.78
  # 1/(1 + A/Ki_A) = 0.78 at A=3,179 uM  =>  Ki_A ~ 11,300 uM
  Ki_A = 11300.0;
  fA := 1 / (1 + Amines/Ki_A);               # amine growth-inhibition factor (1 = none)

  # --- pH modulation of growth (Puebla 2021: L favoured at low pH; G at high pH) ---
  fpH_L := 1 / (1 + exp( 2.5*(pH - 4.5) ));
  fpH_G := 1 / (1 + exp(-2.5*(pH - 5.0) ));

  # --- amine production by Gardnerella (saturating at a ~mM BV load) ---
  k_prodA = 9000.0;  A_max = 6000.0;

  # --- amine degradation by Lactobacillus (Puebla 2021), pH-accelerated ---
  k_degA = 6000.0;  Km_degA = 1500.0;
  fdeg_pH := 1 + 1.5*(1/(1+exp(2.5*(pH-4.8))));

  # --- lactate production by Lactobacillus (amine-suppressed; Borgogna) + decay ---
  k_lac = 1.4;  k_lacdecay = 0.8;

  Lactobacillus' = r_L * Lactobacillus * (1 - (Lactobacillus + c_LG*Gardnerella)/K_L) * fA * fpH_L;
  Gardnerella'   = r_G * Gardnerella   * (1 - (Gardnerella + c_GL*Lactobacillus)/K_G) * fpH_G;
  Amines'        = k_prodA * Gardnerella * (A_max - Amines)/A_max - k_degA * Lactobacillus * fdeg_pH * Amines/(Amines + Km_degA);
  Lactate'       = k_lac * Lactobacillus * fA - k_lacdecay * Lactate;
end
"""


_VISUALIZATIONS = [
    {
        "name": "amine_crossfeeding",
        "address": "local:AmineCrossfeeding",
        "config": {
            "inputs_map": {
                "lactobacillus": "stores.species.Lactobacillus",
                "gardnerella": "stores.species.Gardnerella",
                "amines": "stores.species.Amines",
                "lactate": "stores.species.Lactate",
                "time": "global_time",
            }
        },
    },
]


@composite_generator(
    name="mosaic_amine_crossfeeding",
    description=(
        "BV biogenic-amine cross-feeding as a mechanistic ODE — Gardnerella-derived "
        "amines inhibit Lactobacillus growth and suppress lactic acid (raising pH), "
        "while Lactobacillus degrades amines and acidifies (lowering pH). The two-way "
        "loop is bistable: a protective acidic Lactobacillus state vs a BV state with "
        "a ~mM amine pool. Amine inhibition anchored to Borgogna 2021; degradation + "
        "pH coupling from Puebla-Barragan 2021. Authored inline as Antimony; "
        "integrated with libroadrunner/CVODE via viva-tellurium."
    ),
    default_n_steps=350,
    visualizations=_VISUALIZATIONS,
    core_extensions=_CORE_EXTENSIONS,
)
def mosaic_amine_crossfeeding(core=None):
    return strip_emitter(make_tellurium_document(
        model=_BV_AMINE_CROSSFEEDING,
        model_format="antimony",
        interval=0.12,
    ))
