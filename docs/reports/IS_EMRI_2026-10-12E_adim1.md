# İş Emri 2026-10-12-E — Adım 1 Raporu ("ÇED Süreci Durum Yazısı" teşhisi)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — kod/belge DEĞİŞTİRİLMEDİ, LLM çağrısı
yapılmadı. Kaynak: `seed_data/evaluation/results/*adimD*/results.json` ve
`seed_data/documents/`'daki mevcut (eval ortamıyla aynı) render çıktısı.

## 1. Belge: DOC-IZM-DEV-003 — "ÇED Süreci Durum Yazısı" (tam render metni)

> **Süreç Durumu**
> Kızılova RES projesi kapsamında yürütülen çevresel etki değerlendirmesi çalışmaları,
> ilgili mevzuat hükümlerine uygun olarak sürdürülmektedir. Bu süreçte Kızılova RES
> Enerji Üretim A.Ş. tarafından sunulan bilgi ve belgeler, ilgili idare tarafından
> detaylı bir incelemeye tabi tutulmuştur.
> Mevcut aşamada **devam ediyor** durumu geçerliliğini korumakta olup, 12.09.2026
> gelişmesi resmi kayıtlarımıza intikal etmiştir. Bugüne kadar önlisans (15.01.2025) ve
> arazi edinimi (20.01.2025 itibarıyla) adımları tamamlanmıştır. ...
>
> **Bekleyen Adımlar**
> Planlanan takvimin aksamadan yürütülmesi amacıyla MNO Teknik Danışmanlık Ltd.
> nezdindeki onay süreçlerinin tamamlanması beklenmektedir. ...
>
> **Bekleyen Kritik Adımlar** (tablo)
> | Adım | Beklenen |
> |---|---|
> | ÇED | İDK toplantısı bekleniyor (ÇED-2026-057). Ayrıca Orman Ön İzni devam... |
> | İmar Kesinleşme | — |
> | Kat'i Proje Onayı | — |
> | Bağlantı Anlaşması | — |
> | Yapı Ruhsatı | — |
> | Üretim Lisansı | — |

**Not:** Tabloda **"İnşaat"/"İnşaat Başlangıcı" satırı hiç YOK.**

## 2. Dört soru — beklenen cevap (ledger'dan çözümlendi) ve belge metninde açıkça var mı?

| Soru | Beklenen cevap (ledger) | Belgede açıkça var mı? |
|---|---|---|
| **IZM-DEV-002** "ÇED süreci ne durumda?" | `ced_status.value: "ongoing"` → biçimlenmiş: **"devam ediyor"** | ✅ **AÇIKÇA VAR** — metinde birebir "devam ediyor" geçiyor. |
| **IZM-DEV-004** "Yapı ruhsatı var mı?" | `pending_steps` listesinde "Yapı Ruhsatı" → `expected: None` (henüz yok) | ⚠️ **DOLAYLI** — tabloda "Yapı Ruhsatı" satırı var ama "Beklenen" hücresi BOŞ; "henüz alınmadı" şeklinde açık bir düz yazı cümlesi YOK. |
| **IZM-DEV-005** "Üretim lisansı alındı mı?" | `timeline.licence: None` (hayır, yalnız önlisans var) | ⚠️ **DOLAYLI** — "Üretim Lisansı" tabloda boş satır olarak var; açık negatif cümle YOK. |
| **IZM-DEV-006** "İnşaata başlandı mı?" | `timeline.construction_start: None` (hayır) | ❌ **YOK** — belge "inşaat"tan hiç bahsetmiyor; bu soruya dair HİÇBİR doğrudan metin/satır yok. |

## 3. Üç koşuda sonuç (soru bazlı)

| | C1 (Gemini) | C2 (Haiku/Haiku) | C3 (Haiku/Sonnet) |
|---|---|---|---|
| IZM-DEV-002 | ✅ cite | ✅ cite | ✅ cite |
| IZM-DEV-004 | ✅ cite | ❌ cevap yok, kaynak yok | ✅ cite |
| IZM-DEV-005 | ✅ cite | ❌ cevap yok, kaynak yok | ❌ cevap yok, kaynak yok |
| IZM-DEV-006 | ✅ cite | ❌ cevap yok, kaynak yok | ❌ cevap yok, kaynak yok |

**Gemini (C1) belgeyi her 4 soruda da anıyor ve doğru cevaplıyor — IZM-DEV-006'da bile**
(belgede hiç karşılığı olmayan bir soruda). Claude (her iki yapılandırmada da) IZM-DEV-005/
006'da **hiç cevap vermiyor, hiçbir kaynak anmıyor** (`cited_titles: []` — kısmi/yanlış bir
atıf değil, TAM bir çekilme).

## 4. Kök neden sınıfı

- **IZM-DEV-002:** sorun yok — açık metin, her üç yapılandırma da doğru.
- **IZM-DEV-004:** **(c) belge bağlamdaydı, model (yalnız Haiku-answer, C2) cevaplamadı** —
  Sonnet (C3) aynı dolaylı tablo sinyaliyle doğru cevapladı; Haiku daha tutucu/emin olmadığında
  çekiliyor. Katkıda bulunan faktör: belgenin dolaylı (boş hücre) sunumu — (a)'ya yakın ama
  Sonnet'in başarması bunun TEK başına yeterli bir engel olmadığını gösteriyor.
- **IZM-DEV-005:** **(c) belge bağlamdaydı (aynı retrieval, Gemini aynı belgeyi aynı soru
  metniyle buldu), model (Haiku VE Sonnet, ikisi de) cevaplamadı.** Katkıda bulunan faktör:
  (a) — dolaylı tablo sunumu, negatif gerçeği açık cümleyle söylemiyor.
- **IZM-DEV-006: (a) belge soruyu net cevaplamıyor** — birincil sınıf bu, çünkü belgede
  "inşaat" konusuna dair HİÇBİR satır/cümle yok; Gemini'nin doğru cevabı belge alıntısından
  değil, genel çıkarımdan geliyor (ÇED/imar/ruhsat/lisans tamamlanmamış bir projede inşaatın da
  başlamamış olması mantıksal sonucu) — Claude'un ikisi de bu çıkarımı yapmayı reddetti.

**Getirme (class b) KANITI YOK** — router sınıflandırması (DOCUMENT_QUERY) her üç
yapılandırmada aynı, retrieval LLM'den önce ve ondan bağımsız çalışıyor (aynı soru metni →
aynı SQL/vektör arama); C1'in AYNI belgeyi AYNI sorularla başarıyla bulup alıntılaması,
belgenin getirilebilir olduğunu (index/arama tarafında bir eksiklik olmadığını) gösteriyor.
Kesin kanıt için ham `retrieved_document_ids` loglanmamış (bu alan `results.json`'a
yazılmıyor) — bu yüzden (b) tamamen dışlanamaz, ama mevcut kanıtın tamamı (c)'yi işaret
ediyor.

**Beklenti aşırı katı (class d) değil** — kriter yalnız "cevapla ve doğru kaynağı an" (004/
005/006'da `value_check: skipped`, metin eşleşmesi aranmıyor); Gemini bunu rahatça
karşılıyor, bu yüzden eşiğin kendisi makul.
