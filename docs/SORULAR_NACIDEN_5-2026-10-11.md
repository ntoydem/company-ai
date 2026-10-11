# Sorular — Naci'den, 5. tur (11.10.2026)

Demo kütüphanesi için eksik/çelişkili bir değer. Gerçek olması şart değil, tutarlı olması
yeter. **Boş bırakırsan (A) ile, AI_ASSUMPTION etiketiyle ilerleriz** — cevapsız kalması
süreci durdurmaz, yalnız bu değerin kökenini (gerçek bilgi mi, varsayım mı) değiştirir ve
raporda işaretlenir.

| Kod | Proje | Soru | Cevap |
|---|---|---|---|
| T-13.1 | Yeşilova | Özkaynak (24.048.000 USD) + 2023-YS kredisi (2.352.000 USD) = capex (26.400.000 USD). Bu aritmetik, "santral özkaynakla inşa edildi" ifadesiyle çelişiyor — hangisi doğru? **(A)** Santral 26,4 mn USD'lik toplam yatırımla, baştan özkaynakla kuruldu; 2023'te alınan 2,352 mn USD'lik kredi bu özkaynağın bir kısmını SPV'ye geri çevirdi (kredi çekildikten sonra net özkaynak kalan 24,048 mn USD). **(B)** Kredi baştan beri inşaatın 2,352 mn USD'lik kısmını finanse etti — "sonradan alınmış" değil, inşaat kredisinin bir parçasıydı. || **A.** Santral iki fazda sponsor fonuyla kuruldu: Faz 1 12 MWe, COD 28.12.2016, YEKDEM 2017–2026; Faz 2 +10 MWe, COD 15.11.2022, PTF. Capex 26,4 mn iki fazın toplamı. 2023-YS (03.06.2023) inşaat kredisi değil; sponsor fonunun 2,352 mn'ını geri ödedi. Net sponsor katkısı 24,048 mn; etiketi "net sponsor katkısı (kredi sonrası)". Kredi sözleşmesinde inşaat CP'si yok. Kurallar: NACI_CEVAP_2026-10-11 §2 (PR #21). |
| T-13.2.1 | Karatepe | DOC-ANK-DEV-006 (Saha Kullanım Hakkı Sözleşmesi) — sahayı kullanım hakkı veren karşı taraf kim (arazi sahibi, kamu kurumu, vb.)? Boş bırakılırsa metin karşı taraf adı olmadan kalır (AI_ASSUMPTION ile isim UYDURULMAZ). | |
| T-13.2.2 | Kızılova | DOC-IZM-LEG-002 (Kira/İrtifak Hakkı Sözleşmesi Taslağı) — kira/irtifak hakkını veren karşı taraf kim? Boş bırakılırsa metin karşı taraf adı olmadan kalır (AI_ASSUMPTION ile isim UYDURULMAZ). | |

**Cevaplandı — Tansu (ürün sahibi), 11.10.2026 (T-13.1).** Ürün sahibi onaylı; `AI_ASSUMPTION` gerekmez.
