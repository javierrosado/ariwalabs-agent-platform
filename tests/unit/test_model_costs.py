from decimal import Decimal
from pathlib import Path

from adapters.models.errors import ModelConfigError
from ariwalabs.model_costs import ModelCostEstimator, ModelPrice


def test_model_cost_estimator_calculates_input_and_output_cost() -> None:
    estimator = ModelCostEstimator(
        prices={
            "gpt-test": ModelPrice(
                model="gpt-test",
                input_per_1m=Decimal("2.00"),
                output_per_1m=Decimal("12.00"),
            ),
        },
    )

    estimate = estimator.estimate(model="gpt-test", tokens_in=1000, tokens_out=500)

    assert estimate == {
        "currency": "USD",
        "amount": 0.008,
        "input_amount": 0.002,
        "output_amount": 0.006,
        "pricing_unit": "per_1m_tokens",
        "model": "gpt-test",
        "source": "configured",
    }


def test_model_cost_estimator_returns_none_without_configured_price() -> None:
    estimator = ModelCostEstimator(prices={})

    assert estimator.estimate(model="gpt-test", tokens_in=1000, tokens_out=500) is None


def test_model_cost_estimator_loads_prices_from_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        (
            "MODEL_COST_CURRENCY=USD\n"
            "MODEL_COST_GPT_5_6_LUNA_INPUT_PER_1M=0.20\n"
            "MODEL_COST_GPT_5_6_LUNA_OUTPUT_PER_1M=1.20\n"
        ),
        encoding="utf-8",
    )

    estimator = ModelCostEstimator.from_environment(env_file=env_file, env={})
    estimate = estimator.estimate(
        model="gpt-5.6-luna",
        tokens_in=1000000,
        tokens_out=1000000,
    )

    assert estimate is not None
    assert estimate["amount"] == 1.4
    assert estimate["currency"] == "USD"


def test_model_cost_estimator_ignores_empty_price_placeholders() -> None:
    estimator = ModelCostEstimator.from_environment(
        env={
            "MODEL_COST_GPT_5_6_LUNA_INPUT_PER_1M": "",
            "MODEL_COST_GPT_5_6_LUNA_OUTPUT_PER_1M": "",
        },
    )

    assert estimator.prices == {}


def test_model_cost_estimator_rejects_partial_price_config() -> None:
    try:
        ModelCostEstimator.from_environment(
            env={
                "MODEL_COST_GPT_5_6_LUNA_INPUT_PER_1M": "0.20",
                "MODEL_COST_GPT_5_6_LUNA_OUTPUT_PER_1M": "",
            },
        )
    except ModelConfigError as exc:
        assert "OUTPUT_PER_1M es obligatorio" in str(exc)
    else:
        raise AssertionError("tarifa parcial debio fallar")
