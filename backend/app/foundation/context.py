"""Principal, request, and Tenant/Workspace scope envelopes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.foundation.authorization import require_permission
from app.foundation.clock import utc_now
from app.foundation.identity import new_id


class PrincipalType(str, Enum):
    HUMAN = "human"
    SERVICE = "service"
    AGENT = "agent"
    RUNTIME_WRAPPER = "runtime_wrapper"
    MIGRATION = "migration"
    PLATFORM_ADMIN = "platform_admin"


class AuthenticationMethod(str, Enum):
    LOCAL_LOOPBACK = "local_loopback"
    SESSION = "session"
    TOKEN = "token"
    SERVICE_CREDENTIAL = "service_credential"


class RequestOrigin(str, Enum):
    API = "api"
    CLI = "cli"
    UI = "ui"
    MIGRATION = "migration"
    INTERNAL_WORKER = "internal_worker"


@dataclass(frozen=True)
class PrincipalContext:
    principal_id: str
    principal_type: PrincipalType
    authentication_method: AuthenticationMethod
    tenant_id: str
    workspace_id: str | None
    membership_id: str | None = None
    role_names: frozenset[str] = field(default_factory=frozenset)
    permission_names: frozenset[str] = field(default_factory=frozenset)
    authenticated_at: datetime = field(default_factory=utc_now)
    local_mode: bool = False


@dataclass(frozen=True)
class ScopeContext:
    principal: PrincipalContext
    tenant_id: str
    workspace_id: str | None

    def __post_init__(self) -> None:
        if self.tenant_id != self.principal.tenant_id:
            raise ValueError("scope_tenant_mismatch")
        if (
            self.principal.workspace_id is not None
            and self.workspace_id != self.principal.workspace_id
        ):
            raise ValueError("scope_workspace_mismatch")

    @property
    def principal_id(self) -> str:
        return self.principal.principal_id

    @property
    def principal_type(self) -> str:
        return self.principal.principal_type.value

    @property
    def scope_key(self) -> str:
        return f"{self.tenant_id}:{self.workspace_id or '-'}"

    def require(self, permission: str) -> None:
        require_permission(self.principal.permission_names, permission)


@dataclass(frozen=True)
class RequestContext:
    scope: ScopeContext
    origin: RequestOrigin
    correlation_id: str = field(default_factory=lambda: new_id("cor"))
    causation_id: str | None = None
    idempotency_key: str | None = None
    expected_row_version: int | None = None
    mode: str = "os_governed"
