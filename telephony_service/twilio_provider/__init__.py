# Public API: expose the app factory and router for convenience.
from .app.main import app, create_app  # noqa: F401
from .app.api.routes_calls import router  # noqa: F401
