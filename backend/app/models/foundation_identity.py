"""P0 Tenant, Workspace, User, Membership, Role, and Permission models."""

from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from app.models.foundation_base import FoundationBase


class Tenant(FoundationBase):
    __tablename__ = "tenants"

    tenant_id = Column(String(64), primary_key=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(120), nullable=False, unique=True)
    status = Column(String(32), nullable=False, default="active")
    created_by = Column(String(64), nullable=False)
    updated_by = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Workspace(FoundationBase):
    __tablename__ = "workspaces"

    workspace_id = Column(String(64), primary_key=True)
    tenant_id = Column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = Column(String(200), nullable=False)
    slug = Column(String(120), nullable=False)
    status = Column(String(32), nullable=False, default="active")
    created_by = Column(String(64), nullable=False)
    updated_by = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_workspaces_tenant_slug"),
    )


class FoundationUser(FoundationBase):
    __tablename__ = "users"

    user_id = Column(String(64), primary_key=True)
    principal_name = Column(String(160), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    status = Column(String(32), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Membership(FoundationBase):
    __tablename__ = "memberships"

    membership_id = Column(String(64), primary_key=True)
    tenant_id = Column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    workspace_id = Column(
        String(64),
        ForeignKey("workspaces.workspace_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    user_id = Column(
        String(64),
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    scope_key = Column(String(160), nullable=False)
    status = Column(String(32), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "scope_key", name="uq_memberships_user_scope"),
    )


class Role(FoundationBase):
    __tablename__ = "roles"

    role_id = Column(String(64), primary_key=True)
    tenant_id = Column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    name = Column(String(80), nullable=False)
    scope_type = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "name",
            "scope_type",
            name="uq_roles_tenant_name_scope",
        ),
    )


class Permission(FoundationBase):
    __tablename__ = "permissions"

    permission_id = Column(String(64), primary_key=True)
    name = Column(String(160), nullable=False, unique=True)
    resource = Column(String(80), nullable=False)
    command = Column(String(80), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RolePermission(FoundationBase):
    __tablename__ = "role_permissions"

    role_id = Column(
        String(64),
        ForeignKey("roles.role_id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id = Column(
        String(64),
        ForeignKey("permissions.permission_id", ondelete="CASCADE"),
        primary_key=True,
    )


class MembershipRole(FoundationBase):
    __tablename__ = "membership_roles"

    membership_id = Column(
        String(64),
        ForeignKey("memberships.membership_id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id = Column(
        String(64),
        ForeignKey("roles.role_id", ondelete="CASCADE"),
        primary_key=True,
    )
