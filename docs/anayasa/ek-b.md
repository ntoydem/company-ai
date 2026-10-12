# BALBAL ANAYASASI — EK-B: YETENEK LİSTESİ

**Balbal Platformu \| Versiyon 2.1 \| 09.10.2026**

01 Ürün Modülünün ayrıntılı ekidir ve **kapalı listedir** (Ü-1): burada olmayan yetenek yoktur; eklemek Ç-3 kapsamında Anayasa değişikliğidir. Her madde bağlı olduğu ürünün sınırlarına (Ü-3, Ü-4, Ü-5) tabidir; Ürün Modülü ile çelişirse Ürün Modülü geçerlidir.

**Fiil kuralı:** Bu listede “hazırlar”, “önerir”, “çıkarır”, “raporlar” fiilleri AI Taslağı üretmek anlamındadır; hiçbiri Resmi Kayıt oluşturmak veya dışarıya göndermek anlamına gelmez (O-6). “Takip eder” ve “hatırlatır” fiilleri Ürün 2 yeteneğidir (Ü-4). “Görüş sunar”, “analiz eder”, “projeksiyon” fiilleri Ürün 3 yeteneğidir.

**Genel mantık:** Sistem şirketin verisini önce **TANIR** (Ürün 1: kesin cevaplar, projeler ayrı ayrı, yorum yok), sonra **BİRLEŞTİRİR** (Ürün 2: farklı kaynak ve projelerden kesin bilgiyi yan yana getirir; hâlâ yorum yok), en sonunda **YORUMLAR** (Ürün 3: departman bazında yorum, görüş ve projeksiyon; son onay insanda).

## T0 — Test

- Çok basit bir kurulumla (birkaç belge ve basit bir kod) tek bir soru test edilir: AI bu belgelerden bilgi çekip anlamlı cevap verebiliyor mu?
- Bu test geçmeden Ürün 1’e kaynak ayrılmaz.

## Ürün 1 — Kurumsal Bilgi ve Doküman Sistemi

- Şirketin departman yapısını tanımlar.
- Personel, ortak alana belgelerini yükler: PDF, Word, Excel, e-posta içerikleri, sözleşmeler, departman belgeleri (teknik, finans, hukuk, İK), proje belgeleri, süreçlere bırakılan Kullanıcı Notları.
- Belgeleri sınıflandırır; bilgileri indeksler; belgeler arasında bağlantı kurar.
- Departman yapısı üzerinden yetkiye göre bilgi erişimi sağlar.
- Bilgiyi bulur; belgeyi bulur; belgeyi okur.
- Şirketin iş akışlarını (talep, onay, satın alma, ödeme talebi, ödeme listesi, masraf/avans, teslim, ödeme kaydı) tek bir akış motoru üzerinde, şirketin tanımladığı adım ve onaycılarla kayıt altına alır (O-13).
- Belgelerden yükümlülükleri (konu, son tarih, sorumlu departman, varsa tutar, kaynak madde) çıkarır (AI Taslağı; ilgili departman onaylar).
- Akış kayıtları, belgeler ve Kullanıcı Notları ile proje, süreç adımı ve yükümlülük arasında bağ önerir; bağ Kullanıcı onayıyla kesinleşir (O-13).
- Birden çok kaynaktan beslenir; her kaynağın söylediğini ayrı ayrı, kaynağını göstererek, yorum katmadan aktarır.
- Tek sohbet penceresinde birden fazla projeyle ilgili soruya, her projeyi ayrı ayrı cevaplayarak hizmet verir (Ü-3). Projeleri kıyaslamaz.
- Geçmiş kayıtları ve Kullanıcı Notlarını bulup gösterir.
- Personel arası sohbet sunar; Balbal AI bu sohbetlere dahil edilemez (Ü-7).

## Ürün 2 — AI Destek Beyni

- Farklı kaynaklardan ve farklı projelerden edindiği kesin bilgileri birleştirir; projeleri yan yana kıyaslar (gösterir, değerlendirmez).
- Belgeleri ve verileri karşılaştırır; yalnızca yan yana gösterir.
- Birleştirme sonuçlarını sözlü olarak yanıtlar.
- Yalnızca gerçekleşmiş verilerle hesaplama desteği verir (toplam, ortalama, fark) ve gerekirse etiketli Excel tablosu olarak sunar.
- Kısıtlı raporlama: gerçekleşmiş veriyi Müşterinin önceden belirlediği Word/Excel şablonlarına işler. Serbest raporlama yoktur.
- Veri taslağı hazırlar (Ü-4).
- Eksik bilgi veya belgeyi gösterir.
- Akış içinde ilgili belge ve kayıtları yan yana gösteren bulgular sunar; onay vermez, akışı durdurmaz.
- Yükümlülük durumunu (bekliyor / yerine getirildi / son gün geçti / kısmi) ve son günden sapmayı bağlı olaylardan hesaplar.
- Bir süreç adımına bağlı olayları tarih sırasıyla, kaynaklarıyla ve Kullanıcı Notlarını aynen aktararak sunar; neden-sonuç kurmaz.
- **Süre ve deadline takibi ve hatırlatması** (her departman için geçerli Ürün 2 yeteneği): kredi, teminat, sigorta, dava, icra, izin/ruhsat, bakım, muayene, milestone, görev süreleri.
- Birikmiş Kullanıcı Notlarını bir araya getirip gösterir.
- Departmanlar sistem üzerinden başka bir departmandan görüş talep edebilir; görüşler Kurumsal Hafızada saklanır.
- Karar vermez; insan onaylar.

## Ürün 3 — Departman Bazlı AI Araçları

Serbest raporlama, AI Yorumu, görüş ve projeksiyon burada başlar. Son onay insandadır. Ürün 2’ye ait süre takibi/hatırlatma yetenekleri bu listede tekrar edilmez; departman araçları onları Ürün 2’den devralır.

### Proje Finans

- Nakit akış raporu hazırlar (projeksiyon içerir).
- Banka sorularına cevap taslağı hazırlar (değerlendirme içerir).
- EPİAŞ verilerini işler ve yorumlar.
- Ödeme takvimi ve tahsilat takvimi önerisi çıkarır.
- Kredi dashboard’u için güncelleme önerisi hazırlar; dashboard verisini yetkili onaylar.
- Birikmiş hafızadan yararlanarak sapmalar hakkında detaylı görüş sunar.

### Mali İşler

- Fatura verisini çıkarır (AI Taslağı).
- Muhasebe kodu önerir.
- Cari mutabakata destek verir.
- Ödeme talimatı taslağı hazırlar; talimat yetkili onayıyla Resmi Kayda dönüşür.
- Banka hareketi ile kayıt eşleştirme önerisi sunar.
- Bütçe ile fatura eşleştirme önerisi sunar.

### Hukuk

- Sisteme girilmiş mevzuat değişikliklerinin mevcut sözleşme ve süreçlere etkisine dair görüş sunar. \[Ek-E/6: dış mevzuat kaynağına otomatik bağlantı ayrı bir Ç-11 kararıdır.\]
- Resmi yazı, cevap, sözleşme, dilekçe ve ihtarname taslağı hazırlar (değerlendirme içerir; gönderim Kritik İşlemdir).
- KEP yazılarını analiz eder.
- Dava ve icra süreçlerinin durumuna dair görüş sunar (süre takibi Ürün 2’dedir).

### İdari İşler

- Araç, bina, ekipman, demirbaş ve zimmet takibine dair raporlar ve görüş hazırlar (hatırlatmalar Ürün 2’dedir).
- Destek hizmeti taleplerini işler ve yönlendirme önerir.
- İdari satın almaya destek verir (karşılaştırma ve öneri).
- İdari raporları hazırlar.

### İnsan Kaynakları

- Çalışan izin talebini doğal dille alır; sistem formu doldurur; **yönetici onaylar; kayıt onayla oluşturulur.**
- Özlük dosyası güncelleme önerisi hazırlar; güncellemeyi yetkili onaylar (Resmi Kayıt, O-6).
- İşe giriş ve işten çıkış işlem taslaklarını hazırlar.
- Puantaj verisini toplar; bordro girdisi taslağı hazırlar.
- İş ilanı taslağı, oryantasyon planı ve İK raporları hazırlar.

### Enerji — Proje Geliştirme

- İzin, ruhsat ve proje süreçlerinin durumuna dair görüş sunar (süre takibi Ürün 2’dedir).
- Bütçe sapması raporunu hazırlar.
- Sapmanın kök nedenine dair detaylı görüş sunar.

### Enerji — O&M

- Arıza geçmişini gösterir ve yorumlar.
- Üretim performansını, emre amadeliği ve kayıp üretimi raporlar.
- Üretim kaybı ile arıza geçmişi arasındaki ilişkiye dair detaylı görüş sunar.

### Enerji — EPC

- Teklifleri karşılaştırır ve değerlendirir.
- Milestone durumuna dair görüş sunar; ilerleme raporu hazırlar.
- Hakedişe ve metraja destek verir (taslak ve kontrol önerisi).
- Toplantı tutanağı taslağı hazırlar.

### Enerji — Üretim/Piyasa

- Üretim verilerini toplar; PTF, YEKDEM, uzlaştırma ve gelir verilerini işler.
- Günlük, haftalık, aylık rapor hazırlar.
- Yıl sonu geliri gibi projeksiyonları hesaplama katmanında hesaplar; varsayımlar Kullanıcıdan alınır veya açıkça listelenir (T-4).
- “Hangi projede üretim sapması var, nedeni ne?” gibi sorulara detaylı görüş sunar.

