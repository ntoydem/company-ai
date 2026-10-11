# İş Emri 2026-10-11 — Adım 2 Raporu

**Konu:** Ek-F (DOC-YSV-FIN-010) — eksik belge adının birebir anılması · **Tarih:** 11.10.2026
**Durum:** ✅ tamamlandı

## 1. Mimari karar

Constitution kuralı (`generate_prose.py`'nin sistem promptu): LLM hiçbir şirket/kurum adı
YAZMAZ, yalnız token'larla verilir. "Yeşilova TEİAŞ bağlantı anlaşması teminat mektubu"
ifadesini LLM'in DOĞRUDAN yazması bu kuralı ihlal ederdi (TEİAŞ bir kurum adı). Bunun yerine:

- `ledger_schema.py::Finance`'e yeni alan: `annex_f_missing_guarantee_letter_name: Fact | None`.
- `yesilova_res.yaml`: değer `"Yeşilova TEİAŞ bağlantı anlaşması teminat mektubu"` (USER_FACT).
- `DOC-YSV-FIN-010`'un `key_facts`'ine `missing_guarantee_letter_name` eklendi.
- `facts.py::_FIELD_KIND`'e `("text", "")` girişi eklendi.
- `document_specs/yesilova.py`: guidance artık `[[missing_guarantee_letter_name]]` token'ının
  **birebir kullanılmasını** açıkça istiyor (önceki tur yalnız paraphrase/dolaylı anlatım
  istemişti — bu, görevin "birebir adıyla" şartını tam karşılamıyordu).

Bu sayede ad hem LLM tarafından icat edilmiyor (gerçek bir ledger değeri) hem de constitution
kuralını ihlal etmiyor (token substitüsyonu, LLM'in kendi yazdığı metin değil).

**1 Claude çağrısı, ilk denemede kabul edildi ($0,0099).**

## 2. Render edilmiş TAM metin (DOC-YSV-FIN-010)

> **1. Purpose and Scope**
> This report, Yeşilova RES Annex F Raporu (2025) (reference DOC-YSV-FIN-010), sets out the Annex F reporting position of Yeşilova RES Enerji Üretim A.Ş. for the Yeşilova RES project. It covers the reporting year 2025 only. The document is dated October 1, 2026 and is currently marked Draft (2025).
> The report is a draft prepared for internal review. It has not yet been sent to any party, and its contents remain subject to confirmation before any onward submission.
> The parties connected with this reporting obligation are Yeşilova RES Enerji Üretim A.Ş., LMN Bank. The relevant counterparties for the purposes of this report are LMN Bank.
>
> **2. Compliance Summary**
> For the reporting year 2025, the debt service coverage ratio is recorded as 3.60x. Interest paid during the period amounts to 104,500 USD. The covenant test result is recorded as pass.
> The position with respect to LMN Bank is reflected in the figures above and is presented on the basis of the information available at the date of this draft.
> **The document Yeşilova TEİAŞ bağlantı anlaşması teminat mektubu is still outstanding and has not yet been submitted.** Until it is provided, the compliance position in this draft should be regarded as incomplete.
>
> **3. Covenant Test History** (kod ile üretilen tablo): Q4_2024 3.90x Pass · Q4_2025 3.60x Pass

**Birebir eşleşme doğrulandı:** "Yeşilova TEİAŞ bağlantı anlaşması teminat mektubu" — tam istenen
ifade, hiç paraphrase edilmeden.

## 3. Küçük gözlem (hata değil)

Bölüm 1'de hem `[[parties_list]]` hem `[[counterparty_list]]` art arda kullanılmış ("The
parties connected... are [[parties_list]]. The relevant counterparties... are
[[counterparty_list]]."). Bu bir HATA değil (self-reference kapısı tetiklenmiyor, farklı
değerler — `parties_list`=SPV+LMN Bank, `counterparty_list`=yalnız LMN Bank), yalnızca hafif
bir anlatım tekrarı. Düzeltme gerekmiyor, not olarak bırakıldı.

## 4. Kapı sonuçları

| Kapı | Sonuç |
|---|---|
| lint | ✅ |
| validate-ledger | ✅ 0 hata/uyarı |
| validate-documents --prose-only | ✅ |
| validate-excel | ✅ |
| validate-documents (full, 84 belge) | ⚠️ **3 hata — DOC-YSV-FIN-010'da DEĞİL** (Adım 1'deki aynı 3: OPS-008/CO-ADM-009/FIN-013, regresyon yok) |
| token-grep | ✅ temiz |
| yasak kelime (delivered/released/disclosed/version 2025/taksit #11) | ✅ temiz |

## 5. Maliyet

1 çağrı, $0,0099. **Kümülatif iş emrinde: $0,0163 (Adım 1) + $0,0099 (Adım 2) = $0,0262 / $1,2.**

## 6. Commit

`ledger_schema.py`, `yesilova_res.yaml`, `facts.py`, `document_specs/yesilova.py`,
`prose/DOC-YSV-FIN-010.yaml` — tek commit, bu rapordan sonra push edilecek.
