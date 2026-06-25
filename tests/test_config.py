from pathlib import Path

from utils.config import AppConfig, load_env


def test_load_env_uses_dotenv_file(tmp_path, monkeypatch):
    monkeypatch.delenv("TOP_N", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("TOP_N=7\nYFINANCE_FALLBACK=true\n")

    values = load_env(env_path)

    assert values["TOP_N"] == "7"
    assert values["YFINANCE_FALLBACK"] == "true"


def test_process_environment_overrides_dotenv(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("TOP_N=7\nDEEPSEEK_API_KEY=from-file\nYFINANCE_FALLBACK=false\n")
    monkeypatch.setenv("TOP_N", "9")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "from-process")
    monkeypatch.setenv("YFINANCE_FALLBACK", "true")

    config = AppConfig.from_env(Path(env_path))

    assert config.top_n == 9
    assert config.deepseek_api_key == "from-process"
    assert config.yfinance_fallback is True
