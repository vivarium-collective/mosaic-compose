"""Shared emitter policy for the MOSAIC Foundations composites.

Every Foundations study emits through the **XArrayEmitter** (streaming
labelled-array / zarr sink) — the one consistent observation sink across the
metabolic (viva-cobra), community + hormone (viva-tellurium), and ABM arms.
The sink itself is selected by the workspace's ``runtime.default_emitter: xarray``
(``workspace.yaml``); the workbench run path builds and injects a correctly
configured ``XArrayEmitter`` step from that choice.

What the composites have to do is get *out of its way*: the upstream library
document builders (``viva_cobra.dfba_document``,
``viva_tellurium.make_tellurium_document``) each hardcode a RAM emitter node so
the document runs standalone under a bare ``Composite()``. Inside the workbench
that node is wrong twice over — it pins the sink to RAM instead of xarray, and
the tellurium builder's address (``local:ram-emitter``) is only registered by
that package's ``core_extensions``, not by the run core, so realizing it fails
with ``no link found at address: local:ram-emitter``.

So each Foundations composite calls ``strip_emitter`` on the builder's document
to drop that RAM node, leaving the run path to inject the workspace's XArray
sink. (We deliberately do NOT declare ``emitters=[{address: local:XArrayEmitter}]``
on the generator: the generic declaration-node builder can't supply the
transducer buffer config XArrayEmitter needs, so a baked declaration node fails
at ``Composite.initialize`` — the workbench's own injector is the thing that
builds a valid XArray node.)
"""
from __future__ import annotations

from typing import Any


def strip_emitter(doc: dict) -> dict:
    """Drop the library builder's hardcoded RAM emitter node from ``doc`` in place.

    Handles both the flat documents these builders return and a
    ``{"state": {...}}``-wrapped document. Removes the ``emitter`` node and any
    ``emitter_<i>`` siblings, leaving the run path to inject the workspace's
    configured sink.
    """
    state: Any = doc.get("state") if isinstance(doc.get("state"), dict) else doc
    for key in [k for k in list(state) if k == "emitter" or k.startswith("emitter_")]:
        state.pop(key, None)
    return doc
