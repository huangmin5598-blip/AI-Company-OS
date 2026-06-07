"""Declarative base isolated from legacy application startup metadata."""

from sqlalchemy.orm import DeclarativeBase


class FoundationBase(DeclarativeBase):
    pass
