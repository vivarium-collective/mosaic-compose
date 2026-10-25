"""MOSAIC composites — importing this fires the @composite_generator decorators
so the workbench composite browser discovers them.

Each composite's import is guarded: a composite is backed by an optional
simulator package (viva-cobra for dFBA, viva-tellurium for the ODE arms,
viva-munk for the biofilm), installed via the ``foundations`` extra. So the
workspace still imports deps-light — a publish build or CI without the extra, or
any environment missing one package — by skipping the composites whose backing
package isn't installed rather than failing the whole import.
"""
from __future__ import annotations

import importlib

# dfba → viva-cobra; community/hormone → viva-tellurium; coculture → viva-cobra;
# colony → viva-munk. Import each independently so one missing package doesn't
# hide the others.
for _mod in ("dfba", "community", "hormone", "coculture", "colony"):
    try:
        importlib.import_module(f"mosaic_compose.composites.{_mod}")
    except Exception:  # noqa: BLE001 — optional simulator package absent
        pass
