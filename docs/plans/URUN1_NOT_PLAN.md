# Tansu — Ürün 1 Notu (`NACI_NOTU_URUN1.md`, 08.10.2026) — Değerlendirme ve Uygulama Planı

**Tarih:** 08.10.2026 · **Durum:** plan; kod yazılmadı, canlı çağrı yapılmadı · **Kaynak:** `ftansu/AI-BalBal` dal `docs/naci-notlari` @ `57fb429`, `docs/NACI_NOTU_URUN1.md` (733 satır; PR #13, main'e birleşmemiş). `NACI_NOTU_URUN2.md` **okunmadı**, uygulanmaz (yazılı onay yok). · **Bizim taraf:** `main` @ `18b9dc6`, ADR-029, eval v6 (80 soru + 10 held-out), `ASSIST_MODE` canlıda kapalı.

Her "bizde ne var" satırı kod tabanından doğrulandı (dosya/satır verildi); tahmin yok. Büyüklük: S ≤ 1 gün, M 2–4 gün, L ≥ 1 hafta (tek geliştirici, mevcut hız).

---

## 1. Bölüm bölüm: bizde ne var, ne eksik, büyüklük, bağımlılık

### A — Kararlar ve iş sırası
| Madde | Bizde ne var | Eksik | Büyüklük | Bağımlılık |
|---|---|---|---|---|
| A.1–2 Ürün 1 hemen, Ürün 2 onay | ADR-022 ürün anahtarı (`company_settings.enabled_products`), P1 yolu | — | — | — |
| A.3 B-18 paralel | Üretim hattı var: ledger (`seed_data/master/*.yaml`) → `make prose` (LLM, 1 kez) → `generate_documents` (WeasyPrint, 3 şablon ailesi: agreement 17 / letter 19 / report 34) → `generate_excel` (4 workbook) → `make seed`; 70 PDF (61 dijital, 9 taranmış) + 4 Excel | Yeni şirket grubu, yeni belge türleri (§4) | L | §4 |
| A.4 Kurgu şirketler = kanvas | `Project` modeli (`name, code, stage: development/construction/operation`), `project_department`, 2 proje seed'li (`demo_projects_seed.py`); ledger şeması `Literal["Ankara RES"]`/`Literal["İzmir RES"]` (`ledger_schema.py:316,376,508`); eval `_PROJECT_NAME_BY_CODE` (`eval_lib.py:33`); prompt örnekleri "Ankara RES/İzmir RES" (`answer_prompt.py:41-42,71`, `router.py:65`) | Holding/SPV kavramı yok (`company_id` yok); proje adları 22 kod dosyasında sabit (`grep` listesi §4.4) | M (kod) + L (veri) | §4 |
| A.5 Her departmanda her SPV klasörü | B-26 klasör ağacı + `folder_grants` + miras (ADR-023); seed yalnızca departman kök klasörlerini açar (`demo_folders_seed.py:1-3`: "gerçek ağaç B-18'in işi"); yüklemede `folder_id` yazma yetkisi kontrolü (`documents.py` upload); Balbal klasör önerisi **yok** (ADR-025 "not here") | SPV alt klasörleri + tür klasörleri seed'i; yetki **şablonu** (SPV eklenince kopyalama) yok; yüklemede SPV tespiti/klasör önerisi yok | M (seed) + M (öneri) | A.4, C.3 |
| A.6 Öncelik B, C.4 | — | — | — | §3 |
| A.7 Belgeden öğrenme | Belgeler ledger değerlerini `[[token]]`'la içeriyor (`facts.py`); hiçbir parametre koda yazılı değil | Yeni ledger alanları (faiz, marj, teminat, imza yetkisi…) | §4 | §4 |

### B — "Balbal fazla tutuk" (LLM'siz teşhis, canlı DB, 08.10.2026)
Tansu'nun dört sorusunu gerçek kapı + gerçek FTS ile yeniden ürettim (LLM çağrısı yok):

| Soru (kullanıcı) | Retrieval ne getirdi | Asıl neden |
|---|---|---|
| "Ankara'nın finansal modeli var mı?" (finans) | 41 parça — Drawdown Notice, Share Pledge, Covenant Report… **"Financial Model 2026" yok** | (1) Finansal model bir **xlsx**; belge hattı yalnızca `document_chunks` arar, workbook'ların parçası yok (ADR-013/SPEC_04: Excel RAG belgesi değil); (2) başlık İngilizce, `search_metadata("finansal model")` **boş** — glossary başlık aramasına uygulanmıyor ve "finansal model" girişi yok (`search_glossary.py` anahtarları: finansman, kredi, … "finansal" **yok**); (3) model ilgisiz 41 parçayla "yetmez" dedi → `insufficient_data` → arayüz "Yeterli veri bulunmamaktadır … belge yükleyebilirsiniz" (`strings.ts:109 uploadLink`). **`ASSIST_MODE` kapalıydı**: açık olsa `build_insufficient_assist` "elimde şunlar var"ı listelerdi ama yine workbook'u değil (metadata eşleşmesi yok) |
| "ankaranın ilk kredi ödemesi ne zaman ne kadar?" (yonetim) | 39 parça — Facility Agreement V01/Draft/… | Geri ödeme planı ledger'da var (`ankara_res.yaml:103 repayment_schedule`, ilk taksit 30.06.2024 / 1.000.000 EUR) ama **yalnızca** "Financial Model 2026" `Debt` sayfasında (`generate_excel.py:169`); hiçbir PDF ilk taksiti yazmıyor; Excel motorunda "ilk taksit" fonksiyonu yok (`functions.py`: dscr, outstanding_debt, budget_variance, production, capacity_factor) → plan `none` → belge hattına düşüş → cevapsız. **Cevap Tansu'ya: bulma hatası değil, veri hattı eksiği** (belge yok + fonksiyon yok) |
| "peki amendment var mı hiç?" (yonetim) | 11 parça — **Amendment 01 ve 02 bulundu** | Varlık sorusu ("var mı") içerik-QA ile cevaplanıyor; model 2 tadil parçasını "yetmez" saydı. Bağlam ("Ankara kredisi") taşınmadı: çok turlu hafıza **yok** (T9 kararı, `AskRequest = question + department`) |
| "amendment ne demek biliyor musun?" (yonetim) | 11 parça — Amendment 01/02 | Kural 1 "genel bilginle boşluk doldurma" + 30.09 `GENERAL_QUERY` kaldırma kararı (`docs/notes` §6.6): tanım yalnızca belgeden. Belgeler terimi tanımlamıyor → sabit cümle |

| Beklenen davranış (B.1–B.6) | Bizde ne var | Eksik | Büyüklük |
|---|---|---|---|
| B.1 Kavramsal genişletme, sözlük parametre tablosu | `search_glossary.py` (46 anahtar, kodda, FTS sorgusuna uygulanıyor, ADR-020); `tag_catalog`/`document_type_guide` admin tabloları örnek desen | "finansal model → {nakit akış, ödeme planı, DSCR, fizibilite, bütçe}" gibi **kavram→belge türü** sözlüğü yok; sözlük admin tablosunda değil; `search_metadata` genişletme yapmıyor; workbook'lar belge hattının adayı değil | M |
| B.2 Bulduğunu söyle (linkli liste + netleştirme) | ADR-027 assist: `available` (metadata + parça), `clarify`/`term_mismatch`, `SORU:` satırı — **bayrak arkasında, canlıda kapalı**; arayüz PR'ı yok (NOT: `assist.question` ana metin olsun) | Bayrağın açılması + arayüz; workbook'ların "elimde şunlar var"a girmesi | S (bayrak) + M (arayüz) |
| B.3 Bulamadıysa bile soru | `build_zero_chunk_assist` (LLM'siz şablon) ✓ | "belge yükleyebilirsiniz" sırası arayüzde (`uploadLink`) | S (arayüz) |
| B.4 Etiket semantiği | `missing_data` (0 parça) / `insufficient_data` (parça var, model yetmez dedi) ayrımı var (`ask_router.py`); V3 kodla tespit (`ambiguity-v3-unmerged`) birleşmedi | "bulundu ama eşleşmeden emin değil → etiket değil soru": insufficient yolunda model `SORU:` yazarsa clarify oluyor (ADR-027) — ölçümde 10/15 (kural 12, dalda) | ölçüm sorunu, §3 |
| B.5 Eminlik eşiği düşsün | G1–G3 kapıları (`eval_lib.safety_checks`) uydurma/kaynaksız/yetkisiz öneriyi ölçüyor; "göster + sor" ADR-027'de kaynaklı | Prompt kural 2 "yetmiyorsa yalnızca sabit cümle" — "göster ve sor" kural 11 ile var; eşik = modelin kararı | §2 Ç-1 |
| B.6 Örnek soru çipleri ve "Yalnızca … arar" kalksın | `strings.ts:42 scopeNote`, `:47 exampleQuestions`, `:54 exampleQuestionsP2`; `AskPanel.tsx:33-34`, `BalbalChat.tsx:130` | Arayüz PR'ı (Tansu'nun reposu) | S |

### C.1 — Hesaplar ve ekip sohbeti
| | Bizde ne var | Eksik | Büyüklük |
|---|---|---|---|
| 36 kişilik hesap | `User(username, display_name, role, title, primary_department_id, departments[])`, roller admin/management/department_manager/employee; 5 demo hesap (`demo_users_seed.py`: yonetim, finans, hukuk, enerji, finans_mudur) + tek `DEMO_USER_PASSWORD`; departman ağacı 12 slug (`demo_departments_seed.py`), `Saha Operasyon` ve `Yönetim` departmanı **yok** | 36 kullanıcı seed'i (`ad.soyad`), e-posta alanı yok (`User`'da e-posta yok), **yönetici** alanı yok (İK şemasından türetilecek: `manager_user_id` ya da departman müdürü rolü), yeni departmanlar (Yönetim, Saha Operasyon + 4 santral birimi, EPC alt birim), her departmana `department_manager` (B-28 onayı için zorunlu — `approver_not_configured`), eski 5 hesabın kaldırılması (eval `DemoUser` Literal'i ve 80 sorunun `ask_as_user`'ı buna bağlı) | M |
| Ekip sohbeti (Ü-7.1) | **Backend'de yok** (model/uç yok; `grep chat backend/app/models` boş). Frontend'de `components/team/TeamChat.tsx` var, `api/proposed.ts` `/api/chats`, `/api/chats/{id}/messages` **önerilen** uçları (henüz yok) kullanıyor; Layout: "Ekip sohbeti Ürün 1'dir, her pakette açık". NOT §2 B-06b = Balbal'ın gruba katılması (Ürün 2 sonrası), kişiler arası sohbet ayrı | Tasarım + 2 tablo + 4 uç (§5) | M |

### C.2 — İş arkadaşı gibi davranmıyor
| Beklenen | Bizde | Eksik | Büyüklük |
|---|---|---|---|
| Terim soruları (anlama kontrolü) | `GENERAL_QUERY` 30.09'da kaldırıldı; tanım soruları DOCUMENT_QUERY (router satır 46) ve yalnızca belgeden | "amendment'ı tadil olarak anlıyorum" cümlesi = kaynaksız tanım → §2 Ç-3 kararı gerekir | S (prompt) — karar sonrası |
| Terimden belgeye köprü | Glossary FTS'te (amendment ↔ tadil zaten var: `"tadil": ("amendment", "amended")`) ✓ — 11 parça geldi | Varlık sorusunda ("var mı") **başlık listesi** cevabı: ADR-027 `available` (bayrak) | S (bayrak) |
| Sohbet bağlamı | **Yok** (T9: "çok turlu hafıza yok ve olmamalı"; CLAUDE.md: soru-cevap bilgi tabanına girmez) | Önceki tur bağlamı → §2 Ç-2 kararı | M (karar sonrası; yalnızca istemci tarafı bağlam taşıma S) |
| Netleştirme ve "nerede aradım" | ADR-027 `clarify` + `available`; V3 tespit birleşmedi | "Ankara RES kredi klasöründe ödeme planı bulamadım" → klasör adı taşıyan şablon yok | S |
| Güvenlik çizgisi | ADR-014/021, G1–G3 ✓ | — | — |

### C.3 — Yüklemede alanları önce kişi dolduruyor
| Bizde | Eksik | Büyüklük |
|---|---|---|
| `POST /upload` zorunlu form: `title, document_type, document_date, counterparty` (`documents.py:271-290`); sonra `suggest-metadata` (LLM, alanlar: department, subdepartment, project_code, document_type, counterparty, document_date, status, confidentiality, **tags** — `metadata_suggestion.py:48-57`), `confidence < 0.8` → "Onaylıyorum" zorunlu (`document_review.py:96`, `low_confidence_not_confirmed`), olay günlüğü ✓ | **Sıra ters:** önce boş form. Gerekli: dosya-önce yükleme (başlık/tür/tarih/karşı taraf opsiyonel ya da OCR sonrası öneri), öneri **başlık + klasör/SPV** alanlarını da kapsamalı (bugün başlık ve klasör önerilmiyor; folder suggestion ADR-025 "not here"); etiketlerin "Mevcut: —" görünmesi öneri uygulanmadan önceki normal durum — arayüz öneriyi ön-doldurmuyor | M (backend: opsiyonel alanlar + başlık/klasör önerisi) + M (arayüz) |

### C.4 — Etiketler (ACİL)
| Bizde | Eksik | Büyüklük |
|---|---|---|
| `tag_catalog(slug, label, kind identity/change, is_active)`, admin CRUD `/api/admin/tags`, retire = `is_active=false`; canlı katalog (DB, 08.10): identity **AMD01, AMD02, ANK_RES, COMPANY, DRAFT, EXECUTED, IZM_RES, onay akışı, test, V01, V02** (+ `pf-kredi` pasif), change 9 Türkçe etiket (faiz-değişikliği, teminat-yapısı-değişikliği…) ✓ — Tansu'nun gördüğü liste bu. Kaynak: generator `tags = [project_code or "COMPANY", version]` (`generate_documents.py:307`) → migration 0014 "kullanımda olan etiketler identity" | Katalog temizliği (11 identity etiketini retire), Türkçe `#proje #konu #tür` kimlik etiketleri (`karatepe-res`, `pf-kredi`, `tadil`…), generator'ın etiket kaynağını ledger'a taşımak (`documents[].tags`), demo belgelerin yeniden etiketlenmesi (seed `extra_fields`'ta olduğu gibi "yalnızca boşsa" deseni), sürüm/imza bilgisinin etiketten çıkması (zaten `version`/`status` alanları var) | S (katalog) + S (generator) + S (reseed) |

### C.5 — Gerçekçi belgeler / kişi adları
`name_whitelist` (company.yaml) + `validate_documents` G2 (whitelist dışı isim = hata) ✓ → 36 kişi whitelist'e girer. S (D ile birlikte).

### C.6 — Önlisans süreci ve geliştirme belge seti
| Bizde | Eksik | Büyüklük |
|---|---|---|
| `izmir_res.yaml development.pending_steps` (2 adım, serbest metin), `ced_status`; `Project.stage`; belge türü/tarih alanları; `expiration_date` + `temporal.expiration_note` (ADR-026) | **Süreç modeli yok**: adım/önkoşul ağı (24 düğüm), adım durumunun belgeden türetilmesi, son tarih uyarıları (önlisans+90/180 gün), "Gerekmez" (GES), olumsuz sonucun bağlı adımları bloke etmesi — API `GET /api/projects/{id}/steps`; **46 belge** (Kızılova 20, Akyar 9, Demirci 17) yeni şablon aileleri gerektiriyor (kurum kararı, tapu, tutanak/fotoğraf, ölçüm Excel eki) | L (model + API) + L (belgeler); NOT §2 B-20/7 "Enerji izin/ruhsat adımları (Ürün 3 veri modeli)" olarak kaydedilmişti → artık Ürün 1'e çekiliyor (§2 Ç-9) |
| C.6.3 tutarsızlıklar | — | Tansu'nun kendisi 4 soru listeledi; belge üretimi bunlara bağlı | — |

### D — Demo veri kütüphanesi
Ayrıntı §4. Özet: ledger 3 dosyadan **8 şirket** (+ holding) dosyasına; klasör ağacı seed'i; **~340 belge** (İK kişi dosyaları hariç) / **~560** (15 ofis personeli × 12 dosya ile); yeni biçimler: `.eml`, e-Fatura XML, `.docx` şablon, MT940, fotoğraf (jpg ✓), Excel (openpyxl ✓). **V0 kapsam dışı olanlar:** Word yükleme (CLAUDE.md, NOT §3.6 B-15), e-posta ingest (B-24) → §2 Ç-7.

### E — 08.10 eklemeleri
Hepsi ledger değeri (Yeşilova 2021-YS parametreleri, 2022-BZ faiz tarihi, KDV takvimi, imza limitleri 500k/A+B, avans AV-26-007 + 6 masraf belgesi, 8 banka ekstresi). Bizde: ledger `Fact{value, tag}` deseni ✓, para biçimleme (`_format_money`, EUR/USD/TRY) ✓. Eksik: faiz hesabı satırları (18.912 vs 18.240 **kasıtlı fark**) → Ç-7 "Çelişkili Veri" ölçümüne girer; MT940 biçimi desteklenmiyor (yalnızca pdf/png/jpg/xlsx/xlsm/csv → Excel olarak üretilir). M (D içinde).

### F — Anayasa uyarıları / beklenen çıktılar
F.1 dış bağlantı yok ✓ (zaten yok); Ç-7 etiketleri ✓; gerçek veri yok ✓ (`validate_ledger` isim whitelist, P1/P2). F.2 çıktı sırası §3 ile uyumlu. F.3 açık sorular Tansu'da.

---

## 2. Çelişkiler ve çakışmalar — her biri için tek cümlelik A/B sorusu

**Notun kendi içinde (Tansu'ya):**

| # | Çelişki | Soru |
|---|---|---|
| İ-1 | Kızılova: §C.6.2 **42 MW, önlisans aşaması** (imar/ruhsat yok) ↔ §D.1.1 **48 MW, "İnşaat (şantiye)"**, EPC S-26-001 imzalı 15.09.2026, 30 mn USD yatırım kredisi kullandırımda (Tansu §C.6.3/3'te kendisi de soruyor) | Kızılova önlisans aşamasında bir geliştirme projesi mi (A), yoksa ruhsatlı ve inşaatta mı (B)? |
| İ-2 | Akyar: §C.6.2 önlisans 03.03.2026 → bitiş 03.03.2028, 60 MW ↔ §D.1.1 bitiş **15.01.2027**, 30 MWp | Akyar için C.6.2 tarihleri/kapasitesi (A) mı D.1.1 (B) mi esas? |
| İ-3 | Demirci: §C.6.2 önlisans 10.10.2024 → 36 ay → 10.10.2027, 80 MW ↔ §D.1.1 bitiş **03.03.2028**, 36 MW | Demirci için C.6.2 (A) mı D.1.1 (B) mi? (Akyar/Demirci bitiş tarihleri D.1.1'de yer değiştirmiş görünüyor) |
| İ-4 | Personel: §C.1 (36 kişi, adlar + unvanlar) ↔ §D.1.2 ("saha adlarını sen üret"; Hakan Tunç "Şantiye Şefi" vs "EPC Proje Mühendisi", Deniz Kaya "Müdürü" vs "Sorumlusu", Pınar Güler "Piyasa Analisti" vs "Üretim/Piyasa Uzmanı", Murat Kılınç "Sorumlusu" vs "Müdürü", Onur Yıldız) | Tek kaynak §C.1 tablosu mu (A), §D.1.2 mi (B)? |
| İ-5 | İmza limitleri: §D.4.1 (≤250k tek B, ≤2 mn A+B) ↔ §E.4 (500k tek A, üstü A+B; "eski geçersiz") | §E.4 esas, §D.4.1 düzeltilecek — doğru mu (A) yoksa iki kademe de kalıyor mu (B)? |
| İ-6 | Demo "bugün": §D.5/6 **06.10.2026** ↔ bizde `DEMO_TODAY=2026-09-15` (ADR-026; ledger "as of demo today" olguları, Excel `Ledger_DemoToday`) | Demo bugün 06.10.2026'ya alınsın (A — ledger "as-of" değerleri yeniden hesaplanır) mı, 15.09.2026 kalsın (B) mı? |
| İ-7 | Sözlük: §B.1 "parametre tablosunda tutulur (P-8), ürün sahibi genişletir" ↔ bugün `search_glossary.py` kodda, `make lint`'te test ("belgeden terim, sorudan değil" ilkesi) | Sözlük admin tablosuna taşınsın ve arayüzden genişletilsin (A) mı, kodda kalıp ürün sahibi PR ile eklesin (B) mi? |
| İ-8 | §B.2 "linkli liste + soru" ↔ §C.2 "Netleştirme ve öneri" ↔ Tansu kararı (a) (07.10: belirsizde **sadece** netleştirme sor, kaynakları sıralama) | Belirsiz soruda: sadece tek netleştirme sorusu (A) mı, "elimde şunlar var" listesi + soru (B — ADR-027 bugünkü şekli) mi? |

**Bizim kararlarımızla / anayasayla çakışmalar (Tansu + Naci):**

| # | Çakışma | Soru |
|---|---|---|
| Ç-1 | §B.5 "eminlik eşiği düşsün" ↔ G1–G3 (uydurma/kaynaksız/yetkisiz öneri %100 kapı) ve ADR-014 sabit hüküm: eşik "cevap üret" yönünde düşerse G2 (kaynaksız cevap) riski; "göster + sor" yönünde düşerse risk yok | Eşik yalnızca "göster ve sor" yönünde düşsün, cevap üretme eşiği aynı kalsın (A) mı; cevap eşiği de gevşesin ve G1–G3 yeniden ölçülsün (B) mi? |
| Ç-2 | §C.2 "sohbet bağlamı taşınmalı" ↔ T9 (çok turlu hafıza yok; soru-cevap bilgi tabanına girmez, CLAUDE.md) ↔ Ü-3 "tek pencerede çok proje" | Bağlam yalnızca **istemcide** taşınıp isteğe bir önceki soru metni eklensin (A — sunucu hafızası yok, audit her isteği bağımsız yazar) mı; sunucu tarafı oturum hafızası (B — T9 değişir, ADR gerekir) mi? |
| Ç-3 | §C.2 terim tanımı ("amendment'ı tadil olarak anlıyorum") ↔ Ç-6 "kaynakta olmayan bilgi" + 30.09 `GENERAL_QUERY` kaldırma; Tansu notu bunu "Açık soru (Proje Yetkilileri)" diye bırakmış | Sözlük karşılığını söyleyip belgede aramak serbest (A — "sözlük eşlemesi" kaynak sayılır, tanım cümlesi kurulmaz) mı; hiç söylenmesin (B — bugünkü) mi? |
| Ç-4 | §B.2 "belgeyi göstermek Tanıma'dır, yorum değil" ↔ Ü-3 "her kaynağın söylediğini ayrı ayrı aktar" ↔ Tansu (a) "sıralama, sor" | İ-8 ile aynı soru |
| Ç-5 | §C.1 ekip sohbeti (Ü-7.1, Ürün 1) ↔ NOT §2 B-06b "Ürün 2 sonrası" (o madde Balbal'ın gruba katılmasıydı) ↔ frontend `TeamChat` hazır, backend yok | Kişiler arası sohbet backend'i Ürün 1'de şimdi yapılsın (A) mı, Ürün 2 onayıyla birlikte (B) mi? |
| Ç-6 | §C.6 önlisans süreç modeli ↔ NOT §2 B-20/7 "Enerji izin/ruhsat adımları = **Ürün 3** veri modeli" | Süreç ağı + durum türetme Ürün 1'de backend'e girsin (A — Tansu notu böyle diyor) mı, Ürün 2/3 ile (B) mi? |
| Ç-7 | §D.3.6 `.eml` ingest, §D.4.1 `.docx` şablon/ödeme talimatı, §E.6 MT940 ↔ CLAUDE.md V0 kapsam dışı (Word/e-posta ingest), NOT §3.6 (B-15/B-24 benimsenmedi), yükleme beyaz listesi pdf/png/jpg/xlsx/xlsm/csv | E-posta ve Word demo setine **dosya olarak** girip (`.eml`/`.docx` → PDF'e dönüştürülmüş kopya + orijinal ek) yüklensin (A) mı, yükleme hattı `.eml/.docx/.txt` kabul etsin (B — V0 kararı değişir) mi? |
| Ç-8 | §C.6 "güncel mevzuatı webden kontrol et" + gerçek kurum adları ↔ Ç-12/P-9 kurgu + CLAUDE.md "ledger'da olmayan rakamı uydurma" | Mevzuat tarih/süre/bedelleri (90/180 gün, teminat) ledger'a **Tansu'nun verdiği** değerlerle yazılsın (A) mı; biz webden araştırıp öneri listesi sunalım, Tansu onaylasın (B) mi? |
| Ç-9 | §A.4 "Ankara/İzmir aşaması geçildi" ↔ eval v6 (80 soru + 10 held-out) ve R0/R1/R2 ölçümleri **tamamen** Ankara/İzmir'e bağlı | Eski set arşivlenip yeni 80+ soru yazılsın (A) mı; Ankara→Karatepe / İzmir→Kızılova **yeniden adlandırma** ile mevcut 70 belge + 80 soru korunup üzerine eklensin (B — §4.3 maliyet) mi? |
| Ç-10 | §B.6 "öneri çipi/örnek soru olmaz" ↔ frontend `exampleQuestions`/`exampleQuestionsP2` + bizim arayüz notu "`assist.question` ana metin" | Çipler kalkar, netleştirme sorusu metin olarak kalır (A) — onay? |

---

## 3. Önerilen uygulama sırası (B ve C.4 önce)

| Adım | İçerik | Bitiş kriteri (ölçülebilir) | 80 soruluk eval'e etkisi | Durma noktası |
|---|---|---|---|---|
| **1. B-ölçüm** (S, 0 kod) | `ASSIST_MODE=true` ile Tansu'nun 4 sorusu + "X var mı" türü 10 doğal dil sorusu (taslak §3.1) ×1, bayrak kapalıyla karşılaştır; LLM ≤ 28 çağrı | Tablo: her soru için kapalı/açık metin; `available` listesi doğru belgeleri gösteriyor mu | yok (ölçüm) | G1–G3 ihlali → dur |
| **2. B-kavram sözlüğü + workbook adayları** (M) | (a) `search_glossary`'ye kavram girişleri ("finansal model", "ödeme planı", "nakit akış", "bütçe"…) — FTS + **metadata** aramasına uygulanır; (b) ADR-027 `available_from_metadata` **xlsx/csv belgeleri de** kapsar (zaten `allowed` içinde; chunk şartı yok); (c) varlık sorusu ("var mı / hangi belgeler") için kodla tespit: parça 0 ya da model cevapsız → `available` zorunlu; (d) İ-7 kararına göre sözlük tablosu | 10 doğal dil sorusunda ≥ 9/10 "liste + soru" (Tansu kabul testi), "yeterli veri yok" tek başına 0 | `term_mismatch`/`clarify` beklentileri değişmez; `assist_check` eklenir; **G1–G3 %100** | ≥ 2 yeni yanlış pozitif (cevabı belgede olan soruda liste yerine ret) → dur |
| **3. B-prompt/arayüz** (S) | Kural 11 açıklaması ("bulduğunu söyle, etiket değil soru"), kural 2'ye dokunulmaz (Ç-1 A ise); arayüz: `assist.question` ana metin, `available` linkli, `uploadLink` sona, çipler kalkar (Ç-10) | Tansu kabul testi 9/10; tek prompt revizyonu hakkı | R1 (14 ×3) + 4 negatif kontrol yeniden | clarify oranı eşik altı → dur, revizyon hakkı yoksa raporla |
| **4. C.4 etiketler** (S+S+S) | Katalog temizliği (11 identity retire), Türkçe kimlik etiketleri kataloğa, generator etiket kaynağı ledger, reseed (yalnızca `tags` boş/eski olanlar) | Katalogda İngilizce kod 0; her demo belgede ≥ 1 proje + 1 tür etiketi; `make validate-documents` 0 hata | `search_metadata` tag araması değişir → `/api/search` testleri; `GEN-TRM` beklentileri etkilenmez; **retrieval-only 44/44 korunur** | — |
| **5. C.3 yükleme sırası** (M+M) | Form alanları opsiyonel → yükleme → OCR → öneri (başlık + klasör/SPV + tür + tarih + taraf + etiket) → ön-dolu form → %80 altı "Onaylıyorum" | T-upload: başlık/tür/taraf boş yüklenen PDF'te öneri ≥ 6/8 alan dolu; SPV belirsizse öneri `null` + soru | yok | SPV yanlış atama (G3 benzeri) 1 → dur |
| **6. C.1 hesaplar** (M) | 36 kullanıcı + yeni departmanlar + müdürler + `manager_user_id`; eski 5 hesap pasif; `DemoUser` Literal → eval uyarlaması | Her kullanıcı giriş yapar, kendi departman sayfasını görür; `approver_not_configured` 0 | **80 sorunun `ask_as_user`'ı** yeni adlara eşlenir (yonetim→levent.aksoy, finans→oguz.tekin, enerji→cem.aktas…) — kabul kriterleri aynı | — |
| **7. C.2 kalanlar** (karar sonrası) | Ç-2 (bağlam, istemci A), Ç-3 (terim) | — | yeni `term`/`context` kategorisi | — |
| **8. D/E veri kütüphanesi** (L, §4) | Ç-9 kararına göre; paralel koşabilir ama 1–6 önce | §4.5 | §4.4 | — |
| **9. C.6 süreç modeli** (L, Ç-6 A ise) | tablo + API + 46 belge | "Kızılova'da lisans başvurusunu ne engelliyor?" kaynaklı tespit | yeni kategori | — |
| **10. C.1 ekip sohbeti** (M, Ç-5 A ise) | §5 | §5 | yok | yetki testi düşerse dur |

### 3.1 Adım 1 için 10 doğal dil sorusu (taslak, onay bekler; canlı ölçüm yok)
"Ankara'nın finansal modeli var mı?" (finans) · "Sözleşme var mı?" (finans) · "Sigorta ne zaman bitiyor?" (enerji) · "Lisans durumu ne?" (enerji) · "Amendment var mı?" (yonetim) · "Ödeme planı yüklü mü?" (finans) · "ÇED raporu nerede?" (enerji) · "Bütçe dosyası var mı?" (finans) · "Kredi sözleşmesinin son hali hangisi?" (finans) · "Teminat belgeleri neler?" (hukuk). Beklenen: her birinde **liste + soru**, "yeterli veri yok" tek başına 0.

---

## 4. Veri kütüphanesi (D/E) — maliyet tahmini

### 4.1 Belge sayısı (nottan sayıldı)
| Departman | Belge (yaklaşık) | Not |
|---|---|---|
| Proje Finans (§D.3) | ~80 | 5 kredi sözleşmesi (Karatepe 3), 6 ödeme planı Excel, 5 hesap listesi, ~16 teminat belgesi, ~19 poliçe, ~10 banka raporlama/e-posta, ~15 diğer (nakit akış/DSCR Excel, yatırımcı raporu, kullandırım), holding 3 |
| Hukuk (§D.4.2) | ~50 | 5 dava × ~4, ~22 sözleşme, 4 KEP yazısı, 3 ihtarname/noter |
| Enerji (§C.6 + §D.4.3) | ~105 | geliştirme 46 (Kızılova 20, Akyar 9, Demirci 17), işletme tarihsel ~20, O&M ~18, EPC ~9, üretim/piyasa ~10 |
| Mali İşler (§D.4.1) | ~70 | 8 şirket × 5 sicil/vergi/imza, hesap listeleri, 4 ödeme talimatı şablonu (.docx), 8 muavin Excel, 5 e-fatura (+XML), 4 beyanname, bordro özeti |
| İdari (§D.4.5) | ~20 | zimmet, araç, 2 kira, 3 PO dosyası × ~5 |
| E eklemeleri | ~20 | Yeşilova 4, 6 masraf belgesi, 8 ekstre, imza sirküleri |
| **Ara toplam (İK kişi dosyaları hariç)** | **~345** | bugün 74 |
| İK (§D.4.4) | 15 ofis × 12 = 180 (+ izin/yönetmelik ~40) **ya da** 36 × 12 = 432 | kişi dosyaları form niteliğinde → LLM'siz şablonla üretilebilir |
| **Toplam** | **~560** (ofis) / **~800** (herkes) | |

### 4.2 LLM çağrısı ve kota (Gemini ücretsiz: günde 500, dakikada 5 — Naci)
- `make prose`: **1 çağrı / anlatı belgesi**, en fazla 3 deneme (`generate_prose.py:32 MAX_ATTEMPTS`), gözlenen ret oranı düşük → ~1,2 çağrı/belge. Anlatı belgesi ≈ 345 − Excel (~35) − eml/XML/fotoğraf (~20) ≈ **290 → ~350 çağrı**. İK kişi dosyaları ve formlar (tutanak, dekont, ekstre, sirküler) **LLM'siz şablon** → 0.
- Günlük 500 ile prose **1 gün**; 5/dk sınırıyla ~1,5–2 saat çalışma (26 sn aralık). Parti parti (departman başına) koşulur, her parti `validate_documents` P1/P2.
- Ek LLM: yükleme sırasında Balbal etiket/klasör önerisi demo'da **talep üzerine** (seed çağırmaz) → 0; eval yeniden yazımı ölçümü: ~100 soru × (R0 kapalı + R1 açık) ≈ 200–300 çağrı → **ayrı 1 gün**.
- **Toplam ~2 kota günü** + geliştirme süresi (şablon aileleri, generator, ledger, validator): **L, 2–3 hafta** tek geliştirici — Tansu'nun "frontend ile aynı anda biter" beklentisi takvimle doğrulanmalı.

### 4.3 Maliyeti düşüren bulgu: prose'da proje adı yok
70 prose dosyasında **"Ankara"/"İzmir"/"EUR" literal'i 0**; adlar `[[project_name]]` (90), `[[spv_name]]` (114), `[[counterparty]]` (116) token'larıyla geliyor. Ledger'da "Ankara RES" → "Karatepe RES Enerji Üretim A.Ş." (60 MW, Garanti, DSCR 1,25→1,20 2. tadil — Tansu'nun Karatepe tanımıyla **neredeyse bire bir**) ve "İzmir RES" → "Kızılova RES" (ÇED devam, önlisans) yeniden adlandırması **0 LLM çağrısıyla** 70 belgeyi yeniden üretir; eval'in 80 sorusu ad/değer eşlemesiyle büyük ölçüde korunur. Değişmesi gerekenler: ledger adları/para birimi (EUR→USD), `document_specs/*.py` başlık/alt başlıkları (70 atıf), `ledger_schema` Literal'leri, `_PROJECT_CODE`/`PROJECT_PREFIX`, eval `_PROJECT_NAME_BY_CODE`, prompt örnekleri (`answer_prompt.py:41-42,71`, `router.py:65` — **prompt değişir → R1 yeniden**), `static/ask.html`, frontend `exampleQuestions`. → Ç-9 sorusu.

### 4.4 Eval'in yeniden yazılması gerekenler
- `questions.json` 80 + 10 held-out: `expected_project` Literal, `ask_as_user` (5 eski hesap → yeni kişiler), `required_sources` başlıkları, ledger yolları (`ankara_res.…` → yeni dosya anahtarları); Ç-9 B ile çoğu mekanik eşleme, A ile sıfırdan.
- `validate_ledger.py`: `LEDGER_FILES`, `PROJECT_PREFIX`, `QUOTAS` (İzmir 12/Ankara 35), `CATEGORY_QUOTAS`, G1 taranmış hedef, D2 önek kuralı, F-kuralları (facility chain, covenant tests) → SPV başına genelleştirme.
- `eval_lib.py`: `_PROJECT_NAME_BY_CODE`, `_PROJECT_CODE`, `format_ledger_leaf` türleri (yeni alanlar: IBAN, poliçe no…), `fact_tokens` (TL/USD biçimleri).
- Yeni kategoriler (Tansu §D.5 tuzakları): `conflict` (Karatepe 14,0/13,6; Yeşilova 2 sürüm; Enercon mükerrer), `missing_known` (Annex F teminat mektubu, askerlik belgesi, PO'suz fatura), `spv_isolation` (SPV klasör yetkisi), `versions` (3 halkalı zincir) — eşikler: G1–G3 %100 kalır; `conflict` için "Çelişkili Veri" etiketi/metni bugün **yok** (ADR-014 sabit metin listesine girer, rule 9 benzeri kural + eval kontrolü).
- `run_eval` kullanıcı listesi `DemoUser` Literal'i.

### 4.5 Eski Ankara/İzmir verisi — silme yok, öneri
- **Öneri (Ç-9 B):** ledger'ı yeniden adlandırarak **dönüştür** (Ankara RES → Karatepe RES, İzmir RES → Kızılova RES); 70 belge + 4 workbook + 80 soru yeni adlarla yaşar, kütüphane bunun **üzerine** büyür (6 SPV daha). Eski adlar git geçmişinde (`demo-ankara-izmir` etiketi, bu plan öncesi `main` @ `18b9dc6`).
- **Alternatif (Ç-9 A):** `seed_data/legacy/` altında eski ledger+prose+specs saklanır, `make seed LIBRARY=legacy` anahtarı; eval v6 orada regresyon olarak kalır; yeni set sıfırdan — ~2× LLM maliyeti ve iki paralel set bakım yükü.
- Canlı dev DB: `make backup` (07.10 yedeği var) → yeni seed; eski belgeler `make reset-demo` ile silinir ama yedek ve git ile geri gelir. Audit satırları korunur (FK'sız).

---

## 5. Ekip sohbeti (C.1 / Ü-7.1) — tasarım taslağı ve riskler (Ç-5 kararı sonrası)

**Sözleşme (frontend `api/proposed.ts` zaten bu uçları bekliyor):** `GET /api/chats` (üyesi olunan sohbetler: id, title, members, last_message_at, unread), `POST /api/chats` (`member_ids[]`, `title?`; 2 üye = birebir, >2 grup), `GET /api/chats/{id}/messages` (sayfalı, `since`), `POST /api/chats/{id}/messages` (`text?`, `document_id?` — belge paylaşımı yalnızca gönderenin **ve** alıcının görebildiği belge: her alıcı için `allowed_document_ids` kontrolü; aksi hâlde 403, belge adı sızmaz).
**Tablolar:** `chats(id, title, created_by, created_at)`, `chat_members(chat_id, user_id, joined_at, last_read_at)`, `chat_messages(id, chat_id, sender_id, text, document_id?, created_at)`. Migration 0016. Yetki: yalnızca üye okur/yazar (`chat_members`), **admin/management üye değilse göremez** (Ü-7.1 madde 3) → admin API'de sohbet içeriği **yok**, yalnızca sayım. Canlı güncelleme V0'da polling (5 sn, kart deseni).
**Riskler ve sınırlar:** (1) **Balbal sohbete girmez** (Ü-7.2): `/api/ask` ve retrieval `chat_messages`'a hiç dokunmaz — kodda ayrı modül, `allowed_document_ids`'in dışında; test: sohbet metni hiçbir prompt'a giremez (sentinel testi). (2) Sohbetler kurumsal hafızaya aktarılmaz (03-operasyon Ü-7): ingestion hattına girmez, FTS'te indekslenmez. (3) Belge paylaşımı yetki sızıntısı yapmaz: yalnızca iki tarafın ortak yetkili olduğu belge; aksi hâlde "paylaşılamaz" (P-2 benzeri, ad dönmez). (4) Audit: mesaj içeriği audit'e **yazılmaz**; yalnızca sohbet oluşturma/üye ekleme `admin_events`. (5) Silme/düzenleme yok V0 (basitlik); KVKK: demo kurgu. (6) Grup "görüş talebi" sekmesi (B-06a) Ürün 2 → uç yok. Büyüklük M (2 model, 4 uç, 6–8 test).

---

## SORU (Naci cevaplamalı; İ-1…İ-8 Tansu'ya iletilecek)

1. **Ç-9 yol:** yeniden adlandırma (B, önerim — 0 LLM ile 70 belge korunur) mı, sıfırdan yeni set + eski set `legacy` (A) mı?
2. **Ç-1 eşik:** yalnızca "göster + sor" yönünde (A, önerim) — onay?
3. **Ç-2 bağlam:** istemci tarafı önceki soru metni (A) mı, sunucu hafızası (B, T9 değişir) mi — yoksa karar Tansu'ya mı?
4. **Ç-3 terim:** sözlük karşılığını söyleyip aramak (A) serbest mi? Tansu'ya A/B olarak iletilsin mi?
5. **Ç-5 ekip sohbeti** ve **Ç-6 süreç modeli** Ürün 1'de şimdi mi?
6. **Ç-7 .eml/.docx/MT940:** V0 kapsam kararı değişiyor mu (B) yoksa PDF'e dönüştürülmüş kopya (A) mı?
7. **İ-6 demo bugün:** 06.10.2026'ya alınsın mı?
8. **Adım 1 ölçümü** (≤ 28 LLM çağrısı, bayrak açık/kapalı karşılaştırma, §3.1 soru taslağı) onaylanır mı; §3.1 soruları `questions.json`'a yeni kategori (`discovery`) olarak eklensin mi?
9. **Takvim:** D/E için ~2–3 hafta + 2 kota günü tahminini Tansu'nun "frontend ile aynı anda biter" beklentisiyle siz mi eşleştirirsiniz?
10. İ-1…İ-8 Tansu'ya bu dosyadan mı iletilir, yoksa ayrı bir "sorular" notu mu hazırlansın?
