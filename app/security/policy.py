"""Simple role and permission policy object."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Set


@dataclass
class Policy:
    """Stores roles and permissions for a subject."""

    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)

    def add_role(self, role: str) -> None:
        self.roles.add(role)

    def remove_role(self, role: str) -> None:
        self.roles.discard(role)

    def add_permission(self, permission: str) -> None:
        self.permissions.add(permission)

    def remove_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def update(self, roles: Iterable[str] = (), permissions: Iterable[str] = ()) -> None:
        """Update roles and permissions from iterables."""
        self.roles.update(roles)
        self.permissions.update(permissions)


__all__ = ["Policy"]
