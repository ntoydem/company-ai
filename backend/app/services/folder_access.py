"""Pure folder-access resolution (B-26, ADR-023): given the whole tree and all grants (a
few dozen rows), compute each department's *effective* access on each folder. Kept free of
SQLAlchemy so the rule — nearest ancestor-or-self definition wins, nothing else — is unit
tested on plain data and shared by the gate provider, the admin API and the user view."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.models.folder import Folder, FolderAccess, FolderGrant

Access = Literal["none", "read", "write"]
EffectiveAccess = Literal["none", "read", "write", "owner"]


@dataclass(frozen=True)
class EffectiveGrant:
    department_id: UUID
    access: FolderAccess
    inherited: bool


class FolderAccessMap:
    def __init__(self, folders: Iterable[Folder], grants: Iterable[FolderGrant]) -> None:
        self._folders: dict[UUID, Folder] = {f.id: f for f in folders}
        self._own: dict[UUID, dict[UUID, FolderAccess]] = {}
        for grant in grants:
            self._own.setdefault(grant.folder_id, {})[grant.department_id] = grant.access
        self._children: dict[UUID | None, list[UUID]] = {}
        for folder in self._folders.values():
            self._children.setdefault(folder.parent_id, []).append(folder.id)

    # --- tree ---

    def ancestors_and_self(self, folder_id: UUID) -> list[Folder]:
        """From the folder itself up to the root (cycles are impossible: parents are
        validated on write, but the walk is bounded by the folder count anyway)."""
        chain: list[Folder] = []
        current: UUID | None = folder_id
        while current is not None and current in self._folders and len(chain) <= len(self._folders):
            folder = self._folders[current]
            chain.append(folder)
            current = folder.parent_id
        return chain

    def subtree_ids(self, folder_id: UUID) -> set[UUID]:
        result: set[UUID] = set()
        stack = [folder_id]
        while stack:
            current = stack.pop()
            if current in result:
                continue
            result.add(current)
            stack.extend(self._children.get(current, []))
        return result

    # --- access ---

    def effective_grants(self, folder_id: UUID) -> list[EffectiveGrant]:
        """Every department with a definition on this folder or an ancestor; the nearest
        definition wins (BACKEND_GAPS §2.6.1/5). The owner is not a grant."""
        owner_id = self._folders[folder_id].owner_department_id
        seen: dict[UUID, EffectiveGrant] = {}
        for depth, folder in enumerate(self.ancestors_and_self(folder_id)):
            for department_id, access in self._own.get(folder.id, {}).items():
                if department_id == owner_id or department_id in seen:
                    continue
                seen[department_id] = EffectiveGrant(department_id, access, inherited=depth > 0)
        return sorted(seen.values(), key=lambda g: str(g.department_id))

    def access_for(self, folder_id: UUID, department_ids: Iterable[UUID]) -> EffectiveAccess:
        """Best access any of `department_ids` has on the folder: owner > write > read > none."""
        wanted = set(department_ids)
        if not wanted or folder_id not in self._folders:
            return "none"
        if self._folders[folder_id].owner_department_id in wanted:
            return "owner"
        best: EffectiveAccess = "none"
        for grant in self.effective_grants(folder_id):
            if grant.department_id in wanted:
                if grant.access == FolderAccess.write:
                    return "write"
                best = "read"
        return best

    def readable_folder_ids(self, department_ids: Iterable[UUID]) -> set[UUID]:
        """Folders where any of `department_ids` has at least read access through a grant
        (owned folders are not included — membership already covers them in the gate)."""
        wanted = set(department_ids)
        return {
            folder_id
            for folder_id in self._folders
            if any(g.department_id in wanted for g in self.effective_grants(folder_id))
        }

    def grantee_department_ids(self, folder_id: UUID) -> set[UUID]:
        return {g.department_id for g in self.effective_grants(folder_id)}
