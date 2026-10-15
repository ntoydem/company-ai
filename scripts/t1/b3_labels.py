"""İş Emri 2026-10-15T1 §B3 — LLM-free label consistency check (host, stdlib only).

Input: two `psql -At -F '|'` dumps of the live DB (read-only) —
  docs.txt   : external_ref|title|file_name|document_type|project_scope|project_code|department|
               status|counterparty|tags|extra_fields   (documents ⋈ projects)
  pages.txt  : external_ref|first-page text (document_pages.page_number = 1, newlines removed)
Output: JSON rows with the project names found per field and a verdict.

    python3 scripts/t1/b3_labels.py docs.txt pages.txt results/t1/b3_labels.json
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

NAME_TO_CODE = {
    "karatepe": "ANK_RES",
    "kızılova": "IZM_RES",
    "kizilova": "IZM_RES",
    "yeşilova": "YSV_RES",
    "yesilova": "YSV_RES",
    "boztepe": "BOZ_RES",
    "akyar": "AKY_GES",
    "demirci": "DMR_RES",
    "güneşalan": "GNS_GES",
    "gunesalan": "GNS_GES",
}
FIELDS = ("dosya", "başlık", "sayfa1", "karşı taraf", "extra")


def turkish_lower(text: str) -> str:
    return text.replace("İ", "i").replace("I", "ı").lower()


def verdict_for(scope: str, code: str, found: set[str]) -> tuple[str, str]:
    if scope == "group":
        if len(found) == 1:
            return "⚠", f"grup işaretli, metin tek projeyi anıyor: {sorted(found)[0]}"
        if len(found) > 1:
            return "✓", f"grup; birden çok proje anılıyor {sorted(found)}"
        return "✓", "grup; proje adı yok"
    if code not in found and found:
        return "✗", f"atanan {code} metinde yok; anılan {sorted(found)}"
    if code not in found:
        return "?", "ad/başlık/ilk sayfada hiçbir proje adı yok (yalnız metadata)"
    if found - {code}:
        return "⚠", f"atanan {code} var; ayrıca {sorted(found - {code})} anılıyor"
    return "✓", ""


def main(argv: list[str]) -> int:
    docs_path, pages_path, out_path = (Path(a) for a in argv[1:4])
    pages: dict[str, str] = {}
    for line in pages_path.read_text(encoding="utf-8").splitlines():
        ref, _, text = line.partition("|")
        pages[ref] = text
    rows = []
    for line in docs_path.read_text(encoding="utf-8").splitlines():
        ref, title, fname, dtype, scope, code, dept, status, cpty, _tags, extra = line.split("|")[
            :11
        ]
        values = (fname, title, pages.get(ref, ""), cpty, extra)
        found: dict[str, set[str]] = {}
        for field, value in zip(FIELDS, values, strict=True):
            low = turkish_lower(value)
            for name, c in NAME_TO_CODE.items():
                if re.search(rf"\b{name}", low):
                    found.setdefault(c, set()).add(field)
        verdict, note = verdict_for(scope, code, set(found))
        rows.append(
            {
                "ref": ref,
                "title": title,
                "file_name": fname,
                "type": dtype,
                "scope": scope,
                "code": code,
                "department": dept,
                "status": status,
                "found": {k: sorted(v) for k, v in found.items()},
                "verdict": verdict,
                "note": note,
                "has_page1": ref in pages,
            }
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(Counter((r["scope"], r["verdict"]) for r in rows))
    for r in rows:
        if r["verdict"] != "✓" or r["scope"] == "group":
            print(r["verdict"], r["ref"], r["scope"], r["code"], "|", r["title"], "|", r["note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
