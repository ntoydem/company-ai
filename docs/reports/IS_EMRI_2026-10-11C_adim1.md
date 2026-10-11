# İş Emri 2026-10-11-C — Adım 1 Raporu (tek Haiku çağrısı, rate-limit başlıkları)

**Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı

## Çağrı

`PROSE_ANTHROPIC_API_KEY` (mevcut, .env'de hazır) ile `claude-haiku-5-5`'e tek, minimal
bir çağrı yapıldı ("Reply with exactly one word: OK", max_tokens=16). **`ANTHROPIC_API_KEY`
adı hiç kullanılmadı** (SDK'nın otomatik env-fallback'ine düşmemek için `api_key=` her
zaman açıkça `PROSE_ANTHROPIC_API_KEY`'den verildi). Anahtarın değeri hiçbir yerde
yazdırılmadı/loglanmadı.

## `anthropic-ratelimit-*` başlık DEĞERLERİ (anahtar değil)

| Başlık | Değer |
|---|---|
| `anthropic-ratelimit-requests-limit` | 1000 |
| `anthropic-ratelimit-requests-remaining` | 999 |
| `anthropic-ratelimit-requests-reset` | 2026-10-11T20:20:03Z |
| `anthropic-ratelimit-input-tokens-limit` | 2.000.000 |
| `anthropic-ratelimit-input-tokens-remaining` | 2.000.000 |
| `anthropic-ratelimit-input-tokens-reset` | 2026-10-11T20:20:04Z |
| `anthropic-ratelimit-output-tokens-limit` | 400.000 |
| `anthropic-ratelimit-output-tokens-remaining` | 400.000 |
| `anthropic-ratelimit-output-tokens-reset` | 2026-10-11T20:20:04Z |
| `anthropic-ratelimit-tokens-limit` | 2.400.000 |
| `anthropic-ratelimit-tokens-remaining` | 2.400.000 |
| `anthropic-ratelimit-tokens-reset` | 2026-10-11T20:20:04Z |

**Günlük limit başlığı DÖNMEDİ** — tüm `-reset` zaman damgaları çağrı anından ~1 dakika
sonrasını gösteriyor (dakikalık pencere). Yalnız dakikalık istek/token sınırları var;
günlük bir sınır bu hesap/kademede gözlenmedi.

**Sonuç (Adım 3'ün pacing/geri-çekilme tasarımı için):** dakikada 1000 istek, dakikada
2.400.000 toplam token — bu demo ölçeğindeki eval koşuları (düzinelerce soru) için bol
limit; agresif bir pacing'e gerek yok, yalnız 429/529 için geri-çekilme yeterli.

## Maliyet

1 çağrı, 20 input + 4 output token (claude-haiku-5-5) — ihmal edilebilir (<$0,001).
İş emrinin DUR eşiği `EVAL_BUDGET_USD=4` — bu tek çağrı o sayaca girmiyor (sayaç Adım 3'te
kurulacak, Adım 4'ün eval koşuları için); kümülatif bilgi amaçlı not: ~$0,0001.
