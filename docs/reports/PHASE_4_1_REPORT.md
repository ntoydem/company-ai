# Phase 4.1 Raporu — Eval runner (karne)

**Tarih:** 25.09.2026  **Model:** Sonnet 5  **Tag:** phase-4-1  **Commit:** (bu rapor commit'iyle aynı)

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den kelimesi kelimesine) | Durum | Kanıt (test adı / komut / çıktı) |
|---|---|---|---|
| 1 | `make eval MODEL=…` çalışır | ✅ | `make eval` (gemini-3.5-flash-lite) ve `make eval MODEL=gemini-3.5-flash` ikisi de uçtan uca çalıştı, `results.json`/`results.md` üretti, backend'i .env'deki modele geri döndürdü |
| 2 | isolation/hallucination/authorization %100 | ❌ | hallucination %100 (4/4), authorization %100 (3/3) — **isolation %50 (2/4)**. Bkz. §3 — iki isolation başarısızlığı da `forbidden_sources_hit` boş; gerçek bir proje karışması/yetki sızıntısı **yok**, aynı retrieval/refuse sorunu |
| 3 | document/temporal ≥ %80 | ❌ | document %52,2 (12/23), temporal %33,3 (3/9) — eşiğin altında. PHASES.md'nin kendi kuralı: "değilse Phase 3.2'ye dönülür" — bkz. §3/§7 |
| 4 | iki model karşılaştırma dosyası | ✅ | `seed_data/evaluation/results/gemini-3.5-flash-lite_2026-09-24/` ve `.../gemini-3.5-flash_2026-09-24/` (ikinci koşu Gemini ücretsiz katman kotasına takılıp yarıda kesildi — bu da anlamlı bir karşılaştırma sonucu, bkz. §4) |

**Sonuç:** eval runner'ın kendisi (kriter 1 ve 4) tam çalışıyor ve doğru puanlıyor; **ürünün** eval skoru (kriter 2/3) eşiğin altında. Bu, aracın hatası değil — aracın var olma sebebi tam olarak bunu ölçüp göstermek.

## 2. Yapılanlar
- `scripts/eval_lib.py`: saf puanlama mantığı — `questions.json` yükleme (`ledger_schema.QuestionSet`), `seed_data/documents/manifest.json`'dan `DocumentCatalog` (title/type/proje eşlemesi), ledger yolunu `facts.py::format_ledger_leaf` ile demo belgeye gömülen biçimde formatlayan `resolve_expected()`, kaynak (required/forbidden) kontrolü, `score_question()`, kategori eşiği + rapor toplama (`build_report`), markdown/JSON render.
- `scripts/run_eval.py`: CLI + HTTP katmanı — `ask_as_user` başına tek login/cookie oturumu, paylaşılan hız sınırlayıcı (Gemini ücretsiz katman), 503'te üstel geri çekilmeli yeniden deneme, 5 ardışık hatada güvenli durdurma.
- `seed_data/generator/facts.py`: `guess_field_kind()` ve `format_ledger_leaf()` — eval runner'ın demo belgelerdeki **aynı** biçimlendirmeyi (tarih GG.AA.YYYY, oran `1,20x`, para `50.400.000 EUR`) yeniden kullanması için iki küçük public fonksiyon.
- `infra/docker-compose.yml`: `backend.environment.LLM_MODEL_ANSWER: ${LLM_MODEL_ANSWER}` (env_file tek başına compose'un recreate kararını tetiklemiyor) + `backend.volumes`'a `./scripts:/app/scripts`.
- `Makefile`: `eval` hedefi — `MODEL=` verilirse backend'i o modelle `--wait` ile yeniden başlatır, eval'i koşar, **her koşulda** (başarı/başarısız) backend'i `.env`'deki modele geri döndürür (SORU 2, onaylandı).
- `backend/tests/test_eval_lib.py`: 28 test — gerçek `questions.json`/ledger/manifest üzerinde (43 sorunun tamamının `resolve_expected()`'dan hatasız geçtiğinin duman testi dahil) + el yapımı `Question`/`AskOutcome` fixture'larıyla puanlama kurallarının birim testleri.

## 3. Canlı eval sonucu ve kök neden analizi (gemini-3.5-flash-lite, `.env` varsayılanı, `EMBEDDINGS_ENABLED=false`)

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen |
|---|---|---|---|
| authorization | ≥%100 | ✅ %100,0 | 3/3 |
| hallucination | ≥%100 | ✅ %100,0 | 4/4 |
| isolation | ≥%100 | ❌ %50,0 | 2/4 |
| document | ≥%80 | ❌ %52,2 | 12/23 |
| temporal | ≥%80 | ❌ %33,3 | 3/9 |

**En önemli bulgu — güvenlik sınırı bozulmadı:** 43 sorunun **hiçbirinde** `forbidden_sources_hit` boş değil (sıfır proje-karışması/yetki-sızıntısı). Başarısızlıkların tamamı retrieval/cevap-üretim kalitesiyle ilgili, ADR-004'ün yetki sırası (authorization → allowed documents → retrieval → LLM) hiç bozulmadı. `isolation` kategorisindeki 2 başarısızlık (`ANK-ISO-002`, `ANK-ISO-003`) da bu türden — biri değer-metni eksikliği, diğeri aynı "bilgi bulamadım" reddi (aşağıda).

**document+temporal (32 soru) başarısızlık dağılımı** (birebir puanlama koduyla üretildi):
| Neden | Adet | Örnek |
|---|---|---|
| Doğru geçti | 15 | — |
| Yalnızca değer metni bulunamadı (kaynak/answered doğru) | 1 | `ANK-DEV-001` — model soruyu ("development süreci ne zaman başladı") yanlış anlayıp lisans onay tarihini yazmış |
| Yalnızca eksik kaynak (answered doğru) | 2 | `ANK-DEV-003`, `IZM-DEV-007` — cevap doğru ama beklenen ikinci kaynağı hiç göstermemiş |
| Model reddetti ("bilgi bulamadım"), retrieval **doğru belgeyi zaten bulmuştu** | 14 | `ANK-FIN-001..013`, `ANK-EPC-004`, `IZM-DEV-005/006` — hepsi finans (İngilizce) belgeler |

**Kök neden 1 — FTS: Türkçe soru ↔ İngilizce finans belgesi kelime uyumsuzluğu (Phase 3.2'de tek örnekle tespit edilmişti; bu koşu bunun sistemik olduğunu gösterdi).** Canlı doğrulama: "Ankara RES'in toplam finansman (kredi) tutarı nedir?" sorusu için üretilen FTS sorgusu (`Ankara OR RES OR toplam OR finansman OR kredi OR tutarı`) çalıştırıldığında, tutarın (`50,400,000 EUR`) yazılı olduğu **gerçek sayfa** (Facility Agreement, sayfa 4) ilk 25 sonuç arasında bile çıkmıyor — çünkü o sayfa İngilizce ("The total financial accommodation... is structured as 50,400,000 EUR") ve Türkçe sorgu kelimeleri ("finansman", "kredi", "tutarı") o sayfada hiç geçmiyor; yalnızca her belgede ortak olan "Ankara"/"RES" eşleşiyor, ki bu ayırt edici değil. `retrieved_document_ids` yine de doğru 4 Facility belgesini içeriyordu (belge-seviyesinde OR-FTS başka sayfalarından eşleşme bulmuş) ama **doğru sayfa** LLM'e giden top-20 chunk'ın içinde değildi.

**Kök neden 2 — cevap üretimi tutarsız (yeni bulgu, retrieval'dan bağımsız).** Aynı soru, aynı retrieval bağlamıyla elle tekrar denendiğinde (`Ankara RES'in toplam finansman (kredi) tutarı nedir?`, `finans` kullanıcısı) model bir seferinde doğru cevabı üretti (`"50.400.000 EUR ... [K8]"`, doğru sayfa 4'ü kaynak gösterdi), başka bir seferinde (eval koşusu sırasında) aynı soruyu reddetti. `LLMRequest.temperature=0.0` olmasına rağmen bu değişkenlik gözlendi — yani başarısızlıkların bir kısmı yalnızca "retrieval yanlış sayfayı getirdi" değil, modelin **sınırda kalan durumlarda tutarsız** karar vermesi (bazen yeterli görüp cevaplıyor, bazen aynı bağlamı yetersiz görüp reddediyor).

**Hibrit retrieval (embedding) denemesi — sonuç belirsiz, iyileştirme gösterilemedi.** Önceden başarısız olan 15 soru, `EMBEDDINGS_ENABLED=true` + tam backfill (86/86 chunk embed'li) ile tekrar koşuldu: **0/15 geçti** — aynı "bilgi bulamadım" reddi neredeyse tüm sorularda tekrarladı. Bu, Phase 3.4'ün tek örnekle gösterdiği "embedding düzeltir" bulgusunu bu daha büyük örneklemde **doğrulamadı** — ya kök neden 2 (üretim tutarsızlığı) burada da baskın çıktı, ya da hibrit RRF birleştirmesi bu spesifik sorularda FTS'in düşük sıralı sonuçlarını yeterince yukarı taşımadı. Kesin sonuç için Phase 3.2/3.4 kapsamında ayrı, kontrollü bir deney gerekir (bu fazın kapsamı değil — bkz. §7).

**Veri seti gözlemi (düzeltilmedi, Naci'nin gözden geçirmesi için not):** `ANK-ISO-002` ("Hangi projenin üretim lisansı var?") sorusunun `expected_answer`'ı bir **tarih**e (`timeline.licence.date`) işaret ediyor, ama soru aslında **hangi proje** olduğunu soruyor — model doğru cevabı ("Ankara RES projesinin üretim lisansı vardır") verdi ama beklenen tarih metinde yoktu, bu yüzden `value_check=fail` oldu. Bu `questions.json`'ın kendi içeriğinde bir yol/soru uyuşmazlığı, eval kodunda düzeltilmedi.

## 4. İki model karşılaştırması

| Model | Durum | document | temporal | Not |
|---|---|---|---|---|
| `gemini-3.5-flash-lite` (`.env` varsayılanı) | Tamamlandı | %52,2 (12/23) | %33,3 (3/9) | 0 istek hatası, 43/43 soru puanlandı |
| `gemini-3.5-flash` | **Yarıda kesildi** | %20,0 (1/5 değerlendirilen, 3 hata) | %50,0 (1/2 değerlendirilen, 2 hata) | 5 ardışık 503 sonrası güvenli durdurma tetiklendi ("günlük kota tükenmiş olabilir") |

`gemini-3.5-flash`, `gemini-3.5-flash-lite`'a göre bu hesapta çok daha hızlı hız-sınırına takıldı (art arda 503'ler, her biri 3 yeniden denemeden sonra tükendi). Bu koşuda **`gemini-3.5-flash-lite` gözle görülür şekilde daha güvenilir** — `.env`'in mevcut varsayılanının doğru seçim olduğunu doğruluyor. (Not: önceki bir oturumun hafıza notu "3.8-flash 503 veriyor, 3.5-flash kullan" diyordu — bu, sıra `3.8-flash` içindi; bu oturumda `3.5-flash`'ın kendisi de aynı sorunu yaşadı, muhtemelen hesabın o anki toplam kota/talep durumuna bağlı, kalıcı bir model özelliği değil.)

## 5. Testler
- Backend: 235 (Phase 3.4 sonu) + bu fazın 28'i (`test_eval_lib.py`) — toplam 263 geçti, 5 atlandı (canlı LLM), 0 kırmızı.
- ocr-worker: 9 geçti.
- `make lint`: backend (ruff+mypy), ocr-worker (ruff), frontend (eslint+tsc), ledger/document validator — hepsi temiz.
- Canlı: `make eval` (2 model), embedding karşılaştırma denemesi (15 soruluk alt küme), tüm 43 sorunun `resolve_expected()`'dan hatasız geçtiği duman testi.

## 6. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| `ANK-FIN-013` planımda "tek satırlık düzeltme" olarak onaylanmıştı — **uygulanmadı, gereksiz olduğu ortaya çıktı** | Yakından bakınca soru gerçekten iki değeri birlikte istiyor ("ilk ne kadardı, şimdi ne kadar?", `notes` alanı bunu doğruluyor) — ledger yolunun sözlüğe düşmesi bir hata değil, kasıtlıydı. `questions.json`'a dokunmak yerine `resolve_expected()`'a genel bir "`{initial,current}` sözlüğü → iki bağımsız değer grubu" kuralı eklendi | Veri değişmedi; kod daha genel (ileride benzer bir alan için de çalışır) |
| Para birimi için TR biçiminin yanına EN biçimi (virgüllü) de kabul edilen alternatif olarak eklendi | Canlı koşu bir örnekte (`ANK-FIN-011`) modelin kaynak belgedeki İngilizce virgüllü biçimi (`44,100,000 EUR`) hiç dönüştürmeden aktardığını gösterdi — bu bir anlam hatası değil, biçim tercihi | `document` skoru 1 soru daha doğru puanlandı (%47,8 → %52,2); orijinal koşunun `results.json/md`'si bu düzeltmeyle (yeniden LLM çağrısı yapılmadan, kayıtlı cevap metni üzerinden) yeniden üretildi |
| `make eval`'in ikinci `docker compose up` çağrısına `--wait` eklendi | İlk canlı `MODEL=` koşusunda backend "Started" ama henüz portu dinlemiyorken eval script'i bağlanmaya çalışıp `ConnectionRefused` aldı — plan bunu öngörmemişti | Model değişikliği artık backend gerçekten sağlıklı olana kadar bekleniyor |
| Değer kontrolü atlanan (liste/sözlük/negatif-gerçek/`DOC-*`) sorular nötr sayıldı (SORU 1, onaylandı) | Kaynak+`answered` zaten objektif, doğrulanabilir sinyal; değer metni kontrolü zorlanırsa yanlış-negatif riski var | Rapor bu soruları ayrı bölümde şeffaf listeliyor |
| `make eval MODEL=...` sonunda backend her zaman `.env`'deki modele geri döner (SORU 2, onaylandı) | `.env` "şu an ne çalışıyor" sorusunun tek doğruluk kaynağı kalsın | Başarısız koşularda da (ör. rate-limit'e takılan `gemini-3.5-flash` koşusu) geri dönüş gerçekleşti — doğrulandı |

## 7. Açık sorular (Naci cevaplamalı)
- **Phase 3.2'ye dönülsün mü, yoksa Phase 4.2'ye mi devam edilsin?** PHASES.md'nin kendi kuralı "değilse Phase 3.2'ye dönülür" diyor; §3'teki iki kök neden (FTS dil uyumsuzluğu, cevap üretimi tutarsızlığı) ikisi de Phase 3.2'nin (`answer_prompt.py`, retrieval) kapsamında. Embedding denemesi net bir çözüm göstermedi — bu da ayrı bir inceleme gerektirebilir.
- **Embedding'in gerçekten yardımcı olup olmadığı hâlâ belirsiz.** Phase 3.4'ün tek-örnek kanıtı ile bu fazın 15-örnek denemesi çelişiyor; kontrollü bir A/B (aynı sorular, embedding açık/kapalı, tekrarlı çalıştırma modelin kendi tutarsızlığını da hesaba katarak) ayrı bir çalışma gerektirir.
- `ANK-ISO-002`'nin `expected_answer` yolu düzeltilsin mi (§3, veri seti gözlemi)? Bu fazda dokunulmadı.

## 8. Riskler / sonraki phase için notlar
- **Güvenlik sınırı sağlam** (§3) — bu iyi haber, ama eval skorunun düşüklüğü ürünün "bulur, okur, aktarır" temel vaadini şu an tam karşılamadığı anlamına geliyor; Phase 4.2 (Excel) öncesi bu ele alınmalı.
- Cevap üretimindeki tutarsızlık (aynı soru/bağlam, farklı sonuç) yeni ve endişe verici bir bulgu — yalnızca retrieval'ı iyileştirmek yetmeyebilir; `answer_prompt.py`'nin rule 1/2 dengesi (ne zaman "yetersiz" denir) gözden geçirilmeli.
- Gemini ücretsiz katmanın günlük/anlık kota davranışı hesaba/ana bağlı görünüyor (`gemini-3.5-flash` bu oturumda hızla tükendi) — `run_eval.py`'nin güvenli-durdurma mekanizması (5 ardışık hata) tam olarak bunun için tasarlandı ve beklendiği gibi çalıştı.

## 9. Doğruladığım üçüncü taraf davranışları
- Docker Compose: bir servisin `environment:` bloğunda `${VAR}`, `--env-file`'dan gelen değeri parse-time'da alır; `env_file:` tek başına aynı değişkeni taşısa bile compose bunu "config değişti, recreate gerekir" kararı için **kullanmaz** — yalnızca `environment:`'taki açık `${VAR}` referansı buna sayılıyor. Canlı doğrulandı: `environment:` eklemeden önce `LLM_MODEL_ANSWER=X docker compose up -d backend` mevcut container'ı hiç değiştirmedi.
- `docker compose up -d --wait`, servisin healthcheck'i geçmesini bekliyor (varsayılan `up -d` yalnızca "Started" durumunu bekliyor, "Healthy"yi değil) — canlı doğrulandı (`--wait` eklenmeden önce gerçek bir `ConnectionRefused` yaşandı).

## 10. Kaynak kullanımı
- LLM: 2 model karşılaştırması toplam ~50 gerçek `/api/ask` çağrısı (43 + kısmi 5 + 15'lik embedding denemesi bir kısmı çakışıyor); token sayıları her sorunun kendi `results.json`'unda.
- `embed` servisi diagnostik amaçla tekrar açıldı (`make up-full`, ~10,5 GiB RAM, Phase 3.4'te ölçülen aynı seviye) ve rapor tamamlanmadan **kapatıldı** (`docker compose stop/rm embed`) — VM 16 GB'lık payını normal duruma (embed kapalı) döndürdü.
