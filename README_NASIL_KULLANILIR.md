# Bu paket nasıl kullanılır

## İçerik
```
CLAUDE.md                          → repo köküne (Claude Code her oturumda okur)
docs/PHASES.md                     → 6 adım / 17 phase, kabul kriterleri, durum tablosu
docs/SPEC_01..06_*.md              → orijinal master prompt, bölünmüş + bugünkü kararlar işlenmiş
docs/reports/TEMPLATE.md           → her phase sonunda Claude Code'un dolduracağı rapor
docs/prompts/PHASE_0_1_PROMPT.md   → ilk oturum promptu
```
`docs/ARCHITECTURE.md` ve `docs/DOMAIN_MODEL.md` bu pakette YOK — onları Claude Code Phase 0.1'de yazacak.

## Kurulum (Proxmox dev VM)
1. Proxmox'ta VM: `company-ai-dev`, Ubuntu 24.04 Server, 4 çekirdek, 6 GB (RAM gelince 16 GB), 100 GB NVMe, ağ: LAN'da sabit IP.
2. VM içinde: Docker + compose plugin (resmi Docker apt deposu), git, make, unzip, gh, Node 20, Claude Code (docs.claude.com → Claude Code → Installation, Linux).
3. PC'den Windows Terminal ile `ssh <kullanıcı>@<vm-ip>`. Tüm komutlar VM'de.
4. GitHub'da private repo `company-ai`; VM'de `gh auth login`, `gh repo create company-ai --private --clone`.
5. Bu paketi VM'e kopyala (`scp company-ai-docs.zip <kullanıcı>@<vm-ip>:~`), repo köküne aç, commit + push.
6. `~/company-ai` içinde `claude`, plan modu, `docs/prompts/PHASE_0_1_PROMPT.md` içeriğini yapıştır.

## Döngü (her phase)
1. **Plan:** Claude Code planı yazar → planı Claude (chat) ile paylaş → düzeltmeler → Claude Code'a "onaylandı, uygula" de.
2. **Uygulama:** Claude Code kendi çalışır; test hataları, import hataları onun işi. Yalnızca `SORU:` ile sorduğu ürün/mimari kararlarını Claude (chat)'e taşı.
3. **Rapor:** `docs/reports/PHASE_NN_REPORT.md` dosyasını Claude (chat)'e yükle → kabul/düzeltme → sonraki phase'in promptunu Claude (chat) yazar.

Kural: ham log ve terminal çıktısı chat'e gelmez; rapor gelir.

## Prod'a geçiş
Phase 5.4'te: dev VM'i Proxmox'ta klonla (`company-ai-prod`), klonda `git clone`, `.env`'de `DATA_ROOT=/srv/company-ai`, `make up`, `make seed`. Adım 0–3 dev VM'de 6 GB ile yapılır; yalnızca embedding (Phase 3.4) 16 GB bekler.

Adım 2'de rakam onayı Naci'den (+ enerji finansı ekip arkadaşı) — Claude Code taslak üretir, onlar onaylar.

## Ledger onayı için hazırlık (Adım 2 öncesi)
Ankara RES: kapasite (ilk/güncel), türbin sayısı, capex, toplam borç + ECA/local payı, faiz/margin, tenor (ilk/güncel), grace, DSCR covenant (ilk/güncel), lisans tarihi, financial close, construction, COD (beklenen/gerçek). İzmir RES: hedef kapasite, önlisans/başvuru tarihi, ÇED başlangıç tarihi, tamamlanan/bekleyen adımlar. Claude Code makul taslak değerler önerecek; senin işin "gerçekçi mi" demek, sıfırdan yazmak değil.
