# Phase 3.2c Raporu — Prose yaması (Phase 3.2b'nin kalan 11 sorusu)

**Tarih:** 25.09.2026  **Model:** Fable 5.1  **Tag:** phase-3-2c  **Commit:** (bu rapor commit'iyle aynı)

Naci'nin kararı (25.09.2026): Phase 3.2b'nin belge-içerik boşluklarını Phase 5.1'e bırakmak yerine şimdi, dar
kapsamlı bir prose yamasıyla kapat; negatif-olgu soruları (`IZM-DEV-005/006`, NO OPINION çelişkisi) hariç.
Ayrı faz (3.2c) olarak açıldı: 3.2b kod/prompt fazıydı ve etiketliydi; bu faz yalnızca **içerik** (prose +
`key_facts` eşlemesi) değiştiriyor — ledger **değerleri** değişmedi.

## 1. Kabul kriterleri
| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| 1 | Yalnızca 3.2b'nin kalan sorularını kapatan prose yaması; yeni özellik yok | ✅ | §2 — 6 prose dosyasında 7 cümle, 5 `key_facts` eşlemesi, 4 `_FIELD_KIND` girdisi, 1 validator sağlamlaştırması |
| 2 | Ledger değerleri değişmedi; validator 0 hata | ✅ | `make validate-ledger` 0/0; `validate_documents` (prose P1/P2 + PDF G1-G6) 0/0 |
| 3 | Reseed + 43 çağrılık eval | ✅ | §3 |
| 4 | isolation/hallucination/authorization %100; document/temporal ≥ %80 | ✅ **tüm eşikler karşılandı** (authorization/hallucination/isolation %100, document %87,0, temporal %88,9) | §3 |

## 2. Yapılanlar (yalnızca içerik)

| Soru | Belge (sayfa) | Eklenen/değişen cümle (prose, `[[token]]`) | Ledger `key_facts` eki |
|---|---|---|---|
| `ANK-FIN-003/004` yerli banka / ECA | Facility Agreement §2 | "…comprises a local bank facility of `[[local_debt]]` provided by `[[counterparty]]` and an export credit agency (ECA) facility of `[[eca_debt]]`…" (önce iki tutar etiketsizdi) | — |
| `ANK-FIN-007` ilk DSCR | Facility Agreement §5; Draft §2 | "…a minimum debt service coverage ratio (DSCR) of `[[dscr_covenant]]`" (önce "financial ratios … threshold set for", "DSCR" hiç geçmiyordu) | — |
| `ANK-FIN-001`, `ANK-ISO-003` financial close | Facility Agreement §3 ("scheduled for"); Amendment 01 §1 ("was achieved on") | `[[financial_close_date]]` | FIN-004, FIN-005: `financial_close_date: project.timeline.financial_close.date` |
| `ANK-FIN-012` DSCR ne zaman/hangi belgeyle | Amendment 01 §2 | "…(DSCR) to `[[dscr_covenant]]` with effect from `[[effective_date]]`" | — (`effective_date` standart olgu) |
| `ANK-EPC-004` COD erteleme sebebi | Provisional Acceptance & COD Certificate §1 | "…deferred from the initially expected `[[cod_expected]]`, the recorded reason being `[[cod_deferral_reason]]`" | EPC-002: `cod_expected`, `cod_deferral_reason: change_orders[0].subject.value` |
| `ANK-DEV-001` development başlangıcı | Ankara RES Üretim Lisansı, Lisans Kapsamı | "Projenin geliştirme süreci `[[development_start]]` tarihinde başlamıştır." | DEV-001: `development_start: project.timeline.development_start.date` |
| `IZM-DEV-007` tamamlanan adımlar | ÇED Süreci Durum Yazısı, Süreç Durumu | "Bugüne kadar önlisans (`[[pre_licence_date]]`) ve arazi edinimi (`[[land_acquisition_start]]` itibarıyla) adımları tamamlanmıştır." | IZM-DEV-003: `pre_licence_date`, `land_acquisition_start` |

- `seed_data/generator/facts.py` `_FIELD_KIND`: `financial_close_date`, `development_start` (date), `cod_deferral_reason` (text).
- `seed_data/generator/validate_documents.py` G4: olgu-metinde-var kontrolü artık boşluk-duyarsız (PyMuPDF satır
  başına bir `\n` döndürüyor; "June\n30, 2023" aynı olgu). Önceki koşullarda aynı tarih başka bir yerde kırılmadan
  geçtiği için fark edilmemişti — yalnızca doğrulayıcı sağlamlaştırması, üretim davranışı değişmedi.
- Prose dosyaları `tag: AI_ASSUMPTION` kaldı (elle düzenlenen cümleler de rakam/tarih/isim içermiyor — P1/P2 geçti);
  `make prose` **çalıştırılmadı**, LLM çağrısı yok. Başlıklar/sayfa haritası değişmedi (testlerin `page_of` çapaları).
- `make reset-demo --yes` + `make seed`: 15 belge yeniden üretildi, yüklendi, OCR'landı.

## 3. Eval (reseed sonrası, `make eval`, gemini-3.5-flash-lite, embedding kapalı, top_k=40)
`assets/phase_3_2c/eval_after_prose.{md,json}`; sayfa recall `assets/phase_3_2c/recall_after_prose.md` (24/24 ölçülebilir — yeni
`key_facts` 4 soruyu daha ölçülebilir yaptı).

| Kategori | Phase 4.1 | Phase 3.2b | **Phase 3.2c** | Eşik |
|---|---|---|---|---|
| authorization | %100 (3/3) | %100 (3/3) | **%100 (3/3)** | %100 ✅ |
| hallucination | %100 (4/4) | %100 (4/4) | **%100 (4/4)** | %100 ✅ |
| isolation | %50 (2/4) | %75 (3/4) | **%100 (4/4)** | %100 ✅ |
| document | %52,2 (12/23) | %69,6 (16/23) | **%87,0 (20/23)** | %80 ✅ |
| temporal | %33,3 (3/9) | %66,7 (6/9) | **%88,9 (8/9)** | %80 ✅ |

Yasak kaynak/proje karışması: **0/43** (üç koşuda da). `make eval` sıfır çıkış koduyla döndü. Hedeflenen 9 sorunun
7'si geçti (`ANK-DEV-001`, `ANK-FIN-001/003/004/007/012`, `ANK-ISO-003`); kalan 4 başarısızlık:

| Soru | Durum | Not |
|---|---|---|
| `ANK-EPC-004` | Cevap **doğru** ("…30.06.2023'ten 15.10.2023'e ertelenmiştir [K9]. …sebebi şebeke bağlantı çalışmaları") — yalnızca ikinci `required_source` (`EPC Contract`) gösterilmedi | Soru seti iki kaynak istiyor; sertifika tek başına tam cevabı içeriyor artık. Kaynak beklentisi gözden geçirilebilir |
| `IZM-DEV-007` | Cevap **doğru** (yeni cümleyi birebir aktardı, ÇED yazısını gösterdi) — soru seti `Önlisans Belgesi` + `Arazi Edinim Raporu`'nu istiyor | Aynı: içerik doğru, atıf beklentisi soru setinde |
| `IZM-DEV-005/006` | Kapsam dışı (negatif olgu ↔ NO OPINION; Naci ayrı değerlendirecek) | `IZM-DEV-005` bu koşuda doğru negatif cevabı verdi ama Önlisans'ı göstermedi |

## 4. Testler
- Backend 275 geçti, 6 atlandı (canlı LLM), 0 kırmızı; ocr-worker 9 (prose/manifest değişikliği sonrası tam koşu). `validate_documents` birim testleri (27) yeşil.
- `make lint` temiz.

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| Ayrı faz 3.2c (3.2b'nin devamı değil) | 3.2b kod/prompt, bu faz içerik; tag'ler ayrı izlenebilir | Ek rapor + tag |
| Prose elle düzenlendi, `make prose` yeniden koşulmadı | 7 cümle için LLM üretimi gereksiz ve deterministik değil; P1/P2 aynı sınırları uyguluyor | Prose hâlâ `AI_ASSUMPTION` |
| `financial_close_date` iki belgeye kondu (base "scheduled", AMD01 "achieved") | Base sözleşme kapanıştan önce imzalı — "gerçekleşti" anakronik olurdu; AMD01 geçmiş zamanla doğru | İki kaynak da "Facility Agreement" tipi, eval için ikisi de geçerli |
| G4 boşluk-duyarsız | Satır sonu kırılmasına bağlı yanlış negatif | Doğrulayıcı daha sağlam |

## 6. Riskler / notlar
- `IZM-DEV-005/006` (negatif olgu) bilinçli olarak dışarıda — Naci ayrı değerlendirecek: ya soru seti "bilgi yok"
  beklemeli ya da belgeler açıkça "henüz alınmamıştır" demeli.
- `ANK-EPC-004` ve `IZM-DEV-007`'nin `required_sources` listeleri artık içerikten daha katı (cevap doğru, ikinci atıf
  yok); Phase 5.1'in soru seti v2'sinde "en az biri" / "hepsi" ayrımı (`required_sources_all: bool`?) düşünülebilir —
  bu fazda soru seti **değiştirilmedi**.
- Prose yaması elle yazıldı. **Koruma kod seviyesinde (Naci'nin şartı, aynı gün eklendi):** 6 dosya top-level
  `hand_edited:` notu taşıyor; `generate_prose.py::is_hand_edited()` bu dosyaları `--force` verilse bile atlar
  (mevcut koruma yalnızca "dosya varsa atla" idi, `--force` ezerdi). `tests/test_generate_prose_guard.py` hem
  işaretin algılanmasını hem 6 dosyanın işaretli olduğunu doğrular; `validate_documents`/`generate_documents`
  ekstra anahtarı yok sayar (prose P1/P2 0 hata).

## 7. Kaynak kullanımı
- LLM: 43 çağrı (eval); reseed LLM'siz.
