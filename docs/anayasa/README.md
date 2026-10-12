> **Kaynak notu (company-ai):** Bu klasör `ftansu/AI-BalBal` deposunun `main` dalından
> **salt-okunur bir kopyadır** — İş Emri 2026-10-12-G Adım 5 ile 12.10.2026'da,
> `main` commit `4ab767b973a9f3dc27e3f5aad7025976e26fa4a8` (12.10.2026 09:20:16 +0300)
> hâliyle alındı. company-ai bu depoya yazamaz (bkz. `NACI_CEVAP_2026-10-12.md` §4);
> güncel sürüm gerektiğinde bu kopya yeniden alınmalıdır. `.docx` referans kopyası
> (insanlar için) buraya taşınmadı — bağlayıcı sürüm aşağıdaki Markdown dosyalarıdır.

# Balbal Anayasası — v2.1 (yürürlükte, 09.10.2026)

Bu klasör Balbal Platformunun bağlayıcı çerçevesidir. Tüm Üretici Taraflar ve Üretici AI'lar (frontend, backend, AI katmanı) her görevde bu Anayasaya göre çalışır.

**Yapı:** 00 Çekirdek (herkes okur) · 01 Ürün · 02 Teknik ve Güvenlik · 03 Operasyon ve Veri · Ek-A Proje Yetkilileri · Ek-B Yetenek Listesi · Ek-C Değişiklik Kaydı · Ek-D Süreç Tanımları · Ek-E Karar Bekleyen Noktalar · Ek-F Karakter Tanımı

**v2.1 (09.10.2026):** İş akışı katmanı ve yükümlülük bağı eklendi (Ek-B, Ü-3, Ü-4, O-13); Ç-6, Ç-12, T-13/S-9, Ç-17, Ek-A ve Ek-E güncellendi. Değişikliğin özeti Ek-C’dedir. Ç-3 gereği iki Proje Yetkilisinin onayıyla yürürlüğe girdi (Tansu 09.10.2026, Naci 09.10.2026 · PR #15); .docx kopyası eşlenir (S-5/3).

**Bu taslağın niteliği:** v1.1 üzerine, 30.09.2026 tarihli değerlendirme raporundaki önerilerin uygulanmış hâlidir. Tansu’nun yapısı, madde kodları ve temel mantığı korunmuştur. Yeni maddeler mevcut numaralandırmanın sonuna eklenmiş, değişen maddeler yerinde revize edilmiştir. Proje Yetkililerinin karar vermesi gereken ve bu taslakta *karar verilmemiş* noktalar Ek-E’de listelenmiştir; metin içinde köşeli parantezle gösterilir.

## Dosyalar

| Dosya | İçerik | Kim okur |
|---|---|---|
| [00-cekirdek.md](00-cekirdek.md) | Çekirdek (Ç-1…Ç-17), Ek-A Proje Yetkilileri, Ek-C Değişiklik Kaydı | Herkes, her görevde (T-16) |
| [01-urun.md](01-urun.md) | Ürün Modülü (Ü-1…Ü-11) | Ç-17 tablosuna göre |
| [02-teknik.md](02-teknik.md) | Teknik ve Güvenlik Modülü (T-1…T-16) | Ç-17 tablosuna göre |
| [03-operasyon.md](03-operasyon.md) | Operasyon ve Veri Modülü (O-1…O-12) | Ç-17 tablosuna göre |
| [ek-b.md](ek-b.md) | Ek-B Yetenek Listesi (kapalı liste) | Ç-17 tablosuna göre |
| [ek-d.md](ek-d.md) | Ek-D Süreç Tanımları (S-1…S-10) | Ç-17 tablosuna göre |
| [ek-e.md](ek-e.md) | Ek-E Karar Bekleyen Noktalar | Belirsizlikte |
| [ek-f.md](ek-f.md) | Ek-F Balbal AI Karakter Tanımı (şablon) | Balbal AI davranışı |

Üretici AI için bağlayıcı olan bu Markdown sürümüdür (T-16). Değişiklik yalnızca Ç-3 ve Ek-D S-5'e göre yapılır.
