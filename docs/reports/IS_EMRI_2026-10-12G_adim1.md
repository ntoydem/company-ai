# İş Emri 2026-10-12-G — Adım 1 Raporu (Yeşilova türbin/MW — T-14.1=B)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — kapılar yeşil, 0 LLM çağrısı (belge
içeriği etkilenmedi).

## Düzeltme

`seed_data/master/yesilova_res.yaml`'da T-11.13'ün eski (iptal edilen) "5 × 4,4 MW"
cevabı yerine T-14.1=B (`NACI_CEVAP_2026-10-12.md` §5) işlendi:

- **Faz 1:** 3 × Vestas V136 (4,0 MW modu) = **12 MWe** (YEKDEM, 01.01.2017–31.12.2026,
  73 USD/MWh — değişmedi).
- **Faz 2:** 2 türbin, **"Vestas, 5,0 MW sınıfı"** (model adı uydurulmadı) = **+10 MWe**
  (PTF, YEKDEM dışı).
- **Toplam:** 5 türbin, **22 MWe** (`capacity_mw.current` ile tutarlı). Kontrol:
  3×4,0 + 2×5,0 = 12+10 = **22 ✅**.

Değişen alanlar: `turbines.model_generic`/`count` notları, `timeline.cod_actual` notu,
`finance.yekdem` notu — hepsi yalnız açıklayıcı not metni, **şema değişikliği yok**
(hiçbir belge `turbines`/`capacity_mw` alanlarını Yeşilova için `key_facts` ile
substitue etmiyor — doğrulandı, grep; bu yüzden faz ayrımı için yeni Pydantic alanı
eklemek gereksiz soyutlama olurdu).

## Grep taraması — "5×4,4" / "V136 4,4 MW" temizliği

`seed_data/generator/`, `seed_data/master/`, `seed_data/evaluation/` dizinlerinde
`"4,4 MW"` / `"V136"` için tam tarama yapıldı. Kalan tek "4,4" referansı, yeni eklenen
notun kendisinde — eski cevabın **İPTAL edildiğini** belgeleyen açıklama ("T-11.13'ün
'5 × 4,4 MW' cevabı İPTAL"), güncel bir değer olarak DEĞİL. `questions.json`'da hiç
"4,4"/"V136" referansı yoktu (kontrol edildi, sıfır sonuç).

## DOC-YSV-FIN-009 (Facility Agreement) — dokunulmadı, gerekçe

Bu belgenin spec'i (`seed_data/generator/document_specs/yesilova.py`) "Do not state any
phase-specific MW or turbine count" yönergesini taşıyor — T-14.1 cevaplanmadan önce
modelin faz verisini icat etmesini önlemek için eklenmişti. T-14.1 artık cevaplandı ama
bu kısıtlama **hâlâ geçerli bir içerik kararı**: bir kredi sözleşmesi belgesi türbin
faz detayına girmek zorunda değil, "2. The Facility" bölümü zaten finansman şartlarına
odaklı. Yönerge DEĞİŞTİRİLMEDİ, belge yeniden üretilmedi (gerek yok, LLM maliyeti yok).

## Doğrulama

- `validate_ledger --summary`: 0 hata, 1 uyarı (önceden var, ilgisiz).
- `generate_documents` (102 belge) + `validate_documents` (full): 0 hata, 0 uyarı.
  Hiçbir Yeşilova belgesi `turbines`/`capacity_mw` alanlarını `key_facts` ile
  kullanmıyor (doğrulandı), bu yüzden regenerasyon beklenen şekilde içerik
  değiştirmedi — yalnız ledger'ın kendi doğruluğu (gelecekteki herhangi bir belge/soru
  için) düzeltildi.
- Aritmetik: 3×4,0 + 2×5,0 = 12+10 = 22 ✅.

Devam ediliyor: **Adım 2** (banka adları — Ç-12).
