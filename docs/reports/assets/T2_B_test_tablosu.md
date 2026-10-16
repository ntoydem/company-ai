# T2 — B: Ortam bağımlı testlerin gerçek listesi (16.10.2026 koşusu)

`make test` canlı `.env` ile (özel bayrak yok, `EK_F_MODE=true`), değişiklik öncesi, `logs/t2_before.log`: **27 failed + 1 error = 28** (759 passed, 15 deselected). Tek sorumlu ayar: `settings.ek_f_enabled` (env `EK_F_MODE`) — her satır doğrudan `ek_f_enabled`'i okuyan bir render/format dalına giriyor (`ask.py`'de ~10 dal, `excel_ask.py`'de `format_value(..., ek_f=...)`), ya da `assist_computations` (`assist_mode_enabled or ek_f_enabled`) üzerinden dolaylı. `ASSIST_MODE` ve `ANSWER_THINKING` şu an canlıda dokümante varsayılanla eşleşiyor (`ASSIST_MODE=false`) ya da ilgili test kendi başına `model_copy` ile pinliyor (`ANSWER_THINKING=true` için `test_ask.py::test_answer_thinking_setting_shapes_only_the_answer_call`) — bu ikisinin hiçbiri 28'in nedeni değil, ek pinleme gerekmedi.

| # | Dosya | Test | Tür |
|---|---|---|---|
| 1 | test_ask.py | test_empty_gate_means_no_llm_call | FAILED |
| 2 | test_ask.py | test_no_chunks_means_no_llm_call_and_zero_tokens | FAILED |
| 3 | test_ask.py | test_no_answer_reply_is_canonicalized | FAILED |
| 4 | test_ask.py | test_employee_ask_outside_department_returns_no_answer_with_empty_retrieved | FAILED |
| 5 | test_ask.py | test_audit_log_written_when_no_chunks_retrieved | FAILED |
| 6 | test_ask.py | test_legacy_project_id_is_ignored_not_rejected | FAILED |
| 7 | test_ask_router.py | test_budget_variance_with_reason_only_from_documents | FAILED |
| 8 | test_ask_router.py | test_mixed_with_nothing_on_either_side_keeps_both_fixed_texts | FAILED |
| 9 | test_ask_router.py | test_data_miss_without_documents_is_the_plain_no_answer | FAILED |
| 10 | test_ask_router.py | test_insufficient_data_when_documents_were_retrieved_but_the_model_declined | FAILED |
| 11 | test_ask_router.py | test_ambiguous_excel_result_is_insufficient_data_with_the_tried_ranges | FAILED |
| 12 | test_assist.py | test_flag_off_keeps_todays_contract | FAILED |
| 13 | test_assist.py | test_zero_chunks_clarify_without_any_llm_call | FAILED |
| 14 | test_assist.py | test_insufficient_keeps_a_valid_model_question_and_lists_retrieved_documents | FAILED |
| 15 | test_assist_discovery.py | test_existence_question_lists_the_workbook_when_the_model_declines | FAILED |
| 16 | test_assist_discovery.py | test_hidden_workbook_is_never_named | FAILED |
| 17 | test_assist_ekf.py | test_flag_off_keeps_the_fixed_sentence_and_no_groups | FAILED |
| 18 | test_assist_ekf.py | test_flag_off_value_question_with_a_model_question_is_byte_identical | FAILED |
| 19 | test_assist_ekf.py | test_ambiguous_excel_result_without_the_flag_is_the_s0a_text | FAILED |
| 20 | test_document_review.py | test_employee_upload_is_pending_and_hidden_from_everyone_but_the_handlers | FAILED |
| 21 | test_excel_api.py | test_table_result_triggers_one_replan_with_feedback_and_no_table_to_the_model | FAILED |
| 22 | test_pending_documents.py | test_flag_off_carries_nothing_even_with_a_matching_processing_document | FAILED |
| 23 | test_pending_documents.py | test_question_naming_a_processing_document_gets_state_a_without_an_llm_call | FAILED |
| 24 | test_pending_documents.py | test_unreadable_matching_document_gets_state_b_with_the_turkish_reason | FAILED |
| 25 | test_pending_documents.py | test_mixed_no_answer_keeps_the_fixed_sentence_inside_and_adds_the_notice | FAILED |
| 26 | test_route_without_llm.py | test_unknown_project_makes_no_llm_call_at_all[assist_only] | FAILED |
| 27 | test_route_without_llm.py | test_existence_question_with_every_flag_off_is_the_fixed_sentence_alone | FAILED |
| 28 | test_route_without_llm.py | test_existence_question_without_ek_f_keeps_the_fixed_sentence_and_the_assist_block | ERROR (fixture `assist_only`'nin kendi `assert settings.ek_f_enabled is False` kurulumu) |

Not: 14.10.2026 S2c raporunun "25" sayımı bu koşuda 28'e çıkmış (kod 14.10→16.10 arası evrildi — `test_ask.py::test_legacy_project_id_is_ignored_not_rejected` ve `test_document_review.py::test_employee_upload_is_pending_and_hidden_from_everyone_but_the_handlers` S2c'de yoktu); bu yüzden emir "önce listele" dedi — tahmini sayı yerine gerçek koşu esas alındı.

## Çözüm ve doğrulama

`backend/tests/conftest.py`'ye tek bir autouse fixture (`_pin_ek_f_default`) eklendi: her testten önce `monkeypatch.setattr(get_settings(), "ek_f_enabled", False)`. pytest aynı scope'ta autouse fixture'ları, testin açıkça istediği fixture'lardan (`ek_f_on`, `ek_f_off`, `assist_only` vb.) önce kurduğu için, bir test kendi bayrağını açarsa bu sonradan kazanır — "kendi bayrağını set eden testi bozma" kısıtı kod yazılmadan sağlanıyor.

| Koşu | Sonuç |
|---|---|
| Önce (canlı `.env`, bayraksız) | 27 failed, 1 error, 759 passed, 15 deselected (`logs/t2_before.log`) |
| Sonra (canlı `.env`, bayraksız, fixture + is_active filtresi + 1 yeni birim test) | **788 passed, 15 deselected** (`logs/t2_clean_final.log`) |
| Eski yöntem (`-e EK_F_MODE=false`) — regresyon kontrolü | **788 passed, 15 deselected**, aynı (`logs/t2_old_method.log`) |
| `make lint` | yeşil (ruff, ruff format, mypy 126 dosya, ocr-worker lint, ledger/doküman/excel doğrulamaları) — `logs/t2_lint.log` |
| ocr-worker | 18/18 (`make test`'in üçüncü adımı, her koşuda) |

Üretim koduna, `compose`/`.env` dosyalarına dokunulmadı — yalnız `backend/tests/conftest.py` (+ `is_active` filtresi ve birim testi, bkz. ana rapor A bölümü).
