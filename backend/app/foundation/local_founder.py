"""Explicit loopback-only local Founder identity."""

from __future__ import annotations

from ipaddress import ip_address

from app.foundation.context import (
    AuthenticationMethod,
    PrincipalContext,
    PrincipalType,
)


LOCAL_FOUNDER_PRINCIPAL_ID = "local-founder"
DEFAULT_TENANT_ID = "ten_local"
DEFAULT_WORKSPACE_ID = "wsp_personal"
DEFAULT_MEMBERSHIP_ID = "mem_local_founder_personal"


class LocalFounderUnavailable(PermissionError):
    pass


def _is_loopback(host: str) -> bool:
    normalized = host.strip().lower()
    if normalized == "localhost":
        return True
    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


def resolve_local_founder(
    *,
    client_host: str,
    local_mode_enabled: bool,
    permission_names: frozenset[str],
    forwarded_for: str | None = None,
) -> PrincipalContext:
    if not local_mode_enabled:
        raise LocalFounderUnavailable("local_founder_disabled")
    if forwarded_for:
        raise LocalFounderUnavailable("local_founder_forwarded_request_denied")
    if not _is_loopback(client_host):
        raise LocalFounderUnavailable("local_founder_loopback_required")
    return PrincipalContext(
        principal_id=LOCAL_FOUNDER_PRINCIPAL_ID,
        principal_type=PrincipalType.HUMAN,
        authentication_method=AuthenticationMethod.LOCAL_LOOPBACK,
        tenant_id=DEFAULT_TENANT_ID,
        workspace_id=DEFAULT_WORKSPACE_ID,
        membership_id=DEFAULT_MEMBERSHIP_ID,
        role_names=frozenset({"Owner"}),
        permission_names=permission_names,
        local_mode=True,
    )
