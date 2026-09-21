# Phase NN Raporu — <phase adı>

**Tarih:** DD.MM.YYYY  **Model:** Opus/Sonnet  **Tag:** phase-NN  **Commit:** <hash>

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den kelimesi kelimesine) | Durum | Kanıt (test adı / komut / çıktı) |
|---|---|---|---|
| 1 | ... | ✅ / ❌ / ⏭ atlandı (neden) | `pytest tests/test_x.py::test_y` |

## 2. Yapılanlar
- Kısa madde listesi (ne eklendi, hangi tablolar/endpoint'ler/servisler).

## 3. Değişen dosyalar
`git diff --stat phase-(NN-1)..phase-NN` çıktısı (kısaltılmış).

## 4. Testler
- Toplam: N, geçen: N, atlanan: N (neden), süre.
- `make lint` sonucu.

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|

## 6. Açık sorular (Naci cevaplamalı)
- `SORU:` ...

## 7. Riskler / sonraki phase için notlar
- ...

## 8. Doğruladığım üçüncü taraf davranışları
- Örn. "ocrmypdf `--skip-text` davranışı, resmi doküman sürüm X"

## 9. Kaynak kullanımı
- Container RAM (docker stats özet), toplam LLM token/maliyet (varsa).
