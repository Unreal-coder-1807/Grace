"""
API routes package initialization.

This module exposes the routers from all route modules to be imported by the main API module.
"""
from api.routes.auth import router as auth
from api.routes.voice import router as voice
from api.routes.gestures import router as gestures
from api.routes.system import router as system

__all__ = ['auth', 'voice', 'gestures', 'system']