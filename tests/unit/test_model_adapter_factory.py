from pathlib import Path

from adapters.models.errors import ModelConfigError
from adapters.models.factory import ModelAdapterFactoryConfig, create_model_adapter
from adapters.models.fake import FakeModelAdapter
from adapters.models.openai import OpenAIModelAdapter


def test_factory_defaults_to_fake_adapter() -> None:
    adapter = create_model_adapter(env={})

    assert isinstance(adapter, FakeModelAdapter)


def test_factory_reads_provider_from_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        (
            "MODEL_PROVIDER=openai\n"
            "OPENAI_API_KEY=test-key\n"
            "OPENAI_DEFAULT_MODEL=gpt-test"
        ),
        encoding="utf-8",
    )

    adapter = create_model_adapter(env_file=env_file, env={})

    assert isinstance(adapter, OpenAIModelAdapter)
    assert adapter.config.model_for_profile("generation") == "gpt-test"


def test_factory_rejects_unknown_provider() -> None:
    try:
        ModelAdapterFactoryConfig.from_environment(env={"MODEL_PROVIDER": "unknown"})
    except ModelConfigError as exc:
        assert "MODEL_PROVIDER no soportado" in str(exc)
    else:
        raise AssertionError("provider desconocido debio fallar")


def test_factory_preserves_environment_precedence_over_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("MODEL_PROVIDER=openai\n", encoding="utf-8")

    adapter = create_model_adapter(
        env_file=env_file,
        env={"MODEL_PROVIDER": "fake"},
    )

    assert isinstance(adapter, FakeModelAdapter)
