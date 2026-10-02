# AI-BalBal PR #4 Raporu — iki küçük UX düzeltmesi (`feat/ux-kucuk-duzeltmeler`)

**Tarih:** 02.10.2026  **Model:** Claude Fable 5.1  **Tag:** yok  **company-ai commit:** `<commit>`
**PR:** https://github.com/ftansu/AI-BalBal/pull/4 (**açık, merge edilmedi**; base `main` = `b709f09`) · **Dal:** `feat/ux-kucuk-duzeltmeler` @ `159b46c` (1 commit, 3 dosya) · **Backend:** dokunulmadı · **LLM:** 0

## 1. Kaynak
NOT §0 "UX notu 1/2" (Naci'nin 02.10.2026 tarayıcı testi): (1) P1 paketinde Ürün 1 giriş ekranından Belgeler/Projeler'e görünür bağlantı yok; (2) onaylı belgede "Durum: Taslak" yazması (onay rozeti yalnızca onaylı değilken görünüyordu) yanıltıcı.

## 2. Yapılanlar
| Dosya | Değişiklik |
|---|---|
| `components/Layout.tsx` | `urun1Home` iken (P2 kapalı + `/departman/<slug>`) üst barda "Belge yükle"nin yanına **"Belgeler"** linki (`${pathname}/belgeler`, mevcut `topbar-button` stili, `S.shell.documents` metni). Diğer ekranlarda görünmez. |
| `components/DocumentTable.tsx` | Onay rozeti her belgede: `approved` → `badge ok` "Onaylı"; diğerleri `badge warn`. |
| `components/DocumentDetailPanel.tsx` | Durum hücresinde aynı rozet kuralı. |

Yeni string/CSS yok (`REVIEW_STATUS_LABELS.approved = "Onaylı"` ve `S.shell.documents = "Belgeler"` zaten vardı).

## 3. Doğrulama
- `npm run typecheck`, `lint`, `build` yeşil (node:20 container).
- Tarayıcı görünümü (link konumu, rozet renkleri) Naci/Tansu; dev VM'e deploy edilmedi (istenirse PR-1'deki gibi submodule geçici checkout).

## 4. Anayasa
Ürün 1 etiketi (T-11) · T-12: iki yeni görsel öğe PR'da "tasarım onayı bekliyor" · Ç-16: Projeler linki ve sütun ayrımı yapılmadı, kapsam dışı olarak yazıldı · T-14: dal + PR, main'e push yok, yeni bağımlılık yok · `[ANAYASA KONTROLÜ]` notu PR'da.

## 5. Kendi aldığım küçük kararlar
| Karar | Neden |
|---|---|
| "Belgeler" linki yalnızca Ürün 1 giriş ekranında | P2'de sekmeler zaten var; üst barı kalabalıklaştırmamak (Ü-10) |
| Rozet yaklaşımı (ayrı sütun yerine) | tablo düzeni değişmez; Tansu isterse sütuna çevirir |
| Dev VM'e deploy edilmedi | iki satırlık görsel değişiklik; merge/onay sonrası pin güncellemesiyle gelir |

## 6. Tansu'ya kısa özet
İki küçük düzeltme (PR #4): Ürün 1 ekranında üst bara "Belgeler" linki (yoksa personel belgelere ulaşamıyordu) ve onaylı belgede "Onaylı" rozeti ("Taslak" onaylanmamış gibi okunmasın). İkisi de tasarım onayına tabi; biçimi değiştirebilir ya da geri alabilirsin. Merge kararı sende.
