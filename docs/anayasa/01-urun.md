# BALBAL ANAYASASI — 01 ÜRÜN MODÜLÜ

**Balbal Platformu \| Versiyon 2.1 \| Durum: Yürürlükte \| 09.10.2026 (onay 09.10.2026)**

**Kim okur (insan):** Ürün, frontend ve AI katmanı üzerinde çalışan herkes. Üretici AI için: Ç-17. Önce 00 Çekirdek okunmuş olmalıdır. **Ne düzenler:** Hangi yeteneğin hangi ürüne ait olduğunu ve her ürünün sınırlarını. Ayrıntılı yetenek listesi Ek-B’dedir.

### Ü-1 — Ürün Sınırı Kuralı

- Her özellik, fonksiyon, ekran ve API ucu **tek bir ürüne** aittir ve hangi ürüne ait olduğu kodda ve dokümanda belirtilir (T-11).
- Bir ürün, kendi sınırının üstündeki bir ürünün yeteneğini kullanamaz (ör. Ürün 1 Birleştirme yapamaz, Ürün 2 AI Yorumu üretemez).
- **Ek-B kapalı listedir.** Ek-B’de yer almayan bir yetenek hiçbir üründe geliştirilmez; eklenmesi Ç-3 kapsamında Anayasa değişikliğidir (Ç-11/a).
- Hangi ürüne ait olduğu belirsiz bir özellik geliştirilmez; Ürün Yetkilisine sorulur (Ç-9).

### Ü-2 — T0 / Kavramsal Test

T0, ürün geliştirmesine kaynak ayrılmadan önce yapılan kavramsal testtir: “AI birkaç belgeden anlamlı bilgi çekip doğru cevap verebiliyor mu?” T0 başarıyla geçilmeden Ürün 1’e kaynak ayrılmaz.

### Ü-3 — Ürün 1 / Tanıma — Kurumsal Bilgi ve Doküman Sistemi

**Yapabilir:**

- Şirketin departman ve rol yapısını kurar; yetkilendirme bu yapı üzerinden çalışır.
- Belgeleri toplar, sınıflandırır, indeksler, belgeler arasında ilişki kurar.
- Bilgiyi ve belgeyi bulur, okur ve yetkili Kullanıcıya gösterir.
- Birden çok kaynaktan beslenir ve **her kaynağın söylediğini ayrı ayrı, kaynağını göstererek** aktarır.
- Şirketin **iş akışlarını** (talep, onay, satın alma, ödeme talebi, masraf/avans, teslim, ödeme kaydı) şirketin tanımladığı adımlarla kayıt altına alır. Akışlar şirketin temel verisidir; Balbal AI belgeyi bildiği kadar, o belgenin hayatta nasıl uygulandığını da bu kayıtlardan bilir (O-13).
- Belgelerden **yükümlülükleri** çıkarır ve akış kayıtları, belgeler ve Kullanıcı Notları ile yükümlülükler arasında **bağ önerir**; bağ Kullanıcı onayıyla kesinleşir (O-13).
- Geçmiş kayıt ile Kullanıcı Notu ve Kullanıcı Yorumlarını (Ç-1) bulup gösterir.
- **Personel arası sohbet** sunar (Ü-7).

**Çok projeli sohbet (Ürün 1’de):** Kullanıcı tek bir Balbal AI sohbet penceresinde birden fazla proje hakkında soru sorabilir; her proje için ayrı sohbet açmak zorunlu değildir. Balbal AI her projeyle ilgili cevabı **o projenin kaynaklarıyla ayrı ayrı** verir. Örnek: “A projesinin teminat süresi ne, B projesinin teminat süresi ne?” → iki ayrı cevap, iki ayrı kaynak. “A ile B’nin teminat sürelerini karşılaştır” veya “hangisi daha uzun” → Ürün 1’de yapılmaz; Kullanıcıya bu işlemin aktif üründe yapılamadığı belirtilir (kapalı ürün tanıtılmaz, Ü-10).

**Sınır:** Tanır, bulur, gösterir. Birleştirme (Ç-1) yapmaz: kaynaklar veya projeler arasında tablo, ortak liste, karşılaştırma üretmez. AI Yorumu, hesaplama, tahmin ve projeksiyon yapmaz. Her cevap kaynağını gösterir.

### Ü-4 — Ürün 2 / Birleştirme — AI Destek Beyni

Ürün 1’in tüm yeteneklerini ve sınırlarını içerir. Ürün 1’de kurulan departman ve yetki yapısı içinde çalışır.

**Ek olarak yapabilir:**

- Farklı kaynaklardan ve **farklı projelerden** gelen Kesin Veriyi birleştirir, gruplar ve yan yana karşılaştırır. Proje kıyaslama burada başlar. Karşılaştırma *gösterir*, değerlendirmez (“hangisi daha iyi” demez — bu AI Yorumudur, Ürün 3).
- **Yalnızca gerçekleşmiş ve kesinleşmiş veri** üzerinde temel aritmetik yaptırır (toplam, ortalama, fark). Hesaplama hesaplama katmanında yapılır (T-4); sonuç gerekirse Excel tablosu olarak sunulur (Ç-7 etiket kuralı geçerlidir).
- Müşterinin **önceden tanımlı** Word/Excel şablonlarını gerçekleşmiş veriyle doldurur. Yeni şablon veya serbest rapor üretmez.
- **Veri taslağı** hazırlar: içeriği yalnızca Kesin Veri ve Kullanıcının verdiği bilgiden oluşan yazı taslağı (ör. “şu belgelerdeki tarihleri içeren bir bilgilendirme yazısı”). Kaynakta olmayan değerlendirme içeren taslak Ürün 3’tür.
- Eksik bilgi ve belgeyi gösterir.
- Akış içinde ilgili belge ve kayıtları yan yana gösteren **bulgular** sunar (ör. sözleşme kalemi ile talep tutarı); onay vermez, akışı durdurmaz.
- Yükümlülüğün durumunu ve son günden sapmayı bağlı olaylardan, gerçekleşmiş veriyle hesaplar (T-4). Sorulduğunda bir süreç adımına bağlı olayları tarih sırasıyla, kaynaklarıyla ve Kullanıcı Notlarını aynen aktararak sunar; neden-sonuç kurmaz.
- **Süre, deadline ve görev takibi ve hatırlatması** yapar. Takip edilen sürenin konusu (kredi, dava, bakım, sigorta, izin/ruhsat vb.) ürünü değiştirmez; takip ve hatırlatma her konuda Ürün 2 yeteneğidir. Sürenin *sonucuna dair değerlendirme* Ürün 3’tür.
- Birikmiş Kullanıcı Notu ve Yorumlarını derleyip gösterir.
- Departmanlar arası görüş talebi akışını sağlar; bu görüşler Kurumsal Hafızaya kaydedilir (O-7).

**Sınır:** AI Yorumu, görüş, tahmin ve projeksiyon üretmez. Karar vermez; insan onaylar.

### Ü-5 — Ürün 3 / Yorumlama — Departman Bazlı AI Araçları

Ürün 1 ve Ürün 2’nin tüm yeteneklerini içerir. Fonksiyonel anlamda departmanlara ayrılan tek üründür; her departmanın kendisine ait yetenekleri (skill, Ek-B) vardır.

**Yeteneklerin geliştirilmesi:** Departman yetenekleri **Üretici Taraflar tarafından** geliştirilir ve Ç-11’e göre eklenir. Balbal AI kendi yeteneklerini oluşturamaz, değiştiremez veya genişletemez (Ç-6). \[Ek-E/1: Müşterinin kendi departman yeteneğini tanımlayabilmesi ayrı bir ürün kararıdır; bu taslakta yoktur.\]

**Ek olarak yapabilir:** Analiz, AI Yorumu, sapma analizi, kök neden analizi, serbest raporlama, projeksiyon, değerlendirme içeren taslaklar.

**Departman araçları:** Proje Finans · Mali İşler · Hukuk · İdari İşler · İnsan Kaynakları · Enerji (Proje Geliştirme, O&M, EPC, Üretim/Piyasa).

**Sınır:** Her AI Yorumu ve projeksiyon “AI Yorumu / Projeksiyon” olarak etiketlenir, kaynaklarını ve varsayımlarını gösterir (Ç-7). Projeksiyonun sayısal kısmı hesaplama katmanında üretilir; varsayımlar Kullanıcı tarafından verilir veya açıkça listelenir (T-4). Resmi Kayıt oluşturmaz (O-6). Nihai karar insandadır.

### Ü-6 — Kümülatif Model

| Ürün   | İçerdiği yetenekler              | Temel sınır                                                                                       |
|--------|----------------------------------|---------------------------------------------------------------------------------------------------|
| T0     | Test                             | Kaynak ayrılmaz                                                                                   |
| Ürün 1 | Tanıma                           | Birleştirme, AI Yorumu ve hesaplama yok; projeler ayrı ayrı cevaplanır                            |
| Ürün 2 | Tanıma + Birleştirme             | AI Yorumu ve projeksiyon yok; aritmetik yalnızca gerçekleşmiş veriyle; proje kıyası burada başlar |
| Ürün 3 | Tanıma + Birleştirme + Yorumlama | AI Yorumu etiketlenir; Resmi Kayıt oluşturulmaz; karar insanda                                    |

Üst ürün alt ürünün fonksiyonlarını yeniden yazmaz; onların üzerine inşa edilir.

### Ü-7 — Balbal AI ve Personel Arası Sohbet

**7.1 Personel arası sohbet**

- Personel, Ürün 1’den itibaren birebir veya grup hâlinde kendi arasında sohbet edebilir.
- Balbal AI penceresi ile personel sohbet penceresi ayrı pencerelerdir ve arayüzde birbirine karışmaz.
- Yönetim ve Müşteri Sistem Yöneticisi, üyesi olmadıkları sohbetlerin içeriğini göremez.

**7.2 Ürün 1’de Balbal AI**

- Balbal AI personel arası sohbetlere dahil edilemez.
- Personel sohbetlerini okuyamaz, özetleyemez, cevaplayamaz ve sohbet içeriğini veri kaynağı olarak kullanamaz.

**7.3 Ürün 2 ve sonrasında Balbal AI**

Ürün 2’den itibaren bir Kullanıcı Balbal AI’ı bir sohbete açıkça ekleyebilir. Bu durumda:

- **Yalnızca çağrıldığında:** Balbal AI yalnızca eklendiği andan sonraki mesajları görür. Eklenmeden önceki mesajları okuyamaz.
- **Ortak yetki:** Balbal AI sohbette yalnızca **tüm katılımcıların** ortak olarak erişebildiği veriyle cevap verir (T-5, O-4).
- **Görünürlük:** Balbal AI’ın sohbette bulunduğu tüm katılımcılara açıkça gösterilir. Katılımcılar Balbal AI’ı sohbetten çıkarabilir.
- **Ürün sınırı:** Balbal AI sohbette de aktif ürünün sınırları içinde çalışır (Ü-4, Ü-5).
- **Hafıza:** Sohbet içeriği, bir Kullanıcı içeriği açıkça not olarak eklemediği sürece Kurumsal Hafızaya aktarılmaz (O-7).
- **KVKK:** Balbal AI’ın gördüğü mesajlar loglanıyorsa katılımcılar bilgilendirilir (O-8).
- **Kaynak sınırı:** Sohbet sırasında Balbal AI yalnızca Kurumsal Hafızadaki kayıtları (O-7) ve katılımcıların sohbette verdiği bilgiyi kullanır; Ek-B’deki yeteneklerinin dışına çıkmaz.

### Ü-8 — Sohbet ve Proje Yapısı

- Kullanıcının her soru için proje seçmesi zorunlu değildir; tek bir Balbal AI sohbetinde birden fazla projeden söz edilebilir (her üründe geçerli).
- Projeler varsayılan olarak **ayrı ayrı** değerlendirilir. Ürün 1’de projeler arası Birleştirme yapılmaz (Ü-3). Ürün 2’den itibaren Birleştirme yalnızca Kullanıcı açıkça istediğinde yapılır (Ü-4).

### Ü-9 — Kapsam

Balbal AI şirket arşivi ve iş süreçleriyle ilgili sorulara hizmet eder; iş dışındaki sorulara cevap vermez ve Kullanıcıyı kibarca kapsam içine yönlendirir.

### Ü-10 — Arayüz İlkeleri

- **Sadelik:** Ekranda yalnızca ilk bakışta görülmesi gerekenler bulunur; detay Balbal AI’a sorularak alınır.
- Her Kullanıcı yalnızca kendi departmanının arayüzünü görür.
- Kapalı ürünlerin arayüz öğeleri gösterilmez (T-2).
- Arayüzde gösterilen her belge referansı açılabilir/indirilebilir bir bağlantıdır.
- İç tasarım notları ve geliştirici açıklamaları müşteri arayüzüne konmaz.

### Ü-11 — Balbal AI İletişim Karakteri

- Balbal AI’ın iletişim karakteri Ek-F’de yazılı olarak tanımlanır. Ek-F’nin içeriği ürün davranışıdır ve Ürün Yetkilisi tarafından yazılır/güncellenir (T-8); Anayasa değişikliği gerektirmez. Ancak Ek-F’nin **çerçevesi** (aşağıdaki sınırlar) Anayasa maddesidir ve Ç-3’e tabidir.
- Ek-F yalnızca şunları düzenleyebilir: hitap ve ton, cevap uzunluğu, netleştirici soru sorma eşiği ve biçimi, “Veri Yok” durumunda yardım teklifinin kalıbı (Ç-7.1), iş dışı soruya yönlendirme cümlesi (Ü-9), departmana göre dil/terminoloji tercihleri.
- Ek-F şunları **düzenleyemez:** Ç-6 sınırları, Ç-7 durum etiketleri ve bildirim zorunluluğu, ürün sınırları (Ü-3…Ü-5), yetki kuralları (T-5, O-4), Kritik İşlem ve İnsan Onayı kuralları (O-6). Ek-F’de bu konulara dokunan bir satır varsa geçersizdir; Çekirdek geçerlidir (Ç-2).
- Ek-F’nin Balbal AI sistem promptuna işlenmesi bir Kritik Geliştirme Kararıdır (Ç-15/8); Üretici AI bunu Onay Kanıtı olmadan yapmaz.
- Ek-F’de yazmayan her iletişim davranışı için varsayılan: Ç-7.1’deki dört adım.

