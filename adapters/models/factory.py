import os
from dataclasses import dataclass
from pathlib import Path

from .base import ModelAdapter
from .errors import ModelConfigError

SUPPORTED_MODEL_PROVIDERS = ("fake", "openai")
DEFAULT_MODEL_PROVIDER = "fake"


@dataclass(frozen=True)
class ModelAdapterFactoryConfig:
    provider: str = DEFAULT_MODEL_PROVIDER

    def __post_init__(self) -> None:
        normalized_provider = self.provider.strip().lower() or DEFAULT_MODEL_PROVIDER
        object.__setattr__(self, "provider", normalized_provider)
        if normalized_provider not in SUPPORTED_MODEL_PROVIDERS:
            msg = f"MODEL_PROVIDER no soportado: {normalized_provider}"
            raise ModelConfigError(msg)

    @classmethod
    def from_environment(
        cls,
        *,
        root: Path | None = None,
        env_file: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> "ModelAdapterFactoryConfig":
        values = dict(os.environ if env is None else env)
        config_file = env_file
        if config_file is None and root is not None:
            config_file = root / ".env"
        if config_file is not None:
            values = {**_load_env_file(config_file), **values}
        return cls(provider=values.get("MODEL_PROVIDER", DEFAULT_MODEL_PROVIDER))


def create_model_adapter(
    *,
    root: Path | None = None,
    env_file: Path | None = None,
    env: dict[str, str] | None = None,
) -> ModelAdapter:
    config = ModelAdapterFactoryConfig.from_environment(
        root=root,
        env_file=env_file,
        env=env,
    )
    if config.provider == "fake":
        from .fake import FakeModelAdapter

        return FakeModelAdapter()
    if config.provider == "openai":
        from ariwalabs.model_costs import ModelCostEstimator

        from .openai import OpenAIModelAdapter, OpenAIModelConfig

        openai_config = OpenAIModelConfig.from_environment(
            root=root,
            env_file=env_file,
            env=env,
        )
        cost_estimator = ModelCostEstimator.from_environment(
            root=root,
            env_file=env_file,
            env=env,
        )
        return OpenAIModelAdapter(config=openai_config, cost_estimator=cost_estimator)
    msg = f"MODEL_PROVIDER no soportado: {config.provider}"
    raise ModelConfigError(msg)


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
