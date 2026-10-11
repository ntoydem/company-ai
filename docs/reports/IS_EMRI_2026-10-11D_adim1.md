# İş Emri 2026-10-11-D — Adım 1 Raporu (ücretsiz teşhis, C1 vs C3)

**Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı — **istemci hatası BULUNMADI, kod
değişikliği yapılmadı** (talimatın kendi şartı: yalnız istemci hatasıysa düzelt).

## 1. Yöntem

`gemini-adimC-c1_2026-10-11/results.json` ↔ `claude-haiku-sonnet-adimC-c3_2026-10-11/
results.json` (İş Emri 2026-10-11-C'nin kayıtlı sonuçları, yeniden çağrı yapılmadı —
ücretsiz) soru bazında karşılaştırıldı. Ayrıca `claude-haiku-haiku-adimC-c2` dosyası da
(abstention bulgusu için) incelendi.

## 2. `document` (%25,0 → %12,5) kök nedeni: TEK soru, model davranışı — istemci hatası DEĞİL

**C1'de doğru, C3'te yanlış olan TEK soru: `IZM-DEV-002`** ("Kızılova RES'in ÇED süreci ne
durumda?"). Diğer 7 `document` sorusunun hiçbiri değişmedi (ikisi de aynı 6 soruda
başarısız, 1 soru her ikisinde de doğru — `CO-NEG-005`).

| | C1 (Gemini) | C3 (Haiku router + Sonnet answer) |
|---|---|---|
| `query_type` | DOCUMENT_QUERY | DOCUMENT_QUERY (**aynı** — router kararı sorunlu değil) |
| `cited_titles` | `["ÇED Süreci Durum Yazısı"]` | `[]` (boş — hiçbir kaynak anılmadı) |
| `answered` | true | false |
| cevap | "...çevresel etki değerlendirmesi çalışmaları... sürdürülmektedir [K1]." | "Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım." |
| hata | yok | yok |
| `tokens_in` | 26.515 | 44.401 |
| `tokens_out` | 94 | 232 |
| gecikme | 25.779 ms | 3.333 ms |

**Bulgular:**
- Router kararı (`query_type`) **birebir aynı** — yanlış yönlendirme DEĞİL.
- Hata/istisna **yok** — JSON/biçim ayrıştırma sorunu DEĞİL (`AnthropicClient` temiz bir
  yanıt döndürdü, `error: null`).
- `tokens_out: 232` — kesilme/`max_tokens` sorunu DEĞİL (NO_ANSWER_TEXT kısa, 232 token
  rahat sığıyor; `max_output_tokens=2048` zaten sınırı değil).
- `tokens_in` farkı (26.515 ↔ 44.401) **tokenizer farkı** — retrieval, LLM'den ÖNCE ve
  LLM'den bağımsız çalışır (SQL/vektör arama); Gemini ve Claude'un KENDİ tokenizer'ları
  aynı metni farklı sayıda token'a böler. Bu, retrieval'ın farklı/az chunk getirdiğinin
  KANITI DEĞİL.
- **Sonuç: bu bir istemci hatası değil — Claude (hem Haiku hem Sonnet answer modeli,
  C2'de de aynı soru aynı şekilde yanlış) muhtemelen aynı bağlamda bu belgeyi Gemini'den
  daha TUTUCU/emin-olmadığında-cevaplamayan bir şekilde değerlendirdi.** Model davranış
  farkıdır, prompt/model/eşik/top_k bu raporla OYNATILMADI (talimat gereği).

## 3. `data` (%50,0 → %33,3) kök nedeni: ÖLÇÜM ARTEFAKTI — gerçek bir gerileme YOK

| Soru | C1 | C2 | C3 |
|---|---|---|---|
| `ANK-DAT-002` | ✅ geçti | ✅ geçti | ✅ geçti |
| `ANK-DAT-003` | ❌ kaldı | ❌ kaldı | ❌ kaldı |
| `ANK-FIN-010` | ❌ **hata (HTTP 500), değerlendirme dışı bırakıldı** | ❌ geçemedi (hatasız, değerlendirmeye dahil) | ❌ geçemedi (hatasız, değerlendirmeye dahil) |

**Üç koşunun da soru-bazlı SONUÇLARI birebir aynı** (hangi soru geçti/geçmedi değişmedi).
Yüzde farkı (%50 ↔ %33,3) yalnız PAYDA farkından geliyor: C1'de `ANK-FIN-010` bir backend
hatası (HTTP 500, geçici) aldığı için `eval_lib.py`'nin "değerlendirilen" sayacından
DIŞARIDA kaldı (payda 2), C2/C3'te aynı soru hatasız çalıştı ama YANLIŞ cevap verdi (payda
3'e dahil). **Bu bir Claude kalite sorunu değil** — C1'in kendi HTTP 500'ü (nedeni
araştırılmadı, tek seferlik/geçici görünüyor, 3 koşuda da sadece 1 kez oldu) ölçümün
payda büyüklüğünü değiştirdi.

## 4. Ek bulgu (talimatın asıl kapsamı değil, bilgi amaçlı — C1 vs C2)

`GEN-AMB-001` (ambiguous, `expect_no_answer: true`): C1 doğru şekilde cevap vermedi; **C2
(Haiku answer)** kendinden emin, YANLIŞ bir cevap verdi ("sözleşme vadesi 14 yıl... [K51]").
Bu, C2'nin abstention gerilemesinin (%85,7→%78,6) TEK kaynağı. Yine istemci hatası değil
— Haiku'nun (answer modeli olarak) belirsiz bir soruda Gemini'den daha az tutuk davranması.

## 5. Router/sınıflandırma farkı (benign, sonucu etkilemedi)

`GEN-TRM-001`: C1 `MIXED_QUERY`, C2/C3 (Haiku router) `DOCUMENT_QUERY` sınıflandırdı —
farklı ama her üçünde de nihai sonuç doğru (`passed: true` üçünde de). Düzeltme
gerekmiyor.

## 6. Sonuç

**İstemci hatası (ayrıştırma/`max_tokens`/hata eşleme) bulunamadı — kod değişikliği
yapılmadı.** Adım 4'ün 99 sorulu/geniş EVAL_BUDGET_USD=10 koşusu, bu zayıf n=3 örneklemin
ortaya çıkardığı "tek soru = büyük yüzde sıçraması" sorununu çözecek (daha büyük payda).
