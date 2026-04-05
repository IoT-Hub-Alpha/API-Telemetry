import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sys
import types

from starlette.middleware.base import BaseHTTPMiddleware

# Stub iot_logging
logging_mod = types.ModuleType("iot_logging")


class FastAPIRequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        return await call_next(request)


class StructuredJsonFormatter:
    def format(self, record):
        return record.getMessage()


logging_mod.FastAPIRequestContextMiddleware = FastAPIRequestContextMiddleware
logging_mod.StructuredJsonFormatter = StructuredJsonFormatter
sys.modules["iot_logging"] = logging_mod

# Stub iot_auth.fastapi and iot_auth.types
fastapi_mod = types.ModuleType("iot_auth.fastapi")
types_mod = types.ModuleType("iot_auth.types")


def require_permissions(_permission):
    def dependency():
        return {"sub": "test-user", "permissions": [_permission]}

    return dependency


fastapi_mod.require_permissions = require_permissions
types_mod.JWTPayload = dict
sys.modules["iot_auth.fastapi"] = fastapi_mod
sys.modules["iot_auth.types"] = types_mod
