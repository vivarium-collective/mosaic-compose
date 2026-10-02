# mosaic-compose

<!-- BEGIN dashboard -->
> ## 📊 [**Live dashboard →**](https://vivarium-collective.github.io/mosaic-compose/dashboard/)
> Browse every investigation & study interactively, or read the [published investigation reports](https://vivarium-collective.github.io/mosaic-compose/). Auto-published from `main` on every merge.
<!-- END dashboard -->

<!-- BEGIN:dashboard -->
<!-- `vivarium-workbench gen-readme` fills this with a prominent link to the
     live read-only dashboard (URL derived from the git remote). Before the repo
     is pushed it shows a local-serve note; after the publish-dashboard workflow
     runs (enable once: Settings → Pages → Source = `gh-pages`) it links the live
     GitHub Pages dashboard. Run `vivarium-workbench gen-readme --workspace .`
     (and `--check` in CI) to keep it fresh. -->
<!-- END:dashboard -->

> **Status: planned.** This repository is the newly scaffolded composition
> workspace for MOSAIC. The biology and models described below are the *plan* —
> nothing is wired up yet. This README lays out what will be built here so the
> structure is clear before the first model lands.

The planned composition workspace for **MOSAIC** (**M**odeling **O**f
**S**ex-specific metabolism **A**cross **I**nteracting **C**ommunities) — an open,
multi-scale framework for hormone-regulated host–microbiome metabolism, aimed at
predicting sex-specific therapeutic efficacy and toxicity.

## The biology

Sex-specific differences in drug efficacy and toxicity are pervasive, but the
mechanistic role of **dynamic hormone homeostasis** in shaping them is poorly
understood. MOSAIC treats hormone homeostasis — centered on **estrogen metabolism
and enterohepatic recycling** — as a systemic network linking **gut, liver, and
vaginal** physiology, and asks how perturbations in one compartment propagate
across organ systems to change therapeutic response.

Two conditions anchor the work as demonstration systems, both strongly shaped by
hormone–metabolism–microbiome cross-talk:

- **Bacterial vaginosis (BV)** — dysbiosis of the vaginal microbiome, where the
  interplay of microbial ecology, estrogen-regulated epithelial physiology, and
  antibiotic/probiotic exposure governs recurrence (e.g. metronidazole,
  *Lactobacillus crispatus*).
- **Metabolic dysfunction-associated steatotic liver disease (MASLD)** — where gut
  microbiome-derived metabolites and hormone-regulated hepatic metabolism drive
  sex-specific efficacy of drugs such as resmetirom and GLP-1 receptor agonists.

## The models to be built here

MOSAIC's central idea is that explicit, executable interfaces between disparate
modeling paradigms let independently developed models act as one integrated
representation of hormone-regulated physiology. Four paradigms are planned, each
keeping its own assumptions, units, and biological scope:

| Planned model | What it contributes | Couples via |
|---|---|---|
| **Genome-scale metabolic models (GEMs)** | context-specific host-tissue + microbial metabolism | metabolite exchange, growth rate, reaction bounds |
| **Mechanistic microbiome community models** | population dynamics, community composition, treatment resistance | bacterial composition, flux bounds |
| **PKPD / whole-body compartment models** | systemic & local hormone and drug concentrations | hormone/therapeutic concentration, hormone recycling |
| **Agent-based models (ABM)** | spatiotemporal bacterial–epithelial dynamics | cell location, agent behavior → community/metabolic params |

**Hormone homeostasis is the coupling mechanism** that ties them together: outputs
from one model become inputs or constraints for the others (metabolite exchange,
hormone production/recycling, growth rates, community composition). This workspace
is the Process-Bigraph **seam** that will make those interfaces executable.

## Planned roadmap (grant Aims)

1. **Aim 1 — Vaginal / BV.** A multi-scale model of the hormone-regulated vaginal
   microbiome to predict local therapeutic efficacy (antibiotics, probiotics).
2. **Aim 2 — Gut–liver / MASLD.** An integrated, sex-specific model of gut–liver
   host–microbiome metabolism under hormonal control.
3. **Aim 3 — Integration.** Couple the Aim 1 and Aim 2 models to simulate
   hormone synthesis, microbial deconjugation, enterohepatic recycling, and
   systemic transport across compartments.

MOSAIC is led by the Papin lab (UVA) across a multi-institution team; this
`mosaic-compose` workspace is the software/integration seam, built on
[Vivarium](https://vivarium-collective.github.io/) / process-bigraph.

Scaffolded from
[viva-template](https://github.com/vivarium-collective/viva-template).

## Getting started

    bash scripts/serve.sh           # open the dashboard
    python3 scripts/lint-workspace.py

See `NEXT_STEPS.md` for the full tour.

> 🤖 **Using an AI coding assistant (Claude Code / Cursor / …)?** Hand it
> **[docs/first-run-agent-guide.md](docs/first-run-agent-guide.md)** — a gated
> runbook that takes an agent from a clean clone to a running vivarium-workbench
> with one of this workspace's composites open in the viewer, then on to
> authoring studies and contributing.

## Working with this workspace

The [viva-superpowers](https://github.com/vivarium-collective/viva-superpowers)
Claude Code plugin provides skills that drive the canonical PR flow:

- `/viva-study <slug>` — start a study (8-section spec, `phase: Design|Build|Simulate|Evaluate|Decide`).
- `/viva-investigation <slug>` — group related studies into an investigation (DAG via `pipeline_gate.prerequisites`).
- `/viva-expert <tool>` — wrap a simulator as a process-bigraph Process or Step (sibling repo + tests + report). Pass `--lightweight` to write in-workspace instead.
- `/viva-expert <name> <tools…>` — wire wrapped simulators into a composite (sibling repo, or `--lightweight` for in-workspace).
- `/viva-viz` — generate a Visualization from a natural-language description.
- `/viva-report` — regenerate `workspace/reports/index.html`.

Decide-phase studies can record `followup_proposals[]`; seed a child study
from any proposal with `/viva-study seed-from-followup <parent>/<proposal_id>`.

## Composites & investigations

These two tables are generated from the workspace by
`vivarium-workbench gen-readme` — the same sets the dashboard shows — and kept
fresh by CI (`workspace-ci` runs `gen-readme --check`). They fill in as you add
composites and investigations; regenerate any time with
`vivarium-workbench gen-readme --workspace .`.

### Composites

<!-- BEGIN:composites -->
<!-- generated by `vivarium-workbench gen-readme` — edit the source, not this table -->

| Composite | What it is |
|---|---|
<!-- END:composites -->

### Investigations

<!-- BEGIN:investigations -->
<!-- generated by `vivarium-workbench gen-readme` — edit the source, not this table -->

| Investigation | Research question |
|---|---|
<!-- END:investigations -->

## Layout

Project code lives at the repo root; research state is grouped under `workspace/`
(the `.pbg/` machine state stays at the root like `.git/`). Directory locations
come from the `layout:` map in `workspace.yaml` — edit it to move things.

- `workspace.yaml` — canonical state (validated against `.pbg/schemas/workspace.schema.json`).
- `mosaic_compose/` — your Python package (`core.py` exposes `build_core()`).
- `scripts/` — `lint-workspace.py`, `serve.sh`, helpers.
- `workspace/studies/`, `workspace/composites/`, `workspace/references/`, `workspace/datasets/` — research artifacts.
- `workspace/notes/` — friction logs, walkthroughs, agent transcripts, ADRs. See `workspace/notes/README.md` for the
  cleanup rule: **files under `notes/` survive cleanup sweeps by default**, because they're the
  input to the next round of infrastructure improvements.
- `.pbg/schemas/` — JSON schemas the lint + dashboard validate against.

## Cleanup conventions

Cleanup PRs (`chore(cleanup): …`, `chore(repo): trim …`) routinely remove generated files,
one-shot scripts, and stale planning docs. Two locations are off-limits to bulk cleanup:

- `workspace/notes/**` — see the rule in `workspace/notes/README.md`.
- `workspace/references/notes/**` — per-paper literature notes, used by the findings protocol.

If a specific file in either location is genuinely obsolete, delete it in its own commit
with a one-line justification per file. Don't bundle with unrelated cleanup.
