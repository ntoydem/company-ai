# İş Emri 2026-10-11 — Adım 3 Raporu

**Konu:** Solo `make test` · **Tarih:** 11.10.2026 · **Durum:** 🛑 **DURDU — Adım 3'ün kendi
kuralı ("Hata varsa dur, rapora yaz") tetiklendi.**

## 1. Sonuç

```
FAILED tests/test_validate_documents.py::test_real_prose_and_manifest_validate_clean
1 failed, 656 passed, 15 deselected, 14 warnings in 832.19s (0:13:52)
```

Tek koşu, tek hata. `656 passed` — bu iş emrinin kendi değişiklikleri (Adım 1/2) başka
hiçbir test'i bozmadı.

## 2. Hatanın tam içeriği

```
def test_real_prose_and_manifest_validate_clean() -> None:
    prose_report = validate_prose()
    assert prose_report.errors == []
    generated_report = validate_generated(MANIFEST_PATH)
    assert generated_report.errors == []
E   assert ["DOC-ANK-FIN...ak tescil e'"] == []
E   Left contains 3 more items, first extra item: "DOC-ANK-FIN-013: aynı cümlede
    'Karatepe RES Enerji Üretim A.Ş.' 2 kez + bağlaç ['and']: ..."
```

`generated_report.errors` 3 öğe döndürdü — **Adım 1'in raporunda (`IS_EMRI_2026-10-11_adim1.md`
§4) ZATEN ÖNCEDEN BİLDİRİLEN, aynı 3 bulgu:**

| doc_id | Durum |
|---|---|
| `DOC-ANK-FIN-013` | Yeni bulgu (Adım 1'de bulundu), kapsam dışı — bu iş emrinde adı geçmiyor |
| `DOC-ANK-OPS-008` | Bilinen — ADIM 5'in 19 belgelik listesinde (13 "iç belge" grubunda) |
| `DOC-CO-ADM-009` | Bilinen — ADIM 5'in 19 belgelik listesinde (13 "iç belge" grubunda) |

## 3. Kök neden

Bu hata **sürpriz değil, Adım 1'in kendi işinin DOĞRUDAN, ÖNGÖRÜLEN bir sonucu.** Adım 1'de
eklenen `check_self_referential_sentences` kapısı, `validate_documents.py` içinde — bu kapı
`backend/tests/test_validate_documents.py::test_real_prose_and_manifest_validate_clean`
tarafından da (aynı fonksiyonlar üzerinden) dolaylı olarak çalıştırılıyor. Adım 1'in raporu
bu 3 bulguyu zaten açıkça listelemişti; `make lint`'in kendi `validate-documents --prose-only`
adımı bu 3 hatayı YAKALAMAZ (çünkü onlar `validate_generated`'ın, yani FULL modun, bulduğu
hatalar — `--prose-only` bunları hiç çalıştırmaz). Bu yüzden Adım 1/2'nin kendi "full
validate-documents" komut satırı çalıştırmaları bu 3 hatayı GÖSTERDİ ama `make lint` yeşil
kaldı (farklı kapılar farklı kapsamda).

**`make test` ise `pytest`'in KENDİ test dosyasını çalıştırıyor, o dosya full modu
çağırıyor** — bu yüzden bu hata `make lint`'te görünmüyordu ama `make test`'te göründü.

## 4. Neden burada durdum (plan ile çelişki değil, Adım 3'ün kendi kuralı)

Adım 3'ün talimatı birebir: *"Tek başına tam `make test`. Hata varsa dur, rapora yaz."* Hata
var — durdum. Adım 4 (Boztepe PF-2) ve Adım 5 (Kategori B) **henüz başlatılmadı.**

**Not:** Adım 5 zaten `DOC-ANK-OPS-008` ve `DOC-CO-ADM-009`'u düzeltecekti (19 belgelik
listesinin içinde) — bu ikisi için "düzeltme" ayrı bir karar gerektirmiyor, planın kendisi
zaten bunları kapsıyor. Asıl açık karar noktası **`DOC-ANK-FIN-013`** — hiçbir adımda adı
geçmeyen, Adım 1'in yeni kapısının tesadüfen bulduğu bir belge.

## 5. Bekleyen karar (Naci'den)

`DOC-ANK-FIN-013` için üç seçenek:
1. **Adım 5'e ekle** — aynı kök nedenden (parties_list SPV'yi içeriyor) kaynaklanıyor, Adım
   1'in `counterparty_list` düzeltmesiyle aynı mantıkla 1 Claude çağrısıyla düzeltilebilir
   (~$0,01-0,02, bütçenin çok altında).
2. **Bu iş emrinin kapsamı dışında bırak** — `make test`'in bu TEK testi (3 hata) Adım 4/5
   tamamlandıktan sonra (OPS-008/CO-ADM-009 düzelince) hâlâ 1 hatayla (FIN-013) kırmızı
   kalacak; bu durumda test dosyasının kendisi güncellenmeli (`xfail` işaretlenmeli veya
   FIN-013 ayrı bir round'a not edilmeli).
3. **Şimdi dur, hiçbir şey yapma** — Naci'nin kararını bekle.

**Ben seçenek 3'ü uyguladım (DUR) — talimat gereği.** Devam etmek için onay/karar bekliyorum.

## 6. Maliyet (değişmedi)

Kümülatif: $0,0262 / $1,2 (Adım 1+2). Adım 3 LLM çağrısı yapmadı ($0 ek).

## 7. Durum tablosu

| Adım | Durum |
|---|---|
| 1 | ✅ tamamlandı (`5820fa4`) |
| 2 | ✅ tamamlandı (`81f1b9a`) |
| 3 | 🛑 **DURDU** — hata bulundu, rapor yazıldı (bu dosya) |
| 4 (Boztepe PF-2) | ⏸ başlatılmadı |
| 5 (Kategori B) | ⏸ başlatılmadı |
