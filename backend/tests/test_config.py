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


def test_jwt_secret_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_demo_user_password_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEMO_USER_PASSWORD", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_secrets_are_not_exposed_in_repr(settings: Settings) -> None:
    plain = settings.admin_password.get_secret_value()
    assert plain
    assert plain not in repr(settings)
    assert plain not in str(settings.admin_password)


def test_demo_today_is_fixed_date(settings: Settings) -> None:
    assert settings.demo_today.isoformat() == "2026-09-15"


def test_demo_mode_defaults_on_with_istanbul_as_the_real_calendar_timezone(
    settings: Settings,
) -> None:
    """ADR-026: rollback to the real calendar is this one flag; the demo default must
    never need a second change to go live."""
    assert settings.demo_mode_enabled is True
    assert settings.company_timezone == "Europe/Istanbul"


def test_documented_demo_mode_env_name_is_honoured(monkeypatch: pytest.MonkeyPatch) -> None:
    """`.env.example` says `DEMO_MODE=false` is the rollback switch — without the alias
    pydantic-settings looked for DEMO_MODE_ENABLED and silently kept the demo default
    (found live on 05.10.2026 during the ADR-027 rollback rehearsal)."""
    monkeypatch.setenv("DEMO_MODE", "false")
    assert Settings(_env_file=None).demo_mode_enabled is False  # type: ignore[call-arg]
    monkeypatch.delenv("DEMO_MODE")
    monkeypatch.setenv("DEMO_MODE_ENABLED", "false")
    assert Settings(_env_file=None).demo_mode_enabled is False  # type: ignore[call-arg]
