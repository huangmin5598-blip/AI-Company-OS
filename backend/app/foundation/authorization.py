"""Server-side permission evaluation primitives."""

from __future__ import annotations


class AuthorizationDenied(PermissionError):
    def __init__(self, permission: str):
        self.permission = permission
        super().__init__("authorization_denied")


def is_permission_granted(grants: frozenset[str], permission: str) -> bool:
    if "*" in grants or permission in grants:
        return True
    resource, separator, _action = permission.partition(".")
    return bool(separator and f"{resource}.*" in grants)


def require_permission(grants: frozenset[str], permission: str) -> None:
    if not is_permission_granted(grants, permission):
        raise AuthorizationDenied(permission)
