"""mosaic_compose — workspace Python package."""
from __future__ import annotations

# Import the composites subpackage so its @composite_generator decorators register
# with the workbench composite browser (editable installs are skipped by the
# auto-discovery scan, so the explicit import is what makes them visible). Guarded
# so the package still imports deps-light (e.g. a publish build without viva-cobra /
# cobra installed): the dFBA composites simply won't register.
try:  # noqa: SIM105
    from mosaic_compose import composites as _composites  # noqa: F401
except Exception:
    _composites = None
