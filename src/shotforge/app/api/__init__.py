"""API route namespace."""

from shotforge.app.api.providers import build_provider_router
from shotforge.app.api.runs import build_run_router
from shotforge.app.api.system import build_system_router

__all__ = ["build_provider_router", "build_run_router", "build_system_router"]
