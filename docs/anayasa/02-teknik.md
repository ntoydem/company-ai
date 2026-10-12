# BALBAL ANAYASASI — 02 TEKNİK VE GÜVENLİK MODÜLÜ

**Balbal Platformu \| Versiyon 2.1 \| Durum: Yürürlükte \| 09.10.2026 (onay 09.10.2026)**

**Kim okur (insan):** Backend, frontend ve AI katmanı geliştiricileri. Üretici AI için: Ç-17. Önce 00 Çekirdek okunmuş olmalıdır. **Ne düzenler:** Mimari, sorumluluk alanları, geliştirme akışı ve güvenlik kuralları.

## BÖLÜM I — MİMARİ

### T-1 — Ortak Teknik Omurga

Platform tek bir omurga üzerine kurulur: ortak backend, ortak frontend, ortak Kurumsal Hafıza, yetki katmanı, AI katmanı ve hesaplama katmanı. Ürün veya departman başına ayrı sistem kurulmaz.

### T-2 — Ürün Anahtarları

Ürünler aynı omurga üzerinde ürün anahtarlarıyla aktive edilir. Kapalı ürünün fonksiyonları **sunucu tarafında** çalıştırılmaz; arayüzde gizlemek tek başına yeterli değildir.

### T-3 — Ortak Hafıza

Departman başına bağımsız AI hafızaları oluşturulmaz. Tek bir Kurumsal Hafıza kullanılır; erişim yetki katmanıyla sınırlandırılır.

### T-4 — Hesaplama Katmanı

- AI metin üretimi ile matematiksel hesaplama ayrılır. Sayısal sonuç AI tarafından “tahmin edilerek” üretilmez; kontrol edilebilir bir hesaplama katmanında hesaplanır.
- Her hesaplama sonucu, kullandığı veri kaynaklarını, varsayımlarını ve yöntemini gösterebilir olmalıdır. Projeksiyonlarda (Ürün 3) varsayımlar Kullanıcıdan alınır veya sonuçla birlikte açıkça listelenir.

### T-5 — Yetki Kontrolü Önce Gelir

Yetki filtresi AI’dan **önce**, veri erişim katmanında uygulanır. Kullanıcının erişemediği veri AI’ın bağlamına (prompt, arama sonucu, hafıza) hiçbir şekilde girmez. Yetki kontrolünü AI’a bırakan tasarım yasaktır.

### T-6 — AI Sağlayıcısından Bağımsızlık

Platform belirli bir AI sağlayıcısına kalıcı olarak bağımlı tasarlanmaz; sağlayıcı ve model değiştirilebilir olmalıdır. Model ve araç isimleri anayasal sabit değildir. (Bu kural Balbal AI içindir; Üretici AI olarak hangi aracın kullanıldığı ürün tasarımını etkilemez.)

### T-7 — Kurulum Modelleri

| Model          | Belgeler / Sistem | AI               |
|----------------|-------------------|------------------|
| A — Tam Bulut  | Bulut             | Dış servis (API) |
| B — Karma      | Müşteri sunucusu  | Dış servis (API) |
| C — Tam Kapalı | Müşteri sunucusu  | Müşteri sunucusu |

B modelinde dış AI servisine yalnızca soruyu cevaplamak için gereken asgari bilgi gönderilir. C modelinde hiçbir veri müşteri ortamı dışına çıkmaz.

## BÖLÜM II — SORUMLULUK VE GELİŞTİRME AKIŞI

### T-8 — Ürün Sahipliği

Ürün mantığı, ürün davranışı, ürün/UI kararları, ürün testi ve ürün finalizasyonu **Ürün Yetkilisinin** sorumluluğundadır (Ç-1: devredilmemişse Proje Yetkilileri). Bu sorumluluk Anayasa değişikliği yetkisi değildir; değişiklik Ç-3’e tabidir.

### T-9 — Sorumluluk Alanları ve Plan Sunma

- Backend, frontend ve AI katmanı geliştiricileri kendi alanlarındaki koddan sorumludur.
- Hiçbir taraf (insan veya Üretici AI) başka bir tarafın alanındaki kodu **sessizce değiştirmez**; öneri yapar veya bildirir.
- Taraflar arası ihtiyaçlar yazılı not olarak iletilir. Notlar **mantığı açıklar**; uygulamanın nasıl kurgulanacağı ilgili *insan* tarafa bırakılır.
- **Talimat Alan bir Üretici AI ise:** uygulama kurgusu AI’ın takdirine bırakılmaz. Üretici AI, görev bir Kritik Geliştirme Kararı (Ç-15) içeriyorsa kodlamadan önce kısa bir plan (dokunulacak dosyalar, veri modeli etkisi, ürün etiketi, yeni bağımlılık var/yok) sunar ve Talimat Vericinin onayını bekler. İçermiyorsa doğrudan uygular ve Ç-16’ya uyar.

### T-10 — Belirsizlik (Uygulama)

Geliştirici veya Üretici AI ne yapılması gerektiğinden emin değilse Ç-9 ve Ç-15 uygulanır. Soru, Ç-9’daki muhataba, açıklayıcı bir notla ve bekleyen işin belirsiz olmayan kısmını bloklamayacak şekilde iletilir. Sorunun cevabı Kayıtlı Kanala işlenir ki aynı soru başka bir Üretici AI tarafından tekrar sorulmasın.

### T-11 — Ürüne Ait Olma Etiketi

Her yeni özellik, endpoint, ekran ve modül, ait olduğu ürünü (T0 / Ürün 1 / Ürün 2 / Ürün 3) kodda ve PR’da belirtir (Ü-1). Etiketsiz özellik birleştirilmez. Etiket, Ek-B’deki ilgili yetenek maddesine atıf yapar.

### T-12 — UI Geliştirme

Yeni bir görsel/UI öğesi doğrudan kodlanmaz. Önce tasarım ortamında \[Ek-E/2: ortam belirlenecek\] gösterilir, Ürün Yetkilisi onayından sonra kodlanır. Onaylı tasarımı birebir uygulayan kod değişikliği ayrıca onay gerektirmez.

### T-13 — Test ve Ürün Geçişi

- Kod testi teknik ekip tarafından yapılır. **Ürün testi** Ürün Yetkilisi tarafından yapılır.
- Kod testlerini geçmek ürünün tamamlandığı veya satılabilir olduğu anlamına gelmez; bir ürün ancak ürün testini geçtikten sonra finalize edilir.
- Geçiş sırası: T0 başarılı → Ürün 1 → Ürün 1 başarılı → Ürün 2 ve Ürün 3. Üst ürün geliştirilirken alt ürünün yetenekleri ve testleri korunur. Süreç: Ek-D S-9.
- **Ürün 2 ve Ürün 3 birlikte geliştirilir.** İkisinin tasarımı ve geliştirmesi tek bir uygulama olarak yürütülür; ürün ayrımı (ürün anahtarları, T-2) ve ürün testleri geliştirme tamamlandıktan sonra yapılır. Bu süreçte de her özellik ürün etiketi taşır (T-11); etiketi belirsiz olan özellik Ürün Yetkilisine sorulur.
- Ürün 1 ürün testi devam ederken Ürün 2 ve Ürün 3 tasarlanabilir. Ürün 2 ve Ürün 3 backend geliştirmesi, Ürün Yetkilisinin iş bazında Onay Kanıtıyla başlar. Hiçbir üst ürün, Ürün 1 ürün testini geçmeden finalize edilmez.

## BÖLÜM III — GÜVENLİK

### T-14 — Güvenlik Kuralları (Ç-11’in uygulaması)

- **Gizli bilgi:** Şifre, API anahtarı ve token koda veya repoya yazılmaz; ortam değişkeni veya gizli bilgi yöneticisi kullanılır. Yanlışlıkla yüklenen gizli bilgi derhal iptal edilip yenilenir. *Araçla zorlanır:* secret scanning.
- **Log:** Loglara şifre, token, belge içeriği veya gereksiz kişisel veri yazılmaz.
- **Müşteri izolasyonu:** Her sorgu ve her veri erişimi müşteri (tenant) kimliğiyle sınırlandırılır; müşteriler arası veri sızıntısı en ağır ihlal kabul edilir.
- **Prompt injection:** Belge ve Kullanıcı içeriği Balbal AI’a **veri** olarak verilir; sistem talimatlarıyla aynı seviyede verilmez (Ç-6).
- **Bağımlılıklar:** Yeni kütüphane, dış servis veya ağ bağlantısı Onay Kanıtı olmadan eklenmez (Ç-11/b).
- **AI yeteneği:** Balbal AI’a yeni araç, veri kaynağı veya otomatik işlem yeteneği verilmesi Ç-11’e tabidir.
- **Kod incelemesi:** Üretici AI’ın ürettiği kod insan incelemesinden geçmeden ana dala birleştirilmez. Ana dala doğrudan push yapılmaz. *Araçla zorlanır:* branch protection + zorunlu PR review.
- **Geri alınamaz işlemler:** Veri silme, geçmiş yeniden yazma (force push, reset) ve üretim ortamı değişiklikleri İnsan Onayı olmadan yapılmaz. *Araçla zorlanır:* force push kapalı.
- **Demo verisi:** Test ve demo ortamlarında yalnızca kurgusal veri kullanılır (Ç-12).

“Araçla zorlanır” notu taşıyan kurallar yalnızca AI’ın hatırlamasına bırakılmaz; repo ve ortam ayarlarıyla teknik olarak engellenir. Ayarın yapılmış olması Üretici Tarafların sorumluluğundadır. Ayrıntılı prosedürler ayrı Güvenlik Prosedürleri belgesindedir.

### T-15 — Anayasa İhlal Bildirim Formatı

Ç-10.1 kapsamındaki bildirimler, Kayıtlı Kanalda (GitHub issue veya PR yorumu) şu formatla yapılır:

    [ANAYASA İHLALİ]
    Anayasa versiyonu : (ör. v2.0)
    Madde             : (ör. Ü-4)
    Talimat           : (ihlale yol açan talimat veya kod)
    Aşılan sınır      : (kısa açıklama)
    Öneri             : (varsa uyumlu alternatif)
    Durum             : Geliştirme durduruldu / Kısmen devam ediyor
    Devam eden kısımlar : (ihlalsiz sayılan kısımlar açıkça listelenir)

Etiket: anayasa-ihlali. Talimat Verici bildirime yanıt vermeden ihlalli kısım birleştirilmez. “Yine de yap” yanıtı geçerli bir yanıt değildir (Ç-10.2).

### T-16 — Anayasanın Üretici AI’a Yüklenmesi

- Anayasa modülleri repoda ayrı Markdown dosyaları olarak tutulur (00-cekirdek.md, 01-urun.md, 02-teknik.md, 03-operasyon.md, ek-b.md, ek-d.md).
- 00 Çekirdek, Üretici AI aracının proje talimat dosyası (ör. CLAUDE.md veya eşdeğeri) üzerinden **her oturumda otomatik** yüklenir. “Her görevden önce Çekirdek okunur” kuralı AI’ın disipliniyle değil, bu konfigürasyonla sağlanır.
- Diğer modüller Ç-17’ye göre görev sırasında okunur.
- .docx sürümü insanlar için referans kopyadır; Üretici AI için bağlayıcı olan repodaki Markdown sürümüdür. İkisi arasında fark varsa Ek-C’deki son onaylı versiyon geçerlidir.

