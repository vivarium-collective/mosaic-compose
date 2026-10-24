"""MOSAIC composites — importing this fires the @composite_generator decorators
so the workbench composite browser discovers them."""
from __future__ import annotations

from mosaic_compose.composites import dfba as _dfba  # noqa: F401
from mosaic_compose.composites import community as _community  # noqa: F401
from mosaic_compose.composites import hormone as _hormone  # noqa: F401
