# İş Emri 2026-10-11-D — Adım 5 Raporu (kriter tablosu, sonuç)

**Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı — **iş emrinin tamamı bitti**

Kriter `docs/plans/ADIM_D_KRITERLERI.md`'de sonuçlardan ÖNCE yazıldı, sonuçlar görüldükten
sonra DEĞİŞTİRİLMEDİ. **Hiçbir prompt/ayar/eşik oynatılmadı.**

## 1. Kriter tablosu

| Kriter | C2 (Haiku/Haiku) | C3 (Haiku/Sonnet) |
|---|---|---|
| (a) isolation/hallucination/authorization: sıfır soru kaybı + kritik bulgu ≤ C1 | ✅ (kayıp yok; kritik 1=1) | ✅ (kayıp yok; kritik 0≤1) |
| (b) abstention doğruluğu ≥ C1 | ❌ **%71,4 → %66,7** | ✅ %71,4 → %76,2 |
| (c) toplam doğru sayısı ≥ C1 | ✅ 53 → **60** | ✅ 53 → **62** |
| (d) diğer kategorilerde kategori başına ≤1 soru kaybı | ❌ **`document`: 5 kayıp** | ❌ **`document`: 4 kayıp** |
| **GENEL** | ❌ **RED** | ❌ **RED** |

**İkisi de reddedildi — ama C3, C2'den her ölçütte daha iyi** (abstention geçti, toplam
doğru sayısı daha yüksek, kritik bulgu 0, `document` kaybı 4 < 5) ve **tek bir kriterde**
(d) başarısız oldu.

## 2. `document` kategorisi — tek, tekrarlayan kök neden

C3'ün kaybettiği 4 sorudan **2'si aynı belgeyle ilgili** (`ÇED Süreci Durum Yazısı` —
`IZM-DEV-005`, `IZM-DEV-006`), tıpkı Adım 1'in (İş Emri C) teşhisindeki `IZM-DEV-002`
bulgusuyla **aynı belge, aynı desen**: Claude bu belgeyi retrieval'ın getirdiği bağlamda
bulsa da Gemini kadar kendinden emin biçimde kullanmıyor/anmıyor. C2'nin 5 kaybı da bu
belgeyi içeriyor (`IZM-DEV-004/005/006`). **Bu, tek bir belgeye/konuya özgü, tekrarlayan
bir model-davranış farkı** — rastgele değil, ama istemci hatası da değil (Adım 1'de
doğrulandı: hata yok, kesilme yok, router doğru). Sonuca göre oynama yapılmadı (talimat).

Diğer 2 kayıp çeşitli (`ANK-OPS-003`: yanlış ama ilgili bir belge andı; `ANK-NEG-004`:
C3 FAZLADAN kaynak andı ama beklenen ifade metinde yoktu — aşırı değil yetersiz atıf
sorunu).

## 3. Maliyet ve gecikme

Toplam: **$7,92 / $10,00** (aşılmadı). Gecikme karşılaştırması Adım 4 §4'te — C1'in
pacing'den kaynaklanan yapay yüksek gecikmesi nedeniyle ham hız karşılaştırması için
güvenilir değil.

## 4. Ayrı ortam — temizlik

`company-ai-eval` projesi (postgres/backend/ocr-worker, `./data-eval`, `infra/.env.eval`)
bu rapordan sonra **durduruldu ve kaldırıldı** (`docker compose -p company-ai-eval down`,
veriler `./data-eval` altında — istenirse `rm -rf ./data-eval` ile tamamen silinebilir,
şimdilik dokunulmadı). Canlı sistem (`company-ai` projesi) bu iş emri boyunca **hiç
durdurulmadı/yeniden başlatılmadı** — sürekli Gemini ile çalışır durumda kaldı.

## 5. Sonuç (yorum, karar DEĞİL)

Önceki emrin (C) 40 sorulu/zayıf ölçümü ile bu emrin 99 sorulu/tam ölçümü **aynı yönde**
sonuçlanıyor: C2 ve C3 ikisi de kabul kriterlerini karşılamıyor. Ama bu ölçüm daha net bir
tablo veriyor: **C3'ün tek engeli `document` kategorisindeki, tek bir belgeye
yoğunlaşan bir atıf/güven sorunu** — genel cevap kalitesi (toplam doğru sayısı, abstention,
güvenlik) Gemini'ye göre **daha iyi**. Bu iş emri bir taşıma kararı ALMIYOR, yalnız ölçüyor
ve raporluyor.

## 6. Commit'ler (bu iş emrinde, sırayla)

`b6cee01` (Adım1) → `1b701b7` (Adım2) → `6ae9e42` (Adım3 kriter) → `aa29ae9` (Adım4) →
bu rapor (Adım5).

## 7. Final durum tablosu

| Adım | Durum |
|---|---|
| 1 (ücretsiz teşhis, C1 vs C3) | ✅ istemci hatası yok |
| 2 (ayrı ortam) | ✅ 109 belge doğrulandı |
| 3 (kriter, sonuçlardan önce) | ✅ kilitlendi |
| 4 (C1/C2/C3, 99 soru) | ✅ bir ortam-kurulum hatası bulundu ve düzeltildi |
| 5 (karşılaştırma) | ✅ **C2 ❌, C3 ❌ — ikisi de red, C3 tek kriterde (d) başarısız** |
