# Tutarlılık ölçümü — gemini-3.5-flash-lite · embeddings=off · top_k=80

- **Retrieval kararlılığı** (hedef sayfa her tekrarda aynı şekilde girdi/girmedi): 6/6 (%100.0)
- **Model kararlılığı** (hedef sayfa prompt'tayken cevap verdi): 11/18 (%61.1)
- **Uçtan uca** (beklenen değer cevapta): 7/18 (%38.9)

| Soru | Tekrar | Hedef prompt'ta | Cevapladı | Değer doğru | Hata |
|---|---|---|---|---|---|
| ANK-DEV-004 | 1 | ✅ | ✅ | ✅ |  |
| ANK-DEV-004 | 2 | ✅ | ✅ | ✅ |  |
| ANK-DEV-004 | 3 | ✅ | ✅ | ✅ |  |
| ANK-FIN-005 | 1 | ✅ | ❌ | ❌ |  |
| ANK-FIN-005 | 2 | ✅ | ✅ | ✅ |  |
| ANK-FIN-005 | 3 | ✅ | ❌ | ❌ |  |
| ANK-FIN-010 | 1 | – | ✅ | – |  |
| ANK-FIN-010 | 2 | – | ✅ | – |  |
| ANK-FIN-010 | 3 | – | ✅ | – |  |
| IZM-DEV-003 | 1 | ✅ | ✅ | ❌ |  |
| IZM-DEV-003 | 2 | ✅ | ✅ | ❌ |  |
| IZM-DEV-003 | 3 | ✅ | ✅ | ❌ |  |
| IZM-DEV-004 | 1 | – | ❌ | – |  |
| IZM-DEV-004 | 2 | – | ❌ | – |  |
| IZM-DEV-004 | 3 | – | ❌ | – |  |
| ANK-ISO-002 | 1 | ✅ | ❌ | ❌ |  |
| ANK-ISO-002 | 2 | ✅ | ✅ | ✅ |  |
| ANK-ISO-002 | 3 | ✅ | ❌ | ❌ |  |
| ANK-ISO-003 | 1 | ✅ | ✅ | ✅ |  |
| ANK-ISO-003 | 2 | ✅ | ✅ | ❌ |  |
| ANK-ISO-003 | 3 | ✅ | ✅ | ✅ |  |
| IZM-DEV-011 | 1 | ✅ | ❌ | ❌ |  |
| IZM-DEV-011 | 2 | ✅ | ❌ | ❌ |  |
| IZM-DEV-011 | 3 | ✅ | ❌ | ❌ |  |
