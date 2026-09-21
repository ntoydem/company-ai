from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_data_directories_derive_from_app_data_dir(settings: Settings) -> None:
    assert settings.documents_dir == settings.app_data_dir / "documents"
    assert settings.excel_dir == settings.app_data_dir / "excel"
    assert settings.app_state_dir == settings.app_data_dir / "app-data"
    assert settings.app_data_dir == Path("/data")


def test_database_url_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_secrets_are_not_exposed_in_repr(settings: Settings) -> None:
    plain = settings.admin_password.get_secret_value()
    assert plain
    assert plain not in repr(settings)
    assert plain not in str(settings.admin_password)


def test_demo_today_is_fixed_date(settings: Settings) -> None:
    assert settings.demo_today.isoformat() == "2026-09-15"
