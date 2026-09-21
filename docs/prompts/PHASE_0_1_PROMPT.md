# Claude Code — Phase 0.1 başlangıç promptu

(Repo kökünde, CLAUDE.md ve docs/ yerleştirilip commit edildikten sonra, plan modunda, Opus ile.)

---

Bu repo Company AI V0 projesidir. Önce CLAUDE.md'yi, sonra docs/PHASES.md'yi, sonra docs/SPEC_01_urun_kapsam_altyapi.md ve docs/SPEC_02_dokuman_metadata_yetki_ux.md'yi oku. Diğer SPEC'lere ADR'ler için gerektikçe bak.

Görev: **Phase 0.1 — İskelet + ADR'ler** (Adım 0'ın ilk phase'i). Kabul kriterleri docs/PHASES.md'de; kelimesi kelimesine sağlanacak.

Şimdi KOD YAZMA. Plan yaz:
1. Oluşturacağın dizin ve dosyalar.
2. docs/ARCHITECTURE.md'ye yazacağın ADR başlıkları (≥ 10) ve her biri için bir cümlelik karar. `allowed_document_ids` sözleşmesi ve `DocumentStore` arayüzü ayrı ADR olsun.
3. docker-compose.yml: aktif servisler (postgres, backend) ve yer tutucular (ocr-worker, caddy, embed/profile full).
4. Makefile hedefleri.
5. Spec'te bulamadığın her şey — `SORU:` ile.

Planı yazıp dur. Onaydan sonra uygulayacaksın.

Hatırlatmalar:
- Stack ve V0-dışı listesi CLAUDE.md'de sabit; Paperless yok, Redis yok; alternatif önerme.
- Postgres image'ı pgvector içermeli.
- Bu VM'de 6 GB RAM var; embed servisi `full` profilinde, bu phase'de açılmaz.
- `DATA_ROOT` env ile dev/prod yol farkı; host'a özel hiçbir şey yok.
- Phase sonunda docs/reports/TEMPLATE.md'ye göre docs/reports/PHASE_0_1_REPORT.md, docs/PHASES.md durum tablosu, commit + `git tag phase-0-1`.
