"""İş Emri 2026-10-15T1 §B5 — LLM-free alias test vector against the `projects` table
(SELECT only): `project_narrowing.unknown_project_names` (unknown-project refusal) and
`assist.named_project_codes` (recognition). The expected columns are the order's reading of the
intended behaviour; the script reports the actual result and whether it matches.

Run inside the backend container: `docker exec -i company-ai-backend-1 python - < this`.
Writes `results/t1/b5_alias_vectors.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.db import get_session_factory
from app.services.assist import named_project_codes
from app.services.project_narrowing import unknown_project_names

OUT_PATH = Path("results/t1/b5_alias_vectors.json")

# (question, expected named codes, expected unknown mentions)
VECTORS: tuple[tuple[str, set[str], list[str]], ...] = (
    ("Karatepe RES'in kapasitesi nedir?", {"ANK_RES"}, []),
    ("Karatepe RES kapasitesi nedir?", {"ANK_RES"}, []),
    ("Karatepe A.Ş.'nin kurulu gücü nedir?", {"ANK_RES"}, []),
    ("KARATEPE RES kapasitesi nedir?", {"ANK_RES"}, []),
    ("KARATEPE res kapasitesi nedir?", {"ANK_RES"}, []),
    ("karatepe kapasitesi nedir?", {"ANK_RES"}, []),
    ("Karatepe'nin kapasitesi nedir?", {"ANK_RES"}, []),
    ("Karatepe GES kapasitesi nedir?", {"ANK_RES"}, []),
    ("Karatepe Res. kapasitesi nedir?", {"ANK_RES"}, []),
    ("Karatepe  RES  kapasitesi nedir?", {"ANK_RES"}, []),
    ("Karatepe-RES kapasitesi nedir?", {"ANK_RES"}, []),
    ("Karatepe RES'in, kapasitesi nedir?", {"ANK_RES"}, []),
    ("Kızılova RES'in COD tarihi nedir?", {"IZM_RES"}, []),
    ("Kizilova RES'in COD tarihi nedir?", {"IZM_RES"}, []),
    ("KIZILOVA RES COD tarihi nedir?", {"IZM_RES"}, []),
    ("kızılova COD tarihi nedir?", {"IZM_RES"}, []),
    ("Kızılova GES COD tarihi nedir?", {"IZM_RES"}, []),
    ("Yeşilova RES'in kredi bakiyesi nedir?", {"YSV_RES"}, []),
    ("Yesilova RES'in kredi bakiyesi nedir?", {"YSV_RES"}, []),
    ("YEŞİLOVA RES kredi bakiyesi nedir?", {"YSV_RES"}, []),
    ("yeşilova kredi bakiyesi nedir?", {"YSV_RES"}, []),
    ("Boztepe RES'in DSRA bakiyesi nedir?", {"BOZ_RES"}, []),
    ("boztepe DSRA bakiyesi nedir?", {"BOZ_RES"}, []),
    ("Boztepe GES DSRA bakiyesi nedir?", {"BOZ_RES"}, []),
    ("Akyar GES kamulaştırma notu nerede?", {"AKY_GES"}, []),
    ("Demirci RES TEA itirazı nerede?", {"DMR_RES"}, []),
    ("Güneşalan GES'in belgeleri var mı?", set(), []),
    ("Bursa RES'in kapasitesi nedir?", set(), ["Bursa RES"]),
    ("Bursa GES'in kapasitesi nedir?", set(), ["Bursa GES"]),
    ("bursa RES'in kapasitesi nedir?", set(), ["bursa RES"]),
    ("BURSA RES kapasitesi nedir?", set(), ["BURSA RES"]),
    ("Bursa Res kapasitesi nedir?", set(), ["Bursa Res"]),
    ("Bursa'nın kapasitesi nedir?", set(), []),
    ("Karatepe RES ile Bursa RES'in kapasitesi nedir?", {"ANK_RES"}, ["Bursa RES"]),
    ("Karatepe RES ile Kızılova RES'in kapasitesi nedir?", {"ANK_RES", "IZM_RES"}, []),
    ("Hangi RES projesinde ÇED tamamlandı?", set(), []),
    ("Bu RES'in kapasitesi nedir?", set(), []),
    ("Tüm RES projelerinin kapasitesi nedir?", set(), []),
    ("Test Project belgeleri nerede?", {"TEST_PRJ"}, []),
    ("Ankara RES'in kapasitesi nedir?", set(), ["Ankara RES"]),
    ("İzmir RES'in kapasitesi nedir?", set(), ["İzmir RES"]),
    ("Kara tepe RES kapasitesi nedir?", set(), []),
    ("Karatepe Rüzgar Enerji Santrali'nin kapasitesi nedir?", {"ANK_RES"}, []),
    ("ANK_RES kapasitesi nedir?", set(), []),
    ("Karatepe RES Enerji Üretim A.Ş. unvanı nedir?", {"ANK_RES"}, []),
)


def main() -> None:
    rows = []
    with get_session_factory()() as session:
        for text, exp_named, exp_unknown in VECTORS:
            named = named_project_codes(session, text)
            unknown = unknown_project_names(session, text)
            rows.append(
                {
                    "question": text,
                    "expected_named": sorted(exp_named),
                    "expected_unknown": exp_unknown,
                    "actual_named": sorted(named),
                    "actual_unknown": unknown,
                    "ok": named == exp_named and unknown == exp_unknown,
                }
            )
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rows:
        mark = "OK " if r["ok"] else "XX "
        print(mark, r["question"], "| named", r["actual_named"], "| unknown", r["actual_unknown"])
    print("total", len(rows), "ok", sum(r["ok"] for r in rows))


if __name__ == "__main__":
    main()
