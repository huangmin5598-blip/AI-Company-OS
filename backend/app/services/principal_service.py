"""Membership-backed Principal Context resolution."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.foundation.context import (
    AuthenticationMethod,
    PrincipalContext,
    PrincipalType,
)
from app.models.foundation_identity import (
    FoundationUser,
    Membership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
    Tenant,
    Workspace,
)


class PrincipalResolutionDenied(PermissionError):
    pass


def resolve_membership_principal(
    session: Session,
    *,
    principal_name: str,
    tenant_id: str,
    workspace_id: str | None,
    authentication_method: AuthenticationMethod,
    principal_type: PrincipalType = PrincipalType.HUMAN,
    local_mode: bool = False,
) -> PrincipalContext:
    """Resolve active identity, membership, roles, and grants without leakage."""
    tenant = session.get(Tenant, tenant_id)
    if tenant is None or tenant.status != "active":
        raise PrincipalResolutionDenied("principal_scope_denied")

    if workspace_id is not None:
        workspace = session.get(Workspace, workspace_id)
        if (
            workspace is None
            or workspace.status != "active"
            or workspace.tenant_id != tenant_id
        ):
            raise PrincipalResolutionDenied("principal_scope_denied")

    user = session.execute(
        select(FoundationUser).where(
            FoundationUser.principal_name == principal_name,
            FoundationUser.status == "active",
        )
    ).scalar_one_or_none()
    if user is None:
        raise PrincipalResolutionDenied("principal_scope_denied")

    membership = session.execute(
        select(Membership).where(
            Membership.user_id == user.user_id,
            Membership.tenant_id == tenant_id,
            Membership.workspace_id == workspace_id,
            Membership.status == "active",
        )
    ).scalar_one_or_none()
    if membership is None:
        raise PrincipalResolutionDenied("principal_scope_denied")

    roles = session.execute(
        select(Role)
        .join(MembershipRole, MembershipRole.role_id == Role.role_id)
        .where(
            MembershipRole.membership_id == membership.membership_id,
            Role.status == "active",
        )
    ).scalars().all()
    role_ids = [role.role_id for role in roles]
    permissions = []
    if role_ids:
        permissions = session.execute(
            select(Permission)
            .join(
                RolePermission,
                RolePermission.permission_id == Permission.permission_id,
            )
            .where(RolePermission.role_id.in_(role_ids))
        ).scalars().all()

    return PrincipalContext(
        principal_id=principal_name,
        principal_type=principal_type,
        authentication_method=authentication_method,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        membership_id=membership.membership_id,
        role_names=frozenset(role.name for role in roles),
        permission_names=frozenset(permission.name for permission in permissions),
        local_mode=local_mode,
    )
