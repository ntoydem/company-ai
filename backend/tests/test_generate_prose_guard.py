"""`generate_prose.py` must never overwrite a hand-edited prose file (Phase 3.2c)."""

from __future__ import annotations

from pathlib import Path

from seed_data.generator.generate_prose import PROSE_DIR, is_hand_edited

HAND_EDITED_DOCS = (
    "DOC-ANK-DEV-001",
    "DOC-ANK-EPC-002",
    "DOC-ANK-FIN-001",
    "DOC-ANK-FIN-004",
    # Adım 5 (09.10.2026): the hand-edited DSCR/tenor-change content moved from
    # DOC-ANK-FIN-005 to DOC-ANK-FIN-006 (the two documents' roles were realigned).
    "DOC-ANK-FIN-006",
    "DOC-IZM-DEV-003",
    "DOC-CO-ADM-003",
)


def test_marker_detected_and_absent_file_is_not_protected(tmp_path: Path) -> None:
    marked = tmp_path / "A.yaml"
    marked.write_text("doc_id: A\nhand_edited: yes, phase 3.2c\nsections: []\n", encoding="utf-8")
    plain = tmp_path / "B.yaml"
    plain.write_text("doc_id: B\nsections: []\n", encoding="utf-8")
    assert is_hand_edited(marked)
    assert not is_hand_edited(plain)
    assert not is_hand_edited(tmp_path / "missing.yaml")


def test_phase_3_2c_prose_files_carry_the_marker() -> None:
    for doc_id in HAND_EDITED_DOCS:
        assert is_hand_edited(PROSE_DIR / f"{doc_id}.yaml"), doc_id
