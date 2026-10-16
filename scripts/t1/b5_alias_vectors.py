"""İş Emri 2026-10-15T1 §B5 / 2026-10-16T3 — LLM-free alias test vector against the `projects`
table (SELECT only): `project_narrowing.unknown_project_names` (unknown-project refusal) and
`assist.named_project_codes` (recognition). The expected columns are the order's reading of the
intended behaviour; the script reports the actual result and whether it matches.

İş Emri 2026-10-16T3 (ADR-033): the `TEST_PRJ` row's expectation was updated for the live
deactivation (İş Emri 2026-10-16T2) — a deactivated project is never named, regardless of the
matcher fix. 15 rows appended (Turkish possessive/locative suffixes, ASCII spelling, case,
punctuation, "covenant testi"-style word-boundary) to re-measure the fix against T1's 36/45
baseline.

Run inside the backend container: `docker exec -i company-ai-backend-1 python - < this`.
Writes `results/t1/b5_alias_vectors.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.db import get_session_factory
from app.services.ask_router import route_without_llm
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
    # İş Emri 2026-10-16T3: this row's `expected_unknown` was `[]` under the old (pre-fix)
    # vector list — an oversight, not a design choice: "Güneşalan" is exactly the same
    # shape of mention as "Bursa RES" below (an unregistered name before RES/GES) and was
    # always detected as such by `_PROJECT_MENTION` (`Güneşalan` is capitalised); the row
    # only looked like it passed before because the *other* column (`named`) carried bug
    # (3) — "ges" alone wrongly named Akyar too. Corrected to match the Bursa rows.
    ("Güneşalan GES'in belgeleri var mı?", set(), ["Güneşalan GES"]),
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
    # İş Emri 2026-10-16T2: TEST_PRJ was deactivated live — a deactivated project is never
    # named, independent of this order's matcher fix.
    ("Test Project belgeleri nerede?", set(), []),
    ("Ankara RES'in kapasitesi nedir?", set(), ["Ankara RES"]),
    ("İzmir RES'in kapasitesi nedir?", set(), ["İzmir RES"]),
    # İş Emri 2026-10-16T3: relaxing the capitalised-first-letter requirement (bug 2) is
    # exactly what now flags "tepe RES" — a lower-case common word ("tepe", "hill") right
    # before RES, not the registered "Karatepe" (one word, no space). This is a direct,
    # intended side effect of the fix, not a new bug: a probable typo of "Karatepe RES"
    # that the matcher does not — and should not — silently guess at (no fuzzy matching in
    # this order's scope); asking for clarification is the safe-side outcome, same as any
    # other unrecognised name. `named` stays empty either way (not a word-for-word match).
    ("Kara tepe RES kapasitesi nedir?", set(), ["tepe RES"]),
    ("Karatepe Rüzgar Enerji Santrali'nin kapasitesi nedir?", {"ANK_RES"}, []),
    ("ANK_RES kapasitesi nedir?", set(), []),
    ("Karatepe RES Enerji Üretim A.Ş. unvanı nedir?", {"ANK_RES"}, []),
    # İş Emri 2026-10-16T3 (ADR-033) — 15 new rows: Turkish suffixes, ASCII, case,
    # punctuation, "covenant testi"-style word boundary.
    ("Kızılova'daki ÇED durumu nedir?", {"IZM_RES"}, []),
    ("Yeşilova'nın kredi bakiyesi nedir?", {"YSV_RES"}, []),
    ("Boztepe'de DSRA bakiyesi nedir?", {"BOZ_RES"}, []),
    ("Akyar'ın kamulaştırma notu nerede?", {"AKY_GES"}, []),
    ("Demirci'nin TEA itirazı nerede?", {"DMR_RES"}, []),
    ("Karatepe projesinde kaç çalışan var?", {"ANK_RES"}, []),
    ("Kizilova RES COD tarihi nedir?", {"IZM_RES"}, []),
    ("yesilova RES'in kredi bakiyesi nedir?", {"YSV_RES"}, []),
    ("Bursa Res'in kapasitesi nedir?", set(), ["Bursa Res"]),
    ("bursa ges'in kapasitesi nedir?", set(), ["bursa ges"]),
    ("BOZTEPE res kapasitesi nedir?", {"BOZ_RES"}, []),
    ("Karatepe (RES) kapasitesi nedir?", {"ANK_RES"}, []),
    ("Kredi covenant testi sonucu nedir?", set(), []),
    ("Performans testi raporu nerede?", set(), []),
    ("Karatepe RES ile BURSA RES'in kapasitesi nedir?", {"ANK_RES"}, ["BURSA RES"]),
)


def main() -> None:
    rows = []
    with get_session_factory()() as session:
        for text, exp_named, exp_unknown in VECTORS:
            named = named_project_codes(session, text)
            unknown = unknown_project_names(session, text)
            # İş Emri 2026-10-16N1: the pre-route reason (information only, not in `ok`).
            routed = route_without_llm(session, text)
            rows.append(
                {
                    "question": text,
                    "expected_named": sorted(exp_named),
                    "expected_unknown": exp_unknown,
                    "actual_named": sorted(named),
                    "actual_unknown": unknown,
                    "ok": named == exp_named and unknown == exp_unknown,
                    "route": routed.reason if routed is not None else "router",
                }
            )
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rows:
        mark = "OK " if r["ok"] else "XX "
        print(
            mark,
            r["question"],
            "| named",
            r["actual_named"],
            "| unknown",
            r["actual_unknown"],
            "| route",
            r["route"],
        )
    print("total", len(rows), "ok", sum(r["ok"] for r in rows))


if __name__ == "__main__":
    main()
