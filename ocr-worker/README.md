# ocr-worker

Phase 0.2'de doldurulacak: `ingestion_jobs` tablosunu poll eden, `ocrmypdf` + PyMuPDF ile sayfa metni çıkaran worker.
Şimdilik `infra/ocr-worker/Dockerfile` yer tutucudur ve `ocr` profili altındadır (`make up` başlatmaz).
