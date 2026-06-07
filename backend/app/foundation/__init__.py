"""Security, identity, scope, and audit foundations for canonical OS work."""

from app.foundation.authorization import AuthorizationDenied, is_permission_granted
from app.foundation.clock import format_utc, parse_utc, utc_now
from app.foundation.context import (
    AuthenticationMethod,
    PrincipalContext,
    PrincipalType,
    RequestContext,
    RequestOrigin,
    ScopeContext,
)
from app.foundation.identity import new_id

__all__ = [
    "AuthenticationMethod",
    "AuthorizationDenied",
    "PrincipalContext",
    "PrincipalType",
    "RequestContext",
    "RequestOrigin",
    "ScopeContext",
    "format_utc",
    "is_permission_granted",
    "new_id",
    "parse_utc",
    "utc_now",
]
