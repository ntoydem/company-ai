# İş Emri 2026-10-11 — Adım 1 Raporu

**Konu:** `parties_list` hatası (DOC-IZM-LEG-002) · **Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı

## 1. Yapılan değişiklikler

### 1.1 `facts.py` — yeni `counterparty_list` token'ı

`parties_list` SPV'yi de içeriyordu (`", ".join(doc["parties"])`), bu yüzden "malikler =
`[[parties_list]]`" gibi kullanımlar SPV'yi de malik gibi gösteriyordu. Yeni token:

```python
if other_parties:
    facts["counterparty_list"] = ", ".join(other_parties)
```

Tek taraflı belgede (`other_parties` boş) bu token **hiç facts dict'ine eklenmiyor** — LLM'e
hiç önerilmiyor; kullanılırsa `check_prose_document`'ın mevcut "bilinmeyen token" reddi devreye
girer.

### 1.2 Yeni render-sonrası kapı — `check_self_referential_sentences`

`validate_documents.py`'ye eklendi: aynı cümlede SPV adı 2+ kez geçiyorsa VE cümlede bir bağlaç
kelimesi (ile/ve/arasında/between/and/with) varsa hata. Cümle bölme, kısaltmalardan ("A.Ş.",
"Ltd.") sonraki noktada BÖLME YAPMAYAN bir regex ile yapılıyor
(`(?<!Ş)(?<!Ltd)(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ0-9])`).

**Eşik ölçümü (84 belgelik gerçek korpus):** İlk ölçüm 7 hata verdi — 4'ü **yanlış-pozitif**
(kapak sayfasının başlık+alt başlık+banner metni, gerçek bir cümle değil, sayfa 1'de SPV adı
doğal olarak 1-2 kez geçiyor). Kalibrasyon: `_body_only()` yardımcı fonksiyonu eklendi —
kapı artık yalnız sayfa 2+ (gövde metni) üzerinde çalışıyor, ilk sayfa footer'ından
(`"DEMO — sentetik demo belgesi — sayfa"` / `"DEMO — synthetic demo document — page"`)
sonrasını tarıyor. Kalibrasyon sonrası: **3 hata** (hepsi gerçek, aşağıda).

**Bu kapı doğası gereği bir SAYISAL eşik taşımıyor** (binary koşul: 2+ tekrar VE bağlaç) —
kalibre edilen şey hangi METNİN tarandığıydı (kapak hariç gövde), sayısal bir sınır değil.

### 1.3 DOC-IZM-LEG-002 spec düzeltmesi

`document_specs/izmir.py`: `prose_suppress_facts` artık `{"counterparty", "parties_list"}`
(ikisi de bastırıldı); `prose_guidance_tr` artık `[[counterparty_list]]` kullanılmasını,
`"[[spv_name]] ile [[counterparty_list]] arasında"` kalıbını açıkça istiyor.

**1 Claude çağrısı, ilk denemede kabul edildi ($0,0163, bütçe $1,2'nin içinde).**

## 2. Render edilmiş TAM metin (DOC-IZM-LEG-002)

> **1. Hakkın Kapsamı**
> Bu taslak, DOC-IZM-LEG-002 numaralı ve Kira/İrtifak Hakkı Sözleşmesi Taslağı başlıklı belge kapsamında, Kızılova RES için Kızılova RES Enerji Üretim A.Ş. ile Hasan Yücel, Mehmet Karadağ, Ayten Sarı arasında imzalanması öngörülen kira ve irtifak hakkı düzenlemesinin çerçevesini içermektedir. Belge DRAFT sürümündedir ve 01.05.2024 tarihlidir. Belgenin mevcut durumu Taslak olarak belirtilmiştir.
> Taslakta öngörülen hakların kapsamı, ilgili taşınmazların proje faaliyetleri için kullanımı ile bu kullanımın gerektirdiği geçiş ve irtifak ihtiyaçlarıyla sınırlı olacaktır. Hakkın hangi taşınmaz bölümlerini ve hangi kullanım biçimlerini kapsayacağı, taraflarca üzerinde mutabık kalınacak nihai metinde ayrıntılı olarak belirlenecektir.
> Hasan Yücel, Mehmet Karadağ, Ayten Sarı, taşınmazlar üzerindeki mülkiyet haklarını muhafaza edecektir. Kızılova RES Enerji Üretim A.Ş. ise yalnızca imzalanacak sözleşmede açıkça tanınan haklara sahip olacaktır. Bu taslak, tarafların nihai iradesini yansıtmamakta olup müzakere sürecinde değiştirilebilecektir.
>
> **2. Yürürlük ve Genel Hükümler**
> Bu belge bir taslaktır ve henüz imzalanmamıştır. Taslaktaki hükümler, ancak Kızılova RES Enerji Üretim A.Ş. ile Hasan Yücel, Mehmet Karadağ, Ayten Sarı tarafından imzalanacak nihai metinle taraflar bakımından hüküm doğurabilecektir. Bu nedenle mevcut metin, taraflar için herhangi bir hak veya yükümlülük oluşturmamaktadır.
> Sözleşmenin süresi, bedeli, ödeme esasları, sona erme halleri ve uyuşmazlıkların çözüm yöntemi gibi hususlar, taraflarca nihai metinde belirlenecektir. Bu hususlara ilişkin hükümler, taslak aşamasında bağlayıcı bir düzenleme olarak değerlendirilmemelidir.
> Sözleşme metninde yapılacak her değişiklik ve ek, tarafların karşılıklı mutabakatıyla ve yazılı olarak düzenlenecektir. Belgenin son hâli, imza için hazırlandığında ilgili tüm taraflara ayrıca iletilecektir.

## 3. Kapı sonuçları

| Kapı | Sonuç |
|---|---|
| lint (ruff+mypy+ocr-worker) | ✅ |
| validate-ledger | ✅ 0 hata/uyarı |
| validate-documents --prose-only | ✅ 0 hata/uyarı |
| validate-excel | ✅ 0 hata |
| validate-documents (full, 84 belge) | ⚠️ **3 hata — DOC-IZM-LEG-002'de DEĞİL** (aşağıda) |
| token-grep (DOC-IZM-LEG-002) | ✅ temiz |
| yasak kelime taraması (akdedilmiştir/bağlayıcı nitelik kazanacaktır/yürürlüğe girmiştir) | ✅ temiz |
| self-referential-sentence kapısı (DOC-IZM-LEG-002) | ✅ artık tetiklenmiyor |

## 4. Yeni kapının bulduğu 3 pre-existing hata (DOC-IZM-LEG-002 DIŞINDA)

| doc_id | Durum |
|---|---|
| `DOC-ANK-OPS-008` | Bilinen — ADIM 5 kapsamında (13 "iç belge" listesinde), o adımda düzeltilecek. |
| `DOC-CO-ADM-009` | Bilinen — ADIM 5 kapsamında (13 "iç belge" listesinde), o adımda düzeltilecek. |
| `DOC-ANK-FIN-013` | **YENİ BULGU, kapsam dışı.** `[[parties_list]]` VE `[[spv_name]]` aynı cümlede birlikte kullanılmış ("including [[parties_list]] and [[spv_name]]") — parties_list zaten SPV'yi içerdiği için SPV adı 2 kez geçiyor. İş emrinde bu belge adı geçmiyor; **düzeltilmedi, gelecek bir round için not edildi.** Hand-edited DEĞİL (serbestçe düzeltilebilir). |

Bu 3 hata DOC-IZM-LEG-002'nin kendi düzeltmesini etkilemiyor — Adım 1'in kendi hedefi
tamamlandı. ADIM 5'in kendi raporunda OPS-008/CO-ADM-009 kapatılacak; FIN-013 bu iş emrinin
kapsamı dışında kaldığı için açık bırakıldı.

## 5. Maliyet

1 çağrı, $0,0163. Kümülatif bu iş emrinde: **$0,0163 / $1,2**.

## 6. Commit

`facts.py`, `validate_documents.py`, `document_specs/izmir.py`, `prose/DOC-IZM-LEG-002.yaml` —
tek commit, bu rapordan sonra push edilecek.
