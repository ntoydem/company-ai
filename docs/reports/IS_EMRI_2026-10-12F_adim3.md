# İş Emri 2026-10-12-F — Adım 3 Raporu (discovery eşleştirme kusuru — yalnız teşhis)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — teşhis + öneri, **UYGULAMA YAPILMADI**
(talimat gereği).

## 1. İlgili kod yolu

Naci'nin işaret ettiği `pending_documents.py`, yalnızca **henüz işlenmekte/okunamayan**
belgeleri eşleştiriyor (Tansu Not 7 §3, A/B/C/D durumları) — "discovery" kategorisinin
asıl mekanizması bu DEĞİL. Gerçek yol **ADR-027 "elimde şunlar var"** özelliği,
`backend/app/services/assist.py`:

- `available_from_metadata()` (satır 501) — soru terimlerini (≥4 harf) + glossary
  genişletmelerini (`search_glossary.py::metadata_terms`/`CONCEPT_GLOSSARY`) alıp
  `document_repo.search_metadata` (title/type/counterparty/tags ILIKE) ile arar.
  **Bir terim `common_threshold` (varsayılan `MAX_AVAILABLE`=5) kadar belgeden FAZLASINA
  isabet ediyorsa o terim TAMAMEN ATLANIR** ("too common to point anywhere").
- `is_existence_question()` (satır 543) — yalnız `var mı|yüklü mü|mevcut mu|nerede|neler|
  hangi dosya|hangisi|hangileri` kalıplarını tanır; bu DOĞRUYSA (veya hiç chunk
  bulunamadıysa) metadata eşleşmesi chunk-tabanlı listenin ÜZERİNE eklenir
  (`build_insufficient_assist`, satır 757); sıfır-chunk yolunda (`build_zero_chunk_assist`,
  satır 625) bu koşul YOK — her zaman `available_from_metadata` çağrılır.
- `EK_F_MODE=false` (canlı/eval `.env`'de, varsayılan) → `common_threshold`/`MAX_AVAILABLE`
  her zaman 5, proje ekseni filtrelemesi (ADR-030) devre dışı.

## 2. Kök neden #1 (DOĞRULANDI, veriyle) — `common_threshold=5` gerçek belge türleri için
çok katı

`seed_data/documents/manifest.json` + `seed_data/excel/manifest.json` üzerinde glossary
genişletmelerinin isabet sayısı ölçüldü:

| Probe (glossary genişlemesi) | İsabet | `common_threshold=5`'i aşıyor mu? |
|---|---|---|
| "Facility Agreement" (kredi/kredi sözleşmesi) | **9** | ✅ ATLANIR |
| "Agreement" (sözleşme) | **17** | ✅ ATLANIR |
| "Sözleşme" (sözleşme) | **6** | ✅ ATLANIR |
| "Report"/"Rapor" (rapor) | 15 / 12 | ✅ ATLANIR |
| "Financial Model" | 1 | hayır |
| "Budget" | 4 | hayır |
| "Pledge"/"Security"/"Teminat" | 2 | hayır |
| "Amendment" (ham terim, glossary değil) | 3 | hayır |

**Sorun:** kurumsal demo korpusunda "Facility Agreement" gibi bir belge TÜRÜ, tasarım
gereği ÇOK sayıda versiyon/proje olarak var (her projede DRAFT/V01/V02/EXECUTED/AMD01/
AMD02) — bu "çok yaygın" OLMASI onu "işaret etmiyor" yapmaz, tam tersi doğru cevaptır.
`common_threshold` eşiği, "bir proje kodu her etikette geçer" gibi GERÇEKTEN anlamsız
terimleri elemek için konmuştu (`assist.py` yorum satırı, 511-524) ama CONCEPT_GLOSSARY
gibi KÜRATE EDİLMİŞ (elle seçilmiş, güvenilir) genişlemelere de aynı sert eşik
uygulanıyor — bu ayrım yok.

**Etkilenen sorular (doğrudan):** GEN-DSC-002 ("Sözleşme var mı?" — "Agreement"/"Sözleşme"
atlanır, geriye kalan "Contract" 1 isabet EPC'ye işaret eder, Facility Agreement'a değil),
GEN-DSC-009 ("Kredi sözleşmesinin son hali" — "Facility Agreement" atlanır),
GEN-DSC-011 / GEN-DSC-011-K ("ankaranın ilk kredi ödemesi" — aynı "Facility Agreement"
probu atlanır; ayrıca bu ikisi zaten Financial Model workbook'una işaret ediyor, ki o da
ayrı bir eşleşme sorunu, bkz. §4).

## 3. Kök neden #2 (DOĞRULANDI, kodla) — `is_existence_question()` regex'i terim-tanımı
sorularını tanımıyor

GEN-DSC-013: *"amendment ne demek biliyor musun?"* — Ç-3 kararı (Tansu): beklenen davranış
tanım CÜMLESİ kurmamak, tadil belgelerini GÖSTERİP sormak. Ham terim "amendment" (soruda
İngilizce geçiyor) `available_from_metadata`'da 3 isabetle (atlanmaz) doğru belgeleri
bulur — ANCAK bu soru `_EXISTENCE_RE`'nin HİÇBİR kalıbına uymuyor ("ne demek", "biliyor
musun" yok listede). Eğer bu soru `build_insufficient_assist` yoluna girer ve FTS zaten
"amendment" kelimesini belge metninde bulup bir miktar chunk getirirse (`available`
listesi boş değilse), satır 757'deki `is_existence_question(question) or not available`
koşulu YANLIŞ olur ve metadata genişlemesi (doğru "Amendment" belgeleri) listeye hiç
EKLENMEZ — yalnızca FTS'in getirdiği (muhtemelen yanlış/ilgisiz) chunk'lar gösterilir.

**Etkilenen soru:** GEN-DSC-013 (doğrudan); muhtemelen benzer "ne demek/tanımı ne" kalıplı
başka terim sorularında da (bu iş emrinde başka örnek yok, ama kalıp genel).

## 4. Diğer sorular — kök neden BAŞKA (bu teşhisin kapsamı dışında, önceki
raporlarda zaten not edildi)

- **GEN-DSC-001 / GEN-DSC-001-M:** Adım 1'in Excel-crash düzeltmesinden ÖNCE bu sorular
  muhtemelen "data" olarak sınıflandırılıp `_load_workbooks` çağrısında çöküyordu (HTTP
  500, E Adım3'te doğrulandı) — Adım 1 sonrası durumları bu adımda YENİDEN TEST EDİLMEDİ
  (gereksiz LLM çağrısından kaçınıldı, iş emrinin "yalnız teşhis" kapsamı); crash düzeldiği
  için muhtemelen artık ilerliyor ama bu İDDİA DEĞİL, DOĞRULANMADI.
- **GEN-DSC-010:** metadata eşleşmesi kendisi sorunsuz göründü ("teminat"→Pledge/Security/
  Teminat/Guarantee, hepsi ≤5 isabet) — E-Adım2 §4'te zaten not edilen "gönüllü çapraz-proje
  referansı" (izolasyon) sorunuyla örtüşüyor, discovery-eşleştirme kusuru DEĞİL.
  GEN-DSC-007/GEN-DSC-007-K ("ÇED" probu 2 isabetle sorunsuz) için de aynı gözlem —
  olası neden FTS'in getirdiği ilgisiz chunk'ların `MAX_AVAILABLE=5` slotunu doldurması
  (DOĞRULANMADI, canlı yeniden test gerektirir).
- **GEN-DSC-008 / GEN-DSC-008-M:** notlar açıkça bunun bir **yetki sınırı testi**
  olduğunu söylüyor ("Budget vs Actual 2026" `enerji_grubu` departmanında — finans/
  finans_mudur görür mü?) — `allowed_document_ids` belgeyi hiç döndürmüyorsa
  `search_metadata` zaten 0 sonuç verir; bu bir EŞLEŞTİRME KUSURU değil, muhtemelen
  TASARLANMIŞ bir yetki davranışı (ya da `questions.json`'ın kendi beklentisi hatalı) —
  bu adımın "discovery eşleştirme" kapsamına girmiyor.

## 5. Düzeltme ÖNERİSİ (UYGULANMADI)

1. `available_from_metadata`'da `common_threshold`'ü ham soru teriminden gelen probe'lar
   için DEĞİL, `CONCEPT_GLOSSARY`/`metadata_terms`'den gelen (küratörlü) genişlemeler için
   kaldırmak veya çok yükseltmek (örn. corpus büyüklüğüne göre orantılı bir eşik, ya da
   küratörlü terimler hiç elenmesin — onları Naci zaten seçti, "anlamsız" olma riski düşük).
2. `_EXISTENCE_RE`'ye terim-tanımı kalıplarını eklemek ("ne demek", "biliyor musun",
   "tanımı ne", "anlamı ne") — Ç-3'ün "tanım cümlesi kurma, belge göster" kararıyla
   tutarlı hâle gelir.
3. (Daha büyük, bu iş emrinin kapsamı dışı) `build_insufficient_assist`'teki chunk-vouched
   doluluk kontrolü (`not available`) yerine, metadata eşleşmesini HER ZAMAN ekleyip
   `MAX_AVAILABLE` sınırını ikisi birleştikten SONRA uygulamak — şu an chunk'lar varsa
   metadata hiç denenmiyor, bu #3'ün kökü #1/#2'den ayrı, daha geniş bir mimari karar.

Devam ediliyor: **Adım 4** (solo `make test`).
