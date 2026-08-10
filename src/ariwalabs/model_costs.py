import os
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from adapters.models.errors import ModelConfigError

COST_QUANTUM = Decimal("0.00000001")
TOKEN_UNIT = Decimal(1000000)


@dataclass(frozen=True)
class ModelPrice:
    model: str
    input_per_1m: Decimal
    output_per_1m: Decimal
    currency: str = "USD"


class ModelCostEstimator:
    def __init__(self, prices: dict[str, ModelPrice]):
        self.prices = prices

    @classmethod
    def from_environment(
        cls,
        *,
        root: Path | None = None,
        env_file: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> "ModelCostEstimator":
        values = dict(os.environ if env is None else env)
        config_file = env_file
        if config_file is None and root is not None:
            config_file = root / ".env"
        if config_file is not None:
            values = {**_load_env_file(config_file), **values}
        return cls(prices=_prices_from_values(values))

    def estimate(
        self,
        *,
        model: str,
        tokens_in: int | None,
        tokens_out: int | None,
    ) -> dict[str, Any] | None:
        if tokens_in is None and tokens_out is None:
            return None
        price = self.prices.get(model)
        if price is None:
            return None
        input_tokens = tokens_in or 0
        output_tokens = tokens_out or 0
        input_cost = (Decimal(input_tokens) * price.input_per_1m / TOKEN_UNIT).quantize(
            COST_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
        output_cost = (Decimal(output_tokens) * price.output_per_1m / TOKEN_UNIT).quantize(
            COST_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
        total = (input_cost + output_cost).quantize(
            COST_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
        return {
            "currency": price.currency,
            "amount": float(total),
            "input_amount": float(input_cost),
            "output_amount": float(output_cost),
            "pricing_unit": "per_1m_tokens",
            "model": model,
            "source": "configured",
        }


def _prices_from_values(values: dict[str, str]) -> dict[str, ModelPrice]:
    currency = values.get("MODEL_COST_CURRENCY", "USD").strip() or "USD"
    prices: dict[str, ModelPrice] = {}
    for key, raw_value in values.items():
        if not key.startswith("MODEL_COST_") or not key.endswith("_INPUT_PER_1M"):
            continue
        slug = key.removeprefix("MODEL_COST_").removesuffix("_INPUT_PER_1M")
        output_key = f"MODEL_COST_{slug}_OUTPUT_PER_1M"
        output_raw_value = values.get(output_key, "")
        if not raw_value.strip() and not output_raw_value.strip():
            continue
        input_rate = _decimal_value(raw_value, key)
        output_rate = _decimal_value(output_raw_value, output_key)
        model = _model_from_slug(slug)
        prices[model] = ModelPrice(
            model=model,
            input_per_1m=input_rate,
            output_per_1m=output_rate,
            currency=currency,
        )
    return prices


def _model_from_slug(slug: str) -> str:
    parts = slug.lower().split("_")
    if len(parts) >= 4 and parts[0] == "gpt" and parts[1].isdigit() and parts[2].isdigit():
        suffix = "-".join(parts[3:])
        return f"gpt-{parts[1]}.{parts[2]}-{suffix}"
    return "-".join(parts)


def _decimal_value(raw_value: str, key: str) -> Decimal:
    if not raw_value.strip():
        msg = f"{key} es obligatorio para estimar costos"
        raise ModelConfigError(msg)
    try:
        value = Decimal(raw_value.strip())
    except InvalidOperation as exc:
        msg = f"{key} debe ser decimal"
        raise ModelConfigError(msg) from exc
    if value < 0:
        msg = f"{key} no puede ser negativo"
        raise ModelConfigError(msg)
    return value


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
