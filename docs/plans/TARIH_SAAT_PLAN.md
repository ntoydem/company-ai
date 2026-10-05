# Tarih/saat — demo takvimi vs gerçek takvim, "bugün" hesaplarının koda taşınması — Teşhis + Uygulama Planı

**Tarih:** 05.10.2026 · **Durum:** **UYGULANDI** — Naci 4 SORU'yu planın önerisiyle onayladı; rapor `docs/reports/TARIH_SAAT_REPORT.md` · **Kapsam:** backend (`app/core/config.py`, `app/services/answer_prompt.py`, `app/services/version_chain.py`, `app/excel/functions.py`, `app/services/excel_ask.py`), ledger (`seed_data/master/*.yaml`, `seed_data/generator/ledger_schema.py`) — ledger içerik değişikliği yalnızca **Naci onayıyla**; `DOC-ANK-OPS-009`'un gerçek `expiration_date`'i hâlâ onay bekliyor (rapor §6), diğer tüm belgeler `expiration_date: null`.

Kaynak: 02.10.2026 teşhisi (bu oturumun önceki turu — `Settings.demo_today`, `build_user_prompt`, `version_chain.evaluate_version_chains`, `outstanding_debt`/`Outstanding_DemoToday`, canlı `/api/ask` testi); CLAUDE.md beş değişmez kural (özellikle 3 — CALCULATION ve 5 — TEMPORAL TRUTH); Balbal Anayasası Ç-7 (Veri Durumları: Kesin Veri / Veri Yok / Yeterli Veri Bulunmamaktadır / Çelişkili Veri / AI Yorumu — NOT §8.2'de alıntılı); `docs/ARCHITECTURE.md` ADR-012 (version-chain, "eski ≠ yanlış").

---

## 0. Tespitler (bu turda yeniden doğrulandı + yenileri)

- **T1 — Tek kaynak, ayrım zaten temiz.** `app/core/config.py:24` `demo_today: date = date(2026, 9, 15)` (env `DEMO_TODAY`, `.env.example`'da aynı değer) — iş mantığına giren **tek** "bugün" kaynağı bu. Gerçek sunucu saati (`datetime.now(UTC)`) yalnızca operasyonel zaman damgalarında kullanılıyor (JWT `iat`, `submitted_at`, `reviewed_at`, audit saklama kesme tarihi, olay `created_at`) — hiçbiri "güncel mi/bugün ne" kararına girmiyor. Ayırma işi büyük ölçüde zaten yapılmış; eksik olan **demo dışı modda `demo_today`'in yerini alacak, saat dilimi bilinçli bir "gerçek bugün" kaynağı**.
- **T2 — `BUGÜN` satırı yalnızca göreli hesap için, kendi başına alıntılanamaz.** `answer_prompt.py` kural 8: *"Bugünün tarihi 'BUGÜN' satırında verilir; 'şu anda', 'kaçıncı yıl' gibi hesaplarda gerçek takvimi değil bu tarihi kullan."* Canlı testte "Bugünün tarihi nedir?" sorusu bu yüzden **cevaplanmadı** (`insufficient_data`) — model `BUGÜN` satırını bir "kaynak" saymıyor, sistem de her cevabı `KAYNAKLAR` bloğuna dayandırmayı zorunlu kılıyor. Bu, rule 2 (SOURCE GROUNDING) açısından doğru ama ayrı bir problemi gizliyor: **hesabın kendisi de modele bırakılmış** (rule 8, "bu tarihi kullan" = LLM zihinsel aritmetik yapsın demek) — bu tam olarak rule 3'ün (CALCULATION: LLM matematik yapmaz) tarih aritmetiğine uygulanmamış hali.
- **T3 — `expiration_date` ledger şemasında hiç yok.** `app/models/document.py:130`'da DB kolonu hazır (`expiration_date: Mapped[date | None]`) ve `version_chain.is_in_force()` bunu zaten okuyor — ama `seed_data/generator/ledger_schema.py`'deki `Document` sınıfında `effective_date: Fact | None` var, **`expiration_date` alanı yok**; generator da hiçbir belgeye yazmıyor. Yani bugün demo'daki **hiçbir belge** "süresi doldu" durumuna düşemez (expiration_date her zaman `None` → `is_in_force` hep `True` döner, belge `expiration_date is None` olduğu sürece sonsuza dek "yürürlükte" sayılır). Canlı testteki "Ankara RES sigorta poliçesi bitmiş mi?" sorusunun cevapsız kalmasının bir nedeni de bu: mekanizma var, veri yok.
- **T4 — Excel `outstanding_debt(as_of="today")` canlı hesap değil, dondurulmuş değer.** `app/excel/functions.py::outstanding_debt`, `as_of` boş/`today`/`bugün`/`güncel` geldiğinde workbook'taki **önceden hesaplanmış** `Outstanding_DemoToday` adlı aralığı okuyor (`seed_data/generator/generate_excel.py:200`, üretim anındaki `meta["demo_today"]`'e göre pişirilmiş). Keşif: generator zaten her workbook'un gizli `_META` sayfasına `demo_today` (B4) ve `Financial_Model_2026.xlsx`'in `Inputs!B12`'sine `DEMO_TODAY` yazıyor; `manifest.json`'ın kökünde de `ledger_demo_today` var. Yani **"bu rakam hangi tarih için pişirildi" bilgisi zaten workbook'ta duruyor, yalnızca hiçbir yerde okunup `settings`'teki değerle karşılaştırılmıyor.**
- **T5 — `/api/me/agenda` henüz yok.** B-01 "Gündeminiz" backend'de uygulanmadı (`docs/BACKEND_GAPS.md`: "Arayüz hazır, backend bekliyor"). Bugün paylaşılacak bir "süresi yaklaşan belgeler" altyapısı **yok** — ama bu planın 2. maddesindeki "kaç gün kaldı" hesabı tam olarak B-01'in de ihtiyaç duyacağı fonksiyon; şimdiden ortak, saf bir fonksiyon olarak tasarlanırsa B-01 geldiğinde tekrar yazılmaz.
- **T6 — Küçük bir ayrı bulgu (kapsam dışı, bilgi amaçlı):** `scripts/run_eval.py:256` çıktı klasörünü adlandırırken `datetime.date.today()` kullanıyor (`retrieval-only_<tarih>` klasör adı). Bu iş mantığına girmiyor, yalnızca dosya adı — düzeltme gerektirmiyor, atlanıyor.
- **T7 — Anayasa uyumu (Ç-7).** Ç-7'nin beş durumu (Kesin Veri / Veri Yok / Yeterli Veri Bulunmamaktadır / Çelişkili Veri / AI Yorumu) **belge sorularının** sınıflandırmasıdır. "Bugünün tarihi nedir?" bir belge sorusu değil — sistemin kendi ayarı. Bu soruyu Ç-7'nin beş durumundan birine zorlamak (ör. "Kesin Veri" gibi davranmak) kavramsal olarak yanlış olur; bu yüzden 5. maddede önerilen çözüm **Ç-7 pipeline'ına hiç girmiyor**, ayrı ve açıkça farklı bir yol.

---

## 1. Gerçek takvim / `DEMO_TODAY` bayrağı

**Yeni ayarlar (`app/core/config.py`):**

```python
demo_mode_enabled: bool = True          # tek geri alma anahtarı — kapat: DEMO_MODE=false
demo_today: date = date(2026, 9, 15)     # yalnızca demo_mode_enabled=True iken okunur
company_timezone: str = "Europe/Istanbul"  # yalnızca demo_mode_enabled=False iken okunur
```

**Tek fonksiyon (`app/services/temporal.py`, yeni — bkz. §6):**

```python
def today(settings: Settings) -> date:
    if settings.demo_mode_enabled:
        return settings.demo_today
    return datetime.now(ZoneInfo(settings.company_timezone)).date()
```

Bu, `ask.py`'deki iki `settings.demo_today` çağrısının, `version_chain.evaluate_version_chains`'in ve Excel tarafının (§4) **tek** giriş noktası olur — `demo_today` alanına artık doğrudan erişilmez (lint/`grep` ile denetlenebilir bir kural: `settings.demo_today` yalnızca `temporal.today()` içinde geçer).

- **Varsayılan davranış değişmez:** `demo_mode_enabled` default `True`, bugünkü `.env.example` aynen kalır. Prod'a geçişte tek satır: `DEMO_MODE=false` + `COMPANY_TIMEZONE=Europe/Istanbul` (veya müşteri neredeyse).
- **Saat dilimi neden gerekli:** sunucu konteyneri UTC çalışıyor (`datetime.now(UTC)` operasyonel damgalarda zaten böyle); "bugün" kavramı müşterinin yerel takvim gününe göre olmalı (TR müşteri → gece yarısından sonraki saatlerde UTC ile yerel gün farklı olabilir). `zoneinfo` (stdlib, Python 3.12'de ek bağımlılık gerektirmez) kullanılır; **Docker imajının IANA tz veritabanına sahip olduğu doğrulanmalı** (slim tabanlı imajlarda `tzdata` paketi eksik olabilir — küçük bir kontrol/ekleme, uygulama adımında).
- **`today()` yalnızca `date` döner, saat bilgisi taşımaz** — mevcut `BUGÜN: GG.AA.YYYY` formatıyla birebir uyumlu, prompt tarafında değişiklik gerekmez.

## 2. "Kaç gün kaldı / süresi doldu mu / kaçıncı yıl" — prompt kuralından kodla hesaba

**Bugün:** rule 8 modele "BUGÜN'ü kullan, hesapla" diyor — hesabın kendisi LLM'de. Rule 3 (CALCULATION) bunun tam karşıtını söylüyor ("LLM matematik yapmaz… LLM ne hesaplanacağını belirler ve sonucu yorumlar"); tarih farkı da bir hesaptır.

**Öneri:**

- `app/services/version_chain.py`'ye (ya da yeni `temporal.py`'ye) saf bir fonksiyon: `expiration_note(document, today) -> str | None` — yalnızca `expiration_date` doluysa üretir, örn. `"Süre: 22.10.2026'ya kadar yürürlükte (37 gün kaldı)"` ya da `"Süre: 15.01.2025'te sona erdi (1 yıl 8 ay önce)"`. Format TR (CLAUDE.md), gün sayısı `(expiration_date - today).days` ile **kodda** hesaplanır.
- `format_source()` (`answer_prompt.py`) bu satırı, var olan `Zincir: …` satırının hemen altına, yalnızca doluysa ekler — `describe_metadata` ile aynı desen (eski kaynaklar byte-identik kalır, boş alan satır eklemez).
- **"Kaçıncı işletme yılı" ayrı bir sorun:** bu proje seviyesinde bir hesap (örn. Ankara RES'in COD/işletmeye giriş tarihinden bu yana kaç yıl), tek bir belgenin `expiration_date`'ine bağlı değil. Ledger'da bunu besleyecek açık bir "işletmeye giriş tarihi" alanı var mı netleştirilmeli (`project.timeline` içinde bir alan olabilir — uygulama adımında ledger'dan doğrulanacak, SORU değil, kod incelemesi). Bulunursa aynı prensiple (kodda hesapla, prompt'a hazır cümle olarak ver) çözülür; proje düzeyinde bir "Bugün X. işletme yılındayız" notu, kaynak bloklarının üstüne (BUGÜN satırının yanına) tek satır eklenebilir.
- **Rule 8 değişir, kaldırılmaz tamamen:** yeni metni öneri — *"8. BUGÜN satırı yalnızca bağlam içindir; tarih farkı, kalan gün, süre hesaplarını SEN yapma — bu bilgi hazır verilmişse (ör. 'Süre: …') onu aynen aktar, hesaplanmamışsa 'belgede/sistemde bu hesap için veri yok' de."* Bu, rule 3'ün dilini (LLM hesap yapmaz) tarih alanına taşır. **Prompt metni değiştiği için `make lint`'teki prompt-doküman eşitlik testi güncellenecek** (`docs/prompts/ANSWER_SYSTEM_PROMPT.md` mirror).
- Eval etkisi: `--retrieval-only` (LLM'siz) zincir/pozisyon alanlarını zaten test ediyor; yeni `expiration_note` saf fonksiyon olduğu için **birim testle** (LLM'siz) doğrulanır. Yalnızca rule 8 metin değişikliği küçük bir canlı örnekle (2-3 soru) teyit ister.

## 3. `expiration_date` adayları (ledger'a eklenecek — Naci onayı gerekir, bu planda eklenmiyor)

Ledger şemasına `expiration_date: Fact | None` alanı eklenmeden (şema değişikliği, §6) hiçbir belgeye değer yazılamaz. Aşağıdaki belgeler, **türleri gereği** süre/geçerlilik kavramı taşıyan, demo senaryosunda anlamlı bir "süresi doldu mu" sorusu üretecek adaylardır. Hiçbirinin **tarihi burada önerilmiyor** — bu bir ürün/veri kararı (CLAUDE.md: "Ledger'da olmayan rakamı UYDURMA").

| Belge | Tür | Neden aday | Hangi soruyu canlı cevaplanabilir yapar |
|---|---|---|---|
| `DOC-ANK-EPC-007` Ankara RES Construction All Risks Insurance Policy Summary | İnşaat dönemi sigortası | İşletme dönemine geçişten (OPS-009, 2024-01-10) sonra mantıken geçerliliğini yitirmiş olmalı; şu an `related: [DOC-ANK-EPC-007]` ile gevşek bağlı, gerçek bir `supersedes` zinciri yok | "İnşaat sigortası hâlâ geçerli mi?" / canlı testteki soruyla doğrudan ilişkili |
| `DOC-ANK-OPS-009` Sigorta Yenileme Bildirimi — İşletme Dönemi | İşletme dönemi sigorta yenileme bildirimi | Yenileme bildirimleri doğası gereği dönemsel (yıllık); ledger'da bir sonraki yenileme belgesi **yok** — **karar gerektirir:** (a) bu belgeye `expiration_date` verip "süresi dolmuş, yenileme belgesi eksik" senaryosu kurgulanır (sistemin expired'ı doğru yakaladığını gösterir), ya da (b) 2025/2026 için ikinci bir yenileme belgesi eklenip zincirlenir (poliçe hâlâ geçerli senaryosu). **Bu ikisi birbirini dışlar, SORU.** |
| `DOC-ANK-DEV-001` Ankara RES Üretim Lisansı | Üretim lisansı | `licence_permit` ailesinin tipik alanı `valid_until` (B-28b rehberinde zaten önerili); ama lisans süreleri genelde çok uzun (onlarca yıl) — demo ufku (2026) içinde "doldu" senaryosu üretmez, yalnızca "X yıl kaldı, uzak" gösterir | "Üretim lisansının süresi ne zaman doluyor?" (uzak, sorun yok senaryosu) |
| `DOC-IZM-DEV-001` İzmir RES Önlisans Belgesi | Önlisans (pre-license) | İzmir RES "development, ÇED tamamlanmamış" — önlisansların sınırlı geçerlilik süresi olması projenin "aciliyet" anlatısına uyar, Ankara RES'ten ayrı bir proje olduğu için demo karışıklığı yaratmaz | "İzmir RES önlisansının süresi ne zaman doluyor, ne kadar kaldı?" |

**Değerlendirme dışı bırakılan:** `DOC-ANK-FIN-013` Insurance Assignment Agreement (bir temlik/teminat sözleşmesi — kredi süresine bağlı, kendi başına "süresi dolar" türünde değil); `DOC-IZM-DEV-003` ÇED Durum Yazısı (bir "yanıt/aksiyon tarihi" taşıyabilir ama bu `expiration_date` değil, ayrı bir `extra_fields` kavramı — B-01/agenda'ya daha yakın, §6).

## 4. Excel `outstanding_debt('today')` — canlı hesap mı, açık uyarı mı

**Öneri: açık uyarı/drift kontrolü (B seçeneği), canlı hesap değil.** Gerekçe:

- Canlı hesap (workbook'taki periyot bazlı (`Outstanding_Q2_2026` vb.) bakiyeler arasında **enterpolasyon**) yeni bir hesap motoru gerektirir — V0 sadeliği ilkesine (CLAUDE.md "premature abstraction istenmiyor") ve mevcut mimariye (DuckDB/fonksiyon kataloğu, önceden tanımlı) aykırı büyüklükte bir ek.
- Keşif (§0 T4): generator zaten her workbook'a üretim anındaki `demo_today`'i gömüyor (`_META!B4`, `Financial_Model_2026.xlsx!Inputs!B12`, `manifest.json.ledger_demo_today`). **Bu bilgi hazır, yalnızca okunmuyor.**
- Plan: generation sırasında bu değeri bir **named range** olarak da işaretle (ör. `Ledger_DemoToday`, `_META!B4`'ü gösteren) — `LoadedWorkbook.info.named_ranges` zaten yükleniyor, ek bir okuma mekanizması gerekmez. `outstanding_debt()` çağrıldığında: workbook'un `Ledger_DemoToday`'i ile `temporal.today(settings)` karşılaştırılır:
  - Eşitse (bugünkü demo akışı): mevcut davranış, `Outstanding_DemoToday` döner.
  - Farklıysa: değer **döndürülmez**; `FunctionError`/`insufficient_data` benzeri açık bir uyarıyla ("bu rakam DD.MM.YYYY için hesaplanmış, bugünün verisi yok") cevaplanır — sessiz bayatlama yerine açık ret, rule 2/5 ile tutarlı.
- Bu, `demo_mode_enabled=False` moduna geçildiğinde (gerçek takvim) otomatik olarak devreye girer: workbook'lar yeniden üretilmediği sürece `outstanding_debt('today')` hep "veri yok" der — ki bu doğru davranıştır (gerçek güncel bakiye, gerçek Excel verisi gelmeden hesaplanamaz).
- **Büyük alternatif (şimdi değil, not düşülüyor):** gerçek bir amortisman tablosu üzerinden interpolasyonlu canlı hesap — yalnızca ürün gerçekten "herhangi bir günün" kesin bakiyesini isterse, ayrı bir plan/ADR konusu.

## 5. "Bugünün tarihi nedir?" — sabit, kodla üretilen cevap

**Öneri: bu, bir Ç-7 veri durumu değil — Balbal'ın belge/Excel cevap hattına hiç girmeyen bir sistem notu.** İki uygulama seçeneği (ikisi birbirini dışlamaz):

- **(a) Frontend:** Balbal ekranında (veya genel üst barda) her zaman görünen küçük bir "Bugün: 15.09.2026 (demo)" / gerçek modda "Bugün: 05.10.2026" rozeti — hiçbir soru sorulmadan, hiç LLM çağrısı olmadan. En basit, en ucuz, Ç-7 tartışmasını hiç açmıyor.
- **(b) Backend, `router.py` öncesi kısa devre:** dar, kapalı bir anahtar kelime kümesi ("bugünün tarihi", "bugün ayın kaçı", "hangi yıldayız" vb.) retrieval/LLM'e hiç girmeden, `temporal.today(settings)`'ten üretilen sabit bir cümleyle ("Bugün 15.09.2026 (demo tarihi)." / "Bugün 05.10.2026.") yanıtlanır — **0 LLM çağrısı**, `query_type` için yeni bir değer (`SYSTEM_FACT`) ya da benzeri, `audit_log`'a yine de yazılır (rule 4 AUDITABILITY).

Önerim **(a)'yı asıl çözüm, (b)'yi isteğe bağlı** yapmak: (a) ürünün "Balbal yorum/sistem bilgisi üretmez, belge aktarır" sınırını hiç bulanıklaştırmıyor; (b) kullanıcı deneyimi açısından "Balbal'a her şeyi sorabilirim" beklentisini karşılar ama yeni bir `query_type` ve yeni bir anahtar-kelime listesi bakımı getirir. **SORU (Naci):** yalnızca (a) mi, yoksa (a)+(b) mi? (b) seçilirse bunun ürün sınırını değiştirdiği için Tansu'ya bilgi notu düşülmesi öneriyorum (Balbal'ın yanıtlayabileceği soru türlerinin genişlemesi, §4.7.7 ruhuna aykırı değil ama yeni bir davranış).

## 6. `/api/me/agenda` ile ortak altyapı

B-01 (Gündeminiz) backend'de **yok** (§0 T5) — bu yüzden bugün paylaşılacak kod yok. Ama **tasarım düzeyinde** ortaklık var ve şimdiden kurulmalı: §2'deki `expiration_note`/tarih-farkı hesabı, "süresi yaklaşan belgeler" sorgusunun da çekirdeği olacak. Öneri:

- §1'in `temporal.today(settings)` fonksiyonu ve §2'nin tarih-farkı saf fonksiyonları **tek modülde** (`app/services/temporal.py`) toplanır, `version_chain.py`'den bağımsız import edilebilir — B-01 geldiğinde `document_repo`'dan `expiration_date is not null` olan belgeleri çekip aynı fonksiyonla "N gün kaldı" listesi üretir, tekrar yazılmaz.
- Bu turda **agenda endpoint'i kodlanmaz** — yalnızca paylaşılacak fonksiyon bu şekilde konumlandırılır ki B-01 ayrı bir fazda bu hesabı yeniden icat etmesin.

## 7. Kabul kriterleri ve kota dostu ölçüm

| # | Kriter | Ölçüm (LLM'siz tercih edilir) |
|---|---|---|
| T01 | `temporal.today(settings)` tek giriş noktası; `settings.demo_today`'e doğrudan erişim yalnızca bu fonksiyonun içinde (`grep -rn "settings.demo_today" app/` → yalnızca `temporal.py`) | statik grep + birim test |
| T02 | `DEMO_MODE=false` + `COMPANY_TIMEZONE` ayarıyla `temporal.today()` gerçek saatten (sahte/monkeypatch'li saat) doğru yerel günü döndürür; `DEMO_MODE=true` (varsayılan) `demo_today`'i aynen döndürür | birim test, saat sahteleştirilir (ör. `monkeypatch`/`freezegun`), gerçek saat beklemez |
| T03 | `expiration_note()` saf fonksiyon: dolu `expiration_date` için doğru TR cümle + gün sayısı; boşsa `None`; eski kaynak metni (expiration_date yoksa) byte-identik kalır | birim test |
| T04 | Rule 8 yeni metni; `make lint` prompt-doküman eşitliği yeşil; sistem promptunun geri kalanı (1-7, 9-10) değişmedi | `make lint` (LLM'siz) |
| T05 | `outstanding_debt('today')`: workbook `Ledger_DemoToday` ile `temporal.today()` eşleşirse eski davranış; eşleşmezse açık uyarı (istisna/`insufficient_data` benzeri), sessiz bayat değer yok | birim test (iki workbook fixture: eşleşen/eşleşmeyen tarih) |
| T06 | (varsa, SORU 5 cevabına göre) sistem-olgusu kısa devresi: regex eşleşen sorularda **0 LLM çağrısı**, `audit_log`'a yazılır | birim/entegrasyon test (LLM client hiç çağrılmadığı mock'la doğrulanır) |
| T07 | `validate-ledger` 0 hata/uyarı; yeni ledger şema testi: `expiration_date` doluysa `>= effective_date` | `make validate-ledger` (LLM'siz) |
| T08 | Canlı doğrulama — yalnızca küçük, hedefli: rule 8 değişikliği + (varsa) yeni ledger `expiration_date` sonrası "Ankara RES/İzmir RES … süresi doldu mu / ne kadar kaldı" 2-3 soru, LLM ≤ 3 | `/api/ask` canlı, Gemini kotası gözetilerek tek tur |

**Genel ilke:** bu planın büyük kısmı (saf fonksiyonlar, prompt metni, ledger şema doğrulaması) **LLM gerektirmeden** test edilebilir — yalnızca T08 gerçek bir model çağrısı ister ve o da 2-3 soruyla sınırlı tutulur.

---

## SORU (Naci cevaplamalı)

1. **§3 — `DOC-ANK-OPS-009` için hangi senaryo:** (a) bu belgeye `expiration_date` verilip "yenileme eksik, poliçe süresi dolmuş" mu kurgulansın, yoksa (b) 2025/2026 için yeni bir yenileme belgesi eklenip zincirlensin, poliçe hâlâ geçerli mi gösterilsin? İkisi ayrı ledger değişikliği, onayınızı bekliyor.
2. **§5 — sistem-olgusu soruları:** yalnızca (a) frontend rozeti mi, yoksa (a)+(b) backend kısa devresi de mi ("Bugünün tarihi nedir?" gibi sorulara Balbal'ın da LLM'siz, sabit metinle cevap vermesi)? (b) seçilirse Tansu'ya kısa bir bilgi notu düşülmesini öneriyorum.
3. **§1 — `company_timezone` varsayılanı** `Europe/Istanbul` öneriliyor; onaylıyor musunuz yoksa farklı bir varsayılan mı istiyorsunuz (örn. müşteri bazlı değişecekse env'den okunur hâliyle kalması zaten yeterli)?
4. **§3 — diğer üç aday** (`DOC-ANK-EPC-007`, `DOC-ANK-DEV-001`, `DOC-IZM-DEV-001`) için `expiration_date` eklensin mi, yoksa yalnızca SORU 1'deki senaryo mu kodlansın (demo kapsamını küçük tutmak için)? Eklenecekse tarihler ayrı bir onay turu ister (bu planda yok).

## Kendi aldığım küçük kararlar

- Yeni modül adı `app/services/temporal.py` (var olan `version_chain.py`'yi şişirmemek, B-01'in de bağımsız import edebilmesi için).
- `Ledger_DemoToday` adlı yeni bir named range (generator tarafı) — mevcut `_META!B4` hücresini göstermesi yeterli, yeni bir sayfa/hücre gerekmez.
- `zoneinfo` (stdlib) kullanılır, yeni üçüncü taraf bağımlılık eklenmez; yalnızca Docker imajının `tzdata` içerdiği uygulama adımında doğrulanır.
- Rule 8'in yeni metni bu planda taslak olarak verildi; kelimesi kelimesine son hâli uygulama adımında `docs/prompts/ANSWER_SYSTEM_PROMPT.md` ile birlikte netleşir.

## Doküman etkileri (uygulama adımında)

- Yeni ADR (sıradaki numara **ADR-026**): "Gerçek takvim / demo takvimi ayrımı ve tarih aritmetiğinin koda taşınması."
- `docs/ARCHITECTURE.md`, `infra/.env.example` (`DEMO_MODE`, `COMPANY_TIMEZONE`), `README.md` (prod'a geçiş notu), `docs/prompts/ANSWER_SYSTEM_PROMPT.md`, `docs/PHASES.md` durum satırı, `docs/reports/TARIH_SAAT_REPORT.md` (uygulama sonrası).
