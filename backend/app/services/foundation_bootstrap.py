"""Explicit, transaction-owned bootstrap for the local P0 foundation."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.foundation.local_founder import (
    DEFAULT_MEMBERSHIP_ID,
    DEFAULT_TENANT_ID,
    DEFAULT_WORKSPACE_ID,
    LOCAL_FOUNDER_PRINCIPAL_ID,
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


DEFAULT_USER_ID = "usr_local_founder"
DEFAULT_TENANT_NAME = "Local Organization"
DEFAULT_WORKSPACE_NAME = "Personal Workspace"

PERMISSIONS = {
    "tenant.manage",
    "workspace.manage",
    "membership.manage",
    "role.manage",
    "policy.manage",
    "workflow.manage",
    "project.manage",
    "work_order.read",
    "work_order.create",
    "work_order.execute",
    "approval.request",
    "approval.decide",
    "review.request",
    "review.decide",
    "asset.read",
    "audit.read",
    "cost.read",
    "promotion.create",
    "customer_data.promote",
}

ROLE_PERMISSIONS = {
    "Owner": PERMISSIONS,
    "Admin": {
        "workspace.manage",
        "policy.manage",
        "workflow.manage",
        "project.manage",
        "work_order.read",
        "work_order.create",
        "work_order.execute",
        "approval.request",
        "review.request",
        "asset.read",
        "audit.read",
        "cost.read",
        "promotion.create",
        "customer_data.promote",
    },
    "Operator": {
        "project.manage",
        "work_order.read",
        "work_order.create",
        "work_order.execute",
        "approval.request",
        "review.request",
        "asset.read",
        "promotion.create",
    },
    "Reviewer": {
        "work_order.read",
        "approval.decide",
        "review.decide",
        "asset.read",
        "audit.read",
    },
    "Viewer": {
        "work_order.read",
        "asset.read",
        "audit.read",
        "cost.read",
    },
}


@dataclass(frozen=True)
class BootstrapResult:
    tenant_id: str
    workspace_id: str
    user_id: str
    membership_id: str
    permission_names: frozenset[str]


def _permission_id(name: str) -> str:
    return "perm_" + name.replace(".", "_")


def _role_id(name: str) -> str:
    return "rol_" + name.lower()


def bootstrap_local_foundation(session: Session) -> BootstrapResult:
    """Create fixed local roots in the caller's transaction; never commits."""
    tenant = session.get(Tenant, DEFAULT_TENANT_ID)
    if tenant is None:
        tenant = Tenant(
            tenant_id=DEFAULT_TENANT_ID,
            name=DEFAULT_TENANT_NAME,
            slug="local",
            status="active",
            created_by=LOCAL_FOUNDER_PRINCIPAL_ID,
            updated_by=LOCAL_FOUNDER_PRINCIPAL_ID,
        )
        session.add(tenant)

    workspace = session.get(Workspace, DEFAULT_WORKSPACE_ID)
    if workspace is None:
        workspace = Workspace(
            workspace_id=DEFAULT_WORKSPACE_ID,
            tenant_id=DEFAULT_TENANT_ID,
            name=DEFAULT_WORKSPACE_NAME,
            slug="personal",
            status="active",
            created_by=LOCAL_FOUNDER_PRINCIPAL_ID,
            updated_by=LOCAL_FOUNDER_PRINCIPAL_ID,
        )
        session.add(workspace)

    user = session.get(FoundationUser, DEFAULT_USER_ID)
    if user is None:
        user = FoundationUser(
            user_id=DEFAULT_USER_ID,
            principal_name=LOCAL_FOUNDER_PRINCIPAL_ID,
            display_name="Founder",
            status="active",
        )
        session.add(user)

    membership = session.get(Membership, DEFAULT_MEMBERSHIP_ID)
    if membership is None:
        membership = Membership(
            membership_id=DEFAULT_MEMBERSHIP_ID,
            tenant_id=DEFAULT_TENANT_ID,
            workspace_id=DEFAULT_WORKSPACE_ID,
            user_id=DEFAULT_USER_ID,
            scope_key=f"{DEFAULT_TENANT_ID}:{DEFAULT_WORKSPACE_ID}",
            status="active",
        )
        session.add(membership)

    session.flush()

    permissions_by_name: dict[str, Permission] = {}
    for name in sorted(PERMISSIONS):
        permission_id = _permission_id(name)
        permission = session.get(Permission, permission_id)
        if permission is None:
            resource, command = name.split(".", 1)
            permission = Permission(
                permission_id=permission_id,
                name=name,
                resource=resource,
                command=command,
            )
            session.add(permission)
        permissions_by_name[name] = permission

    roles_by_name: dict[str, Role] = {}
    for name in ROLE_PERMISSIONS:
        role_id = _role_id(name)
        role = session.get(Role, role_id)
        if role is None:
            role = Role(
                role_id=role_id,
                tenant_id=DEFAULT_TENANT_ID,
                name=name,
                scope_type="workspace",
                status="active",
            )
            session.add(role)
        roles_by_name[name] = role

    session.flush()

    for role_name, permission_names in ROLE_PERMISSIONS.items():
        role = roles_by_name[role_name]
        for permission_name in sorted(permission_names):
            permission = permissions_by_name[permission_name]
            key = (role.role_id, permission.permission_id)
            if session.get(RolePermission, key) is None:
                session.add(
                    RolePermission(
                        role_id=role.role_id,
                        permission_id=permission.permission_id,
                    )
                )

    owner_role = roles_by_name["Owner"]
    membership_role_key = (DEFAULT_MEMBERSHIP_ID, owner_role.role_id)
    if session.get(MembershipRole, membership_role_key) is None:
        session.add(
            MembershipRole(
                membership_id=DEFAULT_MEMBERSHIP_ID,
                role_id=owner_role.role_id,
            )
        )

    session.flush()
    return BootstrapResult(
        tenant_id=DEFAULT_TENANT_ID,
        workspace_id=DEFAULT_WORKSPACE_ID,
        user_id=DEFAULT_USER_ID,
        membership_id=DEFAULT_MEMBERSHIP_ID,
        permission_names=frozenset(PERMISSIONS),
    )
