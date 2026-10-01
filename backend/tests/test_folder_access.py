"""Pure folder-access rules (B-26, ADR-023): nearest ancestor-or-self definition wins; the
owner is never a grant; `write` beats `read`; subtree/readable sets. No database."""

from __future__ import annotations

import uuid

from app.models.folder import Folder, FolderAccess, FolderGrant
from app.services.folder_access import FolderAccessMap

HUKUK, FINANS, ENERJI = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()


def _folder(name: str, owner: uuid.UUID, parent: Folder | None = None) -> Folder:
    return Folder(
        id=uuid.uuid4(),
        name=name,
        owner_department_id=owner,
        parent_id=parent.id if parent else None,
    )


def _grant(folder: Folder, department: uuid.UUID, access: FolderAccess) -> FolderGrant:
    return FolderGrant(folder_id=folder.id, department_id=department, access=access)


def _tree() -> tuple[Folder, Folder, Folder, Folder]:
    root = _folder("Hukuk", HUKUK)
    contracts = _folder("Proje Sözleşmeleri", HUKUK, root)
    ankara = _folder("Ankara RES", HUKUK, contracts)
    cases = _folder("Davalar", HUKUK, root)
    return root, contracts, ankara, cases


def test_nearest_definition_wins_and_inheritance_flag_is_set() -> None:
    root, contracts, ankara, cases = _tree()
    access = FolderAccessMap(
        [root, contracts, ankara, cases],
        [_grant(contracts, FINANS, FolderAccess.read), _grant(ankara, FINANS, FolderAccess.write)],
    )
    assert access.access_for(root.id, [FINANS]) == "none"
    assert access.access_for(contracts.id, [FINANS]) == "read"
    assert access.access_for(ankara.id, [FINANS]) == "write"  # child definition overrides
    assert access.access_for(cases.id, [FINANS]) == "none"  # sibling branch untouched
    grants = {g.department_id: g for g in access.effective_grants(ankara.id)}
    assert grants[FINANS].access == FolderAccess.write and grants[FINANS].inherited is False
    inherited = {g.department_id: g for g in access.effective_grants(contracts.id)}
    assert inherited[FINANS].inherited is False
    # A grant three levels up is still inherited (depth > 0).
    deep = FolderAccessMap([root, contracts, ankara], [_grant(root, ENERJI, FolderAccess.read)])
    assert deep.effective_grants(ankara.id)[0].inherited is True
    assert deep.access_for(ankara.id, [ENERJI]) == "read"


def test_owner_is_not_a_grant_and_beats_everything() -> None:
    root, contracts, *_ = _tree()
    access = FolderAccessMap([root, contracts], [_grant(contracts, HUKUK, FolderAccess.read)])
    assert access.effective_grants(contracts.id) == []  # owner's own "grant" is ignored
    assert access.access_for(contracts.id, [HUKUK]) == "owner"
    assert access.access_for(contracts.id, [HUKUK, FINANS]) == "owner"


def test_best_access_across_several_departments_and_readable_set() -> None:
    root, contracts, ankara, cases = _tree()
    access = FolderAccessMap(
        [root, contracts, ankara, cases],
        [_grant(contracts, FINANS, FolderAccess.read), _grant(cases, ENERJI, FolderAccess.write)],
    )
    assert access.access_for(contracts.id, [FINANS, ENERJI]) == "read"
    assert access.access_for(cases.id, [FINANS, ENERJI]) == "write"
    assert access.readable_folder_ids([FINANS]) == {contracts.id, ankara.id}
    assert access.readable_folder_ids([ENERJI]) == {cases.id}
    assert access.readable_folder_ids([HUKUK]) == set()  # owned folders come via membership
    assert access.subtree_ids(root.id) == {root.id, contracts.id, ankara.id, cases.id}
    assert access.subtree_ids(contracts.id) == {contracts.id, ankara.id}
    assert access.grantee_department_ids(ankara.id) == {FINANS}
    assert access.access_for(uuid.uuid4(), [FINANS]) == "none"  # unknown folder
